"""ResponseAnalyzerModule - HTTP 응답 헤더 및 본문 분석.

HTTP 응답에서 보안 관련 정보를 추출합니다:
- Server, X-Powered-By 헤더 분석
- CSP, CORS 정책 분석
- Cookie 속성 분석
- 에러 메시지 및 스택 트레이스 탐지
"""

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile

# ============================================================================
# Data Classes for Analysis Results
# ============================================================================


@dataclass
class ServerInfo:
    """서버 정보."""

    name: str
    version: Optional[str] = None
    extra_info: str = ""


@dataclass
class TechnologyInfo:
    """기술 스택 정보."""

    name: str
    version: Optional[str] = None


@dataclass
class CorsInfo:
    """CORS 정보."""

    allow_origin: str
    is_wildcard: bool = False
    allow_credentials: bool = False
    allowed_methods: List[str] = field(default_factory=list)


@dataclass
class HeaderAnalysisResult:
    """헤더 분석 결과."""

    server: Optional[ServerInfo] = None
    powered_by: Optional[TechnologyInfo] = None
    powered_by_list: List[TechnologyInfo] = field(default_factory=list)
    aspnet_version: Optional[str] = None
    cors: Optional[CorsInfo] = None


@dataclass
class CspAnalysisResult:
    """CSP 분석 결과."""

    allowed_domains: List[str] = field(default_factory=list)
    script_sources: List[str] = field(default_factory=list)
    report_uri: Optional[str] = None
    directives: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class CookieInfo:
    """쿠키 정보."""

    name: str
    value: str = ""
    domain: Optional[str] = None
    path: Optional[str] = None
    secure: bool = False
    http_only: bool = False
    same_site: Optional[str] = None
    expires: Optional[str] = None
    max_age: Optional[int] = None


@dataclass
class ErrorDetectionResult:
    """에러 탐지 결과."""

    has_path_leakage: bool = False
    leaked_paths: List[str] = field(default_factory=list)
    has_stack_trace: bool = False
    stack_trace_type: Optional[str] = None


# ============================================================================
# HeaderAnalyzer
# ============================================================================


class HeaderAnalyzer:
    """HTTP 응답 헤더 분석기.

    Server, X-Powered-By, CORS 관련 헤더를 분석하여
    서버 기술 스택 및 보안 설정 정보를 추출합니다.
    """

    # Server 헤더 파싱 패턴: name/version (extra info)
    SERVER_PATTERN = re.compile(
        r"^([A-Za-z0-9_\-\.]+)(?:/(\d+(?:\.\d+)*))?(?:\s+(.*))?$"
    )

    # X-Powered-By 파싱 패턴: name/version 또는 name만
    POWERED_BY_PATTERN = re.compile(r"([A-Za-z0-9_\-\.]+)(?:/(\d+(?:\.\d+)*))?")

    def analyze(self, headers: Dict[str, str]) -> HeaderAnalysisResult:
        """헤더 분석 수행.

        Args:
            headers: HTTP 응답 헤더 딕셔너리

        Returns:
            헤더 분석 결과
        """
        result = HeaderAnalysisResult()

        # Server 헤더 분석
        server_header = headers.get("Server")
        if server_header:
            result.server = self._parse_server_header(server_header)

        # X-Powered-By 헤더 분석
        powered_by_header = headers.get("X-Powered-By")
        if powered_by_header:
            result.powered_by_list = self._parse_powered_by_header(powered_by_header)
            if result.powered_by_list:
                result.powered_by = result.powered_by_list[0]

        # X-AspNet-Version 헤더 분석
        aspnet_version = headers.get("X-AspNet-Version")
        if aspnet_version:
            result.aspnet_version = aspnet_version

        # CORS 헤더 분석
        cors_origin = headers.get("Access-Control-Allow-Origin")
        if cors_origin:
            result.cors = self._parse_cors_headers(headers, cors_origin)

        return result

    def _parse_server_header(self, value: str) -> ServerInfo:
        """Server 헤더 파싱.

        Examples:
            - "nginx/1.21.0" -> ServerInfo(name="nginx", version="1.21.0")
            - "Apache/2.4.41 (Ubuntu) OpenSSL/1.1.1" -> ServerInfo(name="Apache", version="2.4.41", extra_info="(Ubuntu) OpenSSL/1.1.1")
            - "Apache" -> ServerInfo(name="Apache", version=None)
        """
        value = value.strip()
        match = self.SERVER_PATTERN.match(value)

        if match:
            name = match.group(1)
            version = match.group(2)
            extra_info = match.group(3) or ""
            return ServerInfo(name=name, version=version, extra_info=extra_info.strip())

        # 패턴 매칭 실패 시 전체를 이름으로 처리
        return ServerInfo(name=value)

    def _parse_powered_by_header(self, value: str) -> List[TechnologyInfo]:
        """X-Powered-By 헤더 파싱.

        Examples:
            - "PHP/8.1.0" -> [TechnologyInfo(name="PHP", version="8.1.0")]
            - "Express" -> [TechnologyInfo(name="Express", version=None)]
            - "PHP/7.4, PleskLin" -> [TechnologyInfo(name="PHP", version="7.4"), TechnologyInfo(name="PleskLin")]
        """
        results: List[TechnologyInfo] = []
        # 콤마로 분리
        parts = [p.strip() for p in value.split(",")]

        for part in parts:
            if not part:
                continue
            match = self.POWERED_BY_PATTERN.match(part)
            if match:
                name = match.group(1)
                version = match.group(2)
                results.append(TechnologyInfo(name=name, version=version))
            else:
                results.append(TechnologyInfo(name=part))

        return results

    def _parse_cors_headers(
        self, headers: Dict[str, str], cors_origin: str
    ) -> CorsInfo:
        """CORS 관련 헤더 파싱."""
        cors_info = CorsInfo(
            allow_origin=cors_origin,
            is_wildcard=(cors_origin == "*"),
        )

        # Access-Control-Allow-Credentials
        credentials = headers.get("Access-Control-Allow-Credentials", "").lower()
        cors_info.allow_credentials = credentials == "true"

        # Access-Control-Allow-Methods
        methods_header = headers.get("Access-Control-Allow-Methods", "")
        if methods_header:
            cors_info.allowed_methods = [
                m.strip() for m in methods_header.split(",") if m.strip()
            ]

        return cors_info


# ============================================================================
# CspParser
# ============================================================================


class CspParser:
    """Content-Security-Policy 파서.

    CSP 헤더를 파싱하여 허용된 도메인, 스크립트 소스,
    report-uri 등의 정보를 추출합니다.
    """

    # URL/도메인 패턴
    DOMAIN_PATTERN = re.compile(
        r"(https?://[^\s;'\"]+|\*?\.[a-zA-Z0-9\-\.]+|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,})"
    )

    def parse(self, csp_header: str) -> CspAnalysisResult:
        """CSP 헤더 파싱.

        Args:
            csp_header: Content-Security-Policy 헤더 값

        Returns:
            CSP 분석 결과
        """
        result = CspAnalysisResult()

        # 디렉티브별로 분리
        directives = csp_header.split(";")

        for directive in directives:
            directive = directive.strip()
            if not directive:
                continue

            parts = directive.split(None, 1)
            if not parts:
                continue

            directive_name = parts[0].lower()
            directive_value = parts[1] if len(parts) > 1 else ""

            # 디렉티브 저장
            values = [v.strip() for v in directive_value.split() if v.strip()]
            result.directives[directive_name] = values

            # report-uri 특별 처리
            if directive_name == "report-uri":
                result.report_uri = directive_value.strip()
                continue

            # script-src 처리
            if directive_name == "script-src":
                result.script_sources = values

            # 도메인 추출
            domains = self._extract_domains(directive_value)
            for domain in domains:
                if domain not in result.allowed_domains:
                    result.allowed_domains.append(domain)

        return result

    def _extract_domains(self, value: str) -> List[str]:
        """값에서 도메인 추출."""
        domains: List[str] = []

        # 토큰 분리
        tokens = value.split()

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            # 키워드 ('self', 'unsafe-inline' 등)는 도메인 목록에 포함하지 않음
            # 단, script-src에서는 별도 처리
            if token.startswith("'") and token.endswith("'"):
                continue

            # URL 또는 도메인 패턴 검사
            if (
                token.startswith("http://")
                or token.startswith("https://")
                or "." in token
                or token.startswith("*")
            ):
                domains.append(token)

        return domains


# ============================================================================
# CookieAnalyzer
# ============================================================================


class CookieAnalyzer:
    """Set-Cookie 헤더 분석기.

    쿠키의 이름, 값, 도메인, 경로, 보안 플래그 등을 추출합니다.
    """

    # 쿠키 속성 패턴
    DOMAIN_PATTERN = re.compile(r"Domain=([^;]+)", re.IGNORECASE)
    PATH_PATTERN = re.compile(r"Path=([^;]+)", re.IGNORECASE)
    SAMESITE_PATTERN = re.compile(r"SameSite=([^;]+)", re.IGNORECASE)
    EXPIRES_PATTERN = re.compile(r"Expires=([^;]+)", re.IGNORECASE)
    MAX_AGE_PATTERN = re.compile(r"Max-Age=(\d+)", re.IGNORECASE)

    def parse(self, set_cookie: str) -> CookieInfo:
        """Set-Cookie 헤더 파싱.

        Args:
            set_cookie: Set-Cookie 헤더 값

        Returns:
            쿠키 정보
        """
        # 쿠키 이름=값 추출 (첫 번째 세미콜론 전까지)
        parts = set_cookie.split(";", 1)
        name_value = parts[0].strip()

        if "=" in name_value:
            name, value = name_value.split("=", 1)
        else:
            name = name_value
            value = ""

        cookie = CookieInfo(name=name.strip(), value=value.strip())

        # 속성 부분만 추출 (이름=값 이후 부분)
        attributes_part = parts[1] if len(parts) > 1 else ""
        attributes_lower = attributes_part.lower()

        # Domain
        domain_match = self.DOMAIN_PATTERN.search(set_cookie)
        if domain_match:
            cookie.domain = domain_match.group(1).strip()

        # Path
        path_match = self.PATH_PATTERN.search(set_cookie)
        if path_match:
            cookie.path = path_match.group(1).strip()

        # Secure 플래그 (속성 부분에서만 확인)
        cookie.secure = self._has_flag(attributes_lower, "secure")

        # HttpOnly 플래그 (속성 부분에서만 확인)
        cookie.http_only = self._has_flag(attributes_lower, "httponly")

        # SameSite
        samesite_match = self.SAMESITE_PATTERN.search(set_cookie)
        if samesite_match:
            cookie.same_site = samesite_match.group(1).strip()

        # Expires
        expires_match = self.EXPIRES_PATTERN.search(set_cookie)
        if expires_match:
            cookie.expires = expires_match.group(1).strip()

        # Max-Age
        max_age_match = self.MAX_AGE_PATTERN.search(set_cookie)
        if max_age_match:
            cookie.max_age = int(max_age_match.group(1))

        return cookie

    def parse_multiple(self, cookies: List[str]) -> List[CookieInfo]:
        """여러 Set-Cookie 헤더 파싱."""
        return [self.parse(cookie) for cookie in cookies]

    def _has_flag(self, attributes: str, flag: str) -> bool:
        """속성 문자열에서 플래그 존재 여부 확인.

        플래그는 단독으로 존재하거나 세미콜론으로 구분되어야 함.
        예: "; Secure;" 또는 "; Secure" (문자열 끝)

        Args:
            attributes: 세미콜론으로 구분된 속성 문자열
            flag: 찾을 플래그 이름 (소문자)

        Returns:
            플래그가 존재하면 True
        """
        # 속성들을 세미콜론으로 분리하여 각각 확인
        for attr in attributes.split(";"):
            attr = attr.strip()
            # 플래그와 정확히 일치하거나 (값 없음)
            # 플래그= 형태로 시작하면 (값 있음) 해당 플래그임
            if attr == flag or attr.startswith(f"{flag}="):
                return True
        return False


# ============================================================================
# ErrorDetector
# ============================================================================


class ErrorDetector:
    """에러 메시지 및 스택 트레이스 탐지기.

    응답 본문에서 민감한 정보 노출을 탐지합니다:
    - 서버 파일 경로 노출
    - 스택 트레이스 노출
    """

    # 서버 경로 패턴
    # Unix 경로: /var/www, /home/user, /app 등
    UNIX_PATH_PATTERN = re.compile(
        r"(/(?:var|home|usr|app|opt|etc|tmp|srv)[/\\][^\s<>\"']+)"
    )
    # Windows 경로: C:\, D:\ 등
    WINDOWS_PATH_PATTERN = re.compile(
        r"([A-Za-z]:\\(?:[^\s<>\"':*?|]+\\)*[^\s<>\"':*?|]+)"
    )

    # 스택 트레이스 패턴
    PYTHON_TRACE_PATTERN = re.compile(
        r"Traceback \(most recent call last\):", re.IGNORECASE
    )
    JAVA_TRACE_PATTERN = re.compile(
        r"^\s*at\s+[\w\.$]+\([\w\.$]+\.java:\d+\)", re.MULTILINE
    )
    PHP_TRACE_PATTERN = re.compile(r"Stack trace:|#\d+\s+[^\n]+\(\d+\):", re.IGNORECASE)
    NODEJS_TRACE_PATTERN = re.compile(
        r"^\s+at\s+(?:Object\.|Module\.|)[\w<>\.]+\s+\([^\)]+:\d+:\d+\)", re.MULTILINE
    )
    DOTNET_TRACE_PATTERN = re.compile(
        r"^\s+at\s+[\w\.<>]+\([^\)]*\)\s+in\s+[A-Za-z]:\\", re.MULTILINE
    )

    def detect(self, body: str) -> ErrorDetectionResult:
        """응답 본문에서 에러 정보 탐지.

        Args:
            body: HTTP 응답 본문

        Returns:
            에러 탐지 결과
        """
        result = ErrorDetectionResult()

        # 경로 노출 탐지
        leaked_paths = self._detect_paths(body)
        if leaked_paths:
            result.has_path_leakage = True
            result.leaked_paths = leaked_paths

        # 스택 트레이스 탐지
        stack_trace_type = self._detect_stack_trace(body)
        if stack_trace_type:
            result.has_stack_trace = True
            result.stack_trace_type = stack_trace_type

        return result

    def _detect_paths(self, body: str) -> List[str]:
        """경로 탐지."""
        paths: List[str] = []

        # Unix 경로 탐지
        unix_matches = self.UNIX_PATH_PATTERN.findall(body)
        paths.extend(unix_matches)

        # Windows 경로 탐지
        windows_matches = self.WINDOWS_PATH_PATTERN.findall(body)
        paths.extend(windows_matches)

        # 중복 제거 및 정리
        return list(dict.fromkeys(paths))

    def _detect_stack_trace(self, body: str) -> Optional[str]:
        """스택 트레이스 탐지."""
        # Python
        if self.PYTHON_TRACE_PATTERN.search(body):
            return "python"

        # Java
        if self.JAVA_TRACE_PATTERN.search(body):
            return "java"

        # PHP
        if self.PHP_TRACE_PATTERN.search(body):
            return "php"

        # Node.js
        if self.NODEJS_TRACE_PATTERN.search(body):
            return "nodejs"

        # .NET
        if self.DOTNET_TRACE_PATTERN.search(body):
            return "dotnet"

        return None


# ============================================================================
# ResponseAnalyzerModule
# ============================================================================


class ResponseAnalyzerModule(BaseDiscoveryModule):
    """HTTP 응답 분석 모듈.

    crawl_data에 저장된 HTTP 응답을 분석하여
    보안 관련 정보를 추출합니다.

    Attributes:
        name: 모듈 이름 ("response_analyzer")
        profiles: 지원하는 스캔 프로필 (STANDARD, FULL)
    """

    def __init__(self) -> None:
        """모듈 초기화."""
        self._header_analyzer = HeaderAnalyzer()
        self._csp_parser = CspParser()
        self._cookie_analyzer = CookieAnalyzer()
        self._error_detector = ErrorDetector()

    @property
    def name(self) -> str:
        """모듈 고유 이름."""
        return "response_analyzer"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필."""
        return {ScanProfile.STANDARD, ScanProfile.FULL}

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """응답 분석을 통한 자산 발견.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 자산 (서버 정보, 기술 스택, 정보 노출 등)
        """
        responses = context.crawl_data.get("responses", [])

        for response_data in responses:
            url = response_data.get("url", "")
            headers = response_data.get("headers", {})
            body = response_data.get("body", "")
            status_code = response_data.get("status_code", 200)

            # 헤더 분석
            async for asset in self._analyze_headers(url, headers):
                yield asset

            # CSP 분석
            csp_header = headers.get("Content-Security-Policy", "")
            if csp_header:
                async for asset in self._analyze_csp(url, csp_header):
                    yield asset

            # 쿠키 분석
            set_cookie = headers.get("Set-Cookie", "")
            if set_cookie:
                async for asset in self._analyze_cookies(url, set_cookie):
                    yield asset

            # 에러 응답 분석 (4xx, 5xx)
            if status_code >= 400:
                async for asset in self._analyze_error_response(url, body):
                    yield asset

    async def _analyze_headers(
        self, url: str, headers: Dict[str, str]
    ) -> AsyncIterator[DiscoveredAsset]:
        """헤더 분석."""
        result = self._header_analyzer.analyze(headers)

        # Server 정보
        if result.server:
            yield DiscoveredAsset(
                url=url,
                asset_type="server_info",
                source=self.name,
                metadata={
                    "server_name": result.server.name,
                    "server_version": result.server.version,
                    "extra_info": result.server.extra_info,
                },
            )

        # X-Powered-By 정보
        for tech in result.powered_by_list:
            yield DiscoveredAsset(
                url=url,
                asset_type="technology_stack",
                source=self.name,
                metadata={
                    "technology": tech.name,
                    "version": tech.version,
                },
            )

        # CORS 정보
        if result.cors:
            yield DiscoveredAsset(
                url=url,
                asset_type="cors_config",
                source=self.name,
                metadata={
                    "allow_origin": result.cors.allow_origin,
                    "is_wildcard": result.cors.is_wildcard,
                    "allow_credentials": result.cors.allow_credentials,
                    "allowed_methods": result.cors.allowed_methods,
                },
            )

    async def _analyze_csp(
        self, url: str, csp_header: str
    ) -> AsyncIterator[DiscoveredAsset]:
        """CSP 분석."""
        result = self._csp_parser.parse(csp_header)

        yield DiscoveredAsset(
            url=url,
            asset_type="csp_policy",
            source=self.name,
            metadata={
                "allowed_domains": result.allowed_domains,
                "script_sources": result.script_sources,
                "report_uri": result.report_uri,
                "directives": result.directives,
            },
        )

        # 허용된 도메인을 별도 자산으로
        for domain in result.allowed_domains:
            yield DiscoveredAsset(
                url=domain if domain.startswith("http") else f"https://{domain}",
                asset_type="csp_allowed_domain",
                source=self.name,
                metadata={
                    "found_in": url,
                    "directive": "csp",
                },
            )

    async def _analyze_cookies(
        self, url: str, set_cookie: str
    ) -> AsyncIterator[DiscoveredAsset]:
        """쿠키 분석."""
        cookie = self._cookie_analyzer.parse(set_cookie)

        # 보안 플래그 문제 체크
        security_issues = []
        if not cookie.secure:
            security_issues.append("missing_secure_flag")
        if not cookie.http_only:
            security_issues.append("missing_httponly_flag")
        if cookie.same_site is None:
            security_issues.append("missing_samesite_attribute")

        yield DiscoveredAsset(
            url=url,
            asset_type="cookie_info",
            source=self.name,
            metadata={
                "cookie_name": cookie.name,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "http_only": cookie.http_only,
                "same_site": cookie.same_site,
                "security_issues": security_issues,
            },
        )

    async def _analyze_error_response(
        self, url: str, body: str
    ) -> AsyncIterator[DiscoveredAsset]:
        """에러 응답 분석."""
        result = self._error_detector.detect(body)

        # 경로 노출
        if result.has_path_leakage:
            yield DiscoveredAsset(
                url=url,
                asset_type="information_leakage",
                source=self.name,
                metadata={
                    "type": "path_leakage",
                    "leaked_paths": result.leaked_paths,
                },
            )

        # 스택 트레이스 노출
        if result.has_stack_trace:
            yield DiscoveredAsset(
                url=url,
                asset_type="information_leakage",
                source=self.name,
                metadata={
                    "type": "stack_trace",
                    "stack_trace_type": result.stack_trace_type,
                },
            )
