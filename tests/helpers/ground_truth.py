"""Ground Truth 스키마.

벤치마크 정답 데이터의 최상위 스키마를 정의한다.
각 Stage SPEC에서 필요한 필드만 채운다.
SPEC-000 Feature 2 인터페이스 계약 참조.
"""

from pydantic import BaseModel, Field

from src.models.endpoints import Endpoint
from src.models.findings import Vulnerability
from src.models.interfaces import KnowledgeGraphSnapshot


class GroundTruthChain(BaseModel):
    """체인 정답 한 건.

    Attributes:
        chain_id: 체인 식별자.
        steps: 체인 단계 순서 (취약점 ID 리스트).
        impact: 최종 영향 설명.
    """

    chain_id: str = Field(..., description="체인 식별자")
    steps: list[str] = Field(..., description="체인 단계 순서 (취약점 ID 리스트)")
    impact: str = Field(..., description="최종 영향 설명")


class GroundTruth(BaseModel, extra="allow"):
    """벤치마크 ground truth 최상위 스키마.

    각 Stage SPEC에서 필요한 필드만 채운다.
    ``extra="allow"``로 Stage별 확장 필드를 허용한다.

    Attributes:
        app_id: 벤치마크 앱 식별자.
        endpoints: 정답 엔드포인트 목록.
        vulnerabilities: 정답 취약점 목록.
        kg_snapshot: 정답 KG 스냅샷 (ARCHITECTURE 3.2절).
        chains: 정답 공격 체인 목록.
    """

    app_id: str = Field(..., description="벤치마크 앱 식별자")
    endpoints: list[Endpoint] = Field(default_factory=list, description="정답 엔드포인트 목록")
    vulnerabilities: list[Vulnerability] = Field(default_factory=list, description="정답 취약점 목록")
    kg_snapshot: KnowledgeGraphSnapshot | None = Field(default=None, description="정답 KG 스냅샷")
    chains: list[GroundTruthChain] = Field(default_factory=list, description="정답 공격 체인 목록")
