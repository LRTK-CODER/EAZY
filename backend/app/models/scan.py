from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed, stopped
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    stats = Column(JSON, default={})  # pages_visited, endpoints_found, etc.
    
    stats = Column(JSON, default={})  # pages_visited, endpoints_found, etc.
    
    target = relationship("Target", back_populates="scan_jobs")
    endpoints = relationship("Endpoint", secondary="scan_job_endpoints", backref="scan_jobs")

from sqlalchemy import Table
scan_job_endpoints = Table(
    "scan_job_endpoints",
    Base.metadata,
    Column("scan_job_id", Integer, ForeignKey("scan_jobs.id"), primary_key=True),
    Column("endpoint_id", Integer, ForeignKey("endpoints.id"), primary_key=True),
)

class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    source = Column(String, nullable=True) # network, html_form, etc.
    description = Column(Text, nullable=True)
    spec_hash = Column(String, nullable=True, index=True) # For quick deduplication check
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    target = relationship("Target", back_populates="endpoints")
    parameters = relationship("Parameter", back_populates="endpoint", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('target_id', 'method', 'path', name='uix_target_method_path'),
    )

class Parameter(Base):
    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=False)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False) # query, path, body, header
    type = Column(String, nullable=True) # int, string, uuid, etc.
    
    endpoint = relationship("Endpoint", back_populates="parameters")
