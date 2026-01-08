[← 메인 문서로 돌아가기](../README.md)

# Backend 설정 가이드

EAZY Backend (Python + FastAPI + UV) 개발 환경을 구축하고 실행하는 방법을 설명합니다.

## 목차

- [개요](#개요)
- [UV 패키지 매니저](#uv-패키지-매니저)
  - [UV란?](#uv란)
  - [UV 설치](#uv-설치)
  - [UV 주요 명령어](#uv-주요-명령어)
- [Backend 프로젝트 구조](#backend-프로젝트-구조)
- [설정 단계](#설정-단계)
  - [1. 저장소 클론](#1-저장소-클론)
  - [2. Docker 컨테이너 시작](#2-docker-컨테이너-시작)
  - [3. 의존성 설치](#3-의존성-설치)
  - [4. 환경 변수 설정](#4-환경-변수-설정)
  - [5. 데이터베이스 마이그레이션](#5-데이터베이스-마이그레이션)
  - [6. 개발 서버 실행](#6-개발-서버-실행)
  - [7. Worker 실행](#7-worker-실행)
- [개발 도구](#개발-도구)
  - [테스트 실행](#테스트-실행)
  - [코드 포맷팅](#코드-포맷팅)
  - [타입 체크](#타입-체크)
- [API 문서](#api-문서)
- [문제 해결](#문제-해결)

---

## 개요

EAZY Backend는 다음 기술 스택으로 구성되어 있습니다:

| 기술 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.12.10 | 백엔드 언어 |
| **UV** | latest | 고속 Python 패키지 매니저 |
| **FastAPI** | 0.115.0+ | 웹 프레임워크 (비동기 지원) |
| **SQLModel** | 0.0.22+ | ORM (Pydantic + SQLAlchemy) |
| **PostgreSQL** | 15 (Alpine) | 메인 데이터베이스 |
| **Redis** | 7 (Alpine) | 비동기 작업 큐 |
| **Playwright** | 1.42.0+ | 브라우저 자동화 (크롤링) |
| **Alembic** | 1.13.0+ | 데이터베이스 마이그레이션 |
| **Pytest** | 8.1.0+ | 테스트 프레임워크 |

---

## UV 패키지 매니저

### UV란?

**UV**는 Rust로 작성된 차세대 Python 패키지 매니저로, pip/poetry/pipenv를 대체합니다.

#### 주요 특징

- **고속 성능**: Rust 기반으로 pip 대비 **10-100배 빠른 설치 속도**
- **자동 가상환경**: venv를 자동으로 생성하고 관리
- **표준 준수**: pyproject.toml 기반 의존성 관리 (PEP 621)
- **Lock 파일**: 재현 가능한 빌드 보장
- **크로스 플랫폼**: macOS, Linux, Windows 모두 지원

#### UV vs pip 비교

```bash
# ❌ pip (기존 방식)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# ✅ UV (새로운 방식)
uv sync  # venv 자동 생성 + 의존성 설치
uv run python script.py  # venv 활성화 없이 실행
```

---

### UV 설치

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell)

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Homebrew (macOS)

```bash
brew install uv
```

#### 설치 확인

```bash
uv --version
# 출력 예: uv 0.5.0
```

> **중요:** UV 설치 후 터미널을 재시작해야 PATH가 적용됩니다.

---

### UV 주요 명령어

#### 의존성 관리

```bash
# pyproject.toml 기반 의존성 설치 (venv 자동 생성)
uv sync

# 패키지 추가 (프로덕션 의존성)
uv add fastapi sqlmodel

# 개발 의존성 추가
uv add --dev pytest black mypy

# 패키지 제거
uv remove <package-name>

# Lock 파일 생성 (의존성 고정)
uv lock

# 설치된 패키지 목록 확인
uv pip list
```

#### 명령 실행

```bash
# venv 내에서 Python 스크립트 실행
uv run python script.py

# venv 내에서 모듈 실행
uv run python -m app.worker

# venv 내에서 Uvicorn 실행
uv run uvicorn app.main:app --reload

# venv 내에서 Pytest 실행
uv run pytest
```

#### 가상환경 관리

```bash
# venv 경로 확인
uv venv --path

# Python REPL 실행
uv run python

# venv 수동 활성화 (선택 사항)
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

> **참고:** UV는 venv를 자동 관리하므로 수동 활성화가 필요 없습니다.

---

## Backend 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 애플리케이션 진입점
│   ├── worker.py                  # Redis Queue Worker
│   │
│   ├── core/                      # 핵심 인프라
│   │   ├── config.py              # 환경 설정 (Pydantic Settings)
│   │   ├── db.py                  # PostgreSQL AsyncEngine
│   │   ├── redis.py               # Redis 연결
│   │   └── queue.py               # TaskManager (Redis Queue)
│   │
│   ├── models/                    # SQLModel 엔티티 (4개)
│   │   ├── project.py
│   │   ├── target.py
│   │   ├── task.py
│   │   └── asset.py
│   │
│   ├── services/                  # 비즈니스 로직 레이어 (5개)
│   │   ├── project_service.py
│   │   ├── target_service.py
│   │   ├── task_service.py
│   │   ├── crawler_service.py
│   │   └── asset_service.py
│   │
│   └── api/v1/endpoints/          # RESTful API (2개)
│       ├── project.py
│       └── task.py
│
├── tests/                         # Pytest 테스트 (11개)
├── alembic/                       # DB 마이그레이션
├── docker/
│   └── docker-compose.yml         # PostgreSQL + Redis
│
├── pyproject.toml                 # UV 의존성 관리
├── alembic.ini                    # Alembic 설정
└── .env                           # 환경 변수 (Git 제외)
```

---

## 설정 단계

### 1. 저장소 클론

```bash
git clone <repository-url>
cd EAZY/backend
```

---

### 2. Docker 컨테이너 시작

PostgreSQL과 Redis 컨테이너를 실행합니다.

```bash
cd docker
docker compose up -d
```

컨테이너 상태 확인:

```bash
docker ps
```

다음과 같은 출력이 나와야 합니다:

```
CONTAINER ID   IMAGE                PORTS                    NAMES
abc123def456   postgres:15-alpine   0.0.0.0:5432->5432/tcp   eazy-postgres
xyz789ghi012   redis:7-alpine       0.0.0.0:6379->6379/tcp   eazy-redis
```

> **자세한 내용:** [Docker 설정 가이드](./DOCKER_SETUP.md)를 참고하세요.

---

### 3. 의존성 설치

프로젝트 루트 (backend/)로 돌아가서 의존성을 설치합니다:

```bash
cd ..  # backend/ 디렉토리로 이동
uv sync
```

**출력 예:**
```
Creating virtualenv at: .venv
Resolved 45 packages in 1.2s
Installed 45 packages in 0.8s
```

> **참고:** `uv sync`는 다음을 자동으로 수행합니다:
> 1. `.venv` 가상환경 생성 (없을 경우)
> 2. `pyproject.toml`에 정의된 모든 의존성 설치
> 3. Lock 파일 생성

---

### 4. 환경 변수 설정

`.env` 파일을 생성합니다:

```bash
touch .env
```

다음 내용을 `.env` 파일에 추가:

```env
# PostgreSQL 설정
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=eazy_db

# Redis 설정
REDIS_URL=redis://localhost:6379/0

# 보안 설정
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8일

# 애플리케이션 설정
PROJECT_NAME=EAZY
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

> **보안 주의:**
> - `SECRET_KEY`는 프로덕션에서 반드시 강력한 랜덤 문자열로 변경
> - `.env` 파일은 Git에 커밋하지 않음 (`.gitignore`에 포함)

---

### 5. 데이터베이스 마이그레이션

Alembic을 사용하여 데이터베이스 스키마를 생성합니다:

```bash
uv run alembic upgrade head
```

**출력 예:**
```
INFO  [alembic.runtime.migration] Running upgrade -> 3d8835436778, create_projects_table
INFO  [alembic.runtime.migration] Running upgrade 3d8835436778 -> b72e50c328e9, create_targets_table
INFO  [alembic.runtime.migration] Running upgrade b72e50c328e9 -> b4ffda872654, create_tasks_table
...
```

---

### 6. 개발 서버 실행

FastAPI 개발 서버를 시작합니다:

```bash
uv run uvicorn app.main:app --reload
```

**출력 예:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**서버 접속:**
- API 기본 URL: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**옵션 설명:**
- `--reload`: 코드 변경 시 자동 재시작 (개발 모드)
- `--host 0.0.0.0`: 외부 접근 허용
- `--port 8000`: 포트 변경

---

### 7. Worker 실행

비동기 크롤링 작업을 처리하는 Worker를 별도 터미널에서 실행합니다:

**새 터미널 창을 열고:**

```bash
cd backend
uv run python -m app.worker
```

**출력 예:**
```
Worker started. Listening for tasks...
```

Worker는 Redis Queue에서 작업을 가져와 Playwright 크롤링을 수행합니다.

---

## 개발 도구

### 테스트 실행

#### 전체 테스트

```bash
uv run pytest
```

#### 특정 파일 테스트

```bash
uv run pytest tests/api/test_projects.py
```

#### 특정 테스트 함수

```bash
uv run pytest tests/api/test_projects.py::test_create_project
```

#### Verbose 모드

```bash
uv run pytest -v
```

#### 커버리지 리포트

```bash
uv run pytest --cov=app --cov-report=html
```

커버리지 리포트는 `htmlcov/index.html`에서 확인 가능합니다.

---

### 코드 포맷팅

#### Black (코드 포맷터)

```bash
# 전체 코드 포맷팅
uv run black .

# 특정 파일 포맷팅
uv run black app/main.py

# Dry-run (변경사항 미리보기)
uv run black --check .
```

#### isort (Import 정렬)

```bash
# Import 정렬
uv run isort .

# 특정 파일
uv run isort app/main.py

# Dry-run
uv run isort --check-only .
```

#### ruff (린터)

```bash
# 린트 검사
uv run ruff check .

# 자동 수정
uv run ruff check --fix .
```

---

### 타입 체크

#### mypy (정적 타입 체크)

```bash
# 전체 타입 체크
uv run mypy .

# 특정 파일
uv run mypy app/main.py

# Strict 모드
uv run mypy --strict .
```

---

## API 문서

FastAPI는 자동으로 API 문서를 생성합니다.

### Swagger UI

http://localhost:8000/docs

**특징:**
- 인터랙티브 API 탐색
- "Try it out" 버튼으로 직접 API 호출 가능
- Request/Response 스키마 자동 생성

### ReDoc

http://localhost:8000/redoc

**특징:**
- 읽기 편한 3단 레이아웃
- 검색 기능
- 다운로드 가능한 OpenAPI JSON

### OpenAPI 스키마

http://localhost:8000/openapi.json

원시 OpenAPI 3.1 스키마를 JSON 형식으로 제공합니다.

---

## 문제 해결

### 1. UV 명령어를 찾을 수 없음

**증상:**
```
command not found: uv
```

**해결 방법:**
```bash
# PATH 확인
echo $PATH

# UV 바이너리 경로 추가
export PATH="$HOME/.local/bin:$PATH"

# 셸 설정 파일에 영구 추가
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc  # bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc   # zsh

# 터미널 재시작
```

---

### 2. PostgreSQL 연결 실패

**증상:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**해결 방법:**
```bash
# 1. Docker 컨테이너 상태 확인
docker ps

# 2. 컨테이너가 없으면 시작
cd docker
docker compose up -d

# 3. PostgreSQL 로그 확인
docker logs eazy-postgres

# 4. 연결 테스트
psql -h localhost -U postgres -d eazy_db
```

---

### 3. Redis 연결 실패

**증상:**
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```

**해결 방법:**
```bash
# 1. Redis 컨테이너 확인
docker ps | grep redis

# 2. 컨테이너 시작
cd docker
docker compose up -d redis

# 3. Redis 연결 테스트
redis-cli ping
# 출력: PONG
```

---

### 4. 포트 충돌 (8000)

**증상:**
```
ERROR:    [Errno 48] error while attempting to bind on address ('127.0.0.1', 8000): address already in use
```

**해결 방법:**
```bash
# 포트 사용 프로세스 확인 (macOS/Linux)
lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
uv run uvicorn app.main:app --reload --port 8001
```

---

### 5. Alembic 마이그레이션 오류

**증상:**
```
FAILED: Target database is not up to date.
```

**해결 방법:**
```bash
# 현재 마이그레이션 상태 확인
uv run alembic current

# 마이그레이션 히스토리 확인
uv run alembic history

# 최신 버전으로 업그레이드
uv run alembic upgrade head

# 문제 지속 시: 데이터베이스 초기화 (개발 환경만)
docker compose down -v  # 볼륨 삭제
docker compose up -d
uv run alembic upgrade head
```

---

### 6. 의존성 설치 실패

**증상:**
```
error: Failed to prepare distributions
```

**해결 방법:**
```bash
# 1. UV 캐시 삭제
uv cache clean

# 2. venv 삭제 후 재생성
rm -rf .venv
uv sync

# 3. 특정 패키지 재설치
uv remove <package-name>
uv add <package-name>
```

---

## 추가 참고 자료

- **[Docker 설정 가이드](./DOCKER_SETUP.md)** - PostgreSQL 및 Redis 관리
- **[문제 해결 가이드](./TROUBLESHOOTING.md)** - 자주 발생하는 오류
- **[API 명세서](../reference/API_REFERENCE.md)** - RESTful API 문서
- **[데이터베이스 스키마](../reference/DATABASE_SCHEMA.md)** - DB 구조 설명
- **UV 공식 문서**: https://github.com/astral-sh/uv

---

**작성:** EAZY Technical Writer
**최종 업데이트:** 2026-01-09
