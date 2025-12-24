from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.models.traffic_log import TrafficLog
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter()

class TrafficMetric(BaseModel):
    id: int
    method: str
    url: str
    path: str
    status_code: Optional[int]
    source: str
    created_at: datetime

class SitemapNode(BaseModel):
    key: str # Full path or segment
    title: str # Display name
    children: List['SitemapNode'] = []
    is_leaf: bool = False
    
    class Config:
        arbitrary_types_allowed = True

@router.get("/", response_model=List[TrafficMetric])
def get_traffic_logs(
    target_id: int,
    path_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get traffic logs, optionally filtered by path (for Site Map selection).
    """
    query = db.query(TrafficLog).filter(TrafficLog.target_id == target_id)
    
    if path_filter:
        if "://" in path_filter:
            # Filter by Domain/Origin (e.g. https://example.com)
            # Since we don't store scheme separately, we can filter by host if the input is https://host
            # Or use startswith on URL? No, URL has full path.
            # But TrafficLog.url IS the full URL. 
            # So url.startswith("https://example.com") works perfectly.
            import urllib.parse
            parsed = urllib.parse.urlparse(path_filter)
            # Use host filter for more robustness if needed, or just url startswith
            query = query.filter(TrafficLog.url.startswith(path_filter))
        else:
            # Simple startswith filter for directory-like selection
            # If user clicks /api, we show everything under /api
            # NOTE: If we are deep in a domain tree, the key might be "https://domain.com/api".
            # The frontend passes the full key as 'path'.
            # So if key is "https://domain.com/api", we want logs where URL starts with that.
            # Wait, our keys in sitemap are now constructed as "https://domain.com/path".
            # So we can ALWAYS use TrafficLog.url.startswith(path_filter)!
            # Because TrafficLog.url = https://domain.com/path...
            # And our sitemap keys are also built to match that structure.
            # EXCEPT: TrafficLog.path column is just `/path`.
            # If we were relying on `path` column before, it was assuming single domain.
            # Now we are multi-domain.
            # So filtering by URL is cleaner and unifies logic.
            
            # Check if path_filter looks like a path or full url.
            if path_filter.startswith("/") and "://" not in path_filter:
                # Legacy or relative path filter?
                # Probably should rely on URL filter if possible.
                query = query.filter(TrafficLog.path.startswith(path_filter))
            else:
                 # It's an absolute URL segment
                 query = query.filter(TrafficLog.url.startswith(path_filter))
    
    logs = query.order_by(TrafficLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs

@router.get("/sitemap", response_model=List[SitemapNode])
def get_sitemap(target_id: int, db: Session = Depends(get_db)):
    """
    Constructs a tree structure from all visited paths for a target, grouped by Domain/Protocol.
    """
    from sqlalchemy import func
    import urllib.parse

    # 1. Fetch distinct Host, Path, and a sample URL (to extract scheme)
    # We group by host and path to reconstruct the tree.
    # We use MIN(url) to get a sample URL for scheme detection.
    rows = db.query(
        TrafficLog.host, 
        TrafficLog.path, 
        func.min(TrafficLog.url)
    ).filter(
        TrafficLog.target_id == target_id
    ).group_by(
        TrafficLog.host, 
        TrafficLog.path
    ).all()
    
    # Structure: { "https://example.com": { "children": ..., "paths": [] } }
    domain_roots = {}
    
    for host, path, sample_url in rows:
        parsed = urllib.parse.urlparse(sample_url)
        scheme = parsed.scheme or "http"
        domain_key = f"{scheme}://{host}"
        
        if domain_key not in domain_roots:
            domain_roots[domain_key] = SitemapNode(
                key=domain_key, # Root key is the domain
                title=domain_key, # Title is full origin
                children=[],
                is_leaf=False
            )
            
        root_node = domain_roots[domain_key]
        
        # Build path tree under this domain
        # Ignore empty path (/) if handle explicitly? 
        # path is usually /foo/bar.
        
        parts = [p for p in path.strip('/').split('/') if p]
        current_node = root_node
        current_path_key = domain_key
        
        for part in parts:
            current_path_key += "/" + part
            
            # Find existing child
            found = None
            for child in current_node.children:
                if child.title == part:
                    found = child
                    break
            
            if not found:
                new_node = SitemapNode(key=current_path_key, title=part, children=[])
                current_node.children.append(new_node)
                current_node = new_node
            else:
                current_node = found
        
        # Mark leaf if this path corresponds to an actual request endpoint?
        # Actually logic is: if we have a log for this path, it's a "file" or "endpoint".
        # But here 'rows' contains actual visited paths, so the specific 'current_node' IS a visited node.
        current_node.is_leaf = True 
        # Note: Intermediate nodes might also be visited (e.g. /api and /api/v1). 
        # But simplistic approach: just mark as leaf if it exists in DB.
        
    return list(domain_roots.values())

@router.get("/{log_id}")
def get_traffic_detail(log_id: int, db: Session = Depends(get_db)):
    log = db.query(TrafficLog).filter(TrafficLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return {
        "id": log.id,
        "method": log.method,
        "url": log.url,
        "request": {
            "headers": json.loads(log.request_headers) if log.request_headers else {},
            "body": log.request_body
        },
        "response": {
            "headers": json.loads(log.response_headers) if log.response_headers else {},
            "body": log.response_body,
            "status": log.status_code
        },
        "created_at": log.created_at
    }
