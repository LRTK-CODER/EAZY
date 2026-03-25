# 코딩 규칙

## 언어 및 런타임

- Python 3.11+
- `async def`가 기본, 동기 함수는 예외적으로만
- 패키지 관리: `uv add` (pip 절대 사용 금지)

## 타입 시스템

- 모든 함수에 타입 힌트 필수 (인자 + 반환값)
- `Any` 사용 금지 — 구체적 타입 또는 제네릭 사용
- Optional은 `X | None` 형식 (`Optional[X]` 아님)
- 컬렉션은 내장 타입 사용 (`list[str]`, `dict[str, int]` — `List`, `Dict` 아님)
- `mypy --strict` 통과 목표

```python
# ✅ 좋은 예
async def scan(target: str, timeout: int = 120) -> ScanResult:
    ...

def classify(vuln_type: str) -> Literal["H", "M", "L"]:
    ...

def find_endpoint(url: str) -> Endpoint | None:
    ...

# ❌ 나쁜 예
def scan(target, timeout=120):        # 타입 힌트 없음
    ...

def find_endpoint(url: str) -> Any:   # Any 사용
    ...
```

## 데이터 모델

- 모든 구조화된 데이터는 Pydantic `BaseModel`
- dict로 데이터 전달 금지
- Stage 간 전달은 ARCHITECTURE.md 3절의 래퍼 모델 사용
- 필드에 `Field(description=...)` 권장
- Enum은 `StrEnum` 사용

```python
# ✅ 좋은 예
from pydantic import BaseModel, Field
from enum import StrEnum

class Impact(StrEnum):
    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"

class Finding(BaseModel):
    cwe: str = Field(..., description="CWE 코드")
    endpoint: str = Field(..., description="대상 엔드포인트")
    severity: Impact = Field(..., description="영향도")
    confidence: float = Field(..., ge=0.0, le=1.0)

# ❌ 나쁜 예
finding = {
    "cwe": "CWE-89",
    "endpoint": "/api/login",
    "severity": "H",
}
```

## 함수 설계

- 한 함수 = 한 책임
- "판단 + 실행 + 검증"을 하나의 함수에 넣지 않는다
- 함수 길이 30줄 이내 권장, 50줄 초과 시 분리
- 순환 복잡도 10 미만 (`radon cc --min C`)
- 중첩 3단계 이내 (if 안에 for 안에 if 금지)

```python
# ✅ 좋은 예 — 각각 한 책임
def generate_payload(template: str, params: dict[str, str]) -> str:
    """페이로드를 생성한다. 전송하지 않는다."""
    ...

async def send_payload(endpoint: str, payload: str) -> httpx.Response:
    """페이로드를 전송한다. 결과를 판정하지 않는다."""
    ...

def verify_response(response: httpx.Response, rules: VerifyRules) -> Verdict:
    """응답을 검증한다. LLM을 호출하지 않는다."""
    ...

# ❌ 나쁜 예 — 판단 + 실행 + 검증이 하나에
async def attack(target: str) -> bool:
    payload = generate(target)
    response = await send(payload)
    if "admin" in response.text:
        return True
    return False
```

## 주석 및 Docstring (Google 스타일)

- 모든 public 함수/클래스/모듈에 docstring 필수
- private 함수(`_`접두사)는 선택
- 한 줄로 충분하면 한 줄로
- inline 주석은 "왜"를 설명할 때만 (코드가 "무엇"을 이미 말하고 있으므로)

### 함수

```python
def classify_impact(endpoint: Endpoint, vuln_type: str) -> Impact:
    """엔드포인트와 취약점 유형으로 영향도를 분류한다.

    LLM을 호출하지 않는다. 규칙 기반 분류만 수행한다.

    Args:
        endpoint: 대상 엔드포인트 정보.
        vuln_type: CWE 코드 (예: "CWE-89").

    Returns:
        H/M/L 영향도.

    Raises:
        ValueError: vuln_type이 알려지지 않은 CWE인 경우.

    Examples:
        >>> classify_impact(login_endpoint, "CWE-89")
        Impact.HIGH
    """
```

### 한 줄 docstring

```python
def mask_sensitive(value: str) -> str:
    """민감 데이터를 마스킹한다."""
```

### 클래스

```python
class SessionMiddleware:
    """HTTP 세션을 자동 관리하는 결정론적 미들웨어.

    쿠키, JWT, CSRF 토큰을 LLM 외부에서 투명하게 처리한다.
    Burp Suite의 세션 핸들링 룰 패턴을 따른다.

    Attributes:
        cookie_jar: 활성 쿠키 저장소.
        jwt_expiry: JWT 만료 시각 (UTC).
    """
```

### 모듈 (파일 최상단)

```python
"""Stage 1.2 병렬 스캐너 실행기.

등록된 스캐너 플러그인을 asyncio.gather()로 병렬 실행하고,
결과를 통합 스키마로 파싱한다. LLM을 사용하지 않는다.
"""
```

### inline 주석

```python
# ✅ "왜"를 설명
timeout = 120  # WhatWeb이 대규모 사이트에서 60초 초과하는 사례 있음

# ✅ 비자명한 로직 설명
# nmap만 NET_RAW 필요, 나머지는 모든 권한 제거
cap_add = ["NET_RAW"] if tool_name == "nmap" else []

# ❌ 코드를 반복하는 주석
count = count + 1  # count를 1 증가
```

## HTTP 클라이언트

- `httpx` 사용 필수 (`requests` 금지)
- 항상 async (`httpx.AsyncClient`)
- 세션 미들웨어를 통해 요청 (직접 요청 금지)
- 타임아웃 명시

```python
# ✅ 좋은 예
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(url, content=payload)

# ❌ 나쁜 예
import requests
response = requests.post(url, data=payload)
```

## 에러 처리

- bare `except:` 금지 — 구체적 예외 타입 사용
- 커스텀 예외는 도메인별 기본 클래스 상속
- 예외 메시지에 컨텍스트 포함
- 에러 삼키기(silently swallow) 금지 — 최소한 로깅

```python
# ✅ 좋은 예
class ScannerError(Exception):
    """스캐너 실행 중 발생하는 모든 에러의 기본 클래스."""

class ScannerTimeoutError(ScannerError):
    """스캐너 실행 시간이 제한을 초과한 경우."""

try:
    result = await scanner.scan(target)
except ScannerTimeoutError as e:
    logger.warning("스캐너 %s 타임아웃: %s", scanner.name, e)
    return ScanResult(status="timeout", data=None)

# ❌ 나쁜 예
try:
    result = await scanner.scan(target)
except:                    # bare except
    pass                   # 에러 삼키기
```

## 비동기 패턴

- `asyncio.gather()`로 독립 작업 병렬 실행
- `return_exceptions=True`로 하나의 실패가 전체를 죽이지 않게
- 세마포어로 동시 실행 수 제한 (외부 도구, HTTP 요청)

```python
# ✅ 좋은 예 — 병렬 실행 + 격리된 에러 핸들링
results = await asyncio.gather(
    scanner_a.scan(target),
    scanner_b.scan(target),
    scanner_c.scan(target),
    return_exceptions=True,
)

for scanner_name, result in zip(scanner_names, results):
    if isinstance(result, Exception):
        logger.warning("스캐너 %s 실패: %s", scanner_name, result)
        continue
    merged.update(result)
```

## 네이밍

| 대상 | 스타일 | 예시 |
|------|--------|------|
| 변수, 함수, 메서드 | snake_case | `scan_result`, `parse_output` |
| 클래스 | PascalCase | `ScannerPlugin`, `AttackChain` |
| 상수 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `HIGH_IMPACT_TYPES` |
| private | `_` 접두사 | `_parse_raw`, `_internal_state` |
| 파일/모듈 | snake_case | `tool_runner.py`, `payload_factory.py` |
| 테스트 함수 | `test_<행동>_<예상결과>` | `test_scan_timeout_returns_empty` |
| Pydantic 모델 | PascalCase 명사 | `Finding`, `ReconOutput` |
| Enum | PascalCase 클래스 + UPPER 값 | `Impact.HIGH` |

```python
# ✅ 좋은 예 — 이름이 의도를 표현
async def extract_endpoints_from_js(bundle_path: str) -> list[Endpoint]:
    ...

waf_bypass_patterns: dict[str, list[str]] = {}

# ❌ 나쁜 예 — 의미 없는 이름
async def process(data):
    ...

d: dict = {}
```

## import 순서

```python
# 1. 표준 라이브러리
import asyncio
import json
from pathlib import Path

# 2. 서드파티
import httpx
from pydantic import BaseModel, Field
from langchain.tools import tool

# 3. 로컬
from src.agents.core.models import Finding
from src.agents.middleware.session import SessionMiddleware
```

- `ruff`가 자동 정렬 (isort 호환)
- 와일드카드 import 금지 (`from module import *`)
- 순환 import 발생 시 구조 문제 → 모듈 분리로 해결

## 문자열

- f-string 사용 (`.format()`, `%` 연산자 아님)
- 여러 줄은 `textwrap.dedent` 또는 괄호로 묶기
- 프롬프트 템플릿은 별도 파일 또는 상수로 분리

```python
# ✅ 좋은 예
msg = f"스캐너 {scanner.name} 완료: {len(results)}건 발견"

PROMPT_TEMPLATE = (
    "다음 스캐너 결과를 분석하세요:\n"
    "{scanner_results}\n"
    "기술 스택과 WAF 존재 여부를 판단하세요."
)

# ❌ 나쁜 예
msg = "스캐너 {} 완료: {}건 발견".format(scanner.name, len(results))
```

## 로깅

- `print()` 금지 — `logging` 모듈 사용
- 모듈별 로거: `logger = logging.getLogger(__name__)`
- 레벨 가이드: DEBUG(상세 추적), INFO(정상 흐름), WARNING(복구 가능), ERROR(복구 불가)
- 민감 데이터(크레덴셜, 키, 취약점 증거)를 로그에 평문으로 남기지 않는다

```python
# ✅ 좋은 예
import logging

logger = logging.getLogger(__name__)

logger.info("스캔 시작: target=%s", target_url)
logger.warning("스캐너 %s 타임아웃, skip", scanner_name)
logger.error("세션 재인증 실패", exc_info=True)

# 민감 데이터 마스킹
logger.info("JWT 갱신 완료: token=%s...%s", token[:8], token[-4:])

# ❌ 나쁜 예
print(f"스캔 시작: {target_url}")
logger.info(f"JWT: {token}")    # 토큰 평문 노출
```

## 테스트 코드

- 테스트 파일은 소스 미러: `src/a/b.py` → `tests/a/test_b.py`
- 테스트 대상 자체를 mock 금지 — 외부 경계(HTTP, DB, Docker)만 mock
- `@pytest.mark.asyncio`로 async 테스트
- Given/When/Then 주석으로 구조화

```python
# ✅ 좋은 예
@pytest.mark.asyncio
async def test_scan_timeout_returns_empty_result():
    """스캐너 타임아웃 시 빈 결과를 반환한다."""
    # Given
    scanner = WhatWebPlugin()
    mock_runner = MockToolRunner(raise_timeout=True)

    # When
    result = await scanner.scan("http://example.com", runner=mock_runner)

    # Then
    assert result.status == "timeout"
    assert result.data is None

# ❌ 나쁜 예
def test_scan():                          # 동기 + 이름 모호
    result = scan("http://example.com")
    assert result                         # 뭘 검증하는지 불명확
```

## 파일/모듈 구조

- 한 파일 300줄 이내 권장, 500줄 초과 시 분리
- `__init__.py`에 구현 코드 넣지 않음 — re-export만
- 순환 의존 발생 시 모델을 별도 `models.py`로 분리

```python
# ✅ __init__.py — re-export만
from src.agents.middleware.session import SessionMiddleware
from src.agents.middleware.cookie_jar import CookieJar

__all__ = ["SessionMiddleware", "CookieJar"]
```

## 금지 사항

| 금지 | 대안 |
|------|------|
| `requests` | `httpx` (async) |
| `pip install` | `uv add` |
| `print()` | `logging` |
| `dict`로 데이터 전달 | Pydantic `BaseModel` |
| bare `except:` | 구체적 예외 타입 |
| `Any` 타입 힌트 | 구체적 타입 또는 제네릭 |
| `Optional[X]` | `X \| None` |
| `from module import *` | 명시적 import |
| `.format()` / `%` 문자열 | f-string |
| 동기 HTTP 호출 | `async with httpx.AsyncClient()` |
| 민감 데이터 평문 로깅 | 마스킹 후 로깅 |
| `sleep()`으로 타이밍 제어 | 이벤트/콜백 기반 |
| 전역 mutable 상태 | 의존성 주입 또는 클래스 인스턴스 |