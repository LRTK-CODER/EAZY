"""ThirdPartyDetectorModule - 외부 서비스 탐지.

외부 서비스(Google Analytics, Firebase, Stripe 등)를 탐지합니다:
- 스크립트 URL 패턴 매칭
- 글로벌 변수 탐지
- 쿠키 패턴 매칭
- HTML 콘텐츠 패턴 매칭
"""

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ThirdPartyService:
    """외부 서비스 정보.

    Attributes:
        name: 서비스 이름 (예: "Google Analytics")
        category: 서비스 카테고리 (예: "analytics", "payment")
        confidence: 탐지 신뢰도 (0.0 ~ 1.0)
        detected_by: 탐지 방법 (예: "script_src", "global_var", "cookie")
        version: 서비스 버전 (선택)
        metadata: 추가 메타데이터
    """

    name: str
    category: str
    confidence: float
    detected_by: str
    version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceSignature:
    """서비스 시그니처 정의.

    YAML 시그니처 파일에서 로드된 서비스 시그니처.
    """

    name: str
    category: str
    script_patterns: List[Dict[str, Any]] = field(default_factory=list)
    global_variables: List[Dict[str, Any]] = field(default_factory=list)
    cookie_patterns: List[Dict[str, Any]] = field(default_factory=list)
    html_patterns: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================================
# SignatureLoader
# ============================================================================


class SignatureLoader:
    """시그니처 파일 로더.

    YAML 형식의 시그니처 파일을 로드합니다.
    """

    _signatures: Optional[Dict[str, ServiceSignature]] = None

    @classmethod
    def load(cls) -> Dict[str, ServiceSignature]:
        """시그니처 로드 (캐싱).

        Returns:
            서비스 ID -> ServiceSignature 매핑
        """
        if cls._signatures is not None:
            return cls._signatures

        signatures_path = (
            Path(__file__).parent.parent / "data" / "thirdparty_signatures.yaml"
        )

        if not signatures_path.exists():
            cls._signatures = {}
            return cls._signatures

        with open(signatures_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        cls._signatures = {}
        services = data.get("services", {})

        for service_id, service_data in services.items():
            cls._signatures[service_id] = ServiceSignature(
                name=service_data.get("name", service_id),
                category=service_data.get("category", "other"),
                script_patterns=service_data.get("script_patterns", []),
                global_variables=service_data.get("global_variables", []),
                cookie_patterns=service_data.get("cookie_patterns", []),
                html_patterns=service_data.get("html_patterns", []),
            )

        return cls._signatures

    @classmethod
    def reset(cls) -> None:
        """캐시 초기화 (테스트용)."""
        cls._signatures = None


# ============================================================================
# ScriptPatternMatcher
# ============================================================================


class ScriptPatternMatcher:
    """스크립트 URL 패턴 매처.

    스크립트 URL에서 외부 서비스를 탐지합니다.
    """

    def __init__(self) -> None:
        """매처 초기화."""
        self._signatures = SignatureLoader.load()
        self._compiled_patterns: Dict[
            str, List[tuple[re.Pattern[str], Dict[str, Any]]]
        ] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """패턴 사전 컴파일."""
        for service_id, sig in self._signatures.items():
            patterns: List[tuple[re.Pattern[str], Dict[str, Any]]] = []
            for pattern_data in sig.script_patterns:
                pattern_str = pattern_data.get("pattern", "")
                if pattern_str:
                    compiled = re.compile(pattern_str, re.IGNORECASE)
                    patterns.append((compiled, pattern_data))
            self._compiled_patterns[service_id] = patterns

    def match(self, scripts: List[str]) -> List[ThirdPartyService]:
        """스크립트 URL에서 서비스 탐지.

        Args:
            scripts: 스크립트 URL 목록

        Returns:
            탐지된 서비스 목록
        """
        results: List[ThirdPartyService] = []
        detected_services: Set[str] = set()

        for script_url in scripts:
            for service_id, patterns in self._compiled_patterns.items():
                if service_id in detected_services:
                    continue

                sig = self._signatures[service_id]
                for compiled_pattern, pattern_data in patterns:
                    match = compiled_pattern.search(script_url)
                    if match:
                        service = self._create_service(
                            sig, pattern_data, match, script_url
                        )
                        results.append(service)
                        detected_services.add(service_id)
                        break

        return results

    def _create_service(
        self,
        sig: ServiceSignature,
        pattern_data: Dict[str, Any],
        match: re.Match[str],
        script_url: str,
    ) -> ThirdPartyService:
        """서비스 객체 생성."""
        confidence = pattern_data.get("confidence", 0.9)
        version = pattern_data.get("version")

        metadata: Dict[str, Any] = {"script_url": script_url}

        # 버전 추출
        extract_info = pattern_data.get("extract", {})
        if "version" in extract_info:
            group_num = extract_info["version"]
            try:
                extracted_version = match.group(group_num)
                if extracted_version:
                    version = extracted_version
            except IndexError:
                pass

        # 기타 필드 추출
        for field_name, group_num in extract_info.items():
            if field_name == "version":
                continue
            try:
                extracted_value = match.group(group_num)
                if extracted_value:
                    metadata[field_name] = extracted_value
            except IndexError:
                pass

        return ThirdPartyService(
            name=sig.name,
            category=sig.category,
            confidence=confidence,
            detected_by="script_src",
            version=version,
            metadata=metadata,
        )


# ============================================================================
# GlobalVariableMatcher
# ============================================================================


class GlobalVariableMatcher:
    """글로벌 변수 매처.

    JavaScript 글로벌 변수에서 외부 서비스를 탐지합니다.
    """

    def __init__(self) -> None:
        """매처 초기화."""
        self._signatures = SignatureLoader.load()
        self._var_to_service: Dict[str, List[tuple[str, Dict[str, Any]]]] = {}
        self._build_lookup()

    def _build_lookup(self) -> None:
        """변수명 -> 서비스 룩업 테이블 생성."""
        for service_id, sig in self._signatures.items():
            for var_data in sig.global_variables:
                var_name = var_data.get("name", "").lower()
                if var_name:
                    if var_name not in self._var_to_service:
                        self._var_to_service[var_name] = []
                    self._var_to_service[var_name].append((service_id, var_data))

    def match(self, global_vars: List[str]) -> List[ThirdPartyService]:
        """글로벌 변수에서 서비스 탐지.

        Args:
            global_vars: 글로벌 변수 이름 목록

        Returns:
            탐지된 서비스 목록
        """
        results: List[ThirdPartyService] = []
        detected_services: Set[str] = set()

        for var_name in global_vars:
            var_lower = var_name.lower()
            if var_lower in self._var_to_service:
                for service_id, var_data in self._var_to_service[var_lower]:
                    if service_id in detected_services:
                        continue

                    sig = self._signatures[service_id]
                    confidence = var_data.get("confidence", 0.75)

                    results.append(
                        ThirdPartyService(
                            name=sig.name,
                            category=sig.category,
                            confidence=confidence,
                            detected_by="global_var",
                            metadata={"variable_name": var_name},
                        )
                    )
                    detected_services.add(service_id)

        return results


# ============================================================================
# CookieMatcher
# ============================================================================


class CookieMatcher:
    """쿠키 패턴 매처.

    쿠키에서 외부 서비스를 탐지합니다.
    """

    def __init__(self) -> None:
        """매처 초기화."""
        self._signatures = SignatureLoader.load()
        self._compiled_patterns: Dict[
            str, List[tuple[re.Pattern[str], Dict[str, Any]]]
        ] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """패턴 사전 컴파일."""
        for service_id, sig in self._signatures.items():
            patterns: List[tuple[re.Pattern[str], Dict[str, Any]]] = []
            for pattern_data in sig.cookie_patterns:
                pattern_str = pattern_data.get("pattern", "")
                if pattern_str:
                    compiled = re.compile(pattern_str, re.IGNORECASE)
                    patterns.append((compiled, pattern_data))
            self._compiled_patterns[service_id] = patterns

    def match(self, cookies: List[str]) -> List[ThirdPartyService]:
        """쿠키에서 서비스 탐지.

        Args:
            cookies: 쿠키 문자열 목록

        Returns:
            탐지된 서비스 목록
        """
        results: List[ThirdPartyService] = []
        detected_services: Set[str] = set()

        for cookie in cookies:
            for service_id, patterns in self._compiled_patterns.items():
                if service_id in detected_services:
                    continue

                sig = self._signatures[service_id]
                for compiled_pattern, pattern_data in patterns:
                    if compiled_pattern.search(cookie):
                        confidence = pattern_data.get("confidence", 0.75)
                        results.append(
                            ThirdPartyService(
                                name=sig.name,
                                category=sig.category,
                                confidence=confidence,
                                detected_by="cookie",
                                metadata={"cookie": cookie.split("=")[0]},
                            )
                        )
                        detected_services.add(service_id)
                        break

        return results


# ============================================================================
# HtmlPatternMatcher
# ============================================================================


class HtmlPatternMatcher:
    """HTML 콘텐츠 패턴 매처.

    HTML 콘텐츠에서 외부 서비스를 탐지합니다.
    """

    def __init__(self) -> None:
        """매처 초기화."""
        self._signatures = SignatureLoader.load()
        self._compiled_patterns: Dict[
            str, List[tuple[re.Pattern[str], Dict[str, Any]]]
        ] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """패턴 사전 컴파일."""
        for service_id, sig in self._signatures.items():
            patterns: List[tuple[re.Pattern[str], Dict[str, Any]]] = []
            for pattern_data in sig.html_patterns:
                pattern_str = pattern_data.get("pattern", "")
                if pattern_str:
                    compiled = re.compile(pattern_str, re.IGNORECASE)
                    patterns.append((compiled, pattern_data))
            self._compiled_patterns[service_id] = patterns

    def match(self, html_content: str) -> List[ThirdPartyService]:
        """HTML 콘텐츠에서 서비스 탐지.

        Args:
            html_content: HTML 콘텐츠

        Returns:
            탐지된 서비스 목록
        """
        results: List[ThirdPartyService] = []
        detected_services: Set[str] = set()

        for service_id, patterns in self._compiled_patterns.items():
            if service_id in detected_services:
                continue

            sig = self._signatures[service_id]
            for compiled_pattern, pattern_data in patterns:
                if compiled_pattern.search(html_content):
                    confidence = pattern_data.get("confidence", 0.7)
                    results.append(
                        ThirdPartyService(
                            name=sig.name,
                            category=sig.category,
                            confidence=confidence,
                            detected_by="html_content",
                        )
                    )
                    detected_services.add(service_id)
                    break

        return results


# ============================================================================
# ThirdPartyDetectorModule
# ============================================================================


class ThirdPartyDetectorModule(BaseDiscoveryModule):
    """외부 서비스 탐지 모듈.

    crawl_data에서 스크립트, 쿠키, 글로벌 변수, HTML 콘텐츠를 분석하여
    사용 중인 외부 서비스를 탐지합니다.

    Attributes:
        name: 모듈 이름 ("thirdparty_detector")
        profiles: 지원하는 스캔 프로필 (STANDARD, FULL)
    """

    def __init__(self) -> None:
        """모듈 초기화."""
        self._script_matcher = ScriptPatternMatcher()
        self._global_var_matcher = GlobalVariableMatcher()
        self._cookie_matcher = CookieMatcher()
        self._html_matcher = HtmlPatternMatcher()

    @property
    def name(self) -> str:
        """모듈 고유 이름."""
        return "thirdparty_detector"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필."""
        return {ScanProfile.STANDARD, ScanProfile.FULL}

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """외부 서비스 탐지.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 외부 서비스 자산
        """
        crawl_data = context.crawl_data
        if not crawl_data:
            return

        # 데이터 추출
        scripts = crawl_data.get("scripts", [])
        cookies = crawl_data.get("cookies", [])
        global_vars = crawl_data.get("global_variables", [])
        html_content = crawl_data.get("html_content", "")

        # 서비스 탐지
        detected_services: Dict[str, ThirdPartyService] = {}

        # 1. 스크립트 URL 탐지 (가장 높은 신뢰도)
        for service in self._script_matcher.match(scripts):
            key = service.name
            if key not in detected_services:
                detected_services[key] = service
            elif service.confidence > detected_services[key].confidence:
                # 더 높은 신뢰도의 탐지 결과로 업데이트
                detected_services[key] = service

        # 2. 글로벌 변수 탐지
        for service in self._global_var_matcher.match(global_vars):
            key = service.name
            if key not in detected_services:
                detected_services[key] = service

        # 3. 쿠키 탐지
        for service in self._cookie_matcher.match(cookies):
            key = service.name
            if key not in detected_services:
                detected_services[key] = service

        # 4. HTML 콘텐츠 탐지
        for service in self._detect_from_html(html_content):
            key = service.name
            if key not in detected_services:
                detected_services[key] = service

        # 결과 yield
        for service in detected_services.values():
            yield self._create_asset(service, scripts)

    def _detect_from_html(self, html_content: str) -> List[ThirdPartyService]:
        """HTML 콘텐츠에서 서비스 탐지.

        Args:
            html_content: HTML 콘텐츠

        Returns:
            탐지된 서비스 목록
        """
        if not html_content:
            return []

        return self._html_matcher.match(html_content)

    def _create_asset(
        self, service: ThirdPartyService, scripts: List[str]
    ) -> DiscoveredAsset:
        """DiscoveredAsset 생성.

        Args:
            service: 탐지된 서비스 정보
            scripts: 스크립트 URL 목록 (URL 결정용)

        Returns:
            발견된 자산
        """
        # URL 결정: 스크립트 URL이 있으면 사용, 없으면 서비스 메타데이터 활용
        url = service.metadata.get("script_url", "")
        if not url:
            # 대체 URL 생성
            url = f"https://{service.name.lower().replace(' ', '-')}.service"

        metadata = {
            "service_name": service.name,
            "category": service.category,
            "confidence": service.confidence,
            "detected_by": service.detected_by,
        }

        if service.version:
            metadata["version"] = service.version

        # 추가 메타데이터 병합
        for key, value in service.metadata.items():
            if key != "script_url":
                metadata[key] = value

        return DiscoveredAsset(
            url=url,
            asset_type="thirdparty_service",
            source=self.name,
            metadata=metadata,
        )
