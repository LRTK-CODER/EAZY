"""Stage 간 공유 인터페이스 모델.

ARCHITECTURE 3.2절 KnowledgeGraphSnapshot 정의.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class KGNode(BaseModel):
    """KG 노드."""

    id: str
    node_type: str
    properties: dict[str, Any]


class KGEdge(BaseModel):
    """KG 엣지."""

    source_id: str
    target_id: str
    edge_type: str
    properties: dict[str, Any] = {}


class KGMetadata(BaseModel):
    """KG 스냅샷 메타데이터."""

    node_count: int
    edge_count: int
    loop_iteration: int
    last_updated: datetime


class KnowledgeGraphSnapshot(BaseModel):
    """NetworkX 그래프의 Pydantic 직렬화."""

    nodes: list[KGNode]
    edges: list[KGEdge]
    metadata: KGMetadata
