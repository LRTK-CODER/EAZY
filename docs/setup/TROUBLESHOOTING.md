[← 메인 문서로 돌아가기](../README.md)

# 문제 해결 가이드

EAZY 프로젝트 개발 중 자주 발생하는 오류와 해결 방법을 정리한 문서입니다.

## 목차

- [자주 하는 실수 방지](#자주-하는-실수-방지)
- [일반적인 에러 및 해결책](#일반적인-에러-및-해결책)
  - [Backend 오류](#backend-오류)
  - [Frontend 오류](#frontend-오류)
  - [Docker 오류](#docker-오류)
  - [데이터베이스 오류](#데이터베이스-오류)
  - [Redis 오류](#redis-오류)
- [디버깅 팁](#디버깅-팁)
- [추가 도움말](#추가-도움말)

---

## 자주 하는 실수 방지

EAZY 프로젝트에서 자주 하는 실수와 올바른 방법을 정리했습니다.

### 1. Backend 패키지 관리

#### ❌ 잘못된 방법: pip 사용

```bash
pip install fastapi
python app/main.py
```

#### ✅ 올바른 방법: UV 사용

```bash
uv add fastapi
uv run python -m app.main
```

**이유:**
- EAZY Backend는 **UV 패키지 매니저**를 필수로 사용합니다.
- pip 사용 시 의존성 충돌 및 가상환경 문제 발생 가능
- UV는 자동 venv 관리 및 Lock 파일을 통한 재현 가능한 빌드 보장

---

### 2. Python 스크립트 실행

#### ❌ 잘못된 방법: 직접 실행

```bash
python script.py
```

#### ✅ 올바른 방법: uv run 사용

```bash
uv run python script.py
```

**이유:**
- `uv run`을 사용하면 자동으로 venv 내에서 실행됩니다.
- 환경 변수 및 의존성이 올바르게 로드됩니다.

---

### 3. TDD (Test-Driven Development)

#### ❌ 잘못된 방법: 테스트 없이 구현

```bash
# 1. 기능 구현
# 2. 테스트 작성 (또는 생략)
```

#### ✅ 올바른 방법: RED → GREEN → REFACTOR

```bash
# 1. RED: 테스트 작성 (실패)
uv run pytest tests/test_new_feature.py

# 2. GREEN: 최소 코드로 테스트 통과
# (구현)

# 3. REFACTOR: 코드 개선
```

**이유:**
- EAZY는 **TDD를 엄격히 준수**합니다.
- 테스트 먼저 작성하면 요구사항이 명확해집니다.
- 리팩토링 시 안전성이 보장됩니다.

---

### 4. 커뮤니케이션 언어

#### ❌ 잘못된 방법: 영어로 대화

```
User: "Implement the project creation feature"
```

#### ✅ 올바른 방법: 한국어로 대화

```
사용자: "프로젝트 생성 기능을 구현해주세요"
```

**이유:**
- EAZY 프로젝트는 **한국어를 표준 언어**로 사용합니다.
- 문서, 커밋 메시지, 코멘트는 한국어로 작성됩니다.

---

### 5. 환경 변수 커밋

#### ❌ 잘못된 방법: .env 파일 커밋

```bash
git add .env
git commit -m "Add environment variables"
```

#### ✅ 올바른 방법: .env.example 사용

```bash
# .env.example 파일 생성 (샘플 값)
cp .env .env.example

# .env.example만 커밋
git add .env.example
git commit -m "docs: add environment variable examples"
```

**이유:**
- `.env` 파일에는 민감한 정보 (DB 비밀번호, API 키) 포함
- `.gitignore`에 `.env`가 포함되어 있음
- `.env.example`로 필요한 환경 변수 구조만 공유

---

## 일반적인 에러 및 해결책

### Backend 오류

#### 1. ModuleNotFoundError: No module named 'app'

**에러 메시지:**
```
ModuleNotFoundError: No module named 'app'
```

**원인:**
- Python 경로 문제
- venv가 활성화되지 않음

**해결 방법:**
```bash
# 1. 올바른 디렉토리 확인
cd backend

# 2. UV로 실행 (자동 venv 활성화)
uv run python -m app.main

# 3. 또는 PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

#### 2. AsyncSession not found

**에러 메시지:**
```
TypeError: 'AsyncSession' object is not callable
```

**원인:**
- SQLAlchemy 비동기 세션 오용
- `await` 키워드 누락

**해결 방법:**
```python
# ❌ 잘못된 코드
result = db.execute(select(Project))

# ✅ 올바른 코드
result = await db.execute(select(Project))
```

---

#### 3. Alembic migration conflict

**에러 메시지:**
```
FAILED: Multiple head revisions are present
```

**원인:**
- 마이그레이션 히스토리 충돌
- 브랜치 병합 시 마이그레이션 파일 중복

**해결 방법:**
```bash
# 1. 마이그레이션 히스토리 확인
uv run alembic history

# 2. 충돌 해결
uv run alembic merge heads

# 3. 새 마이그레이션 생성
uv run alembic revision --autogenerate -m "merge migrations"

# 4. 적용
uv run alembic upgrade head
```

---

### Frontend 오류

#### 1. React Hook 규칙 위반

**에러 메시지:**
```
Error: Rendered more hooks than during the previous render
```

**원인:**
- 조건문 안에서 Hook 호출
- 반복문 안에서 Hook 호출

**해결 방법:**
```typescript
// ❌ 잘못된 코드
if (condition) {
  const [state, setState] = useState(0);
}

// ✅ 올바른 코드
const [state, setState] = useState(0);
if (condition) {
  // state 사용
}
```

---

#### 2. TanStack Query refetch 실패

**에러 메시지:**
```
Error: Query data is undefined
```

**원인:**
- Query 무효화 키 불일치
- 너무 빠른 refetch

**해결 방법:**
```typescript
// ❌ 잘못된 코드
queryClient.invalidateQueries({ queryKey: ['project'] });

// ✅ 올바른 코드 (정확한 키 사용)
queryClient.invalidateQueries({ queryKey: projectKeys.all });

// 또는 특정 쿼리만 무효화
queryClient.invalidateQueries({ queryKey: projectKeys.detail(id) });
```

---

#### 3. TypeScript 타입 오류

**에러 메시지:**
```
Type 'number' is not assignable to type 'string'
```

**원인:**
- 타입 정의 불일치
- API 응답 타입 변경

**해결 방법:**
```typescript
// 1. 타입 정의 확인
interface Project {
  id: number;  // ← number로 정의되어 있는지 확인
  name: string;
}

// 2. API 응답 타입 맞추기
const project: Project = {
  id: Number(data.id),  // 강제 변환
  name: data.name,
};

// 3. Type Guard 사용
if (typeof data.id === 'number') {
  // 안전한 사용
}
```

---

### Docker 오류

#### 1. 컨테이너 시작 실패

**에러 메시지:**
```
Error response from daemon: driver failed programming external connectivity
```

**원인:**
- 포트 충돌
- Docker 네트워크 문제

**해결 방법:**
```bash
# 1. 포트 사용 프로세스 확인
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# 2. 프로세스 종료
kill -9 <PID>

# 3. Docker 네트워크 재설정
docker network prune

# 4. 컨테이너 재시작
docker compose down
docker compose up -d
```

---

#### 2. 볼륨 마운트 권한 오류

**에러 메시지:**
```
ERROR: for postgres  Cannot start service postgres: error while creating mount source path
```

**원인:**
- 파일 시스템 권한 문제
- Docker Desktop 설정

**해결 방법:**
```bash
# macOS: Docker Desktop 설정
# Preferences → Resources → File Sharing
# 프로젝트 디렉토리 추가

# Linux: 권한 설정
sudo chown -R $USER:$USER backend/docker

# 또는 볼륨 재생성
docker compose down -v
docker compose up -d
```

---

### 데이터베이스 오류

#### 1. PostgreSQL 연결 실패

**에러 메시지:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: Connection refused
```

**원인:**
- PostgreSQL 컨테이너 미실행
- 잘못된 연결 정보

**해결 방법:**
```bash
# 1. 컨테이너 상태 확인
docker ps | grep postgres

# 2. 컨테이너 시작
cd backend/docker
docker compose up -d postgres

# 3. 연결 테스트
psql -h localhost -U postgres -d eazy_db

# 4. 환경 변수 확인
cat backend/.env
# POSTGRES_SERVER=localhost
# POSTGRES_PORT=5432
```

---

#### 2. 테이블이 존재하지 않음

**에러 메시지:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "projects" does not exist
```

**원인:**
- 마이그레이션 미실행
- 잘못된 데이터베이스 연결

**해결 방법:**
```bash
# 1. 마이그레이션 상태 확인
uv run alembic current

# 2. 마이그레이션 실행
uv run alembic upgrade head

# 3. 테이블 확인
psql -h localhost -U postgres -d eazy_db -c "\dt"
```

---

#### 3. 외래 키 제약 위반

**에러 메시지:**
```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "targets" violates foreign key constraint
```

**원인:**
- 참조하는 Project가 존재하지 않음
- Cascade 설정 문제

**해결 방법:**
```python
# 1. 참조 무결성 확인
project = await db.get(Project, project_id)
if not project:
    raise HTTPException(status_code=404, detail="Project not found")

# 2. Target 생성
target = Target(project_id=project_id, ...)

# 3. Cascade 설정 확인 (models/target.py)
class Target(SQLModel, table=True):
    project_id: int = Field(foreign_key="projects.id", ondelete="CASCADE")
```

---

### Redis 오류

#### 1. Redis 연결 실패

**에러 메시지:**
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```

**원인:**
- Redis 컨테이너 미실행
- 잘못된 URL

**해결 방법:**
```bash
# 1. Redis 컨테이너 확인
docker ps | grep redis

# 2. 컨테이너 시작
cd backend/docker
docker compose up -d redis

# 3. 연결 테스트
redis-cli ping
# 출력: PONG

# 4. 환경 변수 확인
cat backend/.env
# REDIS_URL=redis://localhost:6379/0
```

---

#### 2. Task Queue 작업 실패

**에러 메시지:**
```
Worker error: Task execution failed
```

**원인:**
- Worker 프로세스 미실행
- Playwright 설치 실패

**해결 방법:**
```bash
# 1. Worker 실행 확인
ps aux | grep worker

# 2. Worker 시작 (별도 터미널)
cd backend
uv run python -m app.worker

# 3. Playwright 브라우저 설치
uv run playwright install chromium

# 4. Worker 로그 확인
# (Worker 터미널 출력 확인)
```

---

## 디버깅 팁

### 1. Backend 디버깅

#### Uvicorn 디버그 모드

```bash
uv run uvicorn app.main:app --reload --log-level debug
```

#### Python 디버거 (pdb) 사용

```python
# 코드에 브레이크포인트 추가
import pdb; pdb.set_trace()

# 또는 Python 3.7+
breakpoint()
```

#### 로깅 활성화

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

---

### 2. Frontend 디버깅

#### React DevTools

브라우저 확장 프로그램 설치:
- [React Developer Tools (Chrome)](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)

#### TanStack Query DevTools

```typescript
// main.tsx에 추가
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

브라우저에서 TanStack Query 아이콘 클릭.

#### Console 로깅

```typescript
console.log('Debug:', data);
console.table(projects);  // 배열을 테이블로 출력
console.trace();  // 호출 스택 추적
```

---

### 3. 네트워크 디버깅

#### Backend API 요청 확인

```bash
# curl로 API 테스트
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project"}'

# HTTPie 사용 (더 읽기 쉬움)
http POST http://localhost:8000/api/v1/projects/ name="Test Project"
```

#### 브라우저 Network 탭

1. 개발자 도구 (F12) → Network 탭
2. API 요청 클릭 → Headers, Payload, Response 확인
3. "Preserve log" 체크 (페이지 새로고침 시에도 유지)

---

### 4. 데이터베이스 디버깅

#### SQL 쿼리 로깅

```python
# backend/app/core/db.py
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # SQL 쿼리 출력
)
```

#### 직접 SQL 실행

```bash
psql -h localhost -U postgres -d eazy_db

# 쿼리 실행
SELECT * FROM projects WHERE is_archived = false;
```

---

## 추가 도움말

### 공식 문서

- **[Backend 설정 가이드](./BACKEND_SETUP.md)** - Backend 실행 및 관리
- **[Frontend 설정 가이드](./FRONTEND_SETUP.md)** - Frontend 실행 및 관리
- **[Docker 설정 가이드](./DOCKER_SETUP.md)** - Docker 컨테이너 관리
- **[빠른 시작 가이드](../QUICK_START.md)** - 5분 안에 시작하기

### 커뮤니티 및 지원

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **프로젝트 문서**: [docs/README.md](../README.md)
- **기술 스택 공식 문서**:
  - [FastAPI](https://fastapi.tiangolo.com/)
  - [React](https://react.dev/)
  - [UV](https://github.com/astral-sh/uv)
  - [TanStack Query](https://tanstack.com/query/latest)

### 로그 수집 방법

문제 해결을 위해 다음 로그를 수집하세요:

```bash
# Backend 로그
uv run uvicorn app.main:app --reload > backend.log 2>&1

# Worker 로그
uv run python -m app.worker > worker.log 2>&1

# Docker 로그
docker logs eazy-postgres > postgres.log
docker logs eazy-redis > redis.log

# Frontend 콘솔 로그
# 브라우저 개발자 도구 → Console → 우클릭 → Save as...
```

---

**작성:** EAZY Technical Writer
**최종 업데이트:** 2026-01-09
