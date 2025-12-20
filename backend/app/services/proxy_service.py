
import asyncio
import threading
from typing import Optional
from mitmproxy import http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
import structlog
from app.services.semantic_parser import SemanticParser
from app.core.connection_manager import manager

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

    def stop(self):
        if self._master:
            self._master.shutdown()
            self._master = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        logger.info("proxy.stopped")

# Addon method update to use main_loop
def response(self, flow: http.HTTPFlow):
    try:
        url = flow.request.pretty_url
        method = flow.request.method
        # ... Extraction logic ...
        req_headers = dict(flow.request.headers)
        req_body = flow.request.content.decode('utf-8', 'ignore') if flow.request.content else None
        status_code = flow.response.status_code
        res_headers = dict(flow.response.headers)

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
