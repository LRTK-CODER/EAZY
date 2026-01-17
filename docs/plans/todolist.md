# EAZY Active Scan 리팩토링 TDD Todolist

> **생성일**: 2026-01-17
> **기반 문서**: Active Scan 코드 검토 보고서

---

## TDD 개발 방법론

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD Cycle                                │
│                                                             │
│   🔴 RED          🟢 GREEN        🔵 BLUE (Refactor)       │
│   ─────────────   ─────────────   ─────────────────────    │
│   실패하는        테스트 통과     코드 정리 및              │
│   테스트 작성     최소 코드       리팩토링                  │
│                                                             │
│   [Test First] → [Make It Work] → [Make It Right]          │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 기반 구조 (상수, 타입, 에러)

### 1.1 상수 중앙화

#### 🔴 RED - 실패하는 테스트 작성
```
파일: tests/unit/core/test_constants.py
```
- [x] `test_max_body_size_constant_exists` - MAX_BODY_SIZE 상수 존재 확인
- [x] `test_page_timeout_constant_exists` - PAGE_TIMEOUT_MS 상수 존재 확인
- [x] `test_lock_ttl_constant_exists` - LOCK_TTL 상수 존재 확인
- [x] `test_cancellation_interval_constant_exists` - CANCELLATION_CHECK_INTERVAL 상수 존재 확인

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/core/constants.py
```
- [x] `CrawlerConstants` 클래스 생성 (모듈 수준 상수로 구현)
  - `MAX_BODY_SIZE = 10 * 1024`
  - `PAGE_TIMEOUT_MS = 30000`
  - `LOCK_TTL = 600`
  - `CANCELLATION_CHECK_INTERVAL = 5.0`
  - `LOCK_PREFIX = "eazy:lock:"`

#### 🔵 BLUE - 리팩토링
- [x] `crawler_service.py`에서 상수 import로 교체
- [x] `asset_service.py`에서 상수 import로 교체
- [x] `crawl_worker.py`에서 상수 import로 교체
- [x] 중복 상수 정의 제거

---

### 1.2 타입 정의 (TypedDict)

#### 🔴 RED - 실패하는 테스트 작성
```
파일: tests/core/test_http_types.py (tests/unit/types는 Python 내장 모듈과 충돌)
```
- [x] `test_http_request_data_type_has_required_keys` - method, headers 키 확인
- [x] `test_http_response_data_type_has_required_keys` - status, headers, body 키 확인
- [x] `test_http_data_type_structure` - request, response, parameters 구조 확인
- [ ] `test_parsed_content_type_structure` - content_type, body, truncated 구조 확인 (Phase 3로 이동)

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/types/http.py
```
- [x] `HttpRequestData(TypedDict)` 정의
- [x] `HttpResponseData(TypedDict)` 정의
- [x] `HttpData(TypedDict)` 정의
- [ ] `ParsedContent(TypedDict)` 정의 (Phase 3로 이동)

#### 🔵 BLUE - 리팩토링
- [x] `crawler_service.py` 반환 타입을 TypedDict로 교체
- [x] `asset_service.py` 파라미터 타입을 TypedDict로 교체
- [x] 기존 `Dict[str, Any]` 타입 힌트 제거

---

### 1.3 커스텀 예외 클래스

#### 🔴 RED - 실패하는 테스트 작성
```
파일: backend/tests/core/test_exceptions.py
```
- [x] `test_scan_error_is_base_exception` - ScanError가 Exception 상속 확인
- [x] `test_target_not_found_error_inheritance` - TargetNotFoundError가 ScanError 상속
- [x] `test_duplicate_scan_error_inheritance` - DuplicateScanError가 ScanError 상속
- [x] `test_unsafe_url_error_inheritance` - UnsafeUrlError가 ScanError 상속
- [x] `test_exception_message_formatting` - 예외 메시지 포맷 확인
- [x] `test_exception_has_status_code` - 예외별 HTTP 상태 코드 확인 (추가)

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/core/exceptions.py
```
- [x] `ScanError(Exception)` 기본 예외 클래스 (status_code=500)
- [x] `TargetNotFoundError(ScanError)` 대상 미존재 (status_code=404)
- [x] `DuplicateScanError(ScanError)` 중복 스캔 (status_code=409)
- [x] `UnsafeUrlError(ScanError)` 안전하지 않은 URL (status_code=400)

#### 🔵 BLUE - 리팩토링
- [x] `task.py` API 엔드포인트에서 예외별 HTTP 상태 코드 매핑
- [x] `crawl_worker.py`에서 커스텀 예외 사용 (TargetNotFoundError)
- [x] `task_service.py`에서 import 추가 (Task 관련 ValueError는 유지)

---

## Phase 2: 인터페이스 정의 (Protocol)

### 2.1 Crawler 인터페이스 ✅

#### 🔴 RED - 실패하는 테스트 작성
```
파일: tests/services/test_interfaces.py (기존 구조 따름)
```
- [x] `test_icrawler_protocol_has_crawl_method` - ICrawler.crawl() 존재 확인
- [x] `test_crawler_service_implements_icrawler` - CrawlerService가 ICrawler 준수
- [x] `test_mock_crawler_implements_icrawler` - Mock 크롤러 테스트

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/services/interfaces.py
```
- [x] `ICrawler(Protocol)` 정의
  ```python
  class ICrawler(Protocol):
      async def crawl(self, url: str) -> Tuple[List[str], Dict[str, HttpData]]: ...
  ```

#### 🔵 BLUE - 리팩토링
- [x] `CrawlWorker`에서 `ICrawler` 타입 힌트 사용
- [x] 테스트에서 Mock 크롤러 주입 패턴 적용 (기존 conftest.py 패턴 호환)

---

### 2.2 ResponseParser 인터페이스 ✅

#### 🔴 RED - 실패하는 테스트 작성
```
파일: tests/services/parsers/test_parser_protocol.py
```
- [x] `test_response_parser_has_supports_method` - supports() 메서드 존재
- [x] `test_response_parser_has_parse_method` - parse() 메서드 존재
- [x] `test_parser_registry_get_parser_returns_parser` - 레지스트리 동작 확인
- [x] `test_parser_registry_returns_default_for_unknown` - 알 수 없는 타입은 Default 반환
- [x] 추가 테스트 16개 (총 20개 테스트 통과)

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/services/parsers/base.py
```
- [x] `ResponseParser(Protocol)` 정의
- [x] `ResponseParserRegistry` 클래스 정의
  - `register(parser: ResponseParser)`
  - `get_parser(content_type: str) -> ResponseParser`
- [x] `ResponseData` dataclass 정의 (Playwright 추상화)
- [x] `DefaultResponseParser` 클래스 정의

#### 🔵 BLUE - 리팩토링
- [x] 의존성 주입 패턴 결정 (싱글톤 대신 - Phase 4에서 적용)
- [ ] 파서 자동 등록 메커니즘 구현 (Phase 3에서)

---

## Phase 3: 파서 전략 패턴 구현

### 3.0 ParsedContent 타입 정의 (Phase 1.2에서 이동) ✅

#### 🔴 RED - 실패하는 테스트 작성
```
파일: backend/tests/core/test_http_types.py (추가)
```
- [x] `test_parsed_content_type_has_required_keys` - content_type, body, truncated, original_size 키 확인
- [x] `test_parsed_content_content_type_is_str` - content_type이 str 타입인지 확인
- [x] `test_parsed_content_body_is_optional_str` - body가 Optional[str] 타입인지 확인
- [x] `test_parsed_content_truncated_is_bool` - truncated가 bool 타입인지 확인
- [x] `test_create_valid_parsed_content_with_body` - body가 있는 인스턴스 생성
- [x] `test_create_valid_parsed_content_with_none_body` - body가 None인 인스턴스 생성
- [x] `test_create_truncated_parsed_content` - truncated=True인 인스턴스 생성
- [x] `test_parsed_content_with_various_content_types` - 다양한 content_type 테스트

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/types/http.py (추가)
```
- [x] `ParsedContent(TypedDict)` 정의
  - `content_type: str`
  - `body: Optional[str]`
  - `truncated: bool`
  - `original_size: int` (추가: truncated 상황에서 원본 크기 제공)

#### 🔵 BLUE - 리팩토링
```
파일: backend/app/services/parsers/base.py (수정)
```
- [x] `ResponseParser.parse()` 반환 타입을 `Optional[ParsedContent]`로 변경
- [x] `DefaultResponseParser.parse()` 반환 타입 업데이트
- [x] mypy 타입 체크 통과 확인

---

### 3.1 JsonResponseParser ✅

#### 🔴 RED - 실패하는 테스트 작성
```
파일: backend/tests/services/parsers/test_json_parser.py
```
- [x] `test_json_parser_supports_application_json` - application/json 지원
- [x] `test_json_parser_parses_valid_json` - 유효한 JSON 파싱
- [x] `test_json_parser_handles_invalid_json` - 잘못된 JSON 처리
- [x] `test_json_parser_truncates_large_body` - 큰 본문 자르기
- [x] `test_json_parser_returns_parsed_content_type` - 반환 타입 확인
- [x] 추가 테스트 (charset, unicode, nested, empty body, original_size, integration) - 총 15개

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/services/parsers/json_parser.py
```
- [x] `JsonResponseParser` 클래스 구현
  - `supports(content_type: str) -> bool`
  - `async parse(response: ResponseData) -> ParsedContent`

#### 🔵 BLUE - 리팩토링
- [x] __init__.py에 JsonResponseParser export 추가
- [x] Ruff lint/format 통과
- [x] Mypy 타입 체크 통과

---

### 3.2 HtmlResponseParser ✅

#### 🔴 RED - 실패하는 테스트 작성
```
파일: backend/tests/services/parsers/test_html_parser.py
```
- [x] `test_html_parser_supports_text_html` - text/html 지원
- [x] `test_html_parser_supports_text_css` - text/css 지원
- [x] `test_html_parser_supports_text_javascript` - text/javascript 지원
- [x] `test_html_parser_parses_text_content` - 텍스트 콘텐츠 파싱 (HTML, CSS, JS 각각)
- [x] `test_html_parser_truncates_large_body` - 큰 본문 자르기
- [x] 추가 테스트 15개 (charset, application/javascript, empty body, unicode, decode error, registry 통합 등)

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/services/parsers/html_parser.py
```
- [x] `HtmlResponseParser` 클래스 구현 (HTML, CSS, JS 통합)
  - SUPPORTED_TYPES: text/html, text/css, text/javascript, application/javascript, application/x-javascript
  - supports(): charset 파싱 후 base_type 확인
  - parse(): UTF-8 디코딩, truncation 처리, ParsedContent 반환

#### 🔵 BLUE - 리팩토링
- [x] Content-Type 목록 상수화 (frozenset)
- [x] __init__.py에 HtmlResponseParser export 추가
- [x] Ruff lint/format 통과
- [x] Mypy 타입 체크 통과

---

### 3.3 ImageResponseParser ✅

#### 🔴 RED - 실패하는 테스트 작성
```
파일: backend/tests/services/parsers/test_image_parser.py
```
- [x] `test_image_parser_supports_image_types` - image/* 지원 (8개 타입: png, jpeg, gif, webp, svg+xml, x-icon, bmp, tiff)
- [x] `test_image_parser_encodes_to_base64` - Base64 인코딩 확인
- [x] `test_image_parser_truncates_large_image` - 큰 이미지 자르기 (바이너리 먼저)
- [x] `test_image_parser_handles_binary_data` - 바이너리 데이터 처리
- [x] 추가 테스트 19개 (supports 11개, parse 9개, integration 4개) - 총 23개

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/services/parsers/image_parser.py
```
- [x] `ImageResponseParser` 클래스 구현
  - SUPPORTED_TYPES: frozenset (8개 이미지 타입)
  - supports(): base_type 확인 (charset 파라미터 제거)
  - parse(): 바이너리 → Base64 인코딩, truncation 처리, ParsedContent 반환

#### 🔵 BLUE - 리팩토링
- [x] 지원 이미지 타입 목록 상수화 (frozenset)
- [x] __init__.py에 ImageResponseParser export 추가
- [x] Ruff lint/format 통과
- [x] Mypy 타입 체크 통과

---

### 3.4 DefaultResponseParser ✅

#### 🔴 RED - 실패하는 테스트 작성
```
파일: backend/tests/services/parsers/test_default_parser.py
```
- [x] `test_supports_any_content_type` - 모든 타입 지원 (fallback)
- [x] `test_supports_empty_string` - 빈 문자열도 지원
- [x] `test_supports_unknown_type` - 알 수 없는 타입도 지원
- [x] `test_returns_parsed_content_type` - ParsedContent 구조 반환
- [x] `test_returns_none_body` - body를 None으로 반환
- [x] `test_preserves_content_type` - content_type 보존
- [x] `test_returns_original_size` - original_size 정확히 계산
- [x] `test_truncated_is_false` - truncated 항상 False
- [x] `test_handles_empty_body` - 빈 body 처리
- [x] `test_logs_unknown_content_type` - INFO 로깅 확인
- [x] `test_registry_returns_default_as_fallback` - Registry 통합 테스트
- [x] `test_registry_uses_default_when_no_match` - Registry fallback 테스트
- [x] `test_registry_default_parser_returns_parsed_content` - Registry ParsedContent 반환 테스트

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/services/parsers/default_parser.py
```
- [x] `DefaultResponseParser` 클래스 구현
  - `supports()`: 항상 True 반환
  - `parse()`: ParsedContent 반환 (body=None, content_type/original_size 보존)

#### 🔵 BLUE - 리팩토링
- [x] INFO 레벨 로깅 추가 (알 수 없는 타입 처리 시)
- [x] base.py에서 DefaultResponseParser 분리
- [x] __init__.py export 업데이트
- [x] test_parser_protocol.py 중복 테스트 제거
- [x] Ruff lint/format 통과
- [x] Mypy 타입 체크 통과

---

## Phase 4: 통합 및 CrawlerService 리팩토링

### 4.1 CrawlerService 리팩토링

#### 🔴 RED - 실패하는 테스트 작성
```
파일: tests/unit/services/test_crawler_service_refactored.py
```
- [ ] `test_crawler_uses_parser_registry` - 파서 레지스트리 사용 확인
- [ ] `test_crawler_delegates_to_json_parser` - JSON 파서 위임 확인
- [ ] `test_crawler_delegates_to_html_parser` - HTML 파서 위임 확인
- [ ] `test_crawler_delegates_to_image_parser` - 이미지 파서 위임 확인
- [ ] `test_crawler_uses_default_for_unknown` - 알 수 없는 타입 처리

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/services/crawler_service.py (수정)
```
- [ ] `ResponseParserRegistry` 주입
- [ ] `handle_response()` 내부 로직을 파서 호출로 교체
- [ ] 기존 if-elif 분기 제거

#### 🔵 BLUE - 리팩토링
- [ ] 코드 라인 수 감소 확인 (179줄 → 목표 100줄 이하)
- [ ] 메서드 분리 (필요시)
- [ ] 문서화 (docstring 업데이트)

---

### 4.2 API 에러 핸들링 개선

#### 🔴 RED - 실패하는 테스트 작성
```
파일: tests/unit/api/test_task_error_handling.py
```
- [ ] `test_trigger_scan_returns_404_for_missing_target` - 타겟 없음 → 404
- [ ] `test_trigger_scan_returns_409_for_duplicate_scan` - 중복 스캔 → 409
- [ ] `test_trigger_scan_returns_400_for_unsafe_url` - 위험한 URL → 400
- [ ] `test_trigger_scan_returns_500_for_unexpected_error` - 예상치 못한 에러 → 500

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/api/v1/endpoints/task.py (수정)
```
- [ ] `trigger_scan()` 엔드포인트에서 커스텀 예외 처리
- [ ] 예외별 HTTP 상태 코드 매핑

#### 🔵 BLUE - 리팩토링
- [ ] 에러 응답 스키마 통일
- [ ] 에러 핸들러 미들웨어 추출 (선택사항)

---

## Phase 5: 설정 중앙화 (선택사항)

### 5.1 pydantic-settings 적용

#### 🔴 RED - 실패하는 테스트 작성
```
파일: tests/unit/core/test_crawler_settings.py
```
- [ ] `test_crawler_settings_loads_defaults` - 기본값 로드
- [ ] `test_crawler_settings_reads_env_vars` - 환경변수 읽기
- [ ] `test_crawler_settings_validates_values` - 값 검증

#### 🟢 GREEN - 테스트 통과 코드 작성
```
파일: backend/app/core/config.py (추가)
```
- [ ] `CrawlerSettings(BaseSettings)` 클래스 정의

#### 🔵 BLUE - 리팩토링
- [ ] 기존 constants.py와 통합 또는 분리 결정
- [ ] .env.example 업데이트

---

## 검증 체크리스트

### 테스트 실행
```bash
# 전체 테스트
pytest tests/ -v

# 단위 테스트만
pytest tests/unit/ -v

# 커버리지 포함
pytest tests/ --cov=app --cov-report=html
```

### 코드 품질 검사
```bash
# 타입 체크
mypy backend/app/

# 린팅
ruff check backend/app/

# 포맷팅
ruff format backend/app/
```

### 통합 테스트
- [ ] Active Scan 트리거 → Task 생성 확인
- [ ] 크롤링 완료 → Asset 저장 확인
- [ ] 에러 발생 시 적절한 HTTP 상태 코드 반환 확인

---

## 파일 구조 (최종)

```
backend/app/
├── core/
│   ├── constants.py          # NEW: 상수 중앙화
│   ├── exceptions.py         # NEW: 커스텀 예외
│   └── config.py             # NEW: 설정 (선택)
├── types/
│   └── http.py               # NEW: TypedDict 정의
├── services/
│   ├── interfaces.py         # NEW: Protocol 정의
│   ├── crawler_service.py    # MODIFY: 파서 사용
│   ├── asset_service.py      # MODIFY: 상수/타입 사용
│   └── parsers/              # NEW: 파서 디렉토리
│       ├── __init__.py
│       ├── base.py           # ResponseParser, Registry
│       ├── json_parser.py
│       ├── html_parser.py
│       ├── image_parser.py
│       └── default_parser.py
├── workers/
│   └── crawl_worker.py       # MODIFY: 상수/예외 사용
└── api/v1/endpoints/
    └── task.py               # MODIFY: 에러 핸들링

tests/unit/
├── core/
│   ├── test_constants.py     # NEW
│   └── test_exceptions.py    # NEW
├── types/
│   └── test_http_types.py    # NEW
├── services/
│   ├── test_interfaces.py    # NEW
│   └── parsers/              # NEW
│       ├── test_parser_protocol.py
│       ├── test_json_parser.py
│       ├── test_html_parser.py
│       ├── test_image_parser.py
│       └── test_default_parser.py
└── api/
    └── test_task_error_handling.py  # NEW
```

---

## 예상 소요 시간

| Phase | 항목 | Red | Green | Blue | 합계 |
|-------|------|-----|-------|------|------|
| 1 | 상수 중앙화 | 30분 | 30분 | 1시간 | 2시간 |
| 1 | 타입 정의 | 30분 | 1시간 | 1시간 | 2.5시간 |
| 1 | 커스텀 예외 | 30분 | 30분 | 1시간 | 2시간 |
| 2 | 인터페이스 정의 | 1시간 | 1시간 | 30분 | 2.5시간 |
| 3 | 파서 구현 (4개) | 2시간 | 3시간 | 1시간 | 6시간 |
| 4 | CrawlerService 리팩토링 | 1시간 | 2시간 | 1시간 | 4시간 |
| 4 | API 에러 핸들링 | 30분 | 1시간 | 30분 | 2시간 |
| **합계** | | **6시간** | **9시간** | **6시간** | **21시간** |

---

## 참조 파일

### 수정 대상
- `/backend/app/services/crawler_service.py` - 파싱 로직 (리팩토링 대상)
- `/backend/app/services/asset_service.py` - 상수/타입 적용
- `/backend/app/workers/crawl_worker.py` - 상수/예외 적용
- `/backend/app/api/v1/endpoints/task.py` - 에러 핸들링

### 신규 생성
- `/backend/app/core/constants.py`
- `/backend/app/core/exceptions.py`
- `/backend/app/types/http.py`
- `/backend/app/services/interfaces.py`
- `/backend/app/services/parsers/*.py`

---

## 진행 상황 추적

### Phase 1 진행률: 100% (3/3 완료) ✅
- [x] 1.1 상수 중앙화
- [x] 1.2 타입 정의 (ParsedContent는 Phase 3로 이동)
- [x] 1.3 커스텀 예외

### Phase 2 진행률: 100% (2/2 완료) ✅
- [x] 2.1 Crawler 인터페이스
- [x] 2.2 ResponseParser 인터페이스

### Phase 3 진행률: 100% (5/5 완료) ✅
- [x] 3.0 ParsedContent 타입 정의 (Phase 1.2에서 이동) ✅
- [x] 3.1 JsonResponseParser ✅
- [x] 3.2 HtmlResponseParser ✅
- [x] 3.3 ImageResponseParser ✅
- [x] 3.4 DefaultResponseParser ✅

### Phase 4 진행률: 0%
- [ ] 4.1 CrawlerService 리팩토링
- [ ] 4.2 API 에러 핸들링

### Phase 5 진행률: 0%
- [ ] 5.1 pydantic-settings 적용
