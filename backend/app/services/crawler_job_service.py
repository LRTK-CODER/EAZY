from typing import Dict, Any, Optional
import uuid
from datetime import datetime

class CrawlerJobService:
    """
    Manages the state of active crawler jobs in memory AND persists results to DB.
    Singleton pattern for simplicity in this MVP.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrawlerJobService, cls).__new__(cls)
            cls._instance.jobs = {} # type: ignore
        return cls._instance

    def create_job(self, target_id: int) -> Optional[int]:
        from app.core.db import SessionLocal
        from app.models.scan import ScanJob as ScanJobModel
        
        job_id = str(uuid.uuid4())
        
        # Create DB record
        db = SessionLocal()
        try:
            scan_job = ScanJobModel(
                target_id=target_id,
                status="running",
                stats={"pages_visited": 0, "endpoints_found": 0}
            )
            db.add(scan_job)
            db.commit()
            db.refresh(scan_job)
            db_id = scan_job.id
        except Exception as e:
            print(f"Error creating scan job: {e}")
            db_id = None
        finally:
            db.close()

        self.jobs[str(target_id)] = {
            "job_id": job_id,
            "db_id": db_id,
            "target_id": target_id,
            "status": "running",
            "start_time": datetime.utcnow().isoformat(),
            "stats": {
                "pages_visited": 0,
                "queue_size": 0,
                "endpoints_found": 0
            },
            "endpoints": [],
            "seen_hashes": set()
        }
        return db_id

    def get_job(self, target_id: int) -> Optional[Dict[str, Any]]:
        job = self.jobs.get(str(target_id))
        if job:
             job_copy = job.copy()
             job_copy.pop("seen_hashes", None)
             return job_copy
        return None

    def update_stats(self, target_id: int, visited: int, queue: int, endpoints_count: int):
        from app.core.db import SessionLocal
        from app.models.scan import ScanJob as ScanJobModel
        
        if str(target_id) in self.jobs:
            self.jobs[str(target_id)]["stats"].update({
                "pages_visited": visited,
                "queue_size": queue
            })
            
            # Update DB stats periodically (or on every update? maybe too frequent)
            # For simplicity, let's update DB status on completion or periodically?
            # Let's do it on completion mainly, but we can do it here if needed.
            # To avoid DB spam, maybe skip here unless crucial.

    def add_endpoint(self, target_id: int, endpoint: Dict[str, Any]):
        from app.core.db import SessionLocal
        from app.models.scan import Endpoint as EndpointModel, Parameter as ParameterModel
        
        job = self.jobs.get(str(target_id))
        if job:
            spec_hash = endpoint.get("spec_hash")
            if not spec_hash:
                 spec_hash = f"{endpoint.get('method')}|{endpoint.get('url')}"
            
            if spec_hash not in job["seen_hashes"]:
                job["seen_hashes"].add(spec_hash)
                
                if "timestamp" not in endpoint:
                    endpoint["timestamp"] = datetime.utcnow().isoformat()
                
                job["endpoints"].append(endpoint)
                job["stats"]["endpoints_found"] = len(job["endpoints"])
                
                # DB Persistence
                db = SessionLocal()
                try:
                    # Check existing
                    existing_ep = db.query(EndpointModel).filter(
                        EndpointModel.target_id == target_id,
                        EndpointModel.method == endpoint['method'],
                        EndpointModel.path == endpoint['url']
                    ).first()
                    
                    if existing_ep:
                        existing_ep.source = endpoint.get('source', existing_ep.source)
                        existing_ep.updated_at = datetime.utcnow()
                        # Clear old params?
                        db.query(ParameterModel).filter(ParameterModel.endpoint_id == existing_ep.id).delete()
                        db_ep = existing_ep
                    else:
                        db_ep = EndpointModel(
                            target_id=target_id,
                            method=endpoint['method'],
                            path=endpoint['url'],
                            source=endpoint.get('source'),
                            spec_hash=spec_hash
                        )
                        db.add(db_ep)
                        
                    db.commit()
                    db.refresh(db_ep)
                    
                    # Add Params
                    params_to_add = []
                    # Logic to extract params from endpoint dict
                    # endpoint['parameters'] is list of {name, type, location}
                    if endpoint.get('parameters'):
                        for p in endpoint['parameters']:
                            params_to_add.append(ParameterModel(
                                endpoint_id=db_ep.id,
                                name=p['name'],
                                location=p['location'],
                                type=p['type']
                            ))
                    elif endpoint.get('params'): # Legacy
                         for name, val in endpoint['params'].items():
                             params_to_add.append(ParameterModel(
                                endpoint_id=db_ep.id,
                                name=name,
                                location='query',
                                type='string'
                            ))
                            
                    if params_to_add:
                        db.add_all(params_to_add)
                        db.commit()

                    # Link to ScanJob
                    from app.models.scan import ScanJob as ScanJobModel
                    scan_job = db.query(ScanJobModel).filter(ScanJobModel.id == self.jobs[str(target_id)]['db_id']).first()
                    
                    if scan_job and db_ep not in scan_job.endpoints:
                        scan_job.endpoints.append(db_ep)
                        db.commit()
                        
                except Exception as e:
                    print(f"Error persisting endpoint: {e}")
                    db.rollback()
                finally:
                    db.close()

    def set_status(self, target_id: int, status: str):
        from app.core.db import SessionLocal
        from app.models.scan import ScanJob as ScanJobModel
        
        if str(target_id) in self.jobs:
            self.jobs[str(target_id)]["status"] = status
            if status in ["completed", "failed", "stopped"]:
                 self.jobs[str(target_id)]["end_time"] = datetime.utcnow().isoformat()
                 
            # DB Update
            db_id = self.jobs[str(target_id)].get('db_id')
            if db_id:
                db = SessionLocal()
                try:
                    scan_job = db.query(ScanJobModel).filter(ScanJobModel.id == db_id).first()
                    if scan_job:
                        scan_job.status = status
                        scan_job.stats = self.jobs[str(target_id)]["stats"]
                        if status in ["completed", "failed", "stopped"]:
                            scan_job.end_time = datetime.utcnow()
                        db.commit()
                except Exception as e:
                    print(f"Error updating job status: {e}")
                finally:
                    db.close()

    def stop_job(self, target_id: int):
        self.set_status(target_id, "stopped")

crawler_job_service = CrawlerJobService()
