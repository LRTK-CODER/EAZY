# 커밋 메시지 컨벤션

> Conventional Commits 기반 + SPEC 추적

---

## 형식

```
<type>(<scope>): <subject>

[body]

[footer]
```

---

## type

| type | 용도 | 예시 |
|------|------|------|
| `red` | 🔴 실패하는 테스트 작성 (TDD RED) | `red(SPEC-001): 세션 미들웨어 쿠키 저장 테스트` |
| `green` | 🟢 테스트 통과 최소 구현 (TDD GREEN) | `green(SPEC-001): 쿠키 자동 저장 구현` |
| `refactor` | 🔵 동작 변경 없이 코드 개선 (TDD REFACTOR) | `refactor(SPEC-001): CookieJar 클래스 추출` |
| `feat` | TDD 외 신규 기능 | `feat(SPEC-012): LLM 종합 해석 프롬프트 추가` |
| `fix` | 버그 수정 | `fix(SPEC-003): registry.yaml 파싱 시 빈 카테고리 처리` |
| `test` | 테스트 추가/수정 (RED 외) | `test(SPEC-011): WhatWeb 타임아웃 엣지케이스 추가` |
| `docs` | 문서 변경 | `docs: PRD 성공 지표 측정 방법 추가` |
| `plan` | SPEC/TASK/PRD/ARCHITECTURE 변경 | `plan: SPEC-014 Knowledge Graph 검증 기준 작성` |
| `skill` | Skill 파일 추가/수정 | `skill: sqli_blind.skill 타임 기반 변형 추가` |
| `plugin` | 스캐너 플러그인 추가/수정 | `plugin: ffuf 디렉토리 스캐너 플러그인 등록` |
| `docker` | Dockerfile/빌드 스크립트 변경 | `docker: nuclei.Dockerfile 추가` |
| `ci` | CI/CD 설정 변경 | `ci: GitHub Actions pytest 워크플로우` |
| `chore` | 빌드, 의존성, 설정 등 | `chore: httpx 0.28 → 0.29 업데이트` |
| `style` | 포맷팅, 린트 (동작 변경 없음) | `style: ruff 자동 수정 적용` |

---

## scope

**SPEC 번호가 있으면 반드시 포함한다.** SPEC과 무관한 변경만 scope를 생략하거나 자유 형식으로 쓴다.

```
red(SPEC-001): ...       ← SPEC 번호가 scope
fix(SPEC-003): ...       ← SPEC 번호가 scope
docs: ...                ← SPEC 무관, scope 생략
chore(deps): ...         ← 자유 형식 scope
```

---

## subject

- 한국어 또는 영어 (프로젝트 통일)
- 명령문으로 작성 ("추가한다" 아니라 "추가")
- 50자 이내
- 마침표 없음
- "무엇을 했는지"가 아니라 "왜/무엇이 달라졌는지"

```
# 좋은 예
green(SPEC-001): JWT 만료 5초 전 자동 갱신 구현
fix(SPEC-011): 스캐너 타임아웃 시 나머지 플러그인 계속 실행

# 나쁜 예
green(SPEC-001): session_middleware.py 수정       ← 파일명은 의미 없음
fix(SPEC-011): 버그 수정                          ← 무슨 버그인지 안 보임
```

---

## body (선택)

- 빈 줄 하나 띄우고 작성
- "왜" 이 변경이 필요한지 설명
- 72자 줄바꿈

```
green(SPEC-001): JWT 만료 5초 전 자동 갱신 구현

세션 미들웨어가 JWT 만료 시각을 추적하고,
만료 5초 전에 refresh token으로 자동 갱신한다.
갱신 실패 시 SessionExpired 이벤트를 발행하여
코어 엔진이 재인증을 시도할 수 있게 한다.
```

---

## footer (선택)

```
# SPEC 검증 기준 통과 기록
Verifies: SPEC-001 PASS "JWT 만료 전 자동 갱신"

# 관련 이슈
Refs: #42

# 브레이킹 체인지
BREAKING CHANGE: ReconOutput에 crypto_context 필드 추가 (None 허용)
```

---

## TDD 사이클 커밋 예시

하나의 Feature에 대한 전체 사이클:

```bash
# 1. RED — 실패하는 테스트
git add tests/
git commit -m "red(SPEC-001): 세션 미들웨어 쿠키/JWT/CSRF 테스트

SPEC-001의 검증 기준 5개에 대응하는 테스트 작성.
ModuleNotFoundError로 전부 실패 (구현 미존재)."

# 2. GREEN — 최소 구현
git add src/
git commit -m "green(SPEC-001): 쿠키 자동 저장 + JWT 갱신 + CSRF 주입 구현

Verifies: SPEC-001 PASS \"Set-Cookie 자동 저장 후 다음 요청에 주입\"
Verifies: SPEC-001 PASS \"JWT 만료 5초 전 자동 갱신\"
Verifies: SPEC-001 PASS \"CSRF 토큰 응답에서 추출하여 POST에 삽입\""

# 3. REFACTOR — 품질 개선
git commit -m "refactor(SPEC-001): SessionMiddleware에서 CookieJar 분리

단일 책임 원칙 적용. 순환 복잡도 12→4 감소."
```

---

## 문서 변경 커밋 예시

```bash
# PRD 변경
git commit -m "docs: PRD 기능 0 테스트 인프라 추가"

# SPEC 작성
git commit -m "plan: SPEC-000 테스트 인프라 검증 기준 작성"

# ARCHITECTURE 변경
git commit -m "plan: ARCHITECTURE Stage 간 인터페이스 계약 추가

ReconOutput, AttackPlan, ExploitResult Pydantic 모델 정의.
BREAKING CHANGE: Stage 2 입력이 dict에서 ReconOutput으로 변경."

# TASK 작성
git commit -m "plan: TASK-001 세션 미들웨어 TDD 계획 작성"
```

---

## Skill/플러그인/Docker 커밋 예시

```bash
# Skill 추가
git commit -m "skill: waf_cloudflare.skill 더블 인코딩 우회 패턴 추가"

# 플러그인 추가
git commit -m "plugin: ffuf 디렉토리 스캐너 플러그인

registry.yaml에 등록, dockers/ffuf.Dockerfile 추가.
config.yaml에서 enabled: false 기본값."

# Docker
git commit -m "docker: nuclei.Dockerfile v3.4.1 기반 이미지"
```

---

## git log에서 SPEC 추적

```bash
# SPEC-001 관련 모든 커밋
git log --oneline --grep="SPEC-001"

# TDD RED만
git log --oneline --grep="^red("

# 문서 변경만
git log --oneline --grep="^plan:"

# Skill 변경만
git log --oneline --grep="^skill:"
```