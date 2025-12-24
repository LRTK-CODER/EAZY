import asyncio
import threading
from typing import Optional
from mitmproxy import http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
import structlog
from app.services.semantic_parser import SemanticParser
from app.core.connection_manager import manager
from playwright.async_api import async_playwright
import psutil

logger = structlog.get_logger()

class ProxyAddon:
    """
    Mitmproxy Addon to intercept requests and responses.
    Initialized with the main event loop to allow thread-safe broadcasting.
    """
    def __init__(self, main_loop: asyncio.AbstractEventLoop, target_id: Optional[int] = None):
        self.parser = SemanticParser()
        self.main_loop = main_loop
        self.target_id = target_id

    def response(self, flow: http.HTTPFlow):
        """
        Hook for HTTP responses. Captures data and broadcasts it via WebSocket.
        Running in mitmproxy's thread, so it schedules broadcast on the main loop.
        """
        try:
            # Extract request details
            url = flow.request.pretty_url
            method = flow.request.method
            req_headers = {k.lower(): v for k, v in flow.request.headers.items()}
            req_body = flow.request.content.decode('utf-8', 'ignore') if flow.request.content else None
            
            # Extract response details
            status_code = flow.response.status_code
            res_headers = {k.lower(): v for k, v in flow.response.headers.items()}
            
            # Semantic Analysis
            parsed = self.parser.parse_request(method, url, req_headers, req_body)
            
            # Prepare Event Data
            event_data = {
                "type": "proxy_packet",
                "data": {
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "request": {
                        "headers": req_headers,
                        "body": req_body
                    },
                    "response": {
                        "headers": res_headers,
                        "status": status_code
                    },
                    "analysis": parsed
                }
            }
            
            # Thread-safe broadcast
            if self.main_loop and not self.main_loop.is_closed():
                asyncio.run_coroutine_threadsafe(manager.broadcast(event_data), self.main_loop)
                
                # Persist to DB using TrafficService
                from app.services.traffic_service import traffic_service
                from app.models.traffic_log import TrafficSource
                import urllib.parse
                
                parsed_url = urllib.parse.urlparse(url)
                
                if self.target_id:
                    asyncio.run_coroutine_threadsafe(
                        traffic_service.save_traffic(
                            target_id=self.target_id,
                        method=method,
                        url=url,
                        host=parsed_url.netloc,
                        path=parsed_url.path,
                        request_headers=req_headers,
                        request_body=req_body,
                        response_headers=res_headers,
                        response_body=flow.response.content.decode('utf-8', 'ignore') if flow.response.content else None,
                        status_code=status_code,
                        source=TrafficSource.PASSIVE
                    ),
                    self.main_loop
                )
            
        except Exception as e:
            logger.error("proxy.addon_error", error=str(e))

class ProxyService:
    _instance = None
    _master: Optional[DumpMaster] = None
    _thread: Optional[threading.Thread] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _main_loop: Optional[asyncio.AbstractEventLoop] = None
    _browser_instance = None
    _playwright_instance = None
    _target_id: Optional[int] = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProxyService, cls).__new__(cls)
        return cls._instance
    
    def set_main_loop(self, loop):
        self._main_loop = loop

    def start(self, port: int = 8081, target_id: Optional[int] = None):
        if target_id:
            self._target_id = target_id

        if self._thread and self._thread.is_alive():
            logger.warning("proxy.already_running")
            return

        if not self._main_loop:
             logger.warning("proxy.main_loop_missing", msg="Call set_main_loop() before starting proxy to enable WS stats")

        logger.info("proxy.starting", port=port)
        
        def run_proxy():
            # Create a new event loop for this thread (mitmproxy needs it)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop

            async def start_master():
                opts = Options(listen_host='0.0.0.0', listen_port=port)
                self._master = DumpMaster(opts, with_termlog=False, with_dumper=False)
                
                # Verify main_loop is available before init addon
                current_main_loop = self._main_loop
                if not current_main_loop:
                     logger.warning("proxy.addon_init_warning", msg="Main loop not set, WS broadcast will fail")

                # Pass main_loop to Addon
                addon = ProxyAddon(main_loop=current_main_loop, target_id=self._target_id)
                self._master.addons.add(addon)
                
                await self._master.run()

            try:
                loop.run_until_complete(start_master())
            except Exception as e:
                logger.error("proxy.thread_error", error=str(e))
            finally:
                loop.close()

        self._thread = threading.Thread(target=run_proxy, daemon=True)
        self._thread.start()

        # Wait for port to be listening
        import socket
        import time
        
        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                with socket.create_connection(("localhost", port), timeout=0.1):
                    logger.info("proxy.port_ready", port=port)
                    break
            except (OSError, ConnectionRefusedError):
                time.sleep(0.1)
        else:
            logger.warning("proxy.port_timeout", port=port)
              
        logger.info("proxy.started")

    def stop(self):
        """
        Stops the proxy master and thread.
        """
        if self._master:
            self._master.shutdown()
            self._master = None
            
        if self._loop:
            # Loop is running in thread. Shutdown master should stop it.
            pass

        if self._thread and self._thread.is_alive():
            # self._thread.join() # Don't block main thread
            pass
            
        logger.info("proxy.shutdown_requested")

    async def stop_with_browser(self):
        """
        Async stop method to handle browser cleanup.
        """
        self.stop()
        await self.stop_browser()

    def _on_browser_disconnected(self, browser):
        logger.info("proxy.browser.disconnected_event")
        self._browser_instance = None
        self._playwright_instance = None

    def _kill_browser_processes(self):
        """
        Kills any Chrome/Chromium processes running with the specific proxy argument.
        """
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if not cmdline:
                        continue
                        
                    if any('localhost:8081' in arg for arg in cmdline):
                        logger.info("proxy.force_kill_psutil", pid=proc.pid, name=proc.info['name'])
                        proc.kill()
                        killed_count += 1
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if killed_count > 0:
                self._browser_instance = None
                self._playwright_instance = None
                    
        except ImportError:
            logger.error("proxy.cleanup_error", error="psutil not installed")
        except Exception as e:
            logger.warning("proxy.cleanup_error", error=str(e))

    async def launch_browser(self, target_url: str, proxy_port: int = 8081, target_id: Optional[int] = None):
        """
        Launches a headful browser configured to use the proxy.
        """
        if self._browser_instance:
            if not self._browser_instance.is_connected():
                self._browser_instance = None
            else:
                logger.info("proxy.browser.already_running")
                return

        if not (self._thread and self._thread.is_alive()):
            logger.info("proxy.auto_starting_for_browser")
            self.start(proxy_port, target_id=target_id)
            await asyncio.sleep(1) 


        try:
            logger.info("proxy.browser.launching", url=target_url)
            self._playwright_instance = await async_playwright().start()
            
            self._browser_instance = await self._playwright_instance.chromium.launch(
                headless=False, 
                proxy={"server": f"http://localhost:{proxy_port}"},
                args=["--ignore-certificate-errors", "--no-sandbox"]
            )
            
            self._browser_instance.on("disconnected", lambda b: self._on_browser_disconnected(b))
            
            context = await self._browser_instance.new_context(ignore_https_errors=True)
            page = await context.new_page()
            
            logger.info("proxy.browser.navigating", url=target_url)
            try:
                await page.goto(target_url, timeout=30000)
                logger.info("proxy.browser.started")
            except Exception as nav_e:
                logger.warning("proxy.browser.navigation_failed", error=str(nav_e))
            
        except Exception as e:
            logger.error("proxy.browser.failed", error=str(e))
            if not self._browser_instance:
                 await self.stop_browser()
            raise e

    async def stop_browser(self):
        if self._browser_instance:
            try:
                await self._browser_instance.close()
            except Exception as e:
                logger.warning("proxy.browser.close_failed", error=str(e))
            finally:
                self._browser_instance = None
        
        if self._playwright_instance:
            try:
                await self._playwright_instance.stop()
            except Exception as e:
                logger.warning("proxy.playwright.stop_failed", error=str(e))
            finally:
                self._playwright_instance = None
        
        self._kill_browser_processes()

proxy_service = ProxyService()

