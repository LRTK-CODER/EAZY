"""Ground Truth 스키마.

벤치마크 정답 데이터의 최상위 스키마를 정의한다.
각 Stage SPEC에서 필요한 필드만 채운다.
"""

from pydantic import BaseModel, Field

from src.models.chains import ChainResult  # noqa: F401
from src.models.endpoints import Endpoint
from src.models.findings import Vulnerability
from src.models.interfaces import KnowledgeGraphSnapshot


class GroundTruthChain(BaseModel):
    """체인 정답 한 건."""

    chain_id: str
    steps: list[str]
    impact: str


class GroundTruth(BaseModel, extra="allow"):
    """벤치마크 ground truth 최상위 스키마."""

    app_id: str
    endpoints: list[Endpoint] = Field(default_factory=list)
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    kg_snapshot: KnowledgeGraphSnapshot | None = Field(default=None)
    chains: list[GroundTruthChain] = Field(default_factory=list)
