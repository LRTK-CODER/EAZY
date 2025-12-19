from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.models.base import Base

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # User-friendly alias
    provider = Column(String, nullable=False)  # e.g., "openai", "anthropic"
    category = Column(String, default="LLM", nullable=False) # e.g., "LLM", "MCP"
    key = Column(String, nullable=False)  # Encrypted API Key
    api_base = Column(String, nullable=True)   # Optional custom base URL
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
