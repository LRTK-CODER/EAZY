[← 메인 문서로 돌아가기](../README.md)

# Docker 설정 가이드

EAZY 프로젝트의 PostgreSQL 및 Redis 컨테이너를 Docker Compose로 관리하는 방법을 설명합니다.

## 목차

- [개요](#개요)
- [Docker 설치](#docker-설치)
- [Docker Compose 파일 구조](#docker-compose-파일-구조)
- [컨테이너 관리](#컨테이너-관리)
  - [컨테이너 시작](#컨테이너-시작)
  - [컨테이너 상태 확인](#컨테이너-상태-확인)
  - [컨테이너 로그 확인](#컨테이너-로그-확인)
  - [컨테이너 정지](#컨테이너-정지)
  - [컨테이너 재시작](#컨테이너-재시작)
  - [컨테이너 삭제](#컨테이너-삭제)
- [데이터 볼륨 관리](#데이터-볼륨-관리)
- [데이터베이스 접근](#데이터베이스-접근)
- [Redis 접근](#redis-접근)
- [문제 해결](#문제-해결)

---

## 개요

EAZY는 다음 두 개의 Docker 컨테이너를 사용합니다:

| 컨테이너 | 이미지 | 포트 | 용도 |
|---------|--------|------|------|
| **eazy-postgres** | postgres:15-alpine | 5432 | 메인 데이터베이스 (JSONB 지원) |
| **eazy-redis** | redis:7-alpine | 6379 | 비동기 작업 큐 |

**장점:**
- 로컬 설치 없이 일관된 개발 환경
- 빠른 환경 구축 및 초기화
- 데이터 격리 및 안전한 삭제
- Alpine 이미지로 경량화 (약 30MB)

---

## Docker 설치

### macOS

[Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 다운로드 및 설치

설치 확인:
```bash
docker --version
docker compose version
```

### Linux (Ubuntu)

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

# 사용자 권한 추가
sudo usermod -aG docker $USER
newgrp docker
```

### Windows

[Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드 및 설치

> **참고:** WSL2 백엔드 사용 권장

---

## Docker Compose 파일 구조

`backend/docker/docker-compose.yml` 파일 내용:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: eazy-postgres
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: eazy_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: eazy-redis
    restart: always
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 주요 설정 설명

#### PostgreSQL 컨테이너

- **image**: `postgres:15-alpine` - PostgreSQL 15 경량 이미지
- **container_name**: `eazy-postgres` - 컨테이너 식별 이름
- **restart**: `always` - Docker 시작 시 자동 재시작
- **environment**: 환경 변수
  - `POSTGRES_USER`: 사용자 이름 (postgres)
  - `POSTGRES_PASSWORD`: 비밀번호 (postgres)
  - `POSTGRES_DB`: 데이터베이스 이름 (eazy_db)
- **ports**: `5432:5432` - 호스트:컨테이너 포트 매핑
- **volumes**: `postgres_data` - 데이터 영구 저장

#### Redis 컨테이너

- **image**: `redis:7-alpine` - Redis 7 경량 이미지
- **container_name**: `eazy-redis` - 컨테이너 식별 이름
- **restart**: `always` - Docker 시작 시 자동 재시작
- **ports**: `6379:6379` - 호스트:컨테이너 포트 매핑

#### Volumes

- **postgres_data**: PostgreSQL 데이터 영구 저장소
  - 컨테이너 삭제 시에도 데이터 보존
  - `/var/lib/postgresql/data`에 마운트

---

## 컨테이너 관리

### 컨테이너 시작

```bash
cd backend/docker
docker compose up -d
```

**옵션:**
- `-d`: Detached 모드 (백그라운드 실행)

**출력 예:**
```
[+] Running 3/3
 ✔ Network docker_default         Created
 ✔ Container eazy-postgres        Started
 ✔ Container eazy-redis           Started
```

### 포그라운드 실행 (로그 보기)

```bash
docker compose up
```

종료: `Ctrl+C`

---

### 컨테이너 상태 확인

```bash
docker ps
```

**출력 예:**
```
CONTAINER ID   IMAGE                COMMAND                  CREATED         STATUS         PORTS                    NAMES
abc123def456   postgres:15-alpine   "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes   0.0.0.0:5432->5432/tcp   eazy-postgres
xyz789ghi012   redis:7-alpine       "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes   0.0.0.0:6379->6379/tcp   eazy-redis
```

**컨테이너 상세 정보:**
```bash
docker inspect eazy-postgres
```

---

### 컨테이너 로그 확인

#### PostgreSQL 로그

```bash
docker logs eazy-postgres
```

**실시간 로그 스트리밍:**
```bash
docker logs -f eazy-postgres
```

**최근 100줄만 보기:**
```bash
docker logs --tail 100 eazy-postgres
```

#### Redis 로그

```bash
docker logs eazy-redis
```

---

### 컨테이너 정지

```bash
cd backend/docker
docker compose stop
```

**출력 예:**
```
[+] Stopping 2/2
 ✔ Container eazy-redis           Stopped
 ✔ Container eazy-postgres        Stopped
```

**개별 컨테이너 정지:**
```bash
docker stop eazy-postgres
docker stop eazy-redis
```

---

### 컨테이너 재시작

```bash
cd backend/docker
docker compose restart
```

**개별 컨테이너 재시작:**
```bash
docker restart eazy-postgres
docker restart eazy-redis
```

---

### 컨테이너 삭제

#### 컨테이너만 삭제 (데이터 유지)

```bash
cd backend/docker
docker compose down
```

**출력 예:**
```
[+] Running 3/3
 ✔ Container eazy-redis           Removed
 ✔ Container eazy-postgres        Removed
 ✔ Network docker_default         Removed
```

#### 컨테이너 및 볼륨 삭제 (데이터 삭제)

```bash
docker compose down -v
```

**주의:** 모든 데이터베이스 데이터가 삭제됩니다!

---

## 데이터 볼륨 관리

### 볼륨 목록 확인

```bash
docker volume ls
```

**출력 예:**
```
DRIVER    VOLUME NAME
local     docker_postgres_data
```

### 볼륨 상세 정보

```bash
docker volume inspect docker_postgres_data
```

**출력 예:**
```json
[
    {
        "CreatedAt": "2026-01-09T10:00:00Z",
        "Driver": "local",
        "Labels": {
            "com.docker.compose.project": "docker",
            "com.docker.compose.volume": "postgres_data"
        },
        "Mountpoint": "/var/lib/docker/volumes/docker_postgres_data/_data",
        "Name": "docker_postgres_data",
        "Options": null,
        "Scope": "local"
    }
]
```

### 볼륨 백업

```bash
# PostgreSQL 데이터 백업
docker run --rm -v docker_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### 볼륨 복원

```bash
# PostgreSQL 데이터 복원
docker run --rm -v docker_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

### 볼륨 삭제

```bash
# 경고: 모든 데이터 삭제됨!
docker volume rm docker_postgres_data
```

---

## 데이터베이스 접근

### psql 클라이언트로 접근

```bash
docker exec -it eazy-postgres psql -U postgres -d eazy_db
```

**명령어 예시:**
```sql
-- 테이블 목록 조회
\dt

-- 프로젝트 조회
SELECT * FROM projects;

-- 종료
\q
```

### 호스트에서 직접 접근

`psql` 클라이언트가 호스트에 설치된 경우:

```bash
psql -h localhost -U postgres -d eazy_db
```

비밀번호: `postgres`

### GUI 도구 연결

**DBeaver, pgAdmin, TablePlus 등:**

- **Host**: localhost
- **Port**: 5432
- **Database**: eazy_db
- **User**: postgres
- **Password**: postgres

---

## Redis 접근

### redis-cli로 접근

```bash
docker exec -it eazy-redis redis-cli
```

**명령어 예시:**
```bash
# 연결 테스트
PING
# 출력: PONG

# 키 목록 조회
KEYS *

# 큐 확인 (EAZY Task Queue)
LLEN task_queue

# 종료
exit
```

### 호스트에서 직접 접근

`redis-cli`가 호스트에 설치된 경우:

```bash
redis-cli -h localhost -p 6379
```

---

## 문제 해결

### 1. 포트 충돌 (5432)

**증상:**
```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5432 -> 0.0.0.0:0: listen tcp 0.0.0.0:5432: bind: address already in use
```

**해결 방법:**

```bash
# 1. 포트 사용 프로세스 확인 (macOS/Linux)
lsof -i :5432

# 2. 프로세스 종료
kill -9 <PID>

# 3. 또는 docker-compose.yml에서 포트 변경
ports:
  - "5433:5432"  # 호스트 포트를 5433으로 변경
```

---

### 2. 컨테이너 시작 실패

**증상:**
```
Error: Cannot connect to the Docker daemon
```

**해결 방법:**

```bash
# Docker Desktop이 실행 중인지 확인
# macOS: Docker Desktop 아이콘 클릭

# Linux: Docker 서비스 시작
sudo systemctl start docker

# Docker 상태 확인
sudo systemctl status docker
```

---

### 3. 데이터베이스 연결 실패

**증상:**
```
FATAL:  database "eazy_db" does not exist
```

**해결 방법:**

```bash
# 1. 컨테이너 로그 확인
docker logs eazy-postgres

# 2. 컨테이너 재시작
docker compose restart postgres

# 3. 문제 지속 시: 컨테이너 재생성
docker compose down
docker compose up -d
```

---

### 4. 권한 오류 (Linux)

**증상:**
```
Got permission denied while trying to connect to the Docker daemon socket
```

**해결 방법:**

```bash
# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 변경사항 적용
newgrp docker

# 또는 로그아웃 후 재로그인
```

---

### 5. 볼륨 마운트 오류

**증상:**
```
Error response from daemon: error while creating mount source path
```

**해결 방법:**

```bash
# 1. 볼륨 삭제 후 재생성
docker compose down -v
docker compose up -d

# 2. Docker 재시작
# macOS: Docker Desktop 재시작
# Linux:
sudo systemctl restart docker
```

---

### 6. 메모리 부족 오류

**증상:**
```
Error: OOM command not allowed when used memory > 'maxmemory'
```

**해결 방법:**

```bash
# Redis 메모리 제한 설정 (docker-compose.yml)
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

---

## 추가 참고 자료

- **[Backend 설정 가이드](./BACKEND_SETUP.md)** - Backend 실행 방법
- **[환경 설정 가이드](./ENVIRONMENT_SETUP.md)** - Docker 설치 방법
- **[문제 해결 가이드](./TROUBLESHOOTING.md)** - 자주 발생하는 오류
- **Docker 공식 문서**: https://docs.docker.com/
- **Docker Compose 공식 문서**: https://docs.docker.com/compose/

---

**작성:** EAZY Technical Writer
**최종 업데이트:** 2026-01-09
