# EAZY 프로젝트 액션 아이템

**생성일**: 2026-01-08
**총 아이템**: 14개
**예상 시간**: 46시간 (약 1.5 sprints)

---

## 🔴 P0: Critical (즉시 해결 - 오늘 중)

### ✅ ITEM-1: CORS 설정 수정

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🔴 P0 - Critical |
| **파일** | `backend/app/main.py` |
| **라인** | 12 |
| **예상 시간** | 30분 |
| **담당자** | [ ] |

**현재 코드**:
```python
# ❌ 위험: 모든 Origin 허용
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # ⚠️ "*"와 함께 사용 시 위험
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**수정 코드**:
```python
# ✅ 안전: 특정 도메인만 허용
origins = [
    "http://localhost:5173",  # 개발 환경
    "http://localhost:3000",  # 대체 개발 포트
    # 프로덕션 배포 시 추가:
    # settings.FRONTEND_URL,  # 예: "https://eazy.example.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],  # 명시적 제한
    allow_headers=["Content-Type", "Authorization"],   # 명시적 제한
)
```

**검증 방법**:
```bash
# 1. 허용된 Origin 테스트 (성공해야 함)
curl -H "Origin: http://localhost:5173" \
     http://localhost:8000/api/v1/projects/
# 예상: 200 OK

# 2. 거부된 Origin 테스트 (실패해야 함)
curl -H "Origin: http://malicious.com" \
     http://localhost:8000/api/v1/projects/
# 예상: 403 Forbidden 또는 CORS 에러

# 3. 테스트 코드 작성
# tests/test_security_config.py
def test_cors_allows_localhost():
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.status_code != 403

def test_cors_blocks_unknown_origin():
    response = client.get("/", headers={"Origin": "http://malicious.com"})
    assert "access-control-allow-origin" not in response.headers
```

**완료 체크리스트**:
- [ ] `backend/app/main.py` 수정
- [ ] 로컬 테스트 (localhost:5173 허용 확인)
- [ ] 테스트 코드 작성
- [ ] `uv run pytest` 통과
- [ ] 커밋: `fix(security): restrict CORS to specific origins`

---

### ✅ ITEM-2: SQL Echo 조건부 활성화

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🔴 P0 - Critical |
| **파일** | `backend/app/core/db.py` |
| **라인** | 8 |
| **예상 시간** | 10분 |
| **담당자** | [ ] |

**현재 코드**:
```python
# ❌ 위험: 모든 SQL 쿼리 로깅 (프로덕션에서 정보 노출)
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)
```

**수정 코드**:
```python
# ✅ 안전: 개발 환경에서만 SQL 로깅
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 환경 변수로 제어
    future=True
)
```

**추가 작업 (settings.py)**:
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # 기존 설정...

    DEBUG: bool = Field(default=False)  # 추가

    class Config:
        env_file = ".env"
```

**.env 파일 예시**:
```bash
# 개발 환경
DEBUG=true

# 프로덕션 환경
DEBUG=false
```

**검증 방법**:
```bash
# 1. 개발 모드 테스트
echo "DEBUG=true" > .env
uv run uvicorn app.main:app --reload
# 콘솔에 SQL 쿼리 출력 확인

# 2. 프로덕션 모드 테스트
echo "DEBUG=false" > .env
uv run uvicorn app.main:app
# 콘솔에 SQL 쿼리 없어야 함
```

**완료 체크리스트**:
- [ ] `backend/app/core/db.py` 수정
- [ ] `backend/app/core/config.py`에 DEBUG 필드 추가
- [ ] `.env.example` 파일에 DEBUG 예시 추가
- [ ] 개발/프로덕션 모드 각각 테스트
- [ ] 커밋: `fix(security): make SQL echo conditional on DEBUG mode`

---

### ✅ ITEM-3: Secret Key 검증 추가

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🔴 P0 - Critical |
| **파일** | `backend/app/core/config.py` |
| **라인** | 22 |
| **예상 시간** | 20분 |
| **담당자** | [ ] |

**현재 코드**:
```python
# ❌ 위험: 기본값 하드코딩
class Settings(BaseSettings):
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION"
```

**수정 코드**:
```python
# ✅ 안전: 기본값 거부 + 길이 검증
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        # 기본값 거부
        if v == "CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION":
            raise ValueError(
                "SECRET_KEY must be changed from default value. "
                "Generate a secure key with: "
                "python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )

        # 최소 길이 검증
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")

        return v
```

**안전한 키 생성**:
```bash
# 터미널에서 실행
python -c "import secrets; print(secrets.token_urlsafe(64))"

# 출력 예시:
# Xt9kP3mVq7L2wN8sJ4hF6gD1aZ5cR0eK7tY9uI3oP2qW1sA4xE6vB8nM5lK

# .env 파일에 추가
echo "SECRET_KEY=<생성된_키>" >> .env
```

**검증 방법**:
```bash
# 1. 기본값 테스트 (실패해야 함)
SECRET_KEY="CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION" uv run python -c "from app.core.config import Settings; Settings()"
# 예상: ValueError 발생

# 2. 짧은 키 테스트 (실패해야 함)
SECRET_KEY="short" uv run python -c "from app.core.config import Settings; Settings()"
# 예상: ValueError 발생

# 3. 유효한 키 테스트 (성공해야 함)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))") \
uv run python -c "from app.core.config import Settings; Settings()"
# 예상: 에러 없음

# 4. 테스트 코드
# tests/core/test_config.py
import pytest
from app.core.config import Settings

def test_secret_key_rejects_default():
    with pytest.raises(ValueError, match="must be changed"):
        Settings(SECRET_KEY="CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION")

def test_secret_key_rejects_short():
    with pytest.raises(ValueError, match="at least 32 characters"):
        Settings(SECRET_KEY="short")

def test_secret_key_accepts_valid():
    settings = Settings(SECRET_KEY="a" * 64)
    assert len(settings.SECRET_KEY) == 64
```

**완료 체크리스트**:
- [ ] `backend/app/core/config.py`에 validator 추가
- [ ] 안전한 SECRET_KEY 생성 (64자 이상)
- [ ] `.env` 파일에 추가
- [ ] `.env.example` 파일 업데이트 (주석으로 생성 방법 안내)
- [ ] 테스트 코드 작성 (3개)
- [ ] `uv run pytest` 통과
- [ ] 커밋: `fix(security): add SECRET_KEY validation`

---

## 🟠 P1: High Priority (이번 주)

### ✅ ITEM-4: 데이터베이스 인덱스 추가

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟠 P1 - High |
| **파일** | 신규 Alembic 마이그레이션 |
| **예상 시간** | 2시간 |
| **담당자** | [ ] |

**누락된 인덱스 5개**:
1. `projects.is_archived` - archived 필터링
2. `tasks.status` - 폴링 조회
3. `tasks.target_id` - FK JOIN
4. `assets.target_id` - FK JOIN
5. `assets.last_seen_at` - 정렬

**성능 영향 분석**:
| 자산 수 | 인덱스 없음 | 인덱스 있음 | 개선율 |
|--------|------------|-----------|--------|
| 1만 건 | ~100ms | ~10ms | 10배 |
| 10만 건 | ~1초 | ~50ms | 20배 |
| 100만 건 | ~10초 | ~200ms | 50배 |

**작업 순서**:
```bash
# 1. 마이그레이션 파일 생성
cd backend
uv run alembic revision -m "add_performance_indexes"

# 2. 생성된 파일 편집
# alembic/versions/XXXXXXXX_add_performance_indexes.py
```

**마이그레이션 코드**:
```python
"""add_performance_indexes

Revision ID: XXXXXXXX
Revises: 03d37afa12f2
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'XXXXXXXX'
down_revision = '03d37afa12f2'
branch_labels = None
depends_on = None


def upgrade():
    # 1. projects.is_archived (필터링 최적화)
    op.create_index(
        'idx_projects_is_archived',
        'projects',
        ['is_archived']
    )

    # 2. tasks.status (폴링 최적화)
    op.create_index(
        'idx_tasks_status',
        'tasks',
        ['status']
    )

    # 3. tasks.target_id (FK JOIN 최적화)
    op.create_index(
        'idx_tasks_target_id',
        'tasks',
        ['target_id']
    )

    # 4. assets.target_id (FK JOIN 최적화)
    op.create_index(
        'idx_assets_target_id',
        'assets',
        ['target_id']
    )

    # 5. assets.last_seen_at (정렬 최적화)
    op.create_index(
        'idx_assets_last_seen_at',
        'assets',
        ['last_seen_at']
    )

    # 6. 복합 인덱스 (target_id + last_seen_at 동시 조회)
    op.create_index(
        'idx_assets_target_last_seen',
        'assets',
        ['target_id', sa.text('last_seen_at DESC')],
        postgresql_using='btree'
    )


def downgrade():
    op.drop_index('idx_assets_target_last_seen', table_name='assets')
    op.drop_index('idx_assets_last_seen_at', table_name='assets')
    op.drop_index('idx_assets_target_id', table_name='assets')
    op.drop_index('idx_tasks_target_id', table_name='tasks')
    op.drop_index('idx_tasks_status', table_name='tasks')
    op.drop_index('idx_projects_is_archived', table_name='projects')
```

**검증 방법**:
```bash
# 1. 마이그레이션 적용
uv run alembic upgrade head

# 2. 인덱스 생성 확인
psql -U postgres -d eazy_db -c "\d+ assets"
# 예상 출력에 인덱스 목록 표시

# 3. 쿼리 성능 테스트
psql -U postgres -d eazy_db -c "
EXPLAIN ANALYZE
SELECT * FROM assets
WHERE target_id = 1
ORDER BY last_seen_at DESC
LIMIT 10;
"
# 예상 출력: "Index Scan using idx_assets_target_last_seen"

# 4. 통합 테스트
uv run pytest tests/integration/test_asset_queries.py
```

**완료 체크리스트**:
- [ ] Alembic 마이그레이션 파일 생성
- [ ] 6개 인덱스 정의 (단일 5개 + 복합 1개)
- [ ] 로컬 DB에 마이그레이션 적용
- [ ] EXPLAIN ANALYZE로 성능 확인
- [ ] `alembic downgrade -1` 테스트 (롤백 동작 확인)
- [ ] 커밋: `perf(db): add performance indexes for FK and sorting`

---

### ✅ ITEM-5: N+1 쿼리 배치 처리

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟠 P1 - High |
| **파일** | `backend/app/services/asset_service.py` |
| **라인** | 96-98 |
| **예상 시간** | 4시간 |
| **담당자** | [ ] |

**현재 코드 (N+1 문제)**:
```python
# ❌ 문제: 100개 링크 → 100번 쿼리
async def process_asset(self, ...):
    for link in crawled_links:  # 루프
        # 각 link마다 SELECT 실행
        statement = select(Asset).where(Asset.content_hash == hash)
        result = await self.session.exec(statement)
        existing_asset = result.first()  # N+1 문제
```

**수정 코드 (배치 처리)**:
```python
# ✅ 해결: 100개 링크 → 1번 쿼리
from typing import List, Dict, Any

async def process_assets_batch(
    self,
    target_id: int,
    task_id: int,
    assets_data: List[Dict[str, Any]]
) -> List[Asset]:
    """
    여러 Asset을 배치로 처리 (N+1 문제 해결)

    Args:
        target_id: Target ID
        task_id: Task ID
        assets_data: Asset 정보 리스트
            [{"method": "GET", "url": "http://example.com", ...}, ...]

    Returns:
        처리된 Asset 리스트
    """
    if not assets_data:
        return []

    # 1. 모든 content_hash 생성
    content_hashes = [
        self._generate_content_hash(a['method'], a['url'])
        for a in assets_data
    ]

    # 2. 단일 쿼리로 기존 Asset 조회 (N+1 해결!)
    statement = select(Asset).where(Asset.content_hash.in_(content_hashes))
    result = await self.session.exec(statement)
    existing_assets = {a.content_hash: a for a in result.all()}

    # 3. Bulk UPSERT
    processed_assets = []
    for asset_data in assets_data:
        content_hash = self._generate_content_hash(
            asset_data['method'],
            asset_data['url']
        )

        if content_hash in existing_assets:
            # 기존 Asset 업데이트
            asset = existing_assets[content_hash]
            asset.last_seen_at = datetime.utcnow()
        else:
            # 신규 Asset 생성
            asset = Asset(
                target_id=target_id,
                content_hash=content_hash,
                method=asset_data['method'],
                url=asset_data['url'],
                # ... 기타 필드
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow()
            )
            self.session.add(asset)

        # Discovery 레코드 생성
        discovery = AssetDiscovery(
            task_id=task_id,
            asset_id=asset.id if hasattr(asset, 'id') else None,
            parent_asset_id=asset_data.get('parent_asset_id'),
            discovered_at=datetime.utcnow()
        )
        self.session.add(discovery)

        processed_assets.append(asset)

    # 4. 단일 트랜잭션으로 커밋
    await self.session.commit()

    # 5. ID refresh (Discovery의 asset_id 설정을 위해)
    for asset in processed_assets:
        await self.session.refresh(asset)

    return processed_assets
```

**Worker 수정 (CrawlerService 호출 부분)**:
```python
# backend/app/worker.py

# 기존
for link in links:
    await asset_service.process_asset(...)  # N+1

# 수정
assets_data = [
    {"method": "GET", "url": link, ...}
    for link in links
]
await asset_service.process_assets_batch(
    target_id=target_record.id,
    task_id=task_record.id,
    assets_data=assets_data
)
```

**검증 방법**:
```bash
# 1. 쿼리 수 측정 (테스트)
# tests/services/test_asset_service_batch.py
import pytest
from sqlalchemy import event

@pytest.mark.asyncio
async def test_process_assets_batch_reduces_queries(db_session):
    # 쿼리 카운터 설정
    query_count = []

    @event.listens_for(db_session.sync_session, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, *args):
        query_count.append(statement)

    # 100개 Asset 배치 처리
    assets_data = [
        {"method": "GET", "url": f"http://example.com/page{i}"}
        for i in range(100)
    ]

    service = AssetService(db_session)
    await service.process_assets_batch(1, 1, assets_data)

    # 검증: SELECT 쿼리가 1개만 실행되어야 함
    select_queries = [q for q in query_count if q.startswith("SELECT")]
    assert len(select_queries) <= 3  # SELECT Asset, INSERT 쿼리만

# 2. 실제 크롤링 테스트
uv run pytest tests/integration/test_full_crawl_batch.py -v

# 3. 로그로 확인
uv run python -m app.worker
# 콘솔 출력에서 "Saved X assets in 1 query" 확인
```

**완료 체크리스트**:
- [ ] `asset_service.py`에 `process_assets_batch()` 메서드 추가
- [ ] `worker.py`에서 배치 처리 호출로 변경
- [ ] 단위 테스트 작성 (쿼리 수 검증)
- [ ] 통합 테스트 (100개 링크 크롤링)
- [ ] 성능 비교 (이전 vs 배치 처리)
- [ ] 커밋: `perf(asset): implement batch processing to solve N+1 query`

---

### ✅ ITEM-6: print() → logging 교체

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟠 P1 - High |
| **파일** | `backend/app/services/crawler_service.py` |
| **라인** | 66, 132, 158 |
| **예상 시간** | 1시간 |
| **담당자** | [ ] |

**현재 코드 (3곳)**:
```python
# ❌ 문제: 프로덕션 디버깅 불가, 로그 레벨 제어 불가
print(f"Request interception error: {e}")  # 라인 66
print(f"Response interception error: {e}")  # 라인 132
print(f"Crawl error: {e}")  # 라인 158
```

**수정 코드**:
```python
# ✅ 해결: logging 라이브러리 사용
import logging

logger = logging.getLogger(__name__)  # 파일 상단에 추가

# 기존 print() 대체
logger.error(f"Request interception error: {e}", exc_info=True)
logger.error(f"Response interception error: {e}", exc_info=True)
logger.error(f"Crawl error for {url}: {e}", exc_info=True, extra={
    "url": url,
    "target_id": target_id
})
```

**로깅 설정 (main.py)**:
```python
# backend/app/main.py
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        # 프로덕션에서는 파일 핸들러 추가
        # logging.FileHandler("logs/app.log")
    ]
)

# 특정 로거 레벨 조정
logging.getLogger("app.services.crawler_service").setLevel(logging.DEBUG)
```

**검증 방법**:
```bash
# 1. 로그 출력 확인
uv run python -m app.worker
# 예상 출력 (구조화된 로그):
# 2026-01-08 10:00:00,000 - app.services.crawler_service - ERROR - Crawl error for http://example.com: ...

# 2. 로그 레벨 테스트
DEBUG=false uv run python -m app.worker
# ERROR 레벨 로그만 출력 확인

# 3. 테스트 코드
# tests/services/test_crawler_logging.py
import logging
from unittest.mock import patch

def test_crawler_logs_errors(caplog):
    with caplog.at_level(logging.ERROR):
        # 에러 발생시키는 크롤링
        await crawler.crawl("invalid_url")

    assert "Crawl error" in caplog.text
    assert "exc_info" in caplog.records[0].__dict__
```

**완료 체크리스트**:
- [ ] `crawler_service.py`에 logger 추가
- [ ] 모든 print() → logger 교체 (3곳)
- [ ] `main.py`에 logging 설정 추가
- [ ] 로그 출력 테스트 (INFO, ERROR 레벨)
- [ ] 테스트 코드 작성 (caplog 활용)
- [ ] 커밋: `refactor(logging): replace print() with logging library`

---

### ✅ ITEM-7: URL 검증 추가

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟠 P1 - High |
| **파일** | `backend/app/models/target.py` |
| **예상 시간** | 1시간 |
| **담당자** | [ ] |

**현재 코드**:
```python
# ❌ 문제: 악의적 URL 허용
class TargetBase(SQLModel):
    name: str = Field(max_length=255)
    url: str = Field(max_length=2048)  # 검증 없음
```

**수정 코드**:
```python
# ✅ 해결: Pydantic HttpUrl 사용 + 스킴 검증
from pydantic import HttpUrl, field_validator
from sqlmodel import SQLModel, Field

class TargetBase(SQLModel):
    name: str = Field(max_length=255)
    url: HttpUrl  # Pydantic 자동 검증

    @field_validator('url')
    @classmethod
    def validate_url_scheme(cls, v: HttpUrl) -> HttpUrl:
        """HTTP/HTTPS만 허용 (javascript:, file: 등 차단)"""
        if v.scheme not in ['http', 'https']:
            raise ValueError(
                f'Invalid URL scheme: {v.scheme}. '
                'Only http and https are allowed.'
            )
        return v

    @field_validator('url')
    @classmethod
    def validate_url_not_localhost(cls, v: HttpUrl) -> HttpUrl:
        """
        선택적: localhost/127.0.0.1 차단 (프로덕션 환경)
        개발 환경에서는 주석 처리
        """
        # if v.host in ['localhost', '127.0.0.1']:
        #     raise ValueError('Localhost URLs are not allowed')
        return v
```

**검증 방법**:
```bash
# 1. 유효한 URL 테스트 (성공)
curl -X POST http://localhost:8000/api/v1/projects/1/targets/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Valid", "url": "https://example.com"}'
# 예상: 201 Created

# 2. javascript: URL 테스트 (실패)
curl -X POST http://localhost:8000/api/v1/projects/1/targets/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Invalid", "url": "javascript:alert(1)"}'
# 예상: 422 Unprocessable Entity

# 3. file:// URL 테스트 (실패)
curl -X POST http://localhost:8000/api/v1/projects/1/targets/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Invalid", "url": "file:///etc/passwd"}'
# 예상: 422 Unprocessable Entity

# 4. 테스트 코드
# tests/models/test_target.py
import pytest
from app.models.target import TargetBase

def test_target_accepts_http():
    target = TargetBase(name="Test", url="http://example.com")
    assert target.url.scheme == "http"

def test_target_accepts_https():
    target = TargetBase(name="Test", url="https://example.com")
    assert target.url.scheme == "https"

def test_target_rejects_javascript():
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        TargetBase(name="Test", url="javascript:alert(1)")

def test_target_rejects_file():
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        TargetBase(name="Test", url="file:///etc/passwd")
```

**완료 체크리스트**:
- [ ] `target.py`에 HttpUrl 타입 적용
- [ ] URL 스킴 검증 validator 추가
- [ ] API 테스트 (curl로 여러 케이스 확인)
- [ ] 단위 테스트 작성 (4개)
- [ ] `uv run pytest` 통과
- [ ] 커밋: `feat(validation): add URL scheme validation for Target model`

---

### ✅ ITEM-8: 예외 처리 개선

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟠 P1 - High |
| **파일** | 여러 파일 (새 모듈 생성 + 기존 코드 수정) |
| **예상 시간** | 3시간 |
| **담당자** | [ ] |

**현재 코드 (task.py 예시)**:
```python
# ❌ 문제: 모든 예외를 catch하여 구체적 에러 처리 불가
try:
    task = await task_service.create_scan_task(project_id, target_id)
    return {"status": "pending", "task_id": task.id}
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # 내부 에러 노출
```

**Step 1: 커스텀 예외 정의**

새 파일 생성: `backend/app/core/exceptions.py`
```python
"""커스텀 예외 정의"""


class EAZYException(Exception):
    """Base exception for EAZY application"""

    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ResourceNotFound(EAZYException):
    """리소스를 찾을 수 없음"""

    def __init__(self, resource_type: str, resource_id: int):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            code=f"{resource_type.upper()}_NOT_FOUND"
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ProjectNotFound(ResourceNotFound):
    def __init__(self, project_id: int):
        super().__init__("Project", project_id)


class TargetNotFound(ResourceNotFound):
    def __init__(self, target_id: int):
        super().__init__("Target", target_id)


class QueueFullError(EAZYException):
    """작업 큐가 가득 참"""

    def __init__(self):
        super().__init__(
            message="Task queue is full, please try again later",
            code="QUEUE_FULL"
        )


class InvalidScopeError(EAZYException):
    """잘못된 스캔 범위"""

    def __init__(self, scope: str):
        super().__init__(
            message=f"Invalid scan scope: {scope}",
            code="INVALID_SCOPE"
        )
```

**Step 2: Global Exception Handler**

`backend/app/main.py`에 추가:
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from app.core.exceptions import (
    EAZYException,
    ResourceNotFound,
    QueueFullError
)

app = FastAPI()

# Global Exception Handlers 등록
@app.exception_handler(ResourceNotFound)
async def resource_not_found_handler(request: Request, exc: ResourceNotFound):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "resource_type": exc.resource_type,
                "resource_id": exc.resource_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(QueueFullError)
async def queue_full_handler(request: Request, exc: QueueFullError):
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(EAZYException)
async def eazy_exception_handler(request: Request, exc: EAZYException):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

**Step 3: 기존 코드 수정**

`backend/app/api/v1/endpoints/task.py`:
```python
# ✅ 해결: 구체적 예외 처리
from app.core.exceptions import TargetNotFound, QueueFullError

@router.post("/{project_id}/targets/{target_id}/scan")
async def trigger_scan(
    project_id: int,
    target_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        task_service = TaskService(session)
        task = await task_service.create_scan_task(project_id, target_id)
        return {"status": "pending", "task_id": task.id}
    except TargetNotFound:
        # Global handler가 404 반환
        raise
    except QueueFullError:
        # Global handler가 503 반환
        raise
    except Exception as e:
        # 예상치 못한 에러만 500 (내부 상세는 로깅만)
        logger.exception("Unexpected error creating scan task")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"  # 상세 내용 숨김
        )
```

**검증 방법**:
```bash
# 1. 리소스 없음 테스트
curl http://localhost:8000/api/v1/projects/9999
# 예상 응답 (404):
# {
#   "error": {
#     "code": "PROJECT_NOT_FOUND",
#     "message": "Project with ID 9999 not found",
#     "resource_type": "Project",
#     "resource_id": 9999,
#     "timestamp": "2026-01-08T10:00:00Z"
#   }
# }

# 2. 테스트 코드
# tests/api/test_error_handling.py
async def test_project_not_found_returns_structured_error(client):
    response = await client.get("/api/v1/projects/9999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"
    assert "timestamp" in data["error"]
```

**완료 체크리스트**:
- [ ] `app/core/exceptions.py` 생성 (6개 예외 클래스)
- [ ] `main.py`에 Global Exception Handler 추가 (3개)
- [ ] `task.py`, `project.py` 등 기존 엔드포인트 수정
- [ ] 에러 응답 JSON 구조 통일 확인
- [ ] 테스트 코드 작성 (각 예외별)
- [ ] 커밋: `refactor(error): implement custom exceptions and global handlers`

---

## 🟡 P2: Medium Priority (다음 스프린트)

### ✅ ITEM-9: React Error Boundary

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟡 P2 - Medium |
| **파일** | `frontend/src/App.tsx` |
| **예상 시간** | 2시간 |
| **담당자** | [ ] |

**작업 순서**:
```bash
# 1. 패키지 설치
cd frontend
npm install react-error-boundary
```

**구현 코드**:
```typescript
// frontend/src/App.tsx
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error, resetErrorBoundary }: any) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full space-y-4 p-6">
        <h1 className="text-2xl font-bold text-destructive">
          Something went wrong
        </h1>
        <pre className="text-sm text-muted-foreground bg-muted p-4 rounded overflow-auto">
          {error.message}
        </pre>
        <button
          onClick={resetErrorBoundary}
          className="w-full py-2 px-4 bg-primary text-primary-foreground rounded"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={() => window.location.reload()}
      onError={(error, info) => {
        // 프로덕션에서는 Sentry 등으로 전송
        console.error('Error caught by boundary:', error, info);
      }}
    >
      <QueryClientProvider client={queryClient}>
        {/* 기존 라우터 */}
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
```

**완료 체크리스트**:
- [ ] `react-error-boundary` 설치
- [ ] `App.tsx`에 ErrorBoundary 추가
- [ ] ErrorFallback 컴포넌트 스타일링
- [ ] 에러 트리거 테스트 (의도적 에러 발생)
- [ ] 커밋: `feat(frontend): add React Error Boundary`

---

### ✅ ITEM-10: Pagination 추가

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟡 P2 - Medium |
| **파일** | `backend/app/api/v1/endpoints/project.py` |
| **라인** | 142-173 |
| **예상 시간** | 2시간 |
| **담당자** | [ ] |

**현재 코드**:
```python
# ❌ 문제: 모든 Asset 반환 (1000s 가능)
@router.get("/{project_id}/targets/{target_id}/assets")
async def get_target_assets(...):
    statement = select(Asset).where(Asset.target_id == target_id)
    results = await session.exec(statement)
    return results.all()  # 제한 없음
```

**수정 코드**:
```python
# ✅ 해결: Pagination 추가
from typing import List

@router.get("/{project_id}/targets/{target_id}/assets")
async def get_target_assets(
    project_id: int,
    target_id: int,
    skip: int = 0,
    limit: int = 100,  # 기본 100개
    session: AsyncSession = Depends(get_session)
) -> List[AssetRead]:
    """
    Target의 Asset 목록 조회 (페이지네이션)

    Args:
        skip: 건너뛸 레코드 수 (오프셋)
        limit: 반환할 최대 레코드 수 (최대 1000)
    """
    # limit 상한선 설정
    limit = min(limit, 1000)

    statement = (
        select(Asset)
        .where(Asset.target_id == target_id)
        .order_by(Asset.last_seen_at.desc())
        .offset(skip)
        .limit(limit)
    )
    results = await session.exec(statement)
    return results.all()
```

**Frontend 수정** (`frontend/src/services/targetService.ts`):
```typescript
export async function getTargetAssets(
  projectId: number,
  targetId: number,
  skip: number = 0,
  limit: number = 100
): Promise<Asset[]> {
  const response = await api.get(
    `/projects/${projectId}/targets/${targetId}/assets`,
    { params: { skip, limit } }
  );
  return response.data;
}
```

**완료 체크리스트**:
- [ ] Backend API에 `skip`, `limit` 파라미터 추가
- [ ] Frontend 서비스 함수 수정
- [ ] 테스트 코드 작성 (페이지네이션 동작 확인)
- [ ] 커밋: `feat(api): add pagination to assets endpoint`

---

### ✅ ITEM-11: Rate Limiting

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟡 P2 - Medium |
| **파일** | `backend/app/main.py` |
| **예상 시간** | 3시간 |
| **담당자** | [ ] |

**작업 순서**:
```bash
# 1. 패키지 설치
cd backend
uv add slowapi
```

**구현 코드**:
```python
# backend/app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Limiter 설정
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# backend/app/api/v1/endpoints/task.py
from app.main import limiter

@router.post("/{project_id}/targets/{target_id}/scan")
@limiter.limit("5/minute")  # IP당 분당 5회
async def trigger_scan(...):
    # ...
```

**완료 체크리스트**:
- [ ] `slowapi` 설치
- [ ] Limiter 설정
- [ ] 스캔 엔드포인트에 rate limit 적용
- [ ] 초과 테스트 (429 응답 확인)
- [ ] 커밋: `feat(security): add rate limiting to scan endpoint`

---

### ✅ ITEM-12: 중복 코드 제거

| 항목 | 내용 |
|-----|------|
| **우선순위** | 🟡 P2 - Medium |
| **파일** | `backend/app/worker.py` |
| **예상 시간** | 1시간 |
| **담당자** | [ ] |

**작업**: 취소 확인 로직을 함수로 추출

**완료 체크리스트**:
- [ ] `_check_cancellation()` 함수 추출
- [ ] 중복 코드 제거
- [ ] 커밋: `refactor(worker): extract cancellation check logic`

---

## ⚪ P3: Low Priority (향후)

### ✅ ITEM-13: URL 정규화

| 항목 | 내용 |
|-----|------|
| **우선순위** | ⚪ P3 - Low |
| **파일** | 신규 `backend/app/utils/url_normalizer.py` |
| **예상 시간** | 4시간 |
| **담당자** | [ ] |

**작업**: 쿼리 파라미터 정렬, Fragment 제거 등

---

### ✅ ITEM-14: Connection Pooling

| 항목 | 내용 |
|-----|------|
| **우선순위** | ⚪ P3 - Low |
| **파일** | `backend/app/core/db.py` |
| **예상 시간** | 1시간 |
| **담당자** | [ ] |

**작업**: `pool_size`, `max_overflow` 설정

---

## 📊 진행 상황 추적

| 우선순위 | 완료 | 총합 | 진행률 |
|---------|------|------|--------|
| P0 (Critical) | 0 | 3 | 0% |
| P1 (High) | 0 | 5 | 0% |
| P2 (Medium) | 0 | 4 | 0% |
| P3 (Low) | 0 | 2 | 0% |
| **총합** | **0** | **14** | **0%** |

### 예상 시간 요약

| 카테고리 | 예상 시간 |
|---------|----------|
| P0 (보안) | 1시간 |
| P1 (성능 + 품질) | 11시간 |
| P2 (안정성) | 8시간 |
| P3 (최적화) | 5시간 |
| **총합** | **25시간** |

---

## 🎯 Sprint 할당 제안

### Sprint 1 (2주) - 긴급 및 고우선순위
**목표**: 프로덕션 준비 완료

| Week | 아이템 | 시간 | 담당자 |
|------|-------|-----|--------|
| Week 1 | ITEM-1, 2, 3 (P0 전체) | 1시간 | [ ] |
| Week 1 | ITEM-4, 6, 7 (인덱스, 로깅, URL) | 4시간 | [ ] |
| Week 2 | ITEM-5 (N+1 쿼리) | 4시간 | [ ] |
| Week 2 | ITEM-8 (예외 처리) | 3시간 | [ ] |

**Sprint 1 총 시간**: 12시간

---

### Sprint 2 (2주) - 안정성 및 중간 우선순위
**목표**: 안정성 향상

| Week | 아이템 | 시간 | 담당자 |
|------|-------|-----|--------|
| Week 3 | ITEM-9, 10 (Error Boundary, Pagination) | 4시간 | [ ] |
| Week 4 | ITEM-11, 12 (Rate Limiting, 리팩토링) | 4시간 | [ ] |

**Sprint 2 총 시간**: 8시간

---

### Sprint 3 (2주) - 최적화
**목표**: 성능 최적화

| Week | 아이템 | 시간 | 담당자 |
|------|-------|-----|--------|
| Week 5 | ITEM-13 (URL 정규화) | 4시간 | [ ] |
| Week 6 | ITEM-14 (Connection Pooling) | 1시간 | [ ] |
| Week 6 | 모니터링 스택 구축 (Phase 4) | 8시간 | [ ] |

**Sprint 3 총 시간**: 13시간

---

## 📝 Notes

### 우선순위 결정 기준
- **P0 (Critical)**: 보안 위험, 프로덕션 배포 블로커
- **P1 (High)**: 성능 병목, 코드 품질 문제
- **P2 (Medium)**: 안정성 향상, 사용자 경험 개선
- **P3 (Low)**: 최적화, 기술 부채 감소

### 작업 순서 권장
1. P0 전체 → 즉시 (1시간)
2. P1 선택적 → 금주 내 (2-3개씩)
3. P2 선택적 → 다음 스프린트
4. P3 선택적 → 여유 시간

---

## 🚀 시작하기

### 오늘 할 일 (P0 전체)
```bash
# 1. ITEM-1: CORS 수정
cd backend
# backend/app/main.py 편집
# origins = ["http://localhost:5173", ...]

# 2. ITEM-2: SQL Echo 조건부
# backend/app/core/db.py 편집
# echo=settings.DEBUG

# 3. ITEM-3: Secret Key 검증
# backend/app/core/config.py 편집
# @field_validator('SECRET_KEY')

# 4. 테스트 및 커밋
uv run pytest
git add .
git commit -m "fix(security): resolve 3 critical security issues"
git push
```

**예상 완료 시간**: 1시간

---

**문서 생성일**: 2026-01-08
**마지막 업데이트**: 2026-01-08
