# Active Scan 개편 - TDD 구현 계획

**Status**: 🔄 In Progress
**Started**: 2026-01-23
**Last Updated**: 2026-01-24

> **TDD 사이클**: 🔴 Red (실패 테스트) → 🟢 Green (최소 구현) → 🔵 Blue (리팩토링)

---

## 📊 전체 진행률

| Phase | 파일 | 설명 | 항목 | 완료 | 진행률 | 커버리지 |
|-------|------|------|------|------|--------|----------|
| 1 | [phase1-foundation.md](./phase1-foundation.md) | 기반 구조 | 26 | 26 | ✅ 100% | 99% |
| 2 | [phase2-basic-modules.md](./phase2-basic-modules.md) | 기본 모듈 | 37 | 37 | ✅ 100% | 93% |
| 3 | [phase3-network-module.md](./phase3-network-module.md) | 네트워크 모듈 | 12 | 12 | ✅ 100% | 95% |
| 4 | [phase4-analysis-modules.md](./phase4-analysis-modules.md) | 분석 모듈 | 21 | 21 | ✅ 100% | 90% |
| 5 | [phase5-advanced-modules.md](./phase5-advanced-modules.md) | 고급 모듈 | 42 | 42 | ✅ 100% | 92% |
| 6 | [phase6-integration.md](./phase6-integration.md) | 통합 테스트 | 14 | 0 | 0% | 목표 80% |
| 7 | [phase7-performance.md](./phase7-performance.md) | 성능/Edge | 21 | 0 | 0% | 목표 80% |
| **총계** | - | - | **173** | **138** | **80%** | **92%** |

---

## 🔗 Phase 의존성 그래프

```
                    ┌─────────────────────┐
                    │   Phase 1           │
                    │   기반 구조          │
                    │   ✅ COMPLETED      │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Phase 2        │ │   Phase 3        │ │   Phase 4        │
│   기본 모듈       │ │   네트워크 모듈   │ │   분석 모듈       │
│   ✅ COMPLETED   │ │   ✅ COMPLETED   │ │   ✅ COMPLETED   │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         │     ┌──────────────┴──────────────┐     │
         │     │                             │     │
         └─────┼─────────────────────────────┼─────┘
               │                             │
               ▼                             ▼
        ┌─────────────────────────────────────────┐
        │            Phase 5                      │
        │            고급 모듈 (Advanced)          │
        │            ✅ COMPLETED                 │
        │  ┌─────────────────────────────────┐    │
        │  │ 5.1 InteractionEngine     ✅    │    │
        │  │ 5.2 TechFingerprint       ✅    │    │
        │  │ 5.3 ThirdPartyDetector    ✅    │    │
        │  │ 5.4 ApiSchemaGenerator    ✅    │    │
        │  └─────────────────────────────────┘    │
        └────────────────────┬────────────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │      Phase 6            │
                │      통합 테스트         │
                │      (Integration)      │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │      Phase 7            │
                │      성능/Edge Case      │
                │      (Performance)      │
                └─────────────────────────┘
```

### 병렬 실행 가능 구간

**Phase 1, 2, 3, 4, 5 완료** ✅ - 다음 Phase가 준비되었습니다:
- Phase 6 (통합 테스트) ⏳ - 진행 가능
- Phase 7 (성능/Edge Case) ⏳ - Phase 6 완료 후

### 숨겨진 의존성

| 컴포넌트 | 의존 대상 | 설명 |
|----------|-----------|------|
| `InteractionEngine` | `NetworkCapturer` ✅ | 네트워크 이벤트 캡처 결과 소비 (Phase 3 완료) |
| `TechFingerprint` | `ResponseAnalyzer` ✅ | 헤더 분석 정보 활용 (Phase 2 완료) |
| `ApiSchemaGenerator` | `NetworkCapturer` ✅ + `JsAnalyzer` ✅ | 복합 의존 - 의존성 충족 (Phase 3, 4 완료) |

---

## 🧪 테스트 실행 가이드

### pytest 마커

```bash
# Discovery 테스트 실행
uv run pytest tests/services/discovery/ -v

# 커버리지 포함
uv run pytest tests/services/discovery/ --cov=app/services/discovery --cov-report=term-missing

# 전체 테스트 (병렬)
uv run pytest -n auto
```

### 커버리지 측정

```bash
# 전체 커버리지
uv run pytest --cov=app --cov-report=html

# 특정 모듈 커버리지
uv run pytest --cov=app/services/discovery --cov-report=term-missing
```

### 코드 품질 검사

```bash
# 린팅
uv run ruff check app/services/discovery/

# 포맷팅 확인
uv run black --check app/services/discovery/
uv run isort --check app/services/discovery/

# 타입 체크
uv run mypy app/services/discovery/
```

---

## 📋 Quality Gate (공통)

각 Phase 완료 시 반드시 통과해야 하는 검증 항목:

### TDD 준수
- [x] 🔴 RED: 테스트가 먼저 작성되어 실패함
- [x] 🟢 GREEN: 최소 코드로 테스트 통과
- [x] 🔵 BLUE: 리팩토링 후에도 테스트 통과

### Build & Tests
- [x] 빌드 성공
- [x] 모든 테스트 통과 (302개)
- [x] 커버리지 목표 달성 (91%)
- [x] Flaky 테스트 없음

### Code Quality
- [x] `ruff check .` - 린팅 에러 없음
- [x] `black --check .` - 포맷팅 준수
- [x] `isort --check .` - import 정렬 준수
- [x] `mypy app/` - 타입 에러 없음

### Security & Performance
- [x] 보안 취약점 없음
- [x] 성능 저하 없음
- [x] 메모리 누수 없음

---

## 🔄 빠른 링크

- **완료됨**: [Phase 1 - 기반 구조](./phase1-foundation.md) ✅
- **완료됨**: [Phase 2 - 기본 모듈](./phase2-basic-modules.md) ✅
- **완료됨**: [Phase 3 - 네트워크 모듈](./phase3-network-module.md) ✅
- **완료됨**: [Phase 4 - 분석 모듈](./phase4-analysis-modules.md) ✅
- **완료됨**: [Phase 5 - 고급 모듈](./phase5-advanced-modules.md) ✅
- **다음 진행**: Phase 6 (통합 테스트)
- **세션 로그**: [session-logs/](./session-logs/)
- **원본 Todolist**: [../todolist.md](../todolist.md) (deprecated)
- **템플릿 참조**: [../plan-template.md](../plan-template.md)

---

## 📝 변경 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2026-01-25 | Phase 5 완료: 고급 모듈 (499 tests, 92% coverage) |
| 2026-01-24 | Phase 3, 4 완료: 네트워크 + 분석 모듈 (302 tests, 91% coverage) |
| 2026-01-23 | Phase 2 완료: 기본 모듈 (97 tests, 93% coverage) |
| 2026-01-23 | Phase 1 완료: 기반 구조 (54 tests, 99% coverage) |
| 2026-01-23 | 초기 문서 생성, 7개 Phase 파일 구조 확립 |
