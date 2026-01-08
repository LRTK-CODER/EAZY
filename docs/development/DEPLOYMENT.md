# 배포 가이드 (Deployment Guide)

[← 메인 문서로 돌아가기](../README.md)

**작성일**: 2026-01-09
**대상 독자**: DevOps 엔지니어, 백엔드/프론트엔드 개발자

---

## 목차

- [배포 개요](#배포-개요)
- [환경 변수 설정](#환경-변수-설정)
- [프로덕션 빌드](#프로덕션-빌드)
- [Docker 배포](#docker-배포)
- [수동 배포](#수동-배포)
- [배포 체크리스트](#배포-체크리스트)
- [모니터링 및 로깅](#모니터링-및-로깅)
- [롤백 전략](#롤백-전략)
- [트러블슈팅](#트러블슈팅)

---

## 배포 개요

### 배포 아키텍처

```
┌─────────────────┐
│   Load Balancer │  (예: Nginx, Traefik)
└────────┬────────┘
         │
    ┌────┴─────────────┬──────────────┐
    │                  │              │
┌───▼──────┐   ┌──────▼─────┐  ┌─────▼─────┐
│ Frontend │   │  Backend   │  │  Worker   │
│ (Static) │   │  (FastAPI) │  │ (Redis Q) │
└──────────┘   └──────┬─────┘  └─────┬─────┘
                      │              │
              ┌───────┴──────┬───────┘
              │              │
         ┌────▼────┐   ┌─────▼────┐
         │PostgreSQL│   │  Redis   │
         └─────────┘   └──────────┘
```

### 지원 배포 방법

1. **Docker Compose** (권장): 개발 및 소규모 프로덕션
2. **Kubernetes**: 대규모 프로덕션 (추후 지원)
3. **수동 배포**: 단일 서버 환경

---

## 환경 변수 설정

### Backend 환경 변수 (.env)

**개발 환경** (`backend/.env.development`):
```bash
# API 설정
API_V1_STR=/api/v1
PROJECT_NAME=EAZY Backend (Development)

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=eazy_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (개발 환경)
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8 days

# CORS (개발 환경)
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Logging
LOG_LEVEL=DEBUG
```

**프로덕션 환경** (`backend/.env.production`):
```bash
# API 설정
API_V1_STR=/api/v1
PROJECT_NAME=EAZY Backend

# PostgreSQL (프로덕션)
POSTGRES_USER=eazy_prod_user
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE  # 변경 필수!
POSTGRES_SERVER=postgres  # Docker service name or IP
POSTGRES_PORT=5432
POSTGRES_DB=eazy_prod_db

# Redis (프로덕션)
REDIS_URL=redis://redis:6379/0  # Docker service name or IP

# Security (프로덕션 - 필수 변경!)
SECRET_KEY=GENERATE_A_SECURE_RANDOM_KEY_HERE_AT_LEAST_32_CHARS
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# CORS (프로덕션 - 실제 도메인으로 변경!)
BACKEND_CORS_ORIGINS=["https://eazy.example.com","https://app.eazy.example.com"]

# Logging
LOG_LEVEL=INFO

# Workers
WORKER_CONCURRENCY=4
```

### Frontend 환경 변수 (.env)

**개발 환경** (`frontend/.env.development`):
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ENVIRONMENT=development
```

**프로덕션 환경** (`frontend/.env.production`):
```bash
VITE_API_BASE_URL=https://api.eazy.example.com/api/v1
VITE_ENVIRONMENT=production
```

### SECRET_KEY 생성 방법

**Python (권장)**:
```bash
# Backend 디렉토리에서 실행
cd backend
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
# 출력: xGHZ7fJ3mK9pL2nQ8rT5vW1xY4zA6bC7dE8fG9hH0i
```

**OpenSSL**:
```bash
openssl rand -base64 32
```

---

## 프로덕션 빌드

### Backend 빌드

#### 1. 의존성 설치 (UV)

```bash
cd backend

# 프로덕션 의존성만 설치
uv sync --no-dev

# 또는 전체 설치 (개발 도구 포함)
uv sync
```

#### 2. 타입 체크 및 린터

```bash
# 타입 체크
uv run mypy app/

# 코드 포맷팅
uv run black app/ tests/
uv run isort app/ tests/

# 린터
uv run ruff check app/
```

#### 3. 테스트 실행

```bash
# 전체 테스트
uv run pytest

# 커버리지 포함
uv run pytest --cov=app --cov-report=html
```

#### 4. Playwright 브라우저 설치

```bash
# Chromium 브라우저 설치 (크롤러용)
uv run playwright install chromium
```

#### 5. 데이터베이스 마이그레이션

```bash
# 프로덕션 DB 마이그레이션
uv run alembic upgrade head
```

### Frontend 빌드

#### 1. 의존성 설치

```bash
cd frontend

# 의존성 설치
npm ci  # package-lock.json 기반 설치 (재현 가능)
```

#### 2. 린터 및 타입 체크

```bash
# TypeScript 타입 체크
npm run type-check

# ESLint
npm run lint

# Prettier
npm run format
```

#### 3. 테스트 실행

```bash
# 전체 테스트
npm run test

# 커버리지
npm run test:coverage
```

#### 4. 프로덕션 빌드

```bash
# .env.production 파일 사용
npm run build

# 빌드 결과: frontend/dist/
```

#### 5. 빌드 미리보기 (선택 사항)

```bash
npm run preview
# → http://localhost:4173
```

---

## Docker 배포

### Backend Dockerfile

**파일 생성**: `backend/Dockerfile`

```dockerfile
# Multi-stage 빌드로 이미지 크기 최적화

# Stage 1: Builder
FROM python:3.12-slim AS builder

# UV 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 작업 디렉토리 설정
WORKDIR /app

# UV 캐시 디렉토리 설정
ENV UV_CACHE_DIR=/tmp/uv-cache

# 의존성 파일 복사
COPY pyproject.toml uv.lock ./

# 의존성 설치 (venv 생성)
RUN uv sync --frozen --no-dev

# Playwright 브라우저 설치
RUN uv run playwright install --with-deps chromium

# Stage 2: Runtime
FROM python:3.12-slim

# 시스템 패키지 업데이트 및 필수 라이브러리 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Builder stage에서 venv 복사
COPY --from=builder /app/.venv /app/.venv

# Playwright 브라우저 복사
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# 환경 변수 설정
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# 실행 (Gunicorn + Uvicorn Worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Worker Dockerfile

**파일 생성**: `backend/Dockerfile.worker`

```dockerfile
FROM python:3.12-slim

# UV 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_CACHE_DIR=/tmp/uv-cache

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Playwright 브라우저 설치
RUN uv run playwright install --with-deps chromium

# 애플리케이션 코드 복사
COPY app/ ./app/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Worker 실행
CMD ["python", "-m", "app.worker"]
```

### Frontend Dockerfile

**파일 생성**: `frontend/Dockerfile`

```dockerfile
# Multi-stage 빌드

# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# 의존성 파일 복사
COPY package.json package-lock.json ./

# 의존성 설치
RUN npm ci

# 소스 코드 복사
COPY . .

# 프로덕션 빌드
RUN npm run build

# Stage 2: Nginx
FROM nginx:alpine

# Nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드 결과물 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### Nginx 설정

**파일 생성**: `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip 압축
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # SPA 라우팅 (모든 요청을 index.html로)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 정적 파일 캐싱
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 헬스체크 엔드포인트
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### Docker Compose (프로덕션)

**파일 생성**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: eazy-postgres-prod
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - eazy-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: eazy-redis-prod
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - eazy-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: eazy-backend-prod
    restart: always
    env_file:
      - ./backend/.env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - eazy-network
    ports:
      - "8000:8000"

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    container_name: eazy-worker-prod
    restart: always
    env_file:
      - ./backend/.env.production
    depends_on:
      - backend
      - redis
    networks:
      - eazy-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: eazy-frontend-prod
    restart: always
    depends_on:
      - backend
    networks:
      - eazy-network
    ports:
      - "80:80"

volumes:
  postgres_data:
  redis_data:

networks:
  eazy-network:
    driver: bridge
```

### Docker Compose 실행

```bash
# 1. 환경 변수 설정 확인
cp backend/.env.example backend/.env.production
# SECRET_KEY, POSTGRES_PASSWORD 등 수정 필수!

# 2. 이미지 빌드
docker compose -f docker-compose.prod.yml build

# 3. 컨테이너 시작
docker compose -f docker-compose.prod.yml up -d

# 4. 로그 확인
docker compose -f docker-compose.prod.yml logs -f

# 5. 상태 확인
docker compose -f docker-compose.prod.yml ps

# 6. 헬스체크
curl http://localhost:8000/health
curl http://localhost/health
```

---

## 수동 배포

### Backend 수동 배포 (Systemd)

#### 1. Systemd 서비스 파일 생성

**파일 생성**: `/etc/systemd/system/eazy-backend.service`

```ini
[Unit]
Description=EAZY Backend (FastAPI)
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=eazy
Group=eazy
WorkingDirectory=/opt/eazy/backend
Environment="PATH=/opt/eazy/backend/.venv/bin"
Environment="PYTHONPATH=/opt/eazy/backend"
ExecStart=/opt/eazy/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Worker 서비스 파일 생성

**파일 생성**: `/etc/systemd/system/eazy-worker.service`

```ini
[Unit]
Description=EAZY Worker (Redis Queue)
After=network.target redis.service

[Service]
Type=simple
User=eazy
Group=eazy
WorkingDirectory=/opt/eazy/backend
Environment="PATH=/opt/eazy/backend/.venv/bin"
Environment="PYTHONPATH=/opt/eazy/backend"
ExecStart=/opt/eazy/backend/.venv/bin/python -m app.worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 3. 서비스 시작

```bash
# Systemd 데몬 리로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable eazy-backend.service
sudo systemctl enable eazy-worker.service

# 서비스 시작
sudo systemctl start eazy-backend.service
sudo systemctl start eazy-worker.service

# 상태 확인
sudo systemctl status eazy-backend.service
sudo systemctl status eazy-worker.service

# 로그 확인
sudo journalctl -u eazy-backend.service -f
sudo journalctl -u eazy-worker.service -f
```

### Frontend 수동 배포 (Nginx)

#### 1. Nginx 설정

**파일 생성**: `/etc/nginx/sites-available/eazy`

```nginx
server {
    listen 80;
    server_name eazy.example.com;

    # Frontend (Static)
    location / {
        root /opt/eazy/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # Backend API (Reverse Proxy)
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 2. Nginx 활성화

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/eazy /etc/nginx/sites-enabled/

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

---

## 배포 체크리스트

### 배포 전 (Pre-Deployment)

- [ ] **환경 변수 검증**
  - [ ] `SECRET_KEY` 변경 (프로덕션용 랜덤 키)
  - [ ] `POSTGRES_PASSWORD` 변경
  - [ ] `BACKEND_CORS_ORIGINS` 실제 도메인으로 변경
  - [ ] `VITE_API_BASE_URL` 실제 API 도메인으로 변경

- [ ] **코드 품질 확인**
  - [ ] 모든 테스트 통과 (Backend: pytest, Frontend: vitest)
  - [ ] 린터 통과 (Backend: mypy, ruff, Frontend: eslint)
  - [ ] 포맷팅 통과 (Backend: black, isort, Frontend: prettier)

- [ ] **데이터베이스**
  - [ ] 마이그레이션 파일 최신 상태 확인
  - [ ] 백업 정책 수립
  - [ ] 프로덕션 DB 연결 테스트

- [ ] **보안**
  - [ ] HTTPS 인증서 설정 (Let's Encrypt 권장)
  - [ ] 방화벽 규칙 설정
  - [ ] 민감 정보 암호화 확인

- [ ] **문서**
  - [ ] API 문서 업데이트 (Swagger UI)
  - [ ] 변경 사항 기록 (CHANGELOG.md)
  - [ ] 배포 노트 작성

### 배포 중 (During Deployment)

- [ ] **빌드**
  - [ ] Backend Docker 이미지 빌드 성공
  - [ ] Frontend 빌드 성공 (dist/ 폴더 생성)
  - [ ] 이미지 크기 확인 (최적화 필요 시)

- [ ] **마이그레이션**
  - [ ] DB 마이그레이션 실행 (`alembic upgrade head`)
  - [ ] 마이그레이션 성공 확인

- [ ] **컨테이너 시작**
  - [ ] PostgreSQL 컨테이너 시작 및 헬스체크
  - [ ] Redis 컨테이너 시작 및 헬스체크
  - [ ] Backend 컨테이너 시작
  - [ ] Worker 컨테이너 시작
  - [ ] Frontend 컨테이너 시작

### 배포 후 (Post-Deployment)

- [ ] **헬스체크**
  - [ ] Backend API 헬스체크 (`/health`)
  - [ ] Frontend 접속 확인
  - [ ] Database 연결 확인
  - [ ] Redis 연결 확인

- [ ] **기능 검증**
  - [ ] 프로젝트 생성/조회/수정/삭제
  - [ ] Target 생성 및 스캔 트리거
  - [ ] Worker가 작업 처리하는지 확인
  - [ ] Asset 발견 및 저장 확인

- [ ] **모니터링 설정**
  - [ ] 로그 수집 설정
  - [ ] 메트릭 수집 설정 (CPU, 메모리, 디스크)
  - [ ] 알림 설정 (에러 발생 시)

- [ ] **성능 테스트**
  - [ ] 응답 시간 확인
  - [ ] 동시 접속자 부하 테스트
  - [ ] 크롤러 성능 확인

---

## 모니터링 및 로깅

### 애플리케이션 로그

#### Backend 로그 설정

**파일**: `backend/app/core/logging.py` (예시)

```python
import logging
import sys
from app.core.config import settings

def setup_logging():
    """로깅 설정"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/var/log/eazy/backend.log")
        ]
    )
```

#### 로그 확인

```bash
# Docker 컨테이너 로그
docker logs -f eazy-backend-prod
docker logs -f eazy-worker-prod

# Systemd 서비스 로그
sudo journalctl -u eazy-backend.service -f
sudo journalctl -u eazy-worker.service -f

# 파일 로그
tail -f /var/log/eazy/backend.log
```

### 에러 추적

**권장 도구**:
- **Sentry**: 실시간 에러 모니터링
- **Rollbar**: 에러 추적 및 알림

**Sentry 통합 예시** (Backend):

```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        environment=settings.ENVIRONMENT
    )
```

### 성능 모니터링

**권장 도구**:
- **Prometheus + Grafana**: 메트릭 수집 및 시각화
- **Datadog**: 통합 모니터링 플랫폼

**Prometheus 메트릭 엔드포인트** (Backend):

```python
# backend/app/main.py
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('http_requests_total', 'Total HTTP Requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP Request Duration')

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### 로그 수집 (ELK Stack)

**Filebeat 설정** (`filebeat.yml`):

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/eazy/*.log
  json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]

setup.kibana:
  host: "kibana:5601"
```

---

## 롤백 전략

### Docker 롤백

```bash
# 1. 이전 이미지 확인
docker images | grep eazy

# 2. 현재 컨테이너 중지
docker compose -f docker-compose.prod.yml down

# 3. 이전 이미지로 롤백
docker tag eazy-backend:previous eazy-backend:latest

# 4. 컨테이너 재시작
docker compose -f docker-compose.prod.yml up -d

# 5. 상태 확인
docker compose -f docker-compose.prod.yml ps
```

### 데이터베이스 롤백

```bash
# Alembic을 사용한 마이그레이션 롤백

# 1. 현재 리비전 확인
uv run alembic current

# 2. 이전 리비전으로 롤백
uv run alembic downgrade -1

# 또는 특정 리비전으로
uv run alembic downgrade <revision_id>
```

### Git 롤백

```bash
# 1. 배포 태그 확인
git tag -l "v*"

# 2. 이전 버전으로 체크아웃
git checkout v1.0.0

# 3. 재배포
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 롤백 체크리스트

- [ ] 현재 버전 및 이미지 백업
- [ ] DB 백업 생성
- [ ] 이전 버전으로 롤백
- [ ] 헬스체크 통과 확인
- [ ] 기능 검증
- [ ] 모니터링 확인 (에러 로그)
- [ ] 사용자 공지 (필요 시)

---

## 트러블슈팅

### 1. Backend 컨테이너가 시작되지 않음

**증상**:
```bash
docker compose ps
# eazy-backend-prod   Exit 1
```

**원인 및 해결**:

1. **환경 변수 미설정**
   ```bash
   # .env.production 파일 확인
   cat backend/.env.production
   # SECRET_KEY, POSTGRES_PASSWORD 등 확인
   ```

2. **DB 연결 실패**
   ```bash
   # PostgreSQL 상태 확인
   docker logs eazy-postgres-prod

   # 연결 테스트
   docker exec -it eazy-postgres-prod psql -U postgres
   ```

3. **포트 충돌**
   ```bash
   # 8000번 포트 사용 중인 프로세스 확인
   sudo lsof -i :8000

   # 프로세스 종료 또는 포트 변경
   ```

### 2. Frontend가 Backend API 호출 실패

**증상**:
```
Failed to fetch: net::ERR_CONNECTION_REFUSED
```

**원인 및 해결**:

1. **CORS 설정 확인**
   ```python
   # backend/app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://eazy.example.com"],  # 프론트엔드 도메인
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **API URL 확인**
   ```bash
   # frontend/.env.production
   VITE_API_BASE_URL=https://api.eazy.example.com/api/v1
   ```

3. **네트워크 확인**
   ```bash
   # Backend 헬스체크
   curl https://api.eazy.example.com/health
   ```

### 3. Worker가 작업을 처리하지 않음

**증상**:
```
Task 상태가 PENDING에서 변경되지 않음
```

**원인 및 해결**:

1. **Worker 로그 확인**
   ```bash
   docker logs eazy-worker-prod
   ```

2. **Redis 연결 확인**
   ```bash
   docker exec -it eazy-redis-prod redis-cli
   > PING
   PONG
   > LLEN task_queue
   (integer) 5  # 대기 중인 작업 수
   ```

3. **Worker 재시작**
   ```bash
   docker restart eazy-worker-prod
   ```

### 4. 크롤러 실행 실패 (Playwright)

**증상**:
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**원인 및 해결**:

```bash
# Docker 이미지 내에서 Playwright 브라우저 설치
docker exec -it eazy-backend-prod playwright install chromium

# 또는 Dockerfile에 추가
RUN playwright install --with-deps chromium
```

### 5. DB 마이그레이션 실패

**증상**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxxx'
```

**원인 및 해결**:

1. **마이그레이션 히스토리 확인**
   ```bash
   uv run alembic history
   ```

2. **DB 스키마 리셋 (주의: 데이터 손실)**
   ```bash
   # DB 삭제 후 재생성
   docker compose -f docker-compose.prod.yml down -v
   docker compose -f docker-compose.prod.yml up -d postgres

   # 마이그레이션 재실행
   uv run alembic upgrade head
   ```

---

## 참고 자료

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt (HTTPS)](https://letsencrypt.org/)
- [Backend Development Guide (BACKEND_DEVELOPMENT.md)](./BACKEND_DEVELOPMENT.md)
- [Frontend Development Guide (FRONTEND_DEVELOPMENT.md)](./FRONTEND_DEVELOPMENT.md)
- [Git Workflow (GIT_WORKFLOW.md)](./GIT_WORKFLOW.md)

---

**다음 문서**: [Monitoring Guide (MONITORING.md)](./MONITORING.md)
