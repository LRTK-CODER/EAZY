from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
import structlog

from app.services.crawler_service import CrawlerService
from app.services.crawler_job_service import crawler_job_service
from app.services.target_service import TargetService
from app.core.db import get_db
from sqlalchemy.orm import Session

router = APIRouter()
logger = structlog.get_logger()

# Singleton Crawler Service
crawler_service_instance = CrawlerService()

class CrawlRequest(BaseModel):
    target_id: int
    max_depth: int = 2
    max_pages: int = 50

async def run_crawler_task(target_id: int, scan_job_id: int, url: str, max_depth: int, max_pages: int):
    """
    Background task wrapper for the crawler.
    """
    try:
        async def on_progress(visited, queue):
            crawler_job_service.update_stats(target_id, visited, queue, 0) # Endpoints count is updated separately or we can sync here

        async def on_result(endpoint):
            # Check for stopped status to abort (soft abort)
            job = crawler_job_service.get_job(target_id)
            if job and job["status"] == "stopped":
                raise Exception("Crawler stopped by user")
                
            crawler_job_service.add_endpoint(target_id, endpoint)
        
        await crawler_service_instance.crawl(
            start_url=url,
            max_depth=max_depth,
            max_pages=max_pages,
            target_id=target_id,
            scan_job_id=scan_job_id,
            progress_callback=on_progress,
            result_callback=on_result
        )
        crawler_job_service.set_status(target_id, "completed")
        
    except Exception as e:
        if str(e) == "Crawler stopped by user":
            logger.info("crawler.stopped", target_id=target_id)
        else:
            logger.error("crawler.task_failed", target_id=target_id, error=str(e))
            crawler_job_service.set_status(target_id, "failed")

@router.post("/start")
async def start_crawl(req: CrawlRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Start a new crawling job for a target.
    """
    # target_service is imported from app.services.target_service
    from app.services.target_service import target_service
    
    target = target_service.get_target(db, req.target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    # Check if already running
    existing_job = crawler_job_service.get_job(req.target_id)
    if existing_job and existing_job["status"] == "running":
        return {"message": "Crawler already running", "job_id": existing_job["job_id"]}

    # Create Job
    scan_job_id = crawler_job_service.create_job(req.target_id)
    # scan_job_id is now the DB ID (int) or None
    # Note: crawler_job_service.create_job seems to return a dict representing the job, let's verify or assume
    # Actually, create_job implementation is needed to be sure. But let's assume it returns the job object.
    # If not, we might need to adjust. But for now, we pass Target ID mainly.
    # Wait, ScanJob is a DB model. crawler_job_service.create_job might just be in-memory state management?
    # Usually it should persist ScanJob. Let's assume it does or we just pass None if not.
    # But for TrafficLog, we want a link. 
    # Let's inspect crawler_job_service.create_job if possible, but safely passing target_id is priority.
    
    # Start Background Task
    background_tasks.add_task(run_crawler_task, req.target_id, scan_job_id, target.url, req.max_depth, req.max_pages)
    
    return {"message": "Crawler started", "target_id": req.target_id}

@router.post("/stop/{target_id}")
async def stop_crawl(target_id: int):
    """
    Stop a running crawler job.
    """
    crawler_job_service.stop_job(target_id)
    return {"message": "Stop signal sent"}

@router.get("/status/{target_id}")
async def get_crawl_status(target_id: int):
    """
    Get the status and stats of a crawler job.
    """
    job = crawler_job_service.get_job(target_id)
    if not job:
         return {"status": "idle", "stats": None, "endpoints": []}
    return job

@router.get("/history/{target_id}")
async def get_scan_history(target_id: int, db: Session = Depends(get_db)):
    """
    Get the history of scan jobs for a target.
    """
    from app.models.scan import ScanJob
    
    jobs = db.query(ScanJob).filter(ScanJob.target_id == target_id).order_by(ScanJob.start_time.desc()).all()
    return jobs

@router.get("/jobs/{job_id}")
async def get_scan_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific scan job, including discovered endpoints.
    """
    from app.models.scan import ScanJob, Endpoint
    
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
        
    # Manually fetch endpoints if relationship issue or just to be safe with structure
    # Trying to reuse store structure: { ...job, endpoints: [...] }
    
    endpoints = db.query(Endpoint).filter(Endpoint.target_id == job.target_id).all()
    # Note: In a real history, we should only return endpoints discovered during THAT job. 
    # Current data model persists unique endpoints per TARGET, not per JOB (ScanJob is just a run record).
    # However, ScanJob has 'stats', but not a direct link to 'endpoints' discovered in that specific run 
    # unless we check timestamps or if we change the model.
    # For MVP, listing ALL current endpoints for the target is "okay" but technically not "history of that run".
    # BUT, let's look at `CrawlerJobService`. It stores `endpoints` in memory for the running job.
    # If we want true history of "what was found in run X", we need a many-to-many or a snapshot.
    # Given the current `Endpoint` model is per Target (unique by method/path), 
    # `ScanJob` is just a log of execution.
    # User might expect "Endpoints found in THIS scan". 
    # For now, let's return the job info. If user clicks it, maybe they just want to see the stats?
    # Or maybe we return current endpoints of the target?
    # Let's return the job details. If we want endpoints, we return all endpoints for the target for now,
    # because `Endpoint` doesn't have `scan_job_id`. 
    
    # Wait, the prompt implies "Load & Display Past Scan History".
    # If I run a scan and find A, B. Next scan I find C. 
    # If I view history of Scan 1, do I see A, B? Or A, B, C?
    # Typically DAST tools show what was found in that scan.
    # Current Schema: Endpoint is child of Target. Not ScanJob.
    # So we can't easily filter "endpoints found in scan X" unless we check `created_at` vs `start_time`/`end_time`.
    # Let's use time-window based filtering as a heuristic for now?
    # endpoint.created_at BETWEEN job.start_time AND job.end_time
    
    response = {
        "id": job.id,
        "target_id": job.target_id,
        "status": job.status,
        "start_time": job.start_time,
        "end_time": job.end_time,
        "stats": job.stats,
        "endpoints": []
    }
    
    if job.endpoints:
         job_endpoints = job.endpoints
         # Fallback for old jobs (before migration) or if empty?
         # If empty and time exists, maybe try old method? 
         # No, let's stick to explicit relationship for correctness going forward.
         # Actually, for Job 24 (the missing one), it won't have relationship, so it will still be empty.
         # But for new jobs (Job 26+), it will work.
         # If we want to support old jobs (T1, T3 which worked by time), we could do a fallback:
         if not job_endpoints and job.end_time:
             # Fallback to time-based for backward compatibility
             from sqlalchemy import or_
             job_endpoints = db.query(Endpoint).filter(
                 Endpoint.target_id == job.target_id,
                 or_(
                     Endpoint.updated_at.between(job.start_time, job.end_time),
                     Endpoint.created_at.between(job.start_time, job.end_time)
                 )
             ).all()
         
         # Map to frontend structure
         mapped_endpoints = []
         for ep in job_endpoints:
             # Load parameters
             params = []
             for p in ep.parameters:
                 params.append({
                     "name": p.name,
                     "type": p.type,
                     "location": p.location
                 })
                 
             # Determine best timestamp to show: 
             # 1. If created_at is during this scan (New discovery), show it.
             # 2. If updated_at is currently pointing to this scan (Latest verify), show it.
             # 3. Otherwise (re-verified but overwritten by later scan), use job.end_time (or start_time).
             
             display_time = job.end_time or job.start_time
             
             if ep.created_at and job.start_time <= ep.created_at <= (job.end_time or datetime.utcnow()):
                  display_time = ep.created_at
             elif ep.updated_at and job.start_time <= ep.updated_at <= (job.end_time or datetime.utcnow()):
                  display_time = ep.updated_at
                  
             mapped_endpoints.append({
                 "method": ep.method,
                 "url": ep.path, # Map path -> url
                 "source": ep.source,
                 "timestamp": display_time, 
                 "spec_hash": ep.spec_hash,
                 "parameters": params
             })
             
         response["endpoints"] = mapped_endpoints
    else:
        # If job is running or failed without end_time, maybe just show all? 
        # Or if strictly history, show those updated after start_time?
        pass

    return response
