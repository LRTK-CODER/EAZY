"""Stage 간 공유 인터페이스 모델.

ARCHITECTURE 3.2절 KnowledgeGraphSnapshot, KGNode, KGEdge, KGMetadata 정의.
NetworkX 의존성은 Stage 2 내부로 격리한다.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KGNode(BaseModel):
    """KG 노드. ARCHITECTURE 15.2절 노드 타입 참조.

    Attributes:
        id: 노드 고유 식별자.
        node_type: 노드 타입 (endpoint, parameter, vulnerability 등).
        properties: 노드 타입별 속성.
    """

    id: str = Field(..., description="노드 고유 식별자")
    node_type: str = Field(..., description="노드 타입")
    properties: dict[str, Any] = Field(..., description="노드 타입별 속성")


class KGEdge(BaseModel):
    """KG 엣지. ARCHITECTURE 15.3절 엣지 타입 참조.

    Attributes:
        source_id: 출발 노드 ID.
        target_id: 도착 노드 ID.
        edge_type: 엣지 타입 (calls, has_vulnerability 등).
        properties: 엣지 속성.
    """

    source_id: str = Field(..., description="출발 노드 ID")
    target_id: str = Field(..., description="도착 노드 ID")
    edge_type: str = Field(..., description="엣지 타입")
    properties: dict[str, Any] = Field(default_factory=dict, description="엣지 속성")


class KGMetadata(BaseModel):
    """KG 스냅샷 메타데이터.

    Attributes:
        node_count: 노드 수.
        edge_count: 엣지 수.
        loop_iteration: 루프 반복 횟수.
        last_updated: 마지막 갱신 시각 (UTC).
    """

    node_count: int = Field(..., description="노드 수")
    edge_count: int = Field(..., description="엣지 수")
    loop_iteration: int = Field(..., description="루프 반복 횟수")
    last_updated: datetime = Field(..., description="마지막 갱신 시각")


class KnowledgeGraphSnapshot(BaseModel):
    """NetworkX 그래프의 Pydantic 직렬화.

    Attributes:
        nodes: KG 노드 목록.
        edges: KG 엣지 목록.
        metadata: 스냅샷 메타데이터.
    """

    nodes: list[KGNode] = Field(..., description="KG 노드 목록")
    edges: list[KGEdge] = Field(..., description="KG 엣지 목록")
    metadata: KGMetadata = Field(..., description="스냅샷 메타데이터")
