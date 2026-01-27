"""JavaScript Analyzer Regex Module.

정규식 기반 빠른 JavaScript 분석:
- URL 문자열/템플릿 리터럴 추출
- fetch, axios, jQuery, XHR 호출 탐지
- API 키/시크릿 탐지
"""

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import List, Optional, Pattern, Set

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.utils.entropy import EntropyCalculator
from app.services.discovery.utils.secret_patterns import SecretMatch, SecretPatterns

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ExtractedUrl:
    """추출된 URL 정보."""

    url: str
    is_template: bool = False
    placeholders: List[str] = field(default_factory=list)
    source_type: str = ""  # literal, fetch, axios, jquery, xhr


@dataclass
class HttpClientCall:
    """HTTP 클라이언트 호출 정보."""

    client_type: str  # fetch, axios, jquery, xhr
    method: str = "GET"
    url: Optional[str] = None
    has_options: bool = False


# ============================================================================
# UrlPatternMatcher
# ============================================================================


class UrlPatternMatcher:
    """URL 패턴 매칭."""

    # 문자열 URL 패턴
    STRING_URL_PATTERNS: List[Pattern[str]] = [
        # 절대 URL
        re.compile(r'["\']((https?://|wss?://)[^"\']+)["\']'),
        # 상대 URL (API 엔드포인트)
        re.compile(r'["\'](/api/[^"\']+)["\']'),
        re.compile(r'["\'](/v[0-9]+/[^"\']+)["\']'),
        # 일반 경로
        re.compile(r'["\'](/[a-zA-Z][a-zA-Z0-9_\-./]+)["\']'),
    ]

    # 템플릿 리터럴 URL 패턴
    TEMPLATE_URL_PATTERN = re.compile(r"`([^`]*\$\{[^}]+\}[^`]*)`")

    # 템플릿 변수 추출 패턴
    TEMPLATE_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def extract_string_urls(self, content: str) -> List[ExtractedUrl]:
        """문자열에서 URL 추출.

        Args:
            content: JavaScript 소스 코드

        Returns:
            추출된 URL 목록
        """
        urls: List[ExtractedUrl] = []
        seen: Set[str] = set()

        for pattern in self.STRING_URL_PATTERNS:
            matches = pattern.findall(content)
            for match in matches:
                # 튜플인 경우 첫 번째 그룹 사용
                url = match[0] if isinstance(match, tuple) else match

                if url and url not in seen:
                    # 유효한 URL인지 검증
                    if self._is_valid_url(url):
                        seen.add(url)
                        urls.append(
                            ExtractedUrl(
                                url=url,
                                is_template=False,
                                source_type="literal",
                            )
                        )

        return urls

    def extract_template_urls(self, content: str) -> List[ExtractedUrl]:
        """템플릿 리터럴에서 URL 추출.

        Args:
            content: JavaScript 소스 코드

        Returns:
            추출된 URL 목록
        """
        urls: List[ExtractedUrl] = []
        seen: Set[str] = set()

        matches = self.TEMPLATE_URL_PATTERN.findall(content)
        for template in matches:
            # URL처럼 보이는 템플릿만 필터링
            if "/" not in template and "://" not in template:
                continue

            if template in seen:
                continue
            seen.add(template)

            # 템플릿 변수 추출
            placeholders = self.TEMPLATE_VAR_PATTERN.findall(template)

            urls.append(
                ExtractedUrl(
                    url=template,
                    is_template=True,
                    placeholders=placeholders,
                    source_type="template",
                )
            )

        return urls

    def _is_valid_url(self, url: str) -> bool:
        """유효한 URL인지 검증.

        Args:
            url: URL 문자열

        Returns:
            True if valid URL
        """
        # 너무 짧은 URL 제외
        if len(url) < 2:
            return False

        # 파일 확장자만 있는 경우 제외
        if url.startswith("."):
            return False

        # 숫자만 있는 경우 제외
        if url.lstrip("/").isdigit():
            return False

        # 흔한 false positive 제외
        false_positives = [
            "/",
            "//",
            "/*",
            "/**",
            "///",
            "/?",
            "/#",
        ]
        if url in false_positives:
            return False

        return True


# ============================================================================
# HttpClientDetector
# ============================================================================


class HttpClientDetector:
    """HTTP 클라이언트 호출 탐지."""

    # fetch 패턴
    FETCH_PATTERN = re.compile(
        r'fetch\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*(\{[^}]*\}))?'
    )

    # Fetch/Axios options에서 method 추출
    OPTIONS_METHOD_PATTERN = re.compile(r'method\s*:\s*["\'](\w+)["\']', re.IGNORECASE)

    # jQuery ajax에서 type 또는 method 추출
    JQUERY_METHOD_PATTERN = re.compile(
        r'(?:type|method)\s*:\s*["\'](\w+)["\']', re.IGNORECASE
    )

    # axios 패턴 (direct는 전체 config 객체 캡처)
    AXIOS_PATTERNS = {
        "get": re.compile(r'axios\.get\s*\(\s*["\']([^"\']+)["\']'),
        "post": re.compile(r'axios\.post\s*\(\s*["\']([^"\']+)["\']'),
        "put": re.compile(r'axios\.put\s*\(\s*["\']([^"\']+)["\']'),
        "delete": re.compile(r'axios\.delete\s*\(\s*["\']([^"\']+)["\']'),
        "patch": re.compile(r'axios\.patch\s*\(\s*["\']([^"\']+)["\']'),
        "direct": re.compile(
            r'axios\s*\(\s*(\{[^}]*url\s*:\s*["\'][^"\']+["\'][^}]*\})'
        ),
    }
    # axios config에서 URL 추출
    AXIOS_URL_PATTERN = re.compile(r'url\s*:\s*["\']([^"\']+)["\']')

    # jQuery 패턴 (ajax는 전체 config 객체 캡처)
    JQUERY_PATTERNS = {
        "ajax": re.compile(
            r'\$\.ajax\s*\(\s*(\{[^}]*url\s*:\s*["\'][^"\']+["\'][^}]*\})'
        ),
        "get": re.compile(r'\$\.get\s*\(\s*["\']([^"\']+)["\']'),
        "post": re.compile(r'\$\.post\s*\(\s*["\']([^"\']+)["\']'),
        "getJSON": re.compile(r'\$\.getJSON\s*\(\s*["\']([^"\']+)["\']'),
    }
    # ajax config에서 URL 추출
    JQUERY_URL_PATTERN = re.compile(r'url\s*:\s*["\']([^"\']+)["\']')

    # XMLHttpRequest 패턴
    XHR_PATTERN = re.compile(r'\.open\s*\(\s*["\'](\w+)["\']\s*,\s*["\']([^"\']+)["\']')

    def detect_fetch(self, content: str) -> List[HttpClientCall]:
        """fetch 호출 탐지.

        Args:
            content: JavaScript 소스 코드

        Returns:
            탐지된 호출 목록
        """
        calls: List[HttpClientCall] = []

        for match in self.FETCH_PATTERN.finditer(content):
            url = match.group(1)
            options = match.group(2)

            method = "GET"  # 기본값
            if options:
                method_match = self.OPTIONS_METHOD_PATTERN.search(options)
                if method_match:
                    method = method_match.group(1).upper()

            calls.append(
                HttpClientCall(
                    client_type="fetch",
                    method=method,
                    url=url,
                    has_options=bool(options),
                )
            )

        return calls

    def detect_axios(self, content: str) -> List[HttpClientCall]:
        """axios 호출 탐지.

        Args:
            content: JavaScript 소스 코드

        Returns:
            탐지된 호출 목록
        """
        calls: List[HttpClientCall] = []

        for method_name, pattern in self.AXIOS_PATTERNS.items():
            for match in pattern.finditer(content):
                if method_name == "direct":
                    # direct는 전체 config 객체를 캡처
                    config_obj = match.group(1)
                    # config에서 URL 추출
                    url_match = self.AXIOS_URL_PATTERN.search(config_obj)
                    if not url_match:
                        continue
                    url = url_match.group(1)
                    # config에서 method 추출
                    method_match = self.OPTIONS_METHOD_PATTERN.search(config_obj)
                    method = method_match.group(1).upper() if method_match else "GET"
                else:
                    url = match.group(1)
                    method = method_name.upper()

                calls.append(
                    HttpClientCall(
                        client_type="axios",
                        method=method,
                        url=url,
                        has_options=True,
                    )
                )

        return calls

    def detect_jquery(self, content: str) -> List[HttpClientCall]:
        """jQuery AJAX 호출 탐지.

        Args:
            content: JavaScript 소스 코드

        Returns:
            탐지된 호출 목록
        """
        calls: List[HttpClientCall] = []

        for method_name, pattern in self.JQUERY_PATTERNS.items():
            for match in pattern.finditer(content):
                if method_name == "ajax":
                    # ajax는 전체 config 객체를 캡처
                    config_obj = match.group(1)
                    # config에서 URL 추출
                    url_match = self.JQUERY_URL_PATTERN.search(config_obj)
                    if not url_match:
                        continue
                    url = url_match.group(1)
                    # config에서 type/method 추출
                    method_match = self.JQUERY_METHOD_PATTERN.search(config_obj)
                    method = method_match.group(1).upper() if method_match else "GET"
                elif method_name == "getJSON":
                    url = match.group(1)
                    method = "GET"
                else:
                    url = match.group(1)
                    method = method_name.upper()

                calls.append(
                    HttpClientCall(
                        client_type="jquery",
                        method=method,
                        url=url,
                        has_options=method_name == "ajax",
                    )
                )

        return calls

    def detect_xhr(self, content: str) -> List[HttpClientCall]:
        """XMLHttpRequest 호출 탐지.

        Args:
            content: JavaScript 소스 코드

        Returns:
            탐지된 호출 목록
        """
        calls: List[HttpClientCall] = []

        for match in self.XHR_PATTERN.finditer(content):
            method = match.group(1).upper()
            url = match.group(2)

            calls.append(
                HttpClientCall(
                    client_type="xhr",
                    method=method,
                    url=url,
                    has_options=False,
                )
            )

        return calls

    def detect_all(self, content: str) -> List[HttpClientCall]:
        """모든 HTTP 클라이언트 호출 탐지.

        Args:
            content: JavaScript 소스 코드

        Returns:
            탐지된 호출 목록
        """
        calls: List[HttpClientCall] = []
        calls.extend(self.detect_fetch(content))
        calls.extend(self.detect_axios(content))
        calls.extend(self.detect_jquery(content))
        calls.extend(self.detect_xhr(content))
        return calls


# ============================================================================
# SecretDetector
# ============================================================================


class SecretDetector:
    """시크릿 탐지기 (정규식 기반)."""

    def __init__(self) -> None:
        """Initialize SecretDetector."""
        self._patterns = SecretPatterns()
        self._entropy = EntropyCalculator()

    def detect(self, content: str) -> List[SecretMatch]:
        """콘텐츠에서 시크릿 탐지.

        Args:
            content: JavaScript 소스 코드

        Returns:
            탐지된 시크릿 목록
        """
        return self._patterns.scan(content)

    def detect_high_confidence(
        self, content: str, min_confidence: float = 0.8
    ) -> List[SecretMatch]:
        """높은 신뢰도의 시크릿만 탐지.

        Args:
            content: JavaScript 소스 코드
            min_confidence: 최소 신뢰도

        Returns:
            높은 신뢰도 시크릿 목록
        """
        all_matches = self._patterns.scan(content)
        return [
            m
            for m in all_matches
            if m.confidence >= min_confidence and not m.is_false_positive
        ]


# ============================================================================
# JsAnalyzerRegexModule
# ============================================================================


class JsAnalyzerRegexModule(BaseDiscoveryModule):
    """정규식 기반 JavaScript 분석 Discovery 모듈.

    정규식을 사용하여 빠르게 JavaScript에서 URL과 시크릿을 추출합니다.
    모든 프로필 (QUICK, STANDARD, FULL)에서 활성화됩니다.
    """

    def __init__(self) -> None:
        """Initialize JsAnalyzerRegexModule."""
        self._url_matcher = UrlPatternMatcher()
        self._http_detector = HttpClientDetector()
        self._secret_detector = SecretDetector()

    @property
    def name(self) -> str:
        """모듈 고유 이름."""
        return "js_analyzer_regex"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필 집합."""
        return {ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL}

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """자산 발견 수행.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 자산
        """
        js_contents = context.crawl_data.get("js_contents", [])

        if not js_contents:
            return

        seen_urls: Set[str] = set()
        seen_secrets: Set[str] = set()

        for js_item in js_contents:
            js_url = js_item.get("url", "")
            js_code = js_item.get("content", "")

            if not js_code:
                continue

            # 문자열 URL 추출
            string_urls = self._url_matcher.extract_string_urls(js_code)
            for extracted in string_urls:
                if extracted.url not in seen_urls:
                    seen_urls.add(extracted.url)
                    yield DiscoveredAsset(
                        url=extracted.url,
                        asset_type="js_url",
                        source=self.name,
                        metadata={
                            "is_template": extracted.is_template,
                            "source_type": extracted.source_type,
                            "source_file": js_url,
                        },
                    )

            # 템플릿 URL 추출
            template_urls = self._url_matcher.extract_template_urls(js_code)
            for extracted in template_urls:
                if extracted.url not in seen_urls:
                    seen_urls.add(extracted.url)
                    yield DiscoveredAsset(
                        url=extracted.url,
                        asset_type="js_template_url",
                        source=self.name,
                        metadata={
                            "is_template": True,
                            "placeholders": extracted.placeholders,
                            "source_file": js_url,
                        },
                    )

            # HTTP 클라이언트 호출 탐지
            http_calls = self._http_detector.detect_all(js_code)
            for call in http_calls:
                if call.url and call.url not in seen_urls:
                    seen_urls.add(call.url)
                    yield DiscoveredAsset(
                        url=call.url,
                        asset_type="api_call",
                        source=self.name,
                        metadata={
                            "client_type": call.client_type,
                            "method": call.method,
                            "has_options": call.has_options,
                            "source_file": js_url,
                        },
                    )

            # 시크릿 탐지 (STANDARD, FULL 프로필만)
            if context.profile in (ScanProfile.STANDARD, ScanProfile.FULL):
                secrets = self._secret_detector.detect_high_confidence(js_code)
                for secret in secrets:
                    secret_key = f"{secret.pattern_name}:{secret.matched_value[:20]}"
                    if secret_key not in seen_secrets:
                        seen_secrets.add(secret_key)
                        yield DiscoveredAsset(
                            url=f"secret://{secret.pattern_name}",
                            asset_type="secret",
                            source=self.name,
                            metadata={
                                "secret_type": secret.secret_type.value,
                                "pattern_name": secret.pattern_name,
                                "confidence": secret.confidence,
                                "entropy": secret.entropy,
                                "source_file": js_url,
                                # 보안상 실제 값은 일부만 표시
                                "preview": (
                                    f"{secret.matched_value[:10]}..."
                                    if len(secret.matched_value) > 10
                                    else secret.matched_value
                                ),
                            },
                        )
