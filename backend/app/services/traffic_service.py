from sqlalchemy.orm import Session
from app.models.traffic_log import TrafficLog, TrafficSource
from app.core.db import SessionLocal
import structlog
import json

logger = structlog.get_logger()

class TrafficService:
    def __init__(self):
        pass

    async def save_traffic(self, 
                           target_id: int, 
                           method: str, 
                           url: str, 
                           host: str, 
                           path: str,
                           request_headers: dict, 
                           request_body: str, 
                           response_headers: dict, 
                           response_body: str, 
                           status_code: int, 
                           source: TrafficSource,
                           scan_job_id: int = None):
        """
        Saves a traffic log entry to the database.
        Designed to be called asynchronously/background.
        """
        db: Session = SessionLocal()
        try:
            # Serialize headers/body if needed (assuming simple dict/str)
            req_headers_json = json.dumps(request_headers) if request_headers else "{}"
            res_headers_json = json.dumps(response_headers) if response_headers else "{}"
            
            log_entry = TrafficLog(
                target_id=target_id,
                scan_job_id=scan_job_id,
                source=source.value,
                method=method,
                url=url,
                host=host,
                path=path,
                request_headers=req_headers_json,
                request_body=request_body.replace('\x00', '') if request_body else None,
                response_headers=res_headers_json,
                response_body=response_body.replace('\x00', '') if response_body else None,
                status_code=status_code
            )
            
            db.add(log_entry)
            db.commit()
            # logger.info("traffic.saved", url=url, id=log_entry.id)
            
        except Exception as e:
            logger.error("traffic.save_failed", error=str(e), url=url)
            db.rollback()
        finally:
            db.close()

traffic_service = TrafficService()
