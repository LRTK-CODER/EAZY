# Phase 1: 기반 구조 (Foundation)

**Status**: ✅ Completed
**Started**: 2026-01-23
**Completed**: 2026-01-23
**Last Updated**: 2026-01-23
**Coverage Achieved**: 99% (목표: 100%)

---

**✅ PHASE COMPLETED**: 모든 항목이 완료되었습니다.

---

## 📋 Overview

### Feature Description
Active Scan Discovery 시스템의 핵심 기반 구조를 구현합니다. 모든 Discovery 모듈이 공유하는
Enum, 데이터 클래스, Protocol, Registry를 정의합니다.

### Success Criteria
- [x] ScanProfile Enum이 QUICK, STANDARD, FULL 값을 가짐
- [x] DiscoveredAsset이 중복 제거 가능 (hashable)
- [x] BaseDiscoveryModule Protocol이 모듈 계약 정의
- [x] DiscoveryModuleRegistry가 모듈 등록/조회 지원
- [x] DiscoveryContext가 불변 컨텍스트 제공

### Dependencies
- 없음 (기반 구조)

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| `str, Enum` for ScanProfile | 타입 안전성, 문자열 비교 지원 | 확장 시 코드 수정 필요 |
| dataclass with frozen | 불변성 보장, 해시 가능 | 성능 오버헤드 미미 |
| ABC for BaseDiscoveryModule | 명시적 인터페이스, 타입 체크 | 구현 강제 필요 |
| Dictionary-based Registry | 테스트 용이, 인스턴스별 격리 | 전역 레지스트리 필요시 별도 관리 |

---

## 🚀 Implementation Sections

### 1.1 ScanProfile Enum

**Goal**: 스캔 프로필 정의 (QUICK, STANDARD, FULL)

#### 🔴 RED: Write Failing Tests First

- [x] **Test 1.1.1**: `test_scan_profile_values()` - QUICK, STANDARD, FULL 값 검증
  - File: `backend/tests/services/discovery/test_scan_profile.py`
  - Test Cases:
    - `ScanProfile.QUICK` exists and has value
    - `ScanProfile.STANDARD` exists and has value
    - `ScanProfile.FULL` exists and has value
    - All three values are distinct

- [x] **Test 1.1.2**: `test_scan_profile_default()` - 기본값 STANDARD 검증
  - File: `backend/tests/services/discovery/test_scan_profile.py`
  - Test Cases:
    - Default profile is STANDARD
    - Can be used as function default parameter

#### 🟢 GREEN: Implement to Make Tests Pass

- [x] **Task 1.1.3**: `ScanProfile` enum 구현
  - File: `backend/app/services/discovery/models.py`
  - Implementation:
    ```python
    class ScanProfile(str, Enum):
        QUICK = "quick"
        STANDARD = "standard"
        FULL = "full"

    DEFAULT_SCAN_PROFILE = ScanProfile.STANDARD
    ```

#### 🔵 REFACTOR: Clean Up Code

- [x] **Task 1.1.4**: 문서화, 타입 힌트 정리
  - Checklist:
    - [x] Docstring 추가
    - [x] 각 프로필의 용도 설명

---

### 1.2 DiscoveredAsset 데이터 클래스

**Goal**: 발견된 자산 정보를 담는 불변 데이터 클래스

#### 🔴 RED: Write Failing Tests First

- [x] **Test 1.2.1**: `test_discovered_asset_creation()` - 필수 필드 검증
  - File: `backend/tests/services/discovery/test_discovered_asset.py`
  - Test Cases:
    - Can create with required fields (url, asset_type, source)
    - Optional fields have defaults (metadata, discovered_at)

- [x] **Test 1.2.2**: `test_discovered_asset_hash()` - 중복 제거용 해시
  - File: `backend/tests/services/discovery/test_discovered_asset.py`
  - Test Cases:
    - Same URL + type produces same hash
    - Different URL produces different hash
    - Can be used in set()

- [x] **Test 1.2.3**: `test_discovered_asset_equality()` - 동등성 비교
  - File: `backend/tests/services/discovery/test_discovered_asset.py`
  - Test Cases:
    - Same URL + type are equal
    - Different URL are not equal
    - Comparison with non-Asset returns False

#### 🟢 GREEN: Implement to Make Tests Pass

- [x] **Task 1.2.4**: `DiscoveredAsset` dataclass 구현
  - File: `backend/app/services/discovery/models.py`
  - Implementation:
    ```python
    @dataclass(frozen=True)
    class DiscoveredAsset:
        url: str
        asset_type: str
        source: str
        metadata: Dict[str, Any] = field(default_factory=dict, compare=False, hash=False)
        discovered_at: datetime = field(default_factory=utc_now, compare=False, hash=False)

        def __hash__(self) -> int:
            return hash((self.url, self.asset_type))

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, DiscoveredAsset):
                return False
            return self.url == other.url and self.asset_type == other.asset_type
    ```

#### 🔵 REFACTOR: Clean Up Code

- [x] **Task 1.2.5**: `__hash__`, `__eq__` 최적화
  - Checklist:
    - [x] 문서화

---

### 1.3 BaseDiscoveryModule Protocol

**Goal**: Discovery 모듈의 공통 인터페이스 정의

#### 🔴 RED: Write Failing Tests First

- [x] **Test 1.3.1**: `test_module_must_have_name()` - name 속성 필수
  - File: `backend/tests/services/discovery/test_base_module.py`
  - Test Cases:
    - Module without name raises error
    - Module with name passes validation

- [x] **Test 1.3.2**: `test_module_must_have_profiles()` - profiles 속성 필수
  - File: `backend/tests/services/discovery/test_base_module.py`
  - Test Cases:
    - Module must declare supported profiles
    - Profiles must be set of ScanProfile

- [x] **Test 1.3.3**: `test_module_must_have_discover()` - discover 메서드 필수
  - File: `backend/tests/services/discovery/test_base_module.py`
  - Test Cases:
    - Module without discover() raises TypeError
    - discover() is abstract method

- [x] **Test 1.3.4**: `test_module_profile_matching()` - 프로필별 활성화 검증
  - File: `backend/tests/services/discovery/test_base_module.py`
  - Test Cases:
    - Module with QUICK profile activates for QUICK scan
    - Module without FULL profile skipped for FULL scan
    - `is_active_for(profile)` method works correctly

#### 🟢 GREEN: Implement to Make Tests Pass

- [x] **Task 1.3.5**: `BaseDiscoveryModule` ABC 구현
  - File: `backend/app/services/discovery/base.py`
  - Implementation:
    ```python
    class BaseDiscoveryModule(ABC):
        @property
        @abstractmethod
        def name(self) -> str: ...

        @property
        @abstractmethod
        def profiles(self) -> Set[ScanProfile]: ...

        @abstractmethod
        async def discover(self, context: DiscoveryContext) -> AsyncIterator[DiscoveredAsset]: ...

        def is_active_for(self, profile: ScanProfile) -> bool:
            return profile in self.profiles
    ```

#### 🔵 REFACTOR: Clean Up Code

- [x] **Task 1.3.6**: 문서화 완료

---

### 1.4 DiscoveryModuleRegistry

**Goal**: Discovery 모듈 등록 및 조회를 위한 레지스트리

#### 🔴 RED: Write Failing Tests First

- [x] **Test 1.4.1**: `test_registry_register_module()` - 모듈 등록
  - File: `backend/tests/services/discovery/test_registry.py`
  - Test Cases:
    - Can register a module
    - Registered module can be retrieved
    - Registration returns success indicator

- [x] **Test 1.4.2**: `test_registry_get_by_profile()` - 프로필별 모듈 조회
  - File: `backend/tests/services/discovery/test_registry.py`
  - Test Cases:
    - Get modules for QUICK profile
    - Get modules for STANDARD profile
    - Get modules for FULL profile
    - Returns empty list for no matching modules

- [x] **Test 1.4.3**: `test_registry_get_all()` - 전체 모듈 조회
  - File: `backend/tests/services/discovery/test_registry.py`
  - Test Cases:
    - Returns all registered modules
    - Order is consistent
    - Returns copy (not reference)

- [x] **Test 1.4.4**: `test_registry_duplicate_prevention()` - 중복 등록 방지
  - File: `backend/tests/services/discovery/test_registry.py`
  - Test Cases:
    - Same module registered twice raises error
    - Different modules with same name raises error

#### 🟢 GREEN: Implement to Make Tests Pass

- [x] **Task 1.4.5**: `DiscoveryModuleRegistry` 구현
  - File: `backend/app/services/discovery/registry.py`
  - Implementation:
    ```python
    class DuplicateModuleError(Exception):
        pass

    class DiscoveryModuleRegistry:
        def __init__(self) -> None:
            self._modules: Dict[str, BaseDiscoveryModule] = {}

        def register(self, module: BaseDiscoveryModule) -> None: ...
        def get_by_profile(self, profile: ScanProfile) -> List[BaseDiscoveryModule]: ...
        def get_all(self) -> List[BaseDiscoveryModule]: ...
        def get_by_name(self, name: str) -> Optional[BaseDiscoveryModule]: ...
        def clear(self) -> None: ...
    ```

#### 🔵 REFACTOR: Clean Up Code

- [x] **Task 1.4.6**: 테스트용 clear 메서드 추가

---

### 1.5 DiscoveryContext

**Goal**: Discovery 실행에 필요한 컨텍스트 정보를 담는 불변 객체

#### 🔴 RED: Write Failing Tests First

- [x] **Test 1.5.1**: `test_context_creation()` - 필수 필드 검증
  - File: `backend/tests/services/discovery/test_context.py`
  - Test Cases:
    - Can create with target_url, profile, http_client
    - Optional fields have defaults (timeout, max_depth)

- [x] **Test 1.5.2**: `test_context_immutability()` - 불변성 검증
  - File: `backend/tests/services/discovery/test_context.py`
  - Test Cases:
    - Cannot modify fields after creation
    - Attempting modification raises FrozenInstanceError

- [x] **Test 1.5.3**: `test_context_helpers()` - 헬퍼 메서드
  - File: `backend/tests/services/discovery/test_context.py`
  - Test Cases:
    - is_quick_profile() works correctly
    - is_full_profile() works correctly

#### 🟢 GREEN: Implement to Make Tests Pass

- [x] **Task 1.5.4**: `DiscoveryContext` dataclass 구현
  - File: `backend/app/services/discovery/models.py`
  - Implementation:
    ```python
    @dataclass(frozen=True)
    class DiscoveryContext:
        target_url: str
        profile: ScanProfile
        http_client: Any
        timeout: float = 30.0
        max_depth: int = 3
        base_url: str = ""
        crawl_data: Dict[str, Any] = field(default_factory=dict)

        def __post_init__(self) -> None:
            if not self.base_url:
                object.__setattr__(self, "base_url", self.target_url)

        def is_quick_profile(self) -> bool:
            return self.profile == ScanProfile.QUICK

        def is_full_profile(self) -> bool:
            return self.profile == ScanProfile.FULL
    ```

#### 🔵 REFACTOR: Clean Up Code

- [x] **Task 1.5.5**: 문서화 완료

---

## ✋ Quality Gate

**✅ ALL CHECKS PASSED**

### TDD Compliance (CRITICAL)
- [x] **Red Phase**: Tests were written FIRST and initially failed
- [x] **Green Phase**: Production code written to make tests pass
- [x] **Refactor Phase**: Code improved while tests still pass
- [x] **Coverage Check**: Line coverage = 99%

### Build & Tests
- [x] **All Tests Pass**: `uv run pytest tests/services/discovery/` - 54 tests, 100% passing
- [x] **Coverage**: 99% (1줄 미스: 추상 메서드 yield)
- [x] **No Flaky Tests**: Run tests 3+ times consistently

### Code Quality
- [x] **Linting**: `uv run ruff check app/services/discovery/` - All checks passed
- [x] **Formatting**: `uv run black --check app/services/discovery/` - OK
- [x] **Import Sort**: `uv run isort --check app/services/discovery/` - OK
- [x] **Type Check**: `uv run mypy app/services/discovery/` - Success

### Manual Verification
- [x] ScanProfile enum values are correct (QUICK, STANDARD, FULL)
- [x] DiscoveredAsset can be used in set()
- [x] BaseDiscoveryModule subclass requires all abstract methods
- [x] Registry works correctly with clear() for test isolation
- [x] Context is truly immutable

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 1.1 ScanProfile | 4 | 4 | 100% |
| 1.2 DiscoveredAsset | 5 | 5 | 100% |
| 1.3 BaseDiscoveryModule | 6 | 6 | 100% |
| 1.4 Registry | 6 | 6 | 100% |
| 1.5 Context | 5 | 5 | 100% |
| **Total** | **26** | **26** | **100%** |

---

## 📁 생성된 파일

```
backend/
├── app/services/discovery/
│   ├── __init__.py          # Public exports
│   ├── models.py            # ScanProfile, DiscoveredAsset, DiscoveryContext
│   ├── base.py              # BaseDiscoveryModule ABC
│   └── registry.py          # DiscoveryModuleRegistry, DuplicateModuleError
│
└── tests/services/discovery/
    ├── __init__.py
    ├── test_scan_profile.py       # 8 tests
    ├── test_discovered_asset.py   # 12 tests
    ├── test_context.py            # 9 tests
    ├── test_base_module.py        # 12 tests
    └── test_registry.py           # 13 tests
```

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| - | **Phase 1: Foundation** ✅ | [Phase 2: Basic Modules](./phase2-basic-modules.md) |

[← Back to Index](./README.md)
