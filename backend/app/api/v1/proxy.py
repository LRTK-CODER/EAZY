
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.connection_manager import manager
from app.services.proxy_service import proxy_service
import structlog
from pydantic import BaseModel

router = APIRouter()
logger = structlog.get_logger()

@router.websocket("/ws/proxy")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Just keep connection open, we push data from ProxyService
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket.error", error=str(e))
        manager.disconnect(websocket)

@router.post("/start")
async def start_proxy():
    try:
        proxy_service.start()
        return {"status": "started", "port": 8081}
    except Exception as e:
        logger.error("proxy.start_failed", error=str(e))
        return {"status": "error", "message": str(e)}

@router.post("/stop")
async def stop_proxy():
    try:
        await proxy_service.stop_with_browser()
        return {"status": "stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class BrowserLaunchRequest(BaseModel):
    url: str
    proxy_port: int = 8081

@router.post("/browser/launch")
async def launch_browser(req: BrowserLaunchRequest):
    try:
        await proxy_service.launch_browser(req.url, req.proxy_port)
        return {"status": "launched", "url": req.url}
    except Exception as e:
        logger.error("proxy.browser.launch_failed", error=str(e))
        return {"status": "error", "message": str(e)}
