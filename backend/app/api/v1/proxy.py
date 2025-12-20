
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.connection_manager import manager
from app.services.proxy_service import proxy_service
import structlog

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
        proxy_service.stop()
        return {"status": "stopped"}
    except Exception as e:
        logger.error("proxy.stop_failed", error=str(e))
        return {"status": "error", "message": str(e)}
