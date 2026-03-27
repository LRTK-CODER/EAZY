# TASK-003: 벤치마크 환경 — TDD 구현 계획

> **SPEC:** `plans/specs/SPEC-000-test-infra.md` Feature 3
> **ARCHITECTURE:** `plans/ARCHITECTURE.md` 부록 B, 16절
> **PRD 기능:** 기능 0
> **날짜:** 2026-03-27
> **테스트 러너:** pytest | Docker Compose

---

## 문서 계층에서의 위치

```
PRD.md          → 수락 기준 (Given-When-Then)
ARCHITECTURE.md → 구조 설계 (어떤 구조로)
SPEC-000.md     → 검증 기준 + 인터페이스 계약 ← 이것이 테스트의 근거
TASK-003.md     → 이 문서: 벤치마크 환경 TDD 계획
```

---

## 프로젝트 컨텍스트

- **벤치마크 디렉토리**: `benchmarks/`
- **테스트 커맨드**: `uv run pytest tests/benchmarks/test_benchmark_env.py -v`
- **Docker 테스트**: `uv run pytest tests/benchmarks/test_benchmark_env.py -v -m slow` (헬스체크 포함)

## 세션 격리 규칙

- 🔴 RED, 🟢 GREEN, 🔵 REFACTOR는 **각각 별도 AI 세션**에서 실행
- RED 세션에 구현 컨텍스트를 제공하지 않음
- GREEN 세션에서 테스트 파일 수정 절대 금지

---

## SPEC 검증 기준 → 테스트 매핑

| SPEC 검증 기준 | 테스트 함수 |
|---------------|------------|
| `PASS: benchmarks/ 디렉토리 구조 존재` | `test_benchmark_directories_exist` |
| `PASS: docker-compose.yml 유효` | `test_docker_compose_config_valid` |
| `PASS: docker compose up 헬스체크 통과` | `test_docker_compose_up_healthcheck` |
| `PASS: l1 conftest.py 존재 + 픽스처 구조` | `test_l1_conftest_fixture_structure` |

---

## 진행 현황

| 단계 | 상태 |
|------|------|
| 🔴 RED | [ ] pending |
| 🟢 GREEN | [ ] pending |
| 🔵 REFACTOR | [ ] pending |

---

### Task 3.1 🔴 RED — 실패하는 테스트 작성

**세션**: 격리됨 — 구현 컨텍스트 없음
**상태**: [ ] pending

**동작 명세**:
- `benchmarks/` 아래 `l1/`, `l2/owasp-benchmark/`, `l2/wivet/`, `l2/conduit/` 디렉토리가 존재한다
- 각 L2 디렉토리에 `docker-compose.yml`이 있고 `docker compose config`로 유효성 검증 통과
- `docker compose up -d`로 환경 기동 + 헬스체크 통과
- `benchmarks/l1/conftest.py`가 존재하고 pytest 픽스처 구조가 준비됨

**테스트 파일**: `tests/benchmarks/test_benchmark_env.py`

**작성할 테스트 함수**:

| 테스트명 | SPEC 검증 기준 | 검증 내용 |
|----------|---------------|-----------|
| `test_benchmark_directories_exist` | PASS: 디렉토리 존재 | l1, l2/owasp-benchmark, l2/wivet, l2/conduit |
| `test_docker_compose_config_valid` | PASS: docker-compose 유효 | `docker compose config` exit 0 (parametrize: 3개 L2) |
| `test_docker_compose_up_healthcheck` | PASS: 환경 기동 + 헬스체크 | 컨테이너 healthy 상태 (parametrize: 3개 L2) |
| `test_l1_conftest_fixture_structure` | PASS: conftest 구조 | conftest.py 존재 + 픽스처 함수 정의 확인 |

**parametrize 케이스** (`test_docker_compose_config_valid`, `test_docker_compose_up_healthcheck`):

| 벤치마크 디렉토리 |
|------------------|
| `benchmarks/l2/owasp-benchmark` |
| `benchmarks/l2/wivet` |
| `benchmarks/l2/conduit` |

**테스트 마크**:
- `test_docker_compose_up_healthcheck` → `@pytest.mark.slow` (Docker 기동 필요, CI에서 선택 실행)
- `test_docker_compose_config_valid` → `@pytest.mark.docker` (Docker CLI 필요)

**필요한 픽스처**:
- 프로젝트 루트 경로 (`conftest.py`에서 제공)

**예상 실패**: `AssertionError` (디렉토리/파일 미존재)

**단계 게이트 ✓**:
- [ ] `uv run pytest tests/benchmarks/test_benchmark_env.py -v -k "not slow and not docker"` exit non-zero
- [ ] 모든 실패가 `AssertionError`
- [ ] 구현 파일 생성/수정 없음
- [ ] `git add tests/ && git commit -m "red(SPEC-000): 벤치마크 환경 실패 테스트"`

---

### Task 3.2 🟢 GREEN — 벤치마크 환경 구축

**세션**: 격리됨 — 테스트 파일 읽기만, 수정 금지
**상태**: [ ] pending
**의존성**: Task 3.1 ✅

**입력**: `tests/benchmarks/test_benchmark_env.py`
**참조**: `plans/ARCHITECTURE.md` 부록 B

**파일**:

**생성:**
- `benchmarks/l1/__init__.py` — 패키지 초기화
- `benchmarks/l1/conftest.py` — L1 픽스처 앱 기동용 pytest fixture 구조
- `benchmarks/l2/owasp-benchmark/docker-compose.yml` — OWASP Benchmark 환경
- `benchmarks/l2/wivet/docker-compose.yml` — WIVET 환경
- `benchmarks/l2/conduit/docker-compose.yml` — RealWorld Conduit 환경

**Docker Compose 참고** (2026-03-27 사전 조사 완료):
- OWASP Benchmark: `owasp/benchmark:latest` (Docker Hub 공식). 포트 8443. 헬스체크: `/benchmark/`
- WIVET: `andresriancho/wivet` (커뮤니티, 가장 널리 사용). PHP+MySQL. 포트 80. 대안: `owaspvwad/wivet`, `psiinon/wivet`
- Conduit (RealWorld): `TonyMckes/conduit-realworld-example-app` (React + Express + PostgreSQL). docker-compose 포함. RealWorld API 스펙 준수

**수정 금지:**
- `tests/benchmarks/test_benchmark_env.py`

**단계 게이트 ✓**:
- [ ] `uv run pytest tests/benchmarks/test_benchmark_env.py -v -k "not slow"` exit 0 (docker compose up 제외)
- [ ] 각 L2 디렉토리에서 `docker compose config` 통과
- [ ] 테스트 파일 변경 없음
- [ ] `git commit -m "green(SPEC-000): 벤치마크 환경 디렉토리 + Docker Compose"`

---

### Task 3.3 🔵 REFACTOR — 벤치마크 환경 개선

**세션**: 격리됨
**상태**: [ ] pending
**의존성**: Task 3.2 ✅

**평가 체크리스트**:
- [ ] Docker Compose 파일에 헬스체크 정의
- [ ] 불필요한 포트 노출 없음
- [ ] 네트워크 격리 (벤치마크별 독립 네트워크)
- [ ] `.env.example` 필요 여부 검토
- [ ] conftest.py 구조 명확 (fixture 이름, scope 등)

**결정**: [ ] 리팩토링 수행 / [ ] 건너뛰기

**단계 게이트 ✓**:
- [ ] 전체 테스트 스위트 통과
- [ ] 각 Docker Compose에 헬스체크 존재
- [ ] `git commit -m "refactor(SPEC-000): 벤치마크 환경 [개선 내용]"`

---

## SPEC 검증 완료 체크리스트

| SPEC 검증 기준 | 테스트 통과 | 비고 |
|---------------|-----------|------|
| `PASS: 디렉토리 구조 존재` | [ ] | test_benchmark_directories_exist |
| `PASS: docker-compose 유효` | [ ] | test_docker_compose_config_valid |
| `PASS: docker compose up 헬스체크` | [ ] | test_docker_compose_up_healthcheck |
| `PASS: l1 conftest 구조` | [ ] | test_l1_conftest_fixture_structure |
