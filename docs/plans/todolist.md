# EAZY 기능 구현 Todolist (TDD 방식) - 상세

> TDD 사이클: **Red** (실패 테스트) → **Green** (통과 코드) → **Blue** (리팩토링)

---

## 환경 설정

### Python 패키지 관리자: **uv 필수**

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 가상환경 생성 및 활성화
cd backend
uv venv
source .venv/bin/activate  # Linux/macOS

# 의존성 설치
uv pip install -e ".[dev]"

# 테스트 실행
uv run pytest tests/ -v --cov=app

# 마이그레이션
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "message"
```

### Frontend 패키지 관리자: **pnpm**

```bash
cd frontend
pnpm install
pnpm test
```

---

## Feature 1: Active 스캔 재귀 크롤링 [CRITICAL]

### 1.1 Backend - Task 모델 확장

**Red Phase** - `backend/tests/models/test_task_recursive.py`
```python
def test_task_has_depth_field_default_zero():
    """Given: 새 Task 생성, When: depth 미지정, Then: 기본값 0"""

def test_task_has_max_depth_field_default_three():
    """Given: 새 Task 생성, When: max_depth 미지정, Then: 기본값 3"""

def test_task_has_parent_task_id_nullable():
    """Given: 루트 Task, When: parent_task_id=None, Then: 정상 생성"""

def test_task_parent_task_id_foreign_key_cascade():
    """Given: 부모-자식 Task, When: 부모 삭제, Then: 자식 parent_task_id=NULL"""
```
```bash
uv run pytest tests/models/test_task_recursive.py -v
```

**Green Phase** - `backend/app/models/task.py`
```python
class TaskBase(SQLModel):
    # 새 필드 추가
    depth: int = Field(default=0, description="현재 크롤링 깊이")
    max_depth: int = Field(default=3, description="최대 크롤링 깊이")
    parent_task_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    )
```

**Blue Phase** - 리팩토링
```bash
uv run alembic revision --autogenerate -m "add_task_recursive_fields"
uv run alembic upgrade head
# 인덱스 추가: (target_id, depth), (parent_task_id)
```

- [x] Red: 테스트 작성
- [x] Green: 모델 구현
- [x] Blue: 마이그레이션 및 인덱스 ✅ (커밋: ac35d07)

---

### 1.2 Backend - URL 정규화 서비스

**Red Phase** - `backend/tests/services/test_url_normalizer.py`
```python
def test_normalize_removes_fragment():
    """Input: "https://example.com/page#section" → "https://example.com/page" """

def test_normalize_lowercases_scheme_and_host():
    """Input: "HTTPS://EXAMPLE.COM/Path" → "https://example.com/Path" """

def test_normalize_removes_default_port():
    """Input: "https://example.com:443/" → "https://example.com" """

def test_normalize_sorts_query_params():
    """Input: "?z=3&a=1&m=2" → "?a=1&m=2&z=3" """

def test_normalize_removes_trailing_slash():
    """Input: "https://example.com/page/" → "https://example.com/page" """

def test_normalize_handles_relative_url():
    """Input: "../other", base="https://example.com/path/page" → "https://example.com/other" """

def test_get_url_hash_deterministic():
    """동일 URL 다른 포맷 → 동일 해시"""
```
```bash
uv run pytest tests/services/test_url_normalizer.py -v
```

**Green Phase** - `backend/app/services/url_normalizer.py`
```python
def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """URL 정규화: scheme/host 소문자, 기본포트 제거, fragment 제거, 쿼리 정렬"""

def get_url_hash(url: str, method: str = "GET") -> str:
    """SHA-256 해시 생성: f"{method}:{normalized_url}" """

def is_same_resource(url1: str, url2: str) -> bool:
    """정규화 후 동일 여부 비교"""
```

**Blue Phase** - 리팩토링
- 상수 분리: `SESSION_PARAMS = {"sid", "jsessionid", "phpsessid"}`
- `functools.lru_cache` 적용
- `NewType("NormalizedUrl", str)` 타입 정의

- [x] Red: 28개 테스트 작성 ✅
- [x] Green: 정규화 함수 구현 (normalize_url, get_url_hash, is_same_resource) ✅
- [x] Blue: lru_cache, NewType, normalize_urls_batch 추가 ✅ (커버리지 95%)

---

### 1.3 Backend - Scope 필터링

**Red Phase** - `backend/tests/services/test_scope_filter.py`
```python
def test_domain_scope_allows_same_domain():
    """DOMAIN: example.com → example.com/page 허용"""

def test_domain_scope_blocks_subdomain():
    """DOMAIN: example.com → api.example.com 차단"""

def test_subdomain_scope_allows_subdomain():
    """SUBDOMAIN: www.example.com → api.example.com 허용"""

def test_url_only_scope_allows_same_path():
    """URL_ONLY: example.com/app → example.com/app/sub 허용"""

def test_url_only_scope_blocks_different_path():
    """URL_ONLY: example.com/app → example.com/other 차단"""

def test_filter_urls_batch():
    """여러 URL 필터링 → in-scope만 반환"""
```
```bash
uv run pytest tests/services/test_scope_filter.py -v
```

**Green Phase** - `backend/app/services/scope_filter.py`
```python
class ScopeFilter:
    def __init__(self, target_url: str, scope: TargetScope) -> None:
        """target_url과 scope 기반 필터 초기화"""

    def is_in_scope(self, url: str) -> bool:
        """URL이 scope 내인지 확인"""

    def filter_urls(self, urls: List[str]) -> List[str]:
        """in-scope URL만 필터링"""

def extract_base_domain(hostname: str) -> str:
    """api.example.com → example.com"""
```

**Blue Phase** - 리팩토링
- ~~robots.txt 준수 옵션 추가~~ → robots.txt 경로 Assets 수집으로 변경
- URL blocklist 지원 (`/logout`, `/admin` 등) - 향후 구현

- [x] Red: 34개 테스트 작성 ✅
- [x] Green: ScopeFilter 클래스 구현 ✅
- [x] Blue: RobotsTxtService 추가 (Disallow/Sitemap 경로 수집) ✅
- [x] AssetSource enum 확장 (ROBOTS_TXT, SITEMAP) ✅

---

### 1.4 Backend - 재귀 크롤링 로직 (BFS)

**Red Phase** - `backend/tests/services/test_crawl_manager.py`
```python
@pytest.mark.asyncio
async def test_crawl_manager_creates_child_tasks():
    """발견된 URL → 자식 Task 생성 (depth+1, parent_task_id 설정)"""

@pytest.mark.asyncio
async def test_crawl_manager_respects_max_depth():
    """depth == max_depth → 자식 Task 생성 안함"""

@pytest.mark.asyncio
async def test_crawl_manager_deduplicates_urls():
    """중복/방문 URL → 제외"""

@pytest.mark.asyncio
async def test_crawl_manager_applies_scope_filter():
    """out-of-scope URL → 제외"""
```
```bash
uv run pytest tests/services/test_crawl_manager.py -v
```

**Green Phase** - `backend/app/services/crawl_manager.py`
```python
class CrawlManager:
    VISITED_KEY_PREFIX = "crawl:visited:"

    async def spawn_child_tasks(
        self,
        parent_task_id: int,
        target_id: int,
        project_id: int,
        discovered_urls: List[str],
        current_depth: int,
        max_depth: int,
        target_url: Optional[str] = None,
        scope: Optional[TargetScope] = None,
    ) -> List[Task]:
        """발견된 URL에 대해 자식 Task 생성"""

    async def mark_visited(self, target_id: int, urls: List[str]) -> None:
        """Redis SET에 방문 URL 저장"""

    async def is_visited(self, target_id: int, url: str) -> bool:
        """방문 여부 확인"""
```

**Blue Phase** - 리팩토링
- Redis 파이프라인으로 배치 처리
- 회로 차단기(Circuit Breaker) 패턴 적용
- 메트릭 수집 (크롤 속도, 큐 깊이)

- [x] Red: 24개 async 테스트 작성 (상대 URL 변환 테스트 포함) ✅
- [x] Green: CrawlManager 클래스 구현 ✅
- [x] Blue: Redis 파이프라인 구현 ✅

---

### 1.5 Backend - Worker 확장

**Red Phase** - `backend/tests/workers/test_crawl_worker_recursive.py`
```python
@pytest.mark.asyncio
async def test_worker_spawns_child_tasks_after_crawl():
    """크롤 완료 → 자식 Task 생성"""

@pytest.mark.asyncio
async def test_worker_stops_at_max_depth():
    """depth == max_depth → 자식 Task 생성 안함"""
```
```bash
uv run pytest tests/workers/test_crawl_worker_recursive.py -v
```

**Green Phase** - `backend/app/workers/crawl_worker.py`
```python
async def _execute_with_lock(self, ...):
    # 기존 크롤 로직
    links, http_data = await self.crawler.crawl(target.url)
    saved_count = await self._save_assets(...)

    # 새로 추가: 자식 Task 생성
    child_tasks_spawned = 0
    if current_depth < max_depth:
        child_tasks = await self._spawn_child_tasks(
            parent_task_id=db_task_id,
            target=target,
            discovered_urls=links,
            current_depth=current_depth,
            max_depth=max_depth,
        )
        child_tasks_spawned = len(child_tasks)

    return TaskResult.create_success({
        "child_tasks_spawned": child_tasks_spawned,
        ...
    })
```

**Blue Phase** - 리팩토링
- Rate limiting 적용 (요청 간격 100ms)
- 동시 요청 제한 (Semaphore 5개)
- 진행 상황 추적

- [x] Red: 3개 async 테스트 작성 ✅
- [x] Green: Worker에 자식 Task 생성 로직 추가 ✅
- [ ] Blue: Rate limiting, Semaphore (향후 구현)

---

## Feature 2: 스캔 히스토리 페이지 [HIGH]

### 2.1 Backend - Task 목록 API

**Red Phase** - `backend/tests/api/test_task_list.py`
```python
@pytest.mark.asyncio
async def test_get_tasks_for_target_returns_list():
    """GET /targets/{id}/tasks → Task 목록 반환"""

@pytest.mark.asyncio
async def test_get_tasks_for_target_sorted_by_created_at_desc():
    """최신 Task가 먼저 반환"""

@pytest.mark.asyncio
async def test_get_tasks_for_target_with_pagination():
    """skip=2&limit=3 → 3개 Task 반환"""

@pytest.mark.asyncio
async def test_get_tasks_for_target_with_status_filter():
    """status=completed → 완료된 Task만 반환"""
```
```bash
uv run pytest tests/api/test_task_list.py -v
```

**Green Phase** - `backend/app/api/v1/endpoints/task.py`
```python
@router.get("/targets/{target_id}/tasks", response_model=List[TaskRead])
async def get_tasks_for_target(
    target_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TaskStatus] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> List[Task]:
    """타겟의 스캔 히스토리 조회 (페이지네이션, 필터링 지원)"""
```

**Blue Phase** - 리팩토링
- 복합 인덱스: `(target_id, created_at DESC)`
- 응답 메타데이터: `total_count`, `has_more`

- [ ] Red: 4개 API 테스트 작성
- [ ] Green: 엔드포인트 구현
- [ ] Blue: 인덱스, 메타데이터

---

### 2.2-2.5 Frontend - 히스토리 컴포넌트

**Red Phase** - `frontend/src/components/features/target/tabs/HistoryTabContent.test.tsx`
```typescript
describe('HistoryTabContent', () => {
  it('should render loading skeleton');
  it('should render empty state when no tasks');
  it('should render task list with status badges');
  it('should display task duration (started_at → completed_at)');
  it('should handle pagination');
});
```
```bash
pnpm test -- src/components/features/target/tabs/HistoryTabContent.test.tsx
```

**Green Phase**

1. **Service** - `frontend/src/services/taskService.ts`
```typescript
export const getTasksForTarget = async (
  targetId: number,
  params: { skip?: number; limit?: number; status?: TaskStatus }
): Promise<Task[]> => api.get(`/targets/${targetId}/tasks`, params);
```

2. **Hook** - `frontend/src/hooks/useTaskHistory.ts`
```typescript
export function useTaskHistory(targetId: number, params = {}) {
  return useQuery({
    queryKey: ['taskHistory', targetId, params],
    queryFn: () => getTasksForTarget(targetId, params),
    staleTime: 30000,
  });
}
```

3. **Component** - `frontend/src/components/features/target/tabs/HistoryTabContent.tsx`
```typescript
export function HistoryTabContent({ targetId }: Props) {
  const { data: tasks, isLoading } = useTaskHistory(targetId);
  // 테이블: Status Badge, Type, Started, Duration, Results
  // 빈 상태: "No scan history. Run a scan to see history here."
}
```

**Blue Phase** - 리팩토링
- `@tanstack/react-virtual`로 가상화
- Infinite scroll 페이지네이션
- Task 상세 모달 (JSON 뷰어)

- [ ] Red: 5개 컴포넌트 테스트 작성
- [ ] Green: Service, Hook, Component 구현
- [ ] Blue: 가상화, 무한 스크롤

---

## Feature 3: Assets 검색 (Target 도메인) [MEDIUM]

### 3.1 Backend - Target 검색 API

**Red Phase** - `backend/tests/api/test_target_search.py`
```python
@pytest.mark.asyncio
async def test_search_targets_by_name():
    """q=api → name에 'api' 포함된 Target 반환"""

@pytest.mark.asyncio
async def test_search_targets_by_url():
    """q=example.com → URL에 'example.com' 포함된 Target 반환"""

@pytest.mark.asyncio
async def test_search_targets_case_insensitive():
    """q=myapplication → 'MyApplication' 찾음"""

@pytest.mark.asyncio
async def test_search_targets_partial_match():
    """q=aaaa → 'https://aaaa.bbb' 찾음"""
```
```bash
uv run pytest tests/api/test_target_search.py -v
```

**Green Phase** - `backend/app/api/v1/endpoints/project.py`
```python
@router.get("/{project_id}/targets/search", response_model=List[TargetRead])
async def search_targets(
    project_id: int,
    q: str = Query(..., min_length=1, max_length=255),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Target 검색: name 또는 URL로 부분 일치 검색 (대소문자 무시)"""
    search_term = f"%{q}%"
    statement = select(Target).where(
        Target.project_id == project_id,
        or_(
            func.lower(Target.name).contains(q.lower()),
            func.lower(Target.url).contains(q.lower()),
        )
    )
```

**Blue Phase** - 리팩토링
- PostgreSQL `tsvector` 기반 Full-text 검색
- 검색 결과 하이라이팅 (match 위치 반환)

- [ ] Red: 4개 API 테스트 작성
- [ ] Green: 검색 엔드포인트 구현
- [ ] Blue: Full-text 검색

---

### 3.2-3.3 Frontend - 검색 바 컴포넌트

**Red Phase** - `frontend/src/components/features/target/TargetSearchBar.test.tsx`
```typescript
describe('TargetSearchBar', () => {
  it('should render search input');
  it('should debounce search input (300ms)');
  it('should display search results in dropdown');
  it('should call onSelect when result clicked');
  it('should show loading state while searching');
});
```
```bash
pnpm test -- src/components/features/target/TargetSearchBar.test.tsx
```

**Green Phase**

1. **Service** - `frontend/src/services/targetService.ts`
```typescript
export const searchTargets = async (
  projectId: number,
  params: { q: string; limit?: number }
): Promise<Target[]> => api.get(`/projects/${projectId}/targets/search`, params);
```

2. **Hook** - `frontend/src/hooks/useTargetSearch.ts`
```typescript
export function useTargetSearch(projectId: number, query: string) {
  const debouncedQuery = useDebounce(query, 300);
  return useQuery({
    queryKey: ['targets', 'search', projectId, debouncedQuery],
    queryFn: () => searchTargets(projectId, { q: debouncedQuery }),
    enabled: debouncedQuery.length >= 1,
  });
}
```

3. **Component** - `frontend/src/components/features/target/TargetSearchBar.tsx`
```typescript
export function TargetSearchBar({ projectId, onSelect }: Props) {
  // Command + Popover 패턴
  // 결과: Target name, URL, asset_count 표시
}
```

**Blue Phase** - 리팩토링
- 키보드 네비게이션 (화살표, Enter)
- 최근 검색 히스토리 (localStorage)
- 검색어 하이라이팅

- [ ] Red: 5개 컴포넌트 테스트 작성
- [ ] Green: Service, Hook, Component 구현
- [ ] Blue: 키보드 네비게이션, 히스토리

---

## Feature 4: Overview UI/UX 개선 [MEDIUM-LOW]

### 4.1 Backend - Target 통계 API

**Red Phase** - `backend/tests/api/test_target_stats.py`
```python
@pytest.mark.asyncio
async def test_get_target_stats_returns_summary():
    """GET /targets/{id}/stats → 통계 요약 반환"""

@pytest.mark.asyncio
async def test_get_target_stats_includes_asset_breakdown():
    """assets_by_type: {url: 100, form: 30, xhr: 20}"""

@pytest.mark.asyncio
async def test_get_target_stats_includes_task_summary():
    """tasks_by_status: {completed: 4, failed: 1}"""

@pytest.mark.asyncio
async def test_get_target_stats_includes_last_scan_info():
    """last_scan: {task_id, status, duration_seconds, assets_found}"""
```
```bash
uv run pytest tests/api/test_target_stats.py -v
```

**Green Phase** - `backend/app/api/v1/endpoints/task.py`
```python
class TargetStats(BaseModel):
    target_id: int
    total_assets: int
    assets_by_type: Dict[str, int]   # {url: 100, form: 30, xhr: 20}
    assets_by_source: Dict[str, int] # {html: 80, js: 50, network: 20}
    total_scans: int
    tasks_by_status: Dict[str, int]  # {completed: 4, failed: 1}
    last_scan: Optional[LastScanInfo]

@router.get("/targets/{target_id}/stats", response_model=TargetStats)
async def get_target_stats(target_id: int, session: AsyncSession = Depends(get_session)):
    """타겟의 종합 통계 조회"""
```

**Blue Phase** - 리팩토링
- Redis 캐싱 (TTL 1분)
- 트렌드 데이터 (시간대별 asset 수)

- [ ] Red: 4개 API 테스트 작성
- [ ] Green: 통계 엔드포인트 구현
- [ ] Blue: Redis 캐싱

---

### 4.2-4.5 Frontend - Overview 컴포넌트

**Red Phase** - `frontend/src/components/features/target/TargetOverviewStats.test.tsx`
```typescript
describe('TargetOverviewStats', () => {
  it('should render loading skeleton (4개 카드)');
  it('should display total assets count');
  it('should display assets breakdown by type');
  it('should display last scan information');
  it('should display success rate');
});
```
```bash
pnpm test -- src/components/features/target/TargetOverviewStats.test.tsx
```

**Green Phase**

1. **Types** - `frontend/src/types/target.ts`
```typescript
export interface TargetStats {
  total_assets: number;
  assets_by_type: Record<string, number>;
  total_scans: number;
  tasks_by_status: Record<string, number>;
  last_scan: LastScanInfo | null;
}
```

2. **Service/Hook** - `useTargetStats.ts`
```typescript
export function useTargetStats(targetId: number) {
  return useQuery({
    queryKey: ['targetStats', targetId],
    queryFn: () => getTargetStats(targetId),
    staleTime: 60000,
  });
}
```

3. **Component** - `frontend/src/components/features/target/TargetOverviewStats.tsx`
```typescript
// 4개 통계 카드: Total Assets, Total Scans, Last Scan Duration, Success Rate
// Assets Breakdown: Progress bar로 타입별 비율 표시
```

4. **Updated OverviewTabContent**
```typescript
export function OverviewTabContent({ projectId, targetId, targetName }: Props) {
  return (
    <div className="space-y-6">
      <TargetOverviewStats targetId={targetId} />
      <ScanControl projectId={projectId} targetId={targetId} targetName={targetName} />
      <LLMAnalysisPreview /> {/* Coming Soon placeholder */}
    </div>
  );
}
```

**Blue Phase** - 리팩토링
- Recharts로 시각화 차트
- 이전 스캔과 비교 (diff)
- PDF/PNG 내보내기

- [ ] Red: 5개 컴포넌트 테스트 작성
- [ ] Green: Types, Hook, Component 구현
- [ ] Blue: 차트, 내보내기

---

## 진행 상태

| Feature | Backend | Frontend | Status |
|---------|---------|----------|--------|
| 재귀 크롤링 | 5/5 | - | ✅ Complete |
| 스캔 히스토리 | 0/1 | 0/4 | Not Started |
| 도메인 검색 | 0/1 | 0/2 | Not Started |
| Overview UI | 0/1 | 0/4 | Not Started |

### 완료된 항목
- ✅ **1.1** Task 모델 확장 (depth, max_depth, parent_task_id)
- ✅ **1.2** URL 정규화 서비스 (normalize_url, get_url_hash, is_same_resource)
- ✅ **1.3** Scope 필터링 (ScopeFilter, RobotsTxtService, AssetSource 확장)
- ✅ **1.4** 재귀 크롤링 로직 BFS (CrawlManager, 상대 URL 정규화)
- ✅ **1.5** Worker 확장 (자식 Task 생성 로직)

---

## 테스트 명령 (uv 사용)

```bash
# Backend - 전체 테스트
cd backend
uv run pytest tests/ -v --cov=app --cov-report=html

# Backend - 특정 Feature 테스트
uv run pytest tests/models/test_task_recursive.py -v          # 1.1
uv run pytest tests/services/test_url_normalizer.py -v        # 1.2
uv run pytest tests/services/test_scope_filter.py -v          # 1.3
uv run pytest tests/services/test_crawl_manager.py -v         # 1.4
uv run pytest tests/workers/test_crawl_worker_recursive.py -v # 1.5
uv run pytest tests/api/test_task_list.py -v                  # 2.1
uv run pytest tests/api/test_target_search.py -v              # 3.1
uv run pytest tests/api/test_target_stats.py -v               # 4.1

# Frontend - 전체 테스트
cd frontend
pnpm test --coverage

# Frontend - 특정 컴포넌트 테스트
pnpm test -- src/components/features/target/tabs/HistoryTabContent.test.tsx
pnpm test -- src/components/features/target/TargetSearchBar.test.tsx
pnpm test -- src/components/features/target/TargetOverviewStats.test.tsx

# 마이그레이션
cd backend
uv run alembic revision --autogenerate -m "add_task_recursive_fields"
uv run alembic upgrade head
```
