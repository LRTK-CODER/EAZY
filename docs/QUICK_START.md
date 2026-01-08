# 빠른 시작 가이드 (5분)

> EAZY 프로젝트를 로컬 환경에서 빠르게 실행하기

이 가이드를 따라하면 **5분 안에** EAZY의 Backend와 Frontend를 로컬 환경에서 실행할 수 있습니다.

---

## 📋 전제 조건

다음 도구들이 설치되어 있어야 합니다:

- **Docker Desktop** (PostgreSQL, Redis용)
- **UV** (Python 패키지 매니저) - [설치 가이드](setup/BACKEND_SETUP.md#uv-설치)
- **Node.js** (v18 이상) - [설치 가이드](setup/FRONTEND_SETUP.md#nodejs-설치)

> 💡 **도구가 설치되지 않았나요?** [환경 설정 가이드](setup/ENVIRONMENT_SETUP.md)를 먼저 참고하세요.

---

## 🚀 Step 1: Backend 실행 (3단계)

### 1.1 인프라 시작 (PostgreSQL, Redis)

```bash
cd backend/docker
docker compose up -d
```

**확인**:
```bash
docker ps
```

다음 2개의 컨테이너가 실행 중이어야 합니다:
- `eazy-postgres` (포트 5432)
- `eazy-redis` (포트 6379)

### 1.2 의존성 설치 및 DB 마이그레이션

```bash
cd ..  # backend/ 루트로 이동
uv sync  # 의존성 설치 (자동 venv 생성)
uv run alembic upgrade head  # DB 마이그레이션
```

### 1.3 서버 실행

```bash
uv run uvicorn app.main:app --reload
```

**성공 확인**:
- 터미널에 `Application startup complete` 메시지 출력
- 브라우저에서 http://localhost:8000/docs 접속 (Swagger UI)

### 1.4 Worker 실행 (별도 터미널)

```bash
cd backend
uv run python -m app.worker
```

> **Worker란?** 비동기 크롤링 작업을 처리하는 백그라운드 프로세스입니다.

---

## 🎨 Step 2: Frontend 실행 (2단계)

### 2.1 의존성 설치

```bash
cd frontend
npm install
```

### 2.2 개발 서버 실행

```bash
npm run dev
```

**성공 확인**:
- 터미널에 `Local: http://localhost:5173` 메시지 출력
- 브라우저에서 http://localhost:5173 접속

---

## ✅ Step 3: 첫 API 호출 테스트

### 헬스 체크

```bash
curl http://localhost:8000/health
```

**예상 응답**:
```json
{
  "status": "healthy"
}
```

### 프로젝트 생성

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "My first project"
  }'
```

**예상 응답**:
```json
{
  "id": 1,
  "name": "Test Project",
  "description": "My first project",
  "is_archived": false,
  "archived_at": null,
  "created_at": "2026-01-09T...",
  "updated_at": "2026-01-09T..."
}
```

### Frontend에서 확인

1. 브라우저에서 http://localhost:5173 접속
2. Sidebar에서 "Test Project" 프로젝트 확인
3. 클릭하여 프로젝트 상세 페이지 진입

---

## 🎉 완료!

축하합니다! EAZY 프로젝트가 로컬 환경에서 정상적으로 실행되고 있습니다.

### 다음 단계

1. **개발 시작**
   - [Backend 개발 가이드](development/BACKEND_DEVELOPMENT.md)
   - [Frontend 개발 가이드](development/FRONTEND_DEVELOPMENT.md)
   - [TDD 가이드](development/TDD_GUIDE.md)

2. **테스트 실행**
   ```bash
   # Backend 테스트
   cd backend
   uv run pytest

   # Frontend 테스트
   cd frontend
   npm run test
   ```

3. **API 탐색**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

4. **아키텍처 이해**
   - [시스템 아키텍처](reference/ARCHITECTURE.md)
   - [데이터베이스 스키마](reference/db_schema.md)
   - [API 명세](reference/api_spec.md)

---

## 🚨 문제 해결

### Backend 실행 실패

#### 문제 1: `uvicorn: command not found`
```bash
# 해결: UV가 설치되지 않았거나 PATH 설정이 안됨
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 문제 2: `FATAL: password authentication failed`
```bash
# 해결: PostgreSQL 연결 실패 - Docker 컨테이너 재시작
cd backend/docker
docker compose down
docker compose up -d
```

#### 문제 3: `Address already in use (Port 8000)`
```bash
# 해결: 포트 충돌 - 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9  # macOS/Linux
# Windows: netstat -ano | findstr :8000 후 taskkill /PID <PID> /F
```

### Frontend 실행 실패

#### 문제 1: `npm: command not found`
```bash
# 해결: Node.js가 설치되지 않음
# macOS: brew install node
# Windows: https://nodejs.org/ 에서 다운로드
```

#### 문제 2: `ECONNREFUSED ::1:8000`
```bash
# 해결: Backend가 실행되지 않음
# Backend를 먼저 실행하세요 (Step 1 참고)
```

#### 문제 3: `Port 5173 already in use`
```bash
# 해결: 포트 충돌 - 기존 프로세스 종료
lsof -ti:5173 | xargs kill -9  # macOS/Linux
```

### 더 많은 문제 해결

[문제 해결 가이드](setup/TROUBLESHOOTING.md)에서 일반적인 에러와 해결책을 확인하세요.

---

## 📚 추가 자료

- [프로젝트 개요](reference/PROJECT_OVERVIEW.md)
- [기술 스택](reference/TECH_STACK.md)
- [환경 설정 상세](setup/ENVIRONMENT_SETUP.md)
- [코딩 컨벤션](reference/coding_convention.md)

---

**문서 끝**

> 💡 **Tip**: 메인 문서로 돌아가려면 [README.md](README.md)를 참고하세요.
