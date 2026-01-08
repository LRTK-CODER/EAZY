[← 메인 문서로 돌아가기](../README.md)

# 환경 설정 가이드

EAZY 프로젝트 개발 환경을 구축하기 위한 종합 가이드입니다.

## 목차

- [개요](#개요)
- [시스템 요구사항](#시스템-요구사항)
- [필수 도구 설치](#필수-도구-설치)
  - [1. UV (Backend 패키지 매니저)](#1-uv-backend-패키지-매니저)
  - [2. Node.js (Frontend)](#2-nodejs-frontend)
  - [3. Docker & Docker Compose](#3-docker--docker-compose)
  - [4. Git](#4-git)
- [환경 변수 설정](#환경-변수-설정)
  - [Backend 환경 변수](#backend-환경-변수)
  - [Frontend 환경 변수](#frontend-환경-변수)
- [다음 단계](#다음-단계)
- [문제 해결](#문제-해결)

---

## 개요

EAZY는 다음 구성 요소로 이루어진 풀스택 애플리케이션입니다:

```
┌─────────────────────────────────────────────┐
│  Frontend (React + TypeScript + Vite)       │  localhost:5173
├─────────────────────────────────────────────┤
│  Backend (Python + FastAPI + UV)            │  localhost:8000
├─────────────────────────────────────────────┤
│  PostgreSQL (Docker)                        │  localhost:5432
│  Redis (Docker)                             │  localhost:6379
└─────────────────────────────────────────────┘
```

각 구성 요소를 위한 개발 환경을 순서대로 설정합니다.

---

## 시스템 요구사항

### 운영체제
- macOS 10.15 이상
- Linux (Ubuntu 20.04 이상 권장)
- Windows 10/11 (WSL2 권장)

### 하드웨어
- CPU: 2코어 이상
- RAM: 8GB 이상 (16GB 권장)
- 디스크: 10GB 이상 여유 공간

### 네트워크
- 인터넷 연결 (의존성 다운로드용)
- 포트 사용 가능 여부:
  - 8000 (Backend API)
  - 5173 (Frontend Dev Server)
  - 5432 (PostgreSQL)
  - 6379 (Redis)

---

## 필수 도구 설치

### 1. UV (Backend 패키지 매니저)

**UV란?**

Rust 기반의 고속 Python 패키지 매니저로 pip/poetry/pipenv를 대체합니다.

**주요 특징:**
- 10-100배 빠른 설치 속도
- 자동 가상환경 관리
- pyproject.toml 기반 의존성 관리
- Lock 파일을 통한 재현 가능한 빌드

#### 설치 방법

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Homebrew (macOS):**
```bash
brew install uv
```

#### 설치 확인

```bash
uv --version
# 출력 예: uv 0.5.0 (또는 최신 버전)
```

> **참고:** UV 설치 후 터미널을 재시작해야 PATH가 적용됩니다.

---

### 2. Node.js (Frontend)

**버전 요구사항:** Node.js 18.x 이상 (20.x 권장)

#### 설치 방법

**macOS (Homebrew):**
```bash
brew install node@20
```

**Linux (Ubuntu/Debian):**
```bash
# NodeSource 저장소 추가
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows:**
[Node.js 공식 사이트](https://nodejs.org/)에서 LTS 버전 다운로드

#### 설치 확인

```bash
node --version
# 출력 예: v20.11.0

npm --version
# 출력 예: 10.2.4
```

---

### 3. Docker & Docker Compose

PostgreSQL과 Redis 컨테이너를 실행하기 위해 필요합니다.

#### 설치 방법

**macOS:**
[Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 다운로드 및 설치

**Linux (Ubuntu):**
```bash
# Docker 설치
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Windows:**
[Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드 및 설치

#### 설치 확인

```bash
docker --version
# 출력 예: Docker version 24.0.7

docker compose version
# 출력 예: Docker Compose version v2.23.3
```

#### Docker 권한 설정 (Linux)

```bash
# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 변경사항 적용 (로그아웃 후 재로그인 또는)
newgrp docker
```

---

### 4. Git

**버전 요구사항:** Git 2.30 이상

#### 설치 방법

**macOS:**
```bash
brew install git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install -y git
```

**Windows:**
[Git for Windows](https://git-scm.com/download/win) 다운로드 및 설치

#### 설치 확인

```bash
git --version
# 출력 예: git version 2.39.3
```

---

## 환경 변수 설정

### Backend 환경 변수

`backend/.env` 파일을 생성합니다:

```bash
cd backend
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

# 보안 설정 (프로덕션에서는 반드시 변경 필요)
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8일

# 애플리케이션 설정
PROJECT_NAME=EAZY
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

> **보안 주의사항:**
> - `SECRET_KEY`는 프로덕션 환경에서 반드시 강력한 랜덤 문자열로 변경해야 합니다.
> - `.env` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않습니다.

---

### Frontend 환경 변수

`frontend/.env` 파일을 생성합니다:

```bash
cd frontend
touch .env
```

다음 내용을 `.env` 파일에 추가:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

> **참고:** Vite에서 환경 변수는 반드시 `VITE_` 접두사로 시작해야 합니다.

---

## 다음 단계

환경 설정이 완료되었습니다. 이제 각 구성 요소를 설치하고 실행할 수 있습니다:

### Backend 설정
자세한 내용은 **[Backend 설정 가이드](./BACKEND_SETUP.md)**를 참고하세요.

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### Frontend 설정
자세한 내용은 **[Frontend 설정 가이드](./FRONTEND_SETUP.md)**를 참고하세요.

```bash
cd frontend
npm install
npm run dev
```

### Docker 설정
자세한 내용은 **[Docker 설정 가이드](./DOCKER_SETUP.md)**를 참고하세요.

```bash
cd backend/docker
docker compose up -d
```

---

## 문제 해결

### 포트 충돌 오류

**증상:**
```
Error: Port 8000 is already in use
```

**해결 방법:**
```bash
# 포트 사용 프로세스 확인 (macOS/Linux)
lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# Windows (PowerShell)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### UV 설치 후 명령어를 찾을 수 없음

**증상:**
```
command not found: uv
```

**해결 방법:**
```bash
# PATH 확인
echo $PATH

# UV 바이너리 경로 추가 (macOS/Linux)
export PATH="$HOME/.local/bin:$PATH"

# 셸 설정 파일에 영구 추가
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc  # bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc   # zsh
```

### Docker 권한 오류 (Linux)

**증상:**
```
permission denied while trying to connect to the Docker daemon socket
```

**해결 방법:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## 추가 참고 자료

- **[Backend 설정 가이드](./BACKEND_SETUP.md)** - UV 사용법 및 Backend 실행
- **[Frontend 설정 가이드](./FRONTEND_SETUP.md)** - npm 사용법 및 Frontend 실행
- **[Docker 설정 가이드](./DOCKER_SETUP.md)** - PostgreSQL 및 Redis 컨테이너 관리
- **[문제 해결 가이드](./TROUBLESHOOTING.md)** - 자주 발생하는 오류 및 해결 방법
- **[빠른 시작 가이드](../QUICK_START.md)** - 5분 안에 시작하기

---

**작성:** EAZY Technical Writer
**최종 업데이트:** 2026-01-09
