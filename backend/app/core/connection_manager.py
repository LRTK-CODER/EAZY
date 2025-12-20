
from typing import List
from fastapi import WebSocket
import structlog

logger = structlog.get_logger()

class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket.connected", client=websocket.client)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("websocket.disconnected", client=websocket.client)

    async def broadcast(self, message: dict):
        """
        Broadcasts a JSON message to all connected clients.
        Handles checking for closed connections during broadcast.
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("websocket.send_failed", error=str(e))
                # Cleanup will happen on next disconnect event usually, but we could remove here too
                # For now, let disconnect handle it or ignore.

manager = ConnectionManager()
