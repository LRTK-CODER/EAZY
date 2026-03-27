"""Ground Truth 스키마 테스트.

SPEC-000 Feature 2 검증 기준에 대응하는 테스트.
"""

import json

import pytest
from pydantic import ValidationError

from tests.helpers.ground_truth import GroundTruth, GroundTruthChain
from src.models.interfaces import KnowledgeGraphSnapshot, KGNode, KGEdge


# ---------------------------------------------------------------------------
# 유효한 GroundTruth JSON 픽스처
# ---------------------------------------------------------------------------
@pytest.fixture()
def valid_ground_truth_json() -> str:
    """유효한 GroundTruth JSON 문자열."""
    return json.dumps({
        "app_id": "owasp-benchmark-v1.2",
        "endpoints": [],
        "vulnerabilities": [],
        "kg_snapshot": {
            "nodes": [
                {
                    "id": "ep-login",
                    "node_type": "endpoint",
                    "properties": {"path": "/api/login"},
                }
            ],
            "edges": [
                {
                    "source_id": "ep-login",
                    "target_id": "vuln-sqli-1",
                    "edge_type": "has_vulnerability",
                    "properties": {},
                }
            ],
            "metadata": {
                "node_count": 1,
                "edge_count": 1,
                "loop_iteration": 0,
                "last_updated": "2026-03-27T00:00:00",
            },
        },
        "chains": [
            {
                "chain_id": "chain-001",
                "steps": ["vuln-sqli-1", "vuln-idor-2"],
                "impact": "관리자 계정 탈취",
            }
        ],
    })


# ---------------------------------------------------------------------------
# PASS: GroundTruth 필드 존재
# ---------------------------------------------------------------------------
def test_ground_truth_has_required_fields(valid_ground_truth_json: str) -> None:
    """GroundTruth 모델이 app_id, endpoints, vulnerabilities, kg_snapshot, chains 필드를 가진다."""
    gt = GroundTruth.model_validate_json(valid_ground_truth_json)

    assert hasattr(gt, "app_id")
    assert hasattr(gt, "endpoints")
    assert hasattr(gt, "vulnerabilities")
    assert hasattr(gt, "kg_snapshot")
    assert hasattr(gt, "chains")


# ---------------------------------------------------------------------------
# PASS: JSON 로드 시 유효 모델
# ---------------------------------------------------------------------------
def test_ground_truth_loads_from_json(valid_ground_truth_json: str) -> None:
    """model_validate_json으로 JSON을 로드하면 유효한 GroundTruth 인스턴스가 반환된다."""
    gt = GroundTruth.model_validate_json(valid_ground_truth_json)

    assert isinstance(gt, GroundTruth)
    assert gt.app_id == "owasp-benchmark-v1.2"
    assert isinstance(gt.chains, list)
    assert len(gt.chains) == 1


# ---------------------------------------------------------------------------
# PASS: 필수 필드 누락 시 ValidationError
# ---------------------------------------------------------------------------
def test_ground_truth_missing_app_id_raises_validation_error() -> None:
    """필수 필드(app_id) 누락 시 ValidationError가 발생한다."""
    invalid_json = json.dumps({
        "endpoints": [],
        "vulnerabilities": [],
    })

    with pytest.raises(ValidationError):
        GroundTruth.model_validate_json(invalid_json)


# ---------------------------------------------------------------------------
# PASS: kg_snapshot KnowledgeGraphSnapshot 호환
# ---------------------------------------------------------------------------
def test_kg_snapshot_compatible_with_architecture(
    valid_ground_truth_json: str,
) -> None:
    """kg_snapshot은 KnowledgeGraphSnapshot 스키마와 호환된다 (nodes, edges)."""
    gt = GroundTruth.model_validate_json(valid_ground_truth_json)

    assert gt.kg_snapshot is not None
    assert isinstance(gt.kg_snapshot, KnowledgeGraphSnapshot)
    assert isinstance(gt.kg_snapshot.nodes, list)
    assert isinstance(gt.kg_snapshot.edges, list)

    # nodes는 KGNode 인스턴스
    node = gt.kg_snapshot.nodes[0]
    assert isinstance(node, KGNode)
    assert node.id == "ep-login"
    assert node.node_type == "endpoint"

    # edges는 KGEdge 인스턴스
    edge = gt.kg_snapshot.edges[0]
    assert isinstance(edge, KGEdge)
    assert edge.source_id == "ep-login"
    assert edge.target_id == "vuln-sqli-1"
    assert edge.edge_type == "has_vulnerability"


# ---------------------------------------------------------------------------
# PASS: chains에 steps + impact 포함
# ---------------------------------------------------------------------------
def test_chain_has_steps_and_impact(valid_ground_truth_json: str) -> None:
    """chains의 각 항목은 steps(list[str])와 impact(str)을 포함한다."""
    gt = GroundTruth.model_validate_json(valid_ground_truth_json)

    assert len(gt.chains) >= 1
    chain = gt.chains[0]
    assert isinstance(chain, GroundTruthChain)
    assert isinstance(chain.steps, list)
    assert all(isinstance(s, str) for s in chain.steps)
    assert isinstance(chain.impact, str)
    assert chain.steps == ["vuln-sqli-1", "vuln-idor-2"]
    assert chain.impact == "관리자 계정 탈취"


# ---------------------------------------------------------------------------
# 부정: extra 필드 허용 (extra="allow")
# ---------------------------------------------------------------------------
def test_ground_truth_allows_extra_fields() -> None:
    """Stage별 확장 필드를 추가해도 ValidationError가 발생하지 않는다."""
    json_with_extra = json.dumps({
        "app_id": "test-app",
        "stage_1_recon": {"discovered_urls": ["/admin", "/api"]},
        "custom_metadata": "확장 필드 테스트",
    })

    gt = GroundTruth.model_validate_json(json_with_extra)
    assert gt.app_id == "test-app"
    # extra 필드가 보존되어야 한다
    assert gt.stage_1_recon == {"discovered_urls": ["/admin", "/api"]}  # type: ignore[attr-defined]
    assert gt.custom_metadata == "확장 필드 테스트"  # type: ignore[attr-defined]
