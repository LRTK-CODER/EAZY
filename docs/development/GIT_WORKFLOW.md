# Git 워크플로우 (Git Workflow)

[← 메인 문서로 돌아가기](../README.md)

**작성일**: 2026-01-09
**대상 독자**: 모든 개발자

---

## 목차

- [브랜치 전략](#브랜치-전략)
- [Commit 규칙 (Conventional Commits)](#commit-규칙-conventional-commits)
- [Commit 메시지 형식](#commit-메시지-형식)
- [PR 생성 가이드](#pr-생성-가이드)
- [코드 리뷰 프로세스](#코드-리뷰-프로세스)
- [예시 시나리오](#예시-시나리오)

---

## 브랜치 전략

EAZY 프로젝트는 **Trunk-based Development / GitHub Flow** 전략을 사용합니다.

### 핵심 원칙

1. **main 브랜치는 항상 배포 가능한 상태**
2. **짧은 수명의 feature 브랜치**
3. **빠른 통합, 빈번한 배포**

### 브랜치 구조

```
main (프로덕션 배포 브랜치)
  ├── feat/project-management (기능 개발)
  ├── feat/target-crud (기능 개발)
  ├── fix/project-archive-bug (버그 수정)
  ├── docs/api-documentation (문서 작업)
  └── refactor/service-layer (리팩토링)
```

### 브랜치 네이밍 규칙

| 접두사 | 용도 | 예시 |
|--------|------|------|
| `feat/` | 새로운 기능 개발 | `feat/asset-discovery` |
| `fix/` | 버그 수정 | `fix/target-validation-error` |
| `docs/` | 문서 작업 | `docs/setup-guide` |
| `refactor/` | 코드 리팩토링 | `refactor/crawler-service` |
| `test/` | 테스트 코드 추가 | `test/project-crud` |
| `chore/` | 빌드, 패키지 수정 | `chore/update-dependencies` |
| `style/` | 코드 포맷팅 | `style/fix-linting` |

### 브랜치 생성 및 작업 흐름

```bash
# 1. main에서 최신 코드 가져오기
git checkout main
git pull origin main

# 2. feature 브랜치 생성
git checkout -b feat/my-feature

# 3. 작업 수행 (TDD: RED → GREEN → REFACTOR)
# ... 코드 작성 및 커밋 ...

# 4. 원격 브랜치에 push
git push origin feat/my-feature

# 5. Pull Request 생성 (GitHub)
# ... PR 작성 및 리뷰 요청 ...

# 6. 리뷰 승인 후 main에 merge
# ... Squash and Merge 권장 ...

# 7. 로컬 브랜치 삭제
git checkout main
git pull origin main
git branch -d feat/my-feature
```

---

## Commit 규칙 (Conventional Commits)

EAZY 프로젝트는 **Conventional Commits** 규칙을 따릅니다.

### Commit Type

| Type | 설명 | 예시 |
|------|------|------|
| **feat** | 새로운 기능 추가 | `feat: add project archive functionality` |
| **fix** | 버그 수정 | `fix: resolve target validation error` |
| **docs** | 문서 수정 | `docs: update API specification` |
| **style** | 코드 포맷팅 (로직 변경 없음) | `style: format project service with black` |
| **refactor** | 코드 리팩토링 | `refactor: extract common validation logic` |
| **test** | 테스트 코드 추가 | `test: add project CRUD tests (TDD RED)` |
| **chore** | 빌드, 패키지 수정 | `chore: update fastapi to 0.115.1` |
| **perf** | 성능 개선 | `perf: optimize crawler query performance` |
| **ci** | CI/CD 설정 변경 | `ci: add GitHub Actions workflow` |
| **revert** | 커밋 되돌리기 | `revert: revert "feat: add feature X"` |

### Scope (선택 사항)

특정 모듈이나 영역을 명시합니다.

```bash
feat(frontend): implement ProjectDetailPage
fix(backend): resolve asset deduplication bug
docs(setup): add UV installation guide
test(api): add project archive tests (TDD GREEN)
```

**권장 Scope**:
- `frontend`: Frontend 코드
- `backend`: Backend 코드
- `api`: API 엔드포인트
- `db`: 데이터베이스 관련
- `ui`: UI 컴포넌트
- `docs`: 문서
- `deps`: 의존성
- `setup`: 환경 설정

---

## Commit 메시지 형식

### 기본 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 예시 1: 단순 커밋

```bash
feat(frontend): add CreateProjectForm component
```

### 예시 2: 상세 커밋

```bash
feat(frontend): implement ProjectDetailPage Target integration

- Add TargetList component with scan trigger
- Integrate CreateTargetForm dialog
- Add Task status polling (5s interval)
- Write 28 comprehensive tests (TDD GREEN)

Closes #42
```

### 예시 3: TDD 커밋

```bash
test(frontend): add ProjectDetailPage extension tests (TDD RED)

- Test Target list rendering
- Test CreateTargetForm dialog
- Test scan trigger functionality
- Test Task status polling

Total: 28 tests (intentionally failing)
```

```bash
feat(frontend): implement ProjectDetailPage Target features (TDD GREEN)

- Implement TargetList component
- Implement CreateTargetForm integration
- Implement scan trigger with polling
- All 28 tests now passing

Phase 4 Task 4.22 completed
```

### 규칙

1. **subject는 50자 이내**로 간결하게 작성
2. **subject는 명령문**으로 작성 (예: "Add" not "Added")
3. **subject는 대문자로 시작**
4. **subject 끝에 마침표 금지**
5. **body는 72자마다 줄바꿈**
6. **body는 "무엇을", "왜" 했는지 설명** (어떻게는 코드에서 확인 가능)
7. **footer는 이슈 번호 또는 Breaking Changes 명시**

---

## PR 생성 가이드

### PR 템플릿

```markdown
## 변경 사항

<!-- 이 PR에서 무엇을 변경했는지 간략히 설명 -->

### 주요 변경
- [ ] Feature 1
- [ ] Feature 2

### 기술적 세부사항
<!-- 구현 방법, 설계 결정, 트레이드오프 등 -->

## 테스트

### 테스트 전략
- [ ] 단위 테스트 추가 (TDD)
- [ ] 통합 테스트 추가
- [ ] 수동 테스트 완료

### 테스트 결과
<!-- pytest 또는 npm test 실행 결과 -->

```bash
$ uv run pytest -v
... 30 tests passed
```

## 체크리스트

- [ ] 코드가 프로젝트 코딩 컨벤션을 따릅니다
- [ ] 테스트를 작성했고 모두 통과합니다 (TDD)
- [ ] 문서를 업데이트했습니다
- [ ] Commit 메시지가 Conventional Commits 규칙을 따릅니다
- [ ] Breaking Changes가 있다면 명시했습니다

## 관련 이슈

Closes #<issue-number>

## 스크린샷 (UI 변경 시)

<!-- UI 변경 사항이 있다면 스크린샷 첨부 -->
```

### PR 생성 체크리스트

1. **브랜치가 최신 main을 기준으로 하는가?**
   ```bash
   git checkout main
   git pull origin main
   git checkout feat/my-feature
   git rebase main
   ```

2. **모든 테스트가 통과하는가?**
   ```bash
   # Backend
   cd backend && uv run pytest

   # Frontend
   cd frontend && npm run test
   ```

3. **Linter 및 Formatter 실행했는가?**
   ```bash
   # Backend
   cd backend
   uv run black .
   uv run isort .
   uv run mypy .

   # Frontend
   cd frontend
   npm run lint
   npm run format
   ```

4. **Commit 메시지가 Conventional Commits 규칙을 따르는가?**

5. **관련 문서를 업데이트했는가?**

---

## 코드 리뷰 프로세스

### 리뷰어 가이드

#### 1. 리뷰 체크리스트

- [ ] **기능 요구사항 충족**: PR이 요구사항을 만족하는가?
- [ ] **코드 품질**: 가독성, 유지보수성이 좋은가?
- [ ] **테스트 커버리지**: TDD를 따랐는가? 테스트가 충분한가?
- [ ] **성능**: 성능 문제가 없는가?
- [ ] **보안**: 보안 취약점이 없는가?
- [ ] **문서**: 문서가 업데이트되었는가?
- [ ] **컨벤션**: 프로젝트 컨벤션을 따르는가?

#### 2. 리뷰 코멘트 작성

```markdown
# Good: 구체적이고 건설적인 피드백
이 함수는 SRP(Single Responsibility Principle)를 위반합니다.
다음과 같이 분리하는 것을 권장합니다:
- `validate_user()`: 사용자 검증
- `create_user()`: 사용자 생성

# Bad: 모호하고 비판적인 피드백
이 코드는 이상합니다.
```

#### 3. 리뷰 우선순위

1. **Critical**: 버그, 보안 취약점
2. **High**: 성능 문제, 설계 결함
3. **Medium**: 가독성, 컨벤션
4. **Low**: 네이밍, 포맷팅 (자동화 가능한 부분)

### 작성자 가이드

#### 1. 리뷰 요청 전 Self-Review

- [ ] 코드를 다시 한 번 읽어보았는가?
- [ ] 불필요한 디버깅 코드를 제거했는가?
- [ ] 주석이 명확한가?
- [ ] 테스트가 모두 통과하는가?

#### 2. 리뷰 코멘트 대응

- **감사 표현**: "Good catch! 수정하겠습니다."
- **설명 제공**: "이 방식을 선택한 이유는 X입니다."
- **대안 제시**: "Y 방식도 고려했으나, Z 때문에 현재 방식을 선택했습니다."
- **추가 질문**: "A와 B 중 어느 것이 더 좋을까요?"

#### 3. 리뷰 완료 후

- 모든 코멘트에 대응했는지 확인
- Re-review 요청 (필요시)
- Merge 전 최종 테스트 실행

### Merge 전략

EAZY 프로젝트는 **Squash and Merge**를 권장합니다.

**장점**:
- main 브랜치 히스토리가 깔끔해집니다.
- 하나의 PR이 하나의 커밋으로 표현됩니다.
- Revert가 간편합니다.

**예시**:
```bash
# feature 브랜치의 여러 커밋
feat: add CreateProjectForm (TDD RED)
feat: implement CreateProjectForm logic (TDD GREEN)
refactor: improve CreateProjectForm (TDD REFACTOR)
fix: resolve form validation issue

# Squash and Merge 후 main의 하나의 커밋
feat(frontend): implement CreateProjectForm with validation

- Add form component with React Hook Form
- Add Zod schema validation
- Write 12 comprehensive tests (TDD)
- All tests passing (12/12)

Closes #42
```

---

## 예시 시나리오

### 시나리오 1: 새로운 기능 개발 (TDD)

```bash
# 1. feature 브랜치 생성
git checkout main
git pull origin main
git checkout -b feat/asset-discovery

# 2. TDD RED Phase: 테스트 작성
# ... 테스트 코드 작성 ...
git add tests/api/test_assets.py
git commit -m "test(api): add asset discovery tests (TDD RED)"

# 3. TDD GREEN Phase: 최소 구현
# ... 구현 코드 작성 ...
git add app/api/v1/endpoints/asset.py app/services/asset_service.py
git commit -m "feat(backend): implement asset discovery API (TDD GREEN)"

# 4. TDD REFACTOR Phase: 코드 개선
# ... 리팩토링 ...
git add app/services/asset_service.py
git commit -m "refactor(backend): improve asset service readability (TDD REFACTOR)"

# 5. 문서 업데이트
# ... 문서 수정 ...
git add docs/reference/API_REFERENCE.md
git commit -m "docs(api): add asset discovery endpoints"

# 6. Push 및 PR 생성
git push origin feat/asset-discovery
# GitHub에서 PR 생성
```

### 시나리오 2: 버그 수정

```bash
# 1. fix 브랜치 생성
git checkout main
git pull origin main
git checkout -b fix/target-validation-error

# 2. 버그 재현 테스트 작성
# ... 실패하는 테스트 작성 ...
git add tests/api/test_targets.py
git commit -m "test(api): add test for target validation bug (TDD RED)"

# 3. 버그 수정
# ... 버그 수정 코드 ...
git add app/services/target_service.py
git commit -m "fix(backend): resolve target URL validation error

The URL validation was not handling subdomains correctly.
Updated regex pattern to support all subdomain levels.

Fixes #123"

# 4. Push 및 PR 생성
git push origin fix/target-validation-error
```

### 시나리오 3: 문서 작업

```bash
# 1. docs 브랜치 생성
git checkout main
git pull origin main
git checkout -b docs/deployment-guide

# 2. 문서 작성
# ... 문서 작성 ...
git add docs/development/DEPLOYMENT.md
git commit -m "docs(deployment): add deployment guide

- Add Docker build instructions
- Add environment variable configuration
- Add production checklist"

# 3. Push 및 PR 생성
git push origin docs/deployment-guide
```

---

## 참고 자료

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Trunk-based Development](https://trunkbaseddevelopment.com/)
- [Backend Development Guide (BACKEND_DEVELOPMENT.md)](./BACKEND_DEVELOPMENT.md)
- [Frontend Development Guide (FRONTEND_DEVELOPMENT.md)](./FRONTEND_DEVELOPMENT.md)
- [TDD Guide (TDD_GUIDE.md)](./TDD_GUIDE.md)

---

**다음 문서**: [Backend Development Guide (BACKEND_DEVELOPMENT.md)](./BACKEND_DEVELOPMENT.md)
