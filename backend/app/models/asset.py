from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlmodel import Field, SQLModel, Column, JSON
from enum import Enum

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class AssetType(str, Enum):
    URL = "url"
    FORM = "form"
    XHR = "xhr"

class AssetSource(str, Enum):
    HTML = "html"
    JS = "js"
    NETWORK = "network"
    DOM = "dom"

class AssetBase(SQLModel):
    target_id: int = Field(foreign_key="targets.id", nullable=False)
    content_hash: str = Field(index=True, unique=True, max_length=64)
    type: AssetType = Field(default=AssetType.URL)
    source: AssetSource = Field(default=AssetSource.HTML)
    method: str = Field(default="GET", max_length=10)
    url: str = Field(max_length=2048)
    path: str = Field(max_length=2048)
    
    # JSONB fields
    request_spec: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    response_spec: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    parameters: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    last_task_id: Optional[int] = Field(default=None)

class Asset(AssetBase, table=True):
    __tablename__ = "assets"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    first_seen_at: datetime = Field(default_factory=utc_now)
    last_seen_at: datetime = Field(default_factory=utc_now)

class AssetDiscovery(SQLModel, table=True):
    __tablename__ = "asset_discoveries"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id", nullable=False)
    asset_id: int = Field(foreign_key="assets.id", nullable=False)
    parent_asset_id: Optional[int] = Field(default=None, foreign_key="assets.id")
    discovered_at: datetime = Field(default_factory=utc_now)
