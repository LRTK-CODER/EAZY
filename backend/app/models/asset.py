from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import ForeignKey
from sqlmodel import JSON, Column, Field, SQLModel

from app.core.utils import utc_now


class AssetType(str, Enum):
    URL = "url"
    FORM = "form"
    XHR = "xhr"


class AssetSource(str, Enum):
    HTML = "html"
    JS = "js"
    NETWORK = "network"
    DOM = "dom"
    ROBOTS_TXT = "robots_txt"
    SITEMAP = "sitemap"


class AssetBase(SQLModel):
    target_id: int = Field(
        sa_column=Column(ForeignKey("targets.id", ondelete="CASCADE"), nullable=False)
    )
    content_hash: str = Field(index=True, unique=True, max_length=64)
    type: AssetType = Field(default=AssetType.URL)
    source: AssetSource = Field(default=AssetSource.HTML)
    method: str = Field(default="GET", max_length=10)
    url: str = Field()
    path: str = Field()

    # JSONB fields
    request_spec: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    response_spec: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
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
    task_id: int = Field(
        sa_column=Column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    )
    asset_id: int = Field(
        sa_column=Column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    )
    parent_asset_id: Optional[int] = Field(
        default=None, sa_column=Column(ForeignKey("assets.id", ondelete="CASCADE"))
    )
    discovered_at: datetime = Field(default_factory=utc_now)


class AssetRead(AssetBase):
    id: int
    first_seen_at: datetime
    last_seen_at: datetime
