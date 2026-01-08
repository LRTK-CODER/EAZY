# Backend 개발 가이드 (Backend Development)

[← 메인 문서로 돌아가기](../README.md)

**작성일**: 2026-01-09
**대상 독자**: Backend 개발자

---

## 목차

- [코딩 스타일](#코딩-스타일)
- [필수 규칙](#필수-규칙)
- [레이어 분리](#레이어-분리)
- [주요 기능 구현 가이드](#주요-기능-구현-가이드)
  - [프로젝트 관리 (CRUD)](#프로젝트-관리-crud)
  - [Target 관리](#target-관리)
  - [비동기 크롤링](#비동기-크롤링)
- [보안 규칙](#보안-규칙)
- [성능 최적화](#성능-최적화)
- [에러 처리](#에러-처리)
- [로깅 전략](#로깅-전략)

---

## 코딩 스타일

EAZY Backend는 Python 표준 스타일 가이드를 따릅니다.

### 도구

| 도구 | 용도 | 실행 명령 |
|------|------|----------|
| **Black** | 코드 포맷터 (최대 88자) | `uv run black .` |
| **isort** | Import 정렬 | `uv run isort .` |
| **ruff** | 린터 (빠른 Flake8 대체) | `uv run ruff check .` |
| **mypy** | 타입 체크 (Strict Mode) | `uv run mypy .` |

### 스타일 가이드

1. **PEP 8** 준수
2. **최대 줄 길이**: 88자 (Black 기본값)
3. **들여쓰기**: 4 spaces
4. **Import 순서**: 표준 라이브러리 → 서드파티 → 로컬 (isort 자동 처리)
5. **Naming Conventions**:
   - 함수/변수: `snake_case`
   - 클래스: `PascalCase`
   - 상수: `UPPER_SNAKE_CASE`
   - Private: `_leading_underscore`

### 코드 포맷팅 예시

```bash
# 1. Black 실행 (자동 포맷팅)
cd backend
uv run black .

# 2. isort 실행 (Import 정렬)
uv run isort .

# 3. ruff 실행 (린팅)
uv run ruff check .

# 4. mypy 실행 (타입 체크)
uv run mypy .
```

---

## 필수 규칙

### 1. Type Hint 필수

모든 함수에 **Type Hint**를 명시해야 합니다.

```python
# ✅ Good: Type Hint 명시
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project

async def get_project(db: AsyncSession, project_id: int) -> Project | None:
    """프로젝트 조회"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


# ❌ Bad: Type Hint 없음
async def get_project(db, project_id):
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalar_one_or_none()
```

### 2. 비동기 함수 사용

FastAPI는 **비동기 I/O**를 지원하므로, DB 및 외부 API 호출은 반드시 비동기로 처리합니다.

```python
# ✅ Good: 비동기 함수
async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


# ❌ Bad: 동기 함수 (블로킹)
def create_project(db: Session, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
```

### 3. Pydantic 모델 사용

API 요청/응답은 **Pydantic 모델**로 검증합니다.

```python
# ✅ Good: Pydantic 모델로 검증
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    project: ProjectCreate,  # Pydantic 자동 검증
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.create_project(db, project)


# ❌ Bad: dict로 직접 처리 (검증 없음)
@router.post("/")
async def create_project(
    project: dict,  # 검증 없음
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.create_project(db, project)
```

### 4. Exception Handling

FastAPI의 **HTTPException**을 사용하여 에러를 처리합니다.

```python
# ✅ Good: HTTPException 사용
from fastapi import HTTPException, status

async def get_project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    return project


# ❌ Bad: 에러 처리 없음
async def get_project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    return project  # None이 반환될 수 있음
```

---

## 레이어 분리

EAZY Backend는 **Layered Architecture**를 따릅니다.

### 아키텍처

```
┌─────────────────────────────────────────┐
│   API Layer (Controllers/Routers)       │  FastAPI Endpoints
├─────────────────────────────────────────┤
│   Service Layer (Business Logic)        │  ProjectService, CrawlerService
├─────────────────────────────────────────┤
│   Repository Layer (Data Access)        │  SQLModel ORM
├─────────────────────────────────────────┤
│   Infrastructure Layer                  │  DB, Redis, Queue
└─────────────────────────────────────────┘
```

### 레이어별 책임

| 레이어 | 책임 | 위치 |
|--------|------|------|
| **API Layer** | HTTP 요청/응답 처리, 데이터 유효성 검증 | `app/api/v1/endpoints/` |
| **Service Layer** | 비즈니스 로직, 트랜잭션 관리 | `app/services/` |
| **Repository Layer** | DB 접근 추상화 (SQLModel ORM) | `app/models/` |
| **Infrastructure Layer** | DB 연결, Redis 큐, 설정 관리 | `app/core/` |

### 올바른 레이어 분리 예제

#### ✅ Good: 레이어 분리

```python
# app/api/v1/endpoints/project.py (API Layer)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate, ProjectRead

router = APIRouter()


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    프로젝트 생성 API

    책임: HTTP 요청/응답 처리만 담당
    비즈니스 로직은 Service Layer에 위임
    """
    return await ProjectService.create_project(db, project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    프로젝트 조회 API

    책임: HTTP 요청/응답 처리만 담당
    """
    return await ProjectService.get_project(db, project_id)
```

```python
# app/services/project_service.py (Service Layer)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import datetime, timezone

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """
    프로젝트 비즈니스 로직 Service

    책임:
    - 비즈니스 로직 처리
    - 트랜잭션 관리
    - DB 접근 (Repository Layer 사용)
    """

    @staticmethod
    async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
        """프로젝트 생성"""
        project = Project(
            name=data.name,
            description=data.description,
            is_archived=False
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def get_project(db: AsyncSession, project_id: int) -> Project:
        """프로젝트 조회"""
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        return project

    @staticmethod
    async def archive_project(db: AsyncSession, project_id: int) -> None:
        """프로젝트 Archive (Soft Delete)"""
        project = await ProjectService.get_project(db, project_id)

        project.is_archived = True
        project.archived_at = datetime.now(timezone.utc)

        await db.commit()
```

#### ❌ Bad: 레이어 분리 없음

```python
# app/api/v1/endpoints/project.py (안티패턴)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.project import Project

router = APIRouter()


@router.post("/")
async def create_project(
    project: dict,  # Pydantic 모델 미사용
    db: AsyncSession = Depends(get_db)
):
    """
    ❌ 안티패턴:
    - API Layer에서 비즈니스 로직 직접 처리
    - Pydantic 검증 없음
    - 에러 처리 없음
    """
    new_project = Project(
        name=project["name"],
        description=project.get("description"),
        is_archived=False
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project
```

### Dependency Injection

FastAPI의 **Depends**를 활용하여 의존성을 주입합니다.

```python
# app/core/db.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """DB 세션 Dependency"""
    async with async_session() as session:
        yield session


# app/api/v1/endpoints/project.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db


@router.post("/")
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)  # Dependency Injection
):
    return await ProjectService.create_project(db, project)
```

---

## 주요 기능 구현 가이드

### 프로젝트 관리 (CRUD)

#### 1. Create (생성)

```python
# app/services/project_service.py

class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
        """프로젝트 생성"""
        project = Project(
            name=data.name,
            description=data.description,
            is_archived=False
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
```

#### 2. Read (조회)

```python
class ProjectService:
    @staticmethod
    async def get_project(db: AsyncSession, project_id: int) -> Project:
        """프로젝트 조회"""
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        return project

    @staticmethod
    async def get_projects(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        archived: bool = False
    ) -> list[Project]:
        """프로젝트 목록 조회 (아카이브 필터)"""
        result = await db.execute(
            select(Project)
            .where(Project.is_archived == archived)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        return result.scalars().all()
```

#### 3. Update (수정)

```python
class ProjectService:
    @staticmethod
    async def update_project(
        db: AsyncSession,
        project_id: int,
        data: ProjectUpdate
    ) -> Project:
        """프로젝트 수정"""
        project = await ProjectService.get_project(db, project_id)

        # Partial Update (exclude_unset=True)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        await db.commit()
        await db.refresh(project)
        return project
```

#### 4. Delete (삭제 - Soft Delete)

```python
class ProjectService:
    @staticmethod
    async def archive_project(db: AsyncSession, project_id: int) -> None:
        """프로젝트 Archive (Soft Delete)"""
        project = await ProjectService.get_project(db, project_id)

        project.is_archived = True
        project.archived_at = datetime.now(timezone.utc)

        await db.commit()

    @staticmethod
    async def restore_project(db: AsyncSession, project_id: int) -> None:
        """프로젝트 복원"""
        project = await ProjectService.get_project(db, project_id)

        project.is_archived = False
        project.archived_at = None

        await db.commit()

    @staticmethod
    async def permanent_delete(db: AsyncSession, project_id: int) -> None:
        """프로젝트 영구 삭제 (Hard Delete)"""
        project = await ProjectService.get_project(db, project_id)

        await db.delete(project)
        await db.commit()
```

### Target 관리

#### Scope 기반 크롤링 범위 제어

```python
# app/models/target.py

from enum import Enum

class TargetScope(str, Enum):
    """Target 스캔 범위"""
    DOMAIN = "DOMAIN"          # 전체 도메인 (subdomain 포함)
    SUBDOMAIN = "SUBDOMAIN"    # 특정 서브도메인만
    URL_ONLY = "URL_ONLY"      # 단일 URL만


# app/services/target_service.py

class TargetService:
    @staticmethod
    async def create_target(
        db: AsyncSession,
        project_id: int,
        data: TargetCreate
    ) -> Target:
        """Target 생성"""
        # Project 존재 확인
        project = await ProjectService.get_project(db, project_id)

        target = Target(
            project_id=project.id,
            name=data.name,
            url=data.url,
            scope=data.scope,  # DOMAIN, SUBDOMAIN, URL_ONLY
            description=data.description
        )
        db.add(target)
        await db.commit()
        await db.refresh(target)
        return target
```

### 비동기 크롤링

EAZY는 **Redis Queue + Worker** 패턴으로 비동기 크롤링을 처리합니다.

#### 아키텍처

```
FastAPI (API)
    ↓
TaskService.create_scan_task()
    ↓
Redis Queue (RPUSH)
    ↓
Worker (LPOP)
    ↓
CrawlerService.crawl()
    ↓
Playwright Browser
    ↓
AssetService.process_asset()
    ↓
PostgreSQL (Assets 저장)
```

#### 1. Task 생성 및 Enqueue

```python
# app/services/task_service.py

from app.core.queue import TaskManager

class TaskService:
    @staticmethod
    async def create_scan_task(
        db: AsyncSession,
        target_id: int
    ) -> Task:
        """스캔 Task 생성 및 Redis Queue에 Enqueue"""
        # Target 조회
        target = await TargetService.get_target(db, target_id)

        # Task 생성 (DB)
        task = Task(
            project_id=target.project_id,
            target_id=target.id,
            type="CRAWL",
            status="PENDING"
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Redis Queue에 Enqueue
        task_manager = TaskManager()
        await task_manager.enqueue({
            "task_id": task.id,
            "target_id": target.id,
            "url": target.url,
            "scope": target.scope
        })

        return task
```

#### 2. Worker 구현

```python
# app/worker.py

import asyncio
from app.core.queue import TaskManager
from app.core.db import async_session
from app.services.crawler_service import CrawlerService
from app.services.asset_service import AssetService
from app.models.task import Task


async def process_task(task_data: dict):
    """Task 처리"""
    task_id = task_data["task_id"]
    target_id = task_data["target_id"]
    url = task_data["url"]

    async with async_session() as db:
        # Task 상태 업데이트: PENDING → RUNNING
        task = await db.get(Task, task_id)
        task.status = "RUNNING"
        await db.commit()

        try:
            # Crawler 실행
            links = await CrawlerService.crawl(url)

            # Asset 저장
            saved_count = 0
            for link in links:
                await AssetService.process_asset(
                    db,
                    task_id=task_id,
                    target_id=target_id,
                    type="URL",
                    source="HTML",
                    method="GET",
                    url=link,
                    path=link
                )
                saved_count += 1

            # Task 상태 업데이트: RUNNING → COMPLETED
            task.status = "COMPLETED"
            task.result = {
                "found_links": len(links),
                "saved_assets": saved_count
            }
            await db.commit()

        except Exception as e:
            # Task 상태 업데이트: RUNNING → FAILED
            task.status = "FAILED"
            task.result = {"error": str(e)}
            await db.commit()


async def main():
    """Worker 메인 루프"""
    task_manager = TaskManager()
    print("Worker started. Waiting for tasks...")

    while True:
        task_data = await task_manager.dequeue()
        if task_data:
            print(f"Processing task {task_data['task_id']}...")
            await process_task(task_data)
        else:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
```

#### 3. Crawler Service 구현

```python
# app/services/crawler_service.py

from playwright.async_api import async_playwright

class CrawlerService:
    @staticmethod
    async def crawl(url: str) -> list[str]:
        """
        Playwright를 사용한 웹 크롤링

        Returns:
            발견된 링크 목록
        """
        links = set()

        async with async_playwright() as p:
            # Chromium 브라우저 런칭
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 페이지 이동 (JS 렌더링 대기)
            await page.goto(url, wait_until="networkidle")

            # <a> 태그의 href 속성 추출
            link_elements = await page.locator("a[href]").all()
            for element in link_elements:
                href = await element.get_attribute("href")
                if href and href.startswith("http"):
                    links.add(href)

            await browser.close()

        return list(links)
```

#### 4. Asset Service 구현 (중복 제거)

```python
# app/services/asset_service.py

import hashlib
from datetime import datetime, timezone

class AssetService:
    @staticmethod
    async def process_asset(
        db: AsyncSession,
        task_id: int,
        target_id: int,
        **asset_data
    ) -> Asset:
        """
        Asset 처리 (중복 제거)

        - content_hash를 기준으로 UPSERT
        - 기존 Asset이 있으면 last_seen_at 업데이트
        - 없으면 신규 생성
        """
        # content_hash 생성
        method = asset_data["method"]
        url = asset_data["url"]
        content = f"{method}:{url}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # 기존 Asset 조회
        result = await db.execute(
            select(Asset).where(Asset.content_hash == content_hash)
        )
        existing_asset = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if existing_asset:
            # 기존 Asset 업데이트
            existing_asset.last_seen_at = now
            existing_asset.last_task_id = task_id
            asset = existing_asset
        else:
            # 신규 Asset 생성
            asset = Asset(
                target_id=target_id,
                content_hash=content_hash,
                type=asset_data["type"],
                source=asset_data["source"],
                method=method,
                url=url,
                path=asset_data["path"],
                first_seen_at=now,
                last_seen_at=now,
                last_task_id=task_id
            )
            db.add(asset)

        await db.commit()
        await db.refresh(asset)

        # AssetDiscovery 이력 생성
        discovery = AssetDiscovery(
            task_id=task_id,
            asset_id=asset.id,
            discovered_at=now
        )
        db.add(discovery)
        await db.commit()

        return asset
```

---

## 보안 규칙

### 1. SQL Injection 방지

**SQLModel ORM**을 사용하여 SQL Injection을 방지합니다.

```python
# ✅ Good: ORM 사용 (파라미터 바인딩)
async def get_project(db: AsyncSession, project_id: int) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


# ❌ Bad: Raw SQL (SQL Injection 위험)
async def get_project(db: AsyncSession, project_id: int) -> Project:
    query = f"SELECT * FROM projects WHERE id = {project_id}"  # 위험!
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

### 2. Input Validation

**Pydantic**을 사용하여 입력 데이터를 검증합니다.

```python
from pydantic import BaseModel, Field, validator

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v
```

### 3. 환경 변수 보안

**.env 파일을 Git에서 제외**하고, 민감한 정보는 환경 변수로 관리합니다.

```python
# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days

    # Redis
    REDIS_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

### 4. CORS 설정

프로덕션에서는 **특정 도메인만 허용**합니다.

```python
# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # 개발 환경
        "https://yourdomain.com"  # 프로덕션 환경
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 성능 최적화

### 1. DB 쿼리 최적화

#### N+1 문제 방지 (Eager Loading)

```python
# ✅ Good: joinedload로 Eager Loading
from sqlalchemy.orm import selectinload

async def get_projects_with_targets(db: AsyncSession) -> list[Project]:
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.targets))  # Eager Loading
    )
    return result.scalars().all()


# ❌ Bad: Lazy Loading (N+1 문제)
async def get_projects_with_targets(db: AsyncSession) -> list[Project]:
    result = await db.execute(select(Project))
    projects = result.scalars().all()

    for project in projects:
        # 각 프로젝트마다 추가 쿼리 발생 (N+1)
        await project.targets
    return projects
```

### 2. 비동기 I/O 활용

외부 API 호출 시 **병렬 처리**를 활용합니다.

```python
import asyncio
from httpx import AsyncClient

# ✅ Good: 병렬 처리
async def fetch_multiple_urls(urls: list[str]) -> list[str]:
    async with AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.text for r in responses]


# ❌ Bad: 순차 처리 (느림)
async def fetch_multiple_urls(urls: list[str]) -> list[str]:
    async with AsyncClient() as client:
        results = []
        for url in urls:
            response = await client.get(url)
            results.append(response.text)
        return results
```

### 3. Redis 캐싱

자주 조회되는 데이터는 **Redis에 캐싱**합니다.

```python
import json
from redis.asyncio import Redis

class CacheService:
    @staticmethod
    async def get_cached_project(redis: Redis, project_id: int) -> Project | None:
        """Redis 캐시에서 프로젝트 조회"""
        cached_data = await redis.get(f"project:{project_id}")
        if cached_data:
            return Project(**json.loads(cached_data))
        return None

    @staticmethod
    async def cache_project(redis: Redis, project: Project, ttl: int = 300):
        """Redis 캐시에 프로젝트 저장 (TTL: 5분)"""
        await redis.setex(
            f"project:{project.id}",
            ttl,
            project.model_dump_json()
        )
```

---

## 에러 처리

### HTTPException 사용

```python
from fastapi import HTTPException, status

# 404 Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Project not found"
)

# 400 Bad Request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid project data"
)

# 403 Forbidden
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Access denied"
)

# 500 Internal Server Error
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Internal server error"
)
```

---

## 로깅 전략

### Python Logging 사용

```python
import logging

# Logger 설정
logger = logging.getLogger(__name__)


class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
        logger.info(f"Creating project: {data.name}")

        project = Project(**data.model_dump())
        db.add(project)

        try:
            await db.commit()
            await db.refresh(project)
            logger.info(f"Project created: id={project.id}, name={project.name}")
            return project
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            await db.rollback()
            raise
```

---

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLModel 공식 문서](https://sqlmodel.tiangolo.com/)
- [Pydantic 공식 문서](https://docs.pydantic.dev/)
- [TDD Guide (TDD_GUIDE.md)](./TDD_GUIDE.md)
- [Testing Strategy (TESTING_STRATEGY.md)](./TESTING_STRATEGY.md)
- [Git Workflow (GIT_WORKFLOW.md)](./GIT_WORKFLOW.md)

---

**다음 문서**: [Frontend Development Guide (FRONTEND_DEVELOPMENT.md)](./FRONTEND_DEVELOPMENT.md)
