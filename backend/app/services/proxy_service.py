
import asyncio
import threading
from typing import Optional
from mitmproxy import http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
import structlog
import subprocess
from app.services.semantic_parser import SemanticParser
from app.core.connection_manager import manager
from playwright.async_api import async_playwright


logger = structlog.get_logger()

class ProxyAddon:
    """
    Mitmproxy Addon to intercept requests and responses.
    """
    def __init__(self):
        self.parser = SemanticParser()

    def response(self, flow: http.HTTPFlow):
        """
        Hook for HTTP responses. Captures data and broadcasts it.
        """
        try:
            # Extract request details
            url = flow.request.pretty_url
            method = flow.request.method
            req_headers = dict(flow.request.headers)
            req_body = flow.request.content.decode('utf-8', 'ignore') if flow.request.content else None
            
            # Extract response details
            status_code = flow.response.status_code
            res_headers = dict(flow.response.headers)
            
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
            
            # Broadcast to WebSocket
            # Since this runs in mitmproxy's loop/thread, we need to schedule it on the main loop?
            # Or just fire and forget if manager methods are thread-safe?
            # Manager.broadcast is async. 
            # We can use a fire-and-forget approach with a new loop or run_coroutine_threadsafe if we had access to main loop.
            # BUT: ConnectionManager.active_connections is shared. accessing it from another thread is risky without lock.
            # Simplified: Use asyncio.run_coroutine_threadsafe if we can get the main loop.
            # For now, let's try just logging to confirm capture, handling WS is tricky across threads.
            # Strategy: We can't easily wait for the main loop from here.
            # Alternative: Use a synchronous queue to pass data to main thread?
            # Or assume manager.broadcast can be run? No it's async.
            
            # Temporary Fix: Just log for now to verify capture logic.
            # Real impl needs cross-thread communication.
            # logger.info("proxy.captured", url=url)
            
            # To actually broadcast, we need the main event loop.
            # This class is instantiated in the Main Process but running in a Thread.
            # We can pass the main loop to it?
            
            pass 

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


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProxyService, cls).__new__(cls)
        return cls._instance
    
    def set_main_loop(self, loop):
        self._main_loop = loop

    def start(self, port: int = 8081):
        if self._thread and self._thread.is_alive():
            logger.warning("proxy.already_running")
            return

        logger.info("proxy.starting", port=port)
        
        def run_proxy():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop

            async def start_master():
                opts = Options(listen_host='0.0.0.0', listen_port=port)
                # DumpMaster init requires a running loop in newer mitmproxy versions
                self._master = DumpMaster(opts, with_termlog=False, with_dumper=False)
                
                # Add Addon
                addon = ProxyAddon()
                # Inject main loop into addon
                addon.main_loop = self._main_loop
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

        # Wait for port to be listening (non-blocking wait would be better, but this is a sync method called from async)
        # We should verify the port is open before returning
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
            # Proceed anyway, maybe it's just slow or firewall
              
        logger.info("proxy.started")

    def stop(self):
        """
        Stops the proxy master and thread.
        """
        if self._master:
            self._master.shutdown()
            self._master = None
            
        if self._loop:
            # Loop is running in thread. Shutdown master should stop it?
            # master.shutdown() stops the run loop.
            pass

        if self._thread and self._thread.is_alive():
            # self._thread.join() # We shouldn't block main thread too long
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
        Uses psutil for robust, cross-platform process management without shell limits.
        """
        try:
            import psutil
            killed_count = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Access cmdline safely
                    cmdline = proc.info['cmdline']
                    if not cmdline:
                        continue
                        
                    # Check for our specific proxy signature
                    if any('localhost:8081' in arg for arg in cmdline):
                        logger.info("proxy.force_kill_psutil", pid=proc.pid, name=proc.info['name'])
                        proc.kill()
                        killed_count += 1
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Reset internal state if we killed anything (or always, just to be safe)
            if killed_count > 0:
                self._browser_instance = None
                self._playwright_instance = None
                    
        except ImportError:
            logger.error("proxy.cleanup_error", error="psutil not installed")
        except Exception as e:
            logger.warning("proxy.cleanup_error", error=str(e))

    async def launch_browser(self, target_url: str, proxy_port: int = 8081):

        """
        Launches a headful browser configured to use the proxy.
        """
        if self._browser_instance:
            if not self._browser_instance.is_connected():
                self._browser_instance = None
            else:
                logger.info("proxy.browser.already_running")
                return

        # Ensure proxy is running before launching browser
        # This prevents "net::ERR_PROXY_CONNECTION_FAILED" which causes immediate browser closure
        if not (self._thread and self._thread.is_alive()):
            logger.info("proxy.auto_starting_for_browser")
            self.start(proxy_port)
            # Give it a tiny bit to spin up? 
            # start() returns after thread.start(), but thread needs to init loop.
            # Ideally we check connectivity, but a small sleep is safer than nothing.
            await asyncio.sleep(1) 


        try:
            logger.info("proxy.browser.launching", url=target_url)
            self._playwright_instance = await async_playwright().start()
            
            # Launch Chromium with Proxy
            # args ignore-certificate-errors is crucial for mitmproxy self-signed certs
            self._browser_instance = await self._playwright_instance.chromium.launch(
                headless=False, 
                proxy={"server": f"http://localhost:{proxy_port}"},
                args=["--ignore-certificate-errors", "--no-sandbox"]
            )
            
            # Attach Disconnect Listener
            # Note: We need a wrapper because on("disconnected") passes the browser instance
            self._browser_instance.on("disconnected", lambda b: self._on_browser_disconnected(b))
            
            context = await self._browser_instance.new_context(ignore_https_errors=True)
            page = await context.new_page()
            
            # Go to target
            logger.info("proxy.browser.navigating", url=target_url)
            try:
                # We use a shorter timeout for initial navigation so we don't block API too long,
                # but long enough to load. If it fails, we keep browser open.
                await page.goto(target_url, timeout=30000)
                logger.info("proxy.browser.started")
            except Exception as nav_e:
                # Navigation failed (timeout, dns, etc)
                # We DO NOT stop the browser here. The user wants to retry or debug manually.
                logger.warning("proxy.browser.navigation_failed", error=str(nav_e))
            
        except Exception as e:
            logger.error("proxy.browser.failed", error=str(e))
            # Only stop if it's a critical launch failure (e.g. couldn't start process)
            if not self._browser_instance:
                 await self.stop_browser()
            raise e

    async def stop_browser(self):
        # 1. Try Graceful Close
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
        
        # 2. Force Kill any remnants (Zombie check)
        self._kill_browser_processes()


# Addon method update to use main_loop
def response(self, flow: http.HTTPFlow):
    try:
        url = flow.request.pretty_url
        method = flow.request.method
        # ... Extraction logic ...
        req_headers = {k.lower(): v for k, v in flow.request.headers.items()}
        req_body = flow.request.content.decode('utf-8', 'ignore') if flow.request.content else None
        status_code = flow.response.status_code
        res_headers = {k.lower(): v for k, v in flow.response.headers.items()}

        parsed = self.parser.parse_request(method, url, req_headers, req_body)
        
        event_data = {
            "type": "proxy_packet",
            "data": {
                "method": method,
                "url": url,
                "status_code": status_code,
                "analysis": parsed
            }
        }
        
        if hasattr(self, 'main_loop') and self.main_loop:
             asyncio.run_coroutine_threadsafe(manager.broadcast(event_data), self.main_loop)
    except Exception as e:
        logger.error("proxy.addon_error", error=str(e))

ProxyAddon.response = response 
proxy_service = ProxyService()

