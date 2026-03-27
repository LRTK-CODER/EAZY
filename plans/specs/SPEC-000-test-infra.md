# SPEC-000: 테스트 인프라

> **Phase 0** | 우선순위: P0 | PRD 기능: 기능 0 | ARCHITECTURE: 부록 B, 16절

---

## 검증 기준

> **이 섹션이 가장 먼저 온다.** "어떻게 확인할 건가"가 "무엇을 만들 건가"보다 앞선다.
> 검증 기준이 아키텍처를 결정한다.

### 기능 검증

#### Feature 1: 측정 유틸리티

- PASS: `compute_metrics(predicted, ground_truth)` 호출 시 Precision, Recall, F1이 포함된 `MetricsResult` 모델이 반환된다
- PASS: `compute_metrics(predicted, ground_truth, tn=N)` 호출 시 Youden's Index가 추가로 산출된다. `tn` 미제공 시 `youdens_index`는 `None`이다
- PASS: predicted와 ground_truth가 완전히 일치하면 Precision=1.0, Recall=1.0, F1=1.0이 반환된다
- PASS: predicted가 빈 리스트이면 Precision=`None`(정의 불가), Recall=0.0, F1=`None`이 반환된다
- PASS: ground_truth가 빈 리스트이면 Precision=`None`, Recall=`None`(정의 불가), F1=`None`이 반환된다
- PASS: predicted에 FP만 있으면(ground_truth와 교집합 없음) Precision=0.0, Recall=0.0이 반환된다
- PASS: Stage별 매칭 전략을 주입할 수 있다 — `match_fn` 파라미터로 커스텀 매칭 함수를 전달하면 해당 함수로 TP/FP/FN을 판정한다

#### Feature 2: Ground Truth 스키마

- PASS: `GroundTruth` 모델이 endpoints, vulnerabilities, kg_snapshot, chains 필드를 가진다
- PASS: `GroundTruth.model_validate_json(json_str)`로 JSON 파일을 로드하면 유효한 모델 인스턴스가 반환된다
- PASS: 필수 필드 누락 시 `ValidationError`가 발생한다
- PASS: kg_snapshot 필드는 ARCHITECTURE 3.2절 `KnowledgeGraphSnapshot`(nodes: `list[KGNode]`, edges: `list[KGEdge]`) 스키마와 호환된다
- PASS: chains 필드의 각 체인은 단계 순서(steps)와 최종 영향(impact)을 포함한다

#### Feature 3: 벤치마크 환경 디렉토리 구조 + Docker Compose

- PASS: `benchmarks/` 디렉토리 아래 `l1/`, `l2/owasp-benchmark/`, `l2/wivet/`, `l2/conduit/` 디렉토리가 존재한다
- PASS: 각 L2 벤치마크 디렉토리에 `docker-compose.yml`이 있고, `docker compose config`로 유효성 검증이 통과한다
- PASS: `docker compose up -d`로 각 L2 벤치마크 환경이 기동되고 헬스체크가 통과한다
- PASS: `benchmarks/l1/`에 L1 픽스처용 `conftest.py`가 있고, pytest에서 픽스처 앱을 in-process로 기동할 수 있는 구조가 준비된다

### 부정 검증

- PASS: `GroundTruth` 모델에 Stage별 확장 필드를 추가해도 `ValidationError`가 발생하지 않는다 (extra="allow")
- PASS: `compute_metrics`에 predicted와 ground_truth 타입이 불일치하면 `TypeError`가 발생한다

### 성능 검증

- PERF: `compute_metrics` — 10,000개 항목 기준 < 100ms

### 테스트 대상

- 측정 유틸리티: `tests/helpers/metrics.py`
- Ground Truth 스키마: `tests/helpers/ground_truth.py`
- Docker Compose: `benchmarks/l2/*/docker-compose.yml`
- L1 픽스처 conftest: `benchmarks/l1/conftest.py`

---

## 인터페이스 계약

### 입력

```python
# 측정 유틸리티 — 제네릭 타입으로 Stage별 유연성 확보
from typing import TypeVar, Callable

T = TypeVar("T")

# predicted: Stage가 산출한 결과 리스트
# ground_truth: 정답 리스트
# match_fn: 두 항목이 같은지 판정하는 함수 (Stage별 커스텀)
#   기본값: operator.eq
# tn: True Negatives 수 (OWASP Benchmark 등 TN이 명시된 벤치마크에서만 제공)
predicted: list[T]
ground_truth: list[T]
match_fn: Callable[[T, T], bool] = operator.eq
tn: int | None = None
```

### 출력

```python
from pydantic import BaseModel, Field

class MetricsResult(BaseModel):
    """측정 유틸리티 출력."""
    true_positives: int = Field(..., description="정탐 수")
    false_positives: int = Field(..., description="오탐 수")
    false_negatives: int = Field(..., description="미탐 수")
    precision: float | None = Field(..., description="정밀도 (predicted 비어있으면 None)")
    recall: float | None = Field(..., description="재현율 (ground_truth 비어있으면 None)")
    f1: float | None = Field(..., description="F1 스코어")
    true_negatives: int | None = Field(default=None, description="정상 판정 수 (제공된 경우에만)")
    youdens_index: float | None = Field(default=None, description="Youden's J = Sensitivity + Specificity - 1 (TN 제공 시에만 산출)")
```

```python
from pydantic import BaseModel, Field

# ARCHITECTURE 3절 모델 재사용
from src.models.interfaces import KnowledgeGraphSnapshot
from src.models.findings import Vulnerability
from src.models.endpoints import Endpoint
from src.models.chains import ChainResult

class GroundTruthChain(BaseModel):
    """체인 정답 한 건."""
    chain_id: str = Field(..., description="체인 식별자")
    steps: list[str] = Field(..., description="체인 단계 순서 (취약점 ID 리스트)")
    impact: str = Field(..., description="최종 영향 설명")

class GroundTruth(BaseModel, extra="allow"):
    """벤치마크 ground truth 최상위 스키마.

    각 Stage SPEC에서 필요한 필드만 채운다.
    이 SPEC은 스키마만 정의하고, 구체적 데이터는 Stage SPEC에서 작성한다.
    """
    app_id: str = Field(..., description="벤치마크 앱 식별자")
    endpoints: list[Endpoint] = Field(default_factory=list, description="정답 엔드포인트 목록")
    vulnerabilities: list[Vulnerability] = Field(default_factory=list, description="정답 취약점 목록")
    kg_snapshot: KnowledgeGraphSnapshot | None = Field(default=None, description="정답 KG 스냅샷")
    chains: list[GroundTruthChain] = Field(default_factory=list, description="정답 공격 체인 목록")
```

---

## 구현 참조

- **ARCHITECTURE.md:** 부록 B — 벤치마크 전략 (L1/L2/L3 계층 정의)
- **ARCHITECTURE.md:** 3절 — Stage 간 인터페이스 계약 (KnowledgeGraphSnapshot, Endpoint, Vulnerability 등)
- **ARCHITECTURE.md:** 16절 — 프로젝트 구조 (`tests/` 미러, `src/models/`)
- **PRD.md:** 기능 0 — 테스트 인프라 수락 기준

---

## 의존성

| SPEC | 이유 |
|------|------|
| 없음 | 최초 SPEC — 다른 모든 SPEC이 이 SPEC에 의존한다 |

---

## 비고

- **L1 픽스처 앱의 구체적 설계(엔드포인트, CWE, 비즈니스 플로)는 이 SPEC에 포함하지 않는다.** Stage 1 SPEC(SPEC-01x)에서 정찰 대상으로, Stage 2 SPEC(SPEC-02x)에서 KG 정답으로, Stage 3 SPEC(SPEC-03x)에서 취약점 정답으로 각각 정의한다. 이 SPEC은 "틀"만 제공한다.
- **L2 벤치마크의 ground truth 데이터 작성도 해당 Stage SPEC 범위.** 이 SPEC은 Docker Compose로 환경이 기동되는 것까지만 검증한다.
- **`tests/helpers/` 모듈은 테스트 전용 공유 코드.** 프로덕션 코드(`src/`)와 분리하여 경계를 명확히 한다.
- `match_fn` 패턴 예시: Stage 1은 URL 정규화 후 비교, Stage 3은 CWE+엔드포인트 조합으로 비교 — 각 Stage SPEC에서 정의한다.
- Youden's Index 산출에는 True Negatives가 필요하다. TN을 계산할 수 없는 경우(오픈 엔드 탐지) `youdens_index`는 `None`을 반환한다.