from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum

class TrafficSource(str, enum.Enum):
    PASSIVE = "passive"
    ACTIVE = "active"

class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=True) # Only for active scans
    
    source = Column(String, nullable=False) # 'passive' or 'active' (Stored as string for simplicity or Enum)
    
    method = Column(String, nullable=False)
    url = Column(String, nullable=False)
    host = Column(String, nullable=False, index=True) # For Sitemap grouping
    path = Column(String, nullable=False)
    
    # Headers stored as JSON
    request_headers = Column(Text, nullable=True) # JSON String
    response_headers = Column(Text, nullable=True) # JSON String
    
    # Body stored as Text (May be large)
    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)
    
    status_code = Column(Integer, nullable=True)
    
    # Analysis Meta (optional future use)
    content_type = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    target = relationship("Target", backref="traffic_logs")
    scan_job = relationship("ScanJob", backref="traffic_logs")
