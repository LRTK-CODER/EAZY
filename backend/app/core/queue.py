import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from redis.asyncio import Redis
from app.models.task import TaskType

class TaskManager:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.queue_key = "eazy_task_queue"

    async def enqueue_crawl_task(self, project_id: int, target_id: int, db_task_id: int) -> str:
        """
        Enqueue a crawl task into Redis.
        Returns the unique task ID (UUID) used for tracking in Redis.
        """
        task_id = str(uuid.uuid4())
        payload = {
            "id": task_id,
            "db_task_id": db_task_id,
            "type": TaskType.CRAWL.value,
            "project_id": project_id,
            "target_id": target_id,
            "timestamp": str(datetime.now())
        }
        await self.redis.rpush(self.queue_key, json.dumps(payload))
        return task_id

    async def dequeue_task(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue a task from Redis (Left Pop).
        Returns None if queue is empty.
        """
        # lpop returns the element or None
        data = await self.redis.lpop(self.queue_key)
        if data:
            return json.loads(data)
        return None
    

