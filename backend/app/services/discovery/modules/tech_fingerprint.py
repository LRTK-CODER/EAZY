"""TechFingerprintModule - 웹 애플리케이션 기술 스택 탐지.

웹 애플리케이션에서 사용하는 기술 스택을 식별합니다:
- Frontend Framework: React, Vue, Angular
- Library: jQuery
- Server: nginx, Apache
- CDN: Cloudflare
- CMS: WordPress
"""

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.response_analyzer import HeaderAnalyzer

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TechSignature:
    """기술 스택 시그니처.

    Attributes:
        name: 기술 이름 (React, Vue, nginx 등)
        category: 카테고리 (frontend_framework, library, server, cdn, cms)
        version: 버전 정보 (선택)
        confidence: 신뢰도 (0.0 ~ 1.0)
        evidence: 탐지 근거 목록
    """

    name: str
    category: str
    version: Optional[str] = None
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)


# ============================================================================
# HeaderMatcher - 헤더 기반 탐지
# ============================================================================


class HeaderMatcher:
    """HTTP 헤더 기반 기술 탐지.

    Server, X-Powered-By, cf-ray 등의 헤더를 분석하여
    서버, CDN, 백엔드 기술을 식별합니다.
    """

    def __init__(self) -> None:
        """초기화."""
        self._header_analyzer = HeaderAnalyzer()

        # Server 헤더 패턴
        self._server_patterns: List[Tuple[str, str, re.Pattern[str]]] = [
            ("nginx", "server", re.compile(r"nginx(?:/([0-9.]+))?", re.IGNORECASE)),
            ("Apache", "server", re.compile(r"Apache(?:/([0-9.]+))?", re.IGNORECASE)),
            (
                "Cloudflare",
                "cdn",
                re.compile(r"cloudflare", re.IGNORECASE),
            ),
        ]

        # X-Powered-By 패턴
        self._powered_by_patterns: List[Tuple[str, str, re.Pattern[str]]] = [
            ("Express", "server", re.compile(r"Express", re.IGNORECASE)),
            ("PHP", "server", re.compile(r"PHP(?:/([0-9.]+))?", re.IGNORECASE)),
            ("ASP.NET", "server", re.compile(r"ASP\.NET", re.IGNORECASE)),
        ]

        # CDN 특수 헤더
        self._cdn_headers: Dict[str, Tuple[str, str]] = {
            "cf-ray": ("Cloudflare", "cdn"),
            "cf-cache-status": ("Cloudflare", "cdn"),
            "x-amz-cf-id": ("AWS CloudFront", "cdn"),
            "x-amz-cf-pop": ("AWS CloudFront", "cdn"),
        }

    def match(self, headers: Dict[str, str]) -> List[TechSignature]:
        """헤더에서 기술 스택 탐지.

        Args:
            headers: HTTP 응답 헤더 딕셔너리

        Returns:
            탐지된 기술 시그니처 목록
        """
        results: List[TechSignature] = []
        seen_techs: Set[str] = set()

        # 헤더 키를 소문자로 정규화
        normalized_headers = {k.lower(): v for k, v in headers.items()}

        # Server 헤더 분석
        server_value = normalized_headers.get("server", "")
        if server_value:
            for name, category, pattern in self._server_patterns:
                match = pattern.search(server_value)
                if match:
                    version = match.group(1) if match.lastindex else None
                    if name not in seen_techs:
                        results.append(
                            TechSignature(
                                name=name,
                                category=category,
                                version=version,
                                confidence=0.95,
                                evidence=["header"],
                            )
                        )
                        seen_techs.add(name)

        # X-Powered-By 헤더 분석
        powered_by_value = normalized_headers.get("x-powered-by", "")
        if powered_by_value:
            for name, category, pattern in self._powered_by_patterns:
                match = pattern.search(powered_by_value)
                if match:
                    version = match.group(1) if match.lastindex else None
                    if name not in seen_techs:
                        results.append(
                            TechSignature(
                                name=name,
                                category=category,
                                version=version,
                                confidence=0.9,
                                evidence=["header"],
                            )
                        )
                        seen_techs.add(name)

        # CDN 특수 헤더 확인
        for header_name, (tech_name, category) in self._cdn_headers.items():
            if header_name in normalized_headers:
                if tech_name not in seen_techs:
                    results.append(
                        TechSignature(
                            name=tech_name,
                            category=category,
                            version=None,
                            confidence=0.95,
                            evidence=["header"],
                        )
                    )
                    seen_techs.add(tech_name)

        return results


# ============================================================================
# ScriptMatcher - 스크립트 URL 기반 탐지
# ============================================================================


class ScriptMatcher:
    """스크립트 URL 기반 기술 탐지.

    JavaScript 파일 URL 패턴을 분석하여
    프론트엔드 프레임워크 및 라이브러리를 식별합니다.
    """

    def __init__(self) -> None:
        """초기화."""
        # (기술명, 카테고리, 버전 추출 패턴, 단순 매칭 패턴)
        self._patterns: List[Tuple[str, str, re.Pattern[str], re.Pattern[str]]] = [
            # React
            (
                "React",
                "frontend_framework",
                re.compile(r"react(?:@|[-/])([0-9]+\.[0-9]+\.[0-9]+)", re.IGNORECASE),
                re.compile(r"react(?:\.min)?\.js|react-dom", re.IGNORECASE),
            ),
            # Vue
            (
                "Vue",
                "frontend_framework",
                re.compile(r"vue(?:@|[-/])([0-9]+\.[0-9]+\.[0-9]+)", re.IGNORECASE),
                re.compile(r"vue(?:\.global)?(?:\.min)?\.js", re.IGNORECASE),
            ),
            # AngularJS (1.x)
            (
                "AngularJS",
                "frontend_framework",
                re.compile(
                    r"angular(?:js)?(?:@|[-/])([0-9]+\.[0-9]+\.[0-9]+)", re.IGNORECASE
                ),
                re.compile(r"angular(?:\.min)?\.js", re.IGNORECASE),
            ),
            # jQuery
            (
                "jQuery",
                "library",
                re.compile(r"jquery(?:@|[-/])([0-9]+\.[0-9]+\.[0-9]+)", re.IGNORECASE),
                re.compile(r"jquery(?:\.slim)?(?:\.min)?\.js", re.IGNORECASE),
            ),
        ]

    def match(self, scripts: List[str]) -> List[TechSignature]:
        """스크립트 URL에서 기술 스택 탐지.

        Args:
            scripts: 스크립트 URL 목록

        Returns:
            탐지된 기술 시그니처 목록
        """
        results: List[TechSignature] = []
        seen_techs: Set[str] = set()

        for script_url in scripts:
            for name, category, version_pattern, simple_pattern in self._patterns:
                if name in seen_techs:
                    continue

                # 버전 추출 시도
                version_match = version_pattern.search(script_url)
                if version_match:
                    results.append(
                        TechSignature(
                            name=name,
                            category=category,
                            version=version_match.group(1),
                            confidence=0.9,
                            evidence=["script_url"],
                        )
                    )
                    seen_techs.add(name)
                    continue

                # 단순 패턴 매칭
                if simple_pattern.search(script_url):
                    results.append(
                        TechSignature(
                            name=name,
                            category=category,
                            version=None,
                            confidence=0.8,
                            evidence=["script_url"],
                        )
                    )
                    seen_techs.add(name)

        return results


# ============================================================================
# GlobalVariableMatcher - 전역 변수 기반 탐지
# ============================================================================


class GlobalVariableMatcher:
    """JavaScript 전역 변수 기반 기술 탐지.

    window 객체의 전역 변수를 분석하여
    프론트엔드 프레임워크 및 라이브러리를 식별합니다.
    """

    def __init__(self) -> None:
        """초기화."""
        # 전역 변수 -> (기술명, 카테고리, 신뢰도)
        self._variable_map: Dict[str, Tuple[str, str, float]] = {
            # React
            "React": ("React", "frontend_framework", 0.95),
            "__REACT_DEVTOOLS_GLOBAL_HOOK__": ("React", "frontend_framework", 0.9),
            "__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED": (
                "React",
                "frontend_framework",
                0.85,
            ),
            # Vue
            "Vue": ("Vue", "frontend_framework", 0.95),
            "__VUE__": ("Vue", "frontend_framework", 0.9),
            "__VUE_DEVTOOLS_GLOBAL_HOOK__": ("Vue", "frontend_framework", 0.85),
            # Angular/AngularJS
            "angular": ("AngularJS", "frontend_framework", 0.9),
            "ng": ("Angular", "frontend_framework", 0.7),
            "getAllAngularRootElements": ("Angular", "frontend_framework", 0.9),
            "getAllAngularTestabilities": ("Angular", "frontend_framework", 0.85),
            # jQuery
            "jQuery": ("jQuery", "library", 0.95),
            "$": ("jQuery", "library", 0.6),  # 낮은 신뢰도 (다른 라이브러리도 사용)
        }

    def match(self, variables: List[str]) -> List[TechSignature]:
        """전역 변수에서 기술 스택 탐지.

        Args:
            variables: 전역 변수 이름 목록

        Returns:
            탐지된 기술 시그니처 목록
        """
        results: List[TechSignature] = []
        seen_techs: Set[str] = set()

        for var_name in variables:
            if var_name in self._variable_map:
                tech_name, category, confidence = self._variable_map[var_name]
                if tech_name not in seen_techs:
                    results.append(
                        TechSignature(
                            name=tech_name,
                            category=category,
                            version=None,
                            confidence=confidence,
                            evidence=["global_variable"],
                        )
                    )
                    seen_techs.add(tech_name)

        return results


# ============================================================================
# DomSignatureMatcher - DOM 속성 기반 탐지
# ============================================================================


class DomSignatureMatcher:
    """DOM 속성 및 패턴 기반 기술 탐지.

    HTML 문서의 속성, 클래스, 메타 태그 등을 분석하여
    프론트엔드 프레임워크, CMS 등을 식별합니다.
    """

    def __init__(self) -> None:
        """초기화."""
        # (기술명, 카테고리, 패턴, 버전 그룹 또는 None)
        self._dom_patterns: List[Tuple[str, str, re.Pattern[str], Optional[int]]] = [
            # React
            (
                "React",
                "frontend_framework",
                re.compile(r"data-reactroot", re.IGNORECASE),
                None,
            ),
            (
                "React",
                "frontend_framework",
                re.compile(r"data-reactid", re.IGNORECASE),
                None,
            ),
            (
                "React",
                "frontend_framework",
                re.compile(r"data-react-checksum", re.IGNORECASE),
                None,
            ),
            # Vue
            (
                "Vue",
                "frontend_framework",
                re.compile(r"\bv-cloak\b", re.IGNORECASE),
                None,
            ),
            (
                "Vue",
                "frontend_framework",
                re.compile(r"\bv-for\b", re.IGNORECASE),
                None,
            ),
            (
                "Vue",
                "frontend_framework",
                re.compile(r"\bv-if\b", re.IGNORECASE),
                None,
            ),
            (
                "Vue",
                "frontend_framework",
                re.compile(r"\bv-model\b", re.IGNORECASE),
                None,
            ),
            # Angular 2+
            (
                "Angular",
                "frontend_framework",
                re.compile(r'ng-version="([0-9.]+)"', re.IGNORECASE),
                1,
            ),
            (
                "Angular",
                "frontend_framework",
                re.compile(r"_ngcontent-", re.IGNORECASE),
                None,
            ),
            (
                "Angular",
                "frontend_framework",
                re.compile(r"_nghost-", re.IGNORECASE),
                None,
            ),
            # AngularJS
            (
                "AngularJS",
                "frontend_framework",
                re.compile(r"\bng-app\b", re.IGNORECASE),
                None,
            ),
            (
                "AngularJS",
                "frontend_framework",
                re.compile(r"\bng-controller\b", re.IGNORECASE),
                None,
            ),
            (
                "AngularJS",
                "frontend_framework",
                re.compile(r"\bng-model\b", re.IGNORECASE),
                None,
            ),
            # WordPress
            (
                "WordPress",
                "cms",
                re.compile(r"/wp-content/", re.IGNORECASE),
                None,
            ),
            (
                "WordPress",
                "cms",
                re.compile(r"/wp-includes/", re.IGNORECASE),
                None,
            ),
            (
                "WordPress",
                "cms",
                re.compile(
                    r'name="generator"[^>]*content="WordPress\s*([0-9.]+)?',
                    re.IGNORECASE,
                ),
                1,
            ),
            # Drupal
            (
                "Drupal",
                "cms",
                re.compile(r"/sites/default/files/", re.IGNORECASE),
                None,
            ),
            (
                "Drupal",
                "cms",
                re.compile(
                    r'name="generator"[^>]*content="Drupal\s*([0-9.]+)?',
                    re.IGNORECASE,
                ),
                1,
            ),
        ]

    def match(self, html_content: str) -> List[TechSignature]:
        """HTML 콘텐츠에서 기술 스택 탐지.

        Args:
            html_content: HTML 문서 내용

        Returns:
            탐지된 기술 시그니처 목록
        """
        if not html_content:
            return []

        results: List[TechSignature] = []
        seen_techs: Dict[str, TechSignature] = {}

        for name, category, pattern, version_group in self._dom_patterns:
            match = pattern.search(html_content)
            if match:
                version = None
                if version_group is not None and match.lastindex:
                    try:
                        version = match.group(version_group)
                    except IndexError:
                        pass

                # 같은 기술이 이미 있으면 버전 정보 업데이트
                if name in seen_techs:
                    existing = seen_techs[name]
                    if version and not existing.version:
                        existing_idx = results.index(existing)
                        results[existing_idx] = TechSignature(
                            name=name,
                            category=category,
                            version=version,
                            confidence=max(existing.confidence, 0.85),
                            evidence=existing.evidence + ["dom_attribute"],
                        )
                        seen_techs[name] = results[existing_idx]
                else:
                    sig = TechSignature(
                        name=name,
                        category=category,
                        version=version,
                        confidence=0.85,
                        evidence=["dom_attribute"],
                    )
                    results.append(sig)
                    seen_techs[name] = sig

        return results


# ============================================================================
# TechFingerprintModule
# ============================================================================


class TechFingerprintModule(BaseDiscoveryModule):
    """기술 스택 핑거프린팅 모듈.

    웹 애플리케이션의 기술 스택을 탐지합니다:
    - HTTP 헤더 분석 (Server, X-Powered-By, CDN 헤더)
    - 스크립트 URL 분석 (React, Vue, jQuery 등)
    - 전역 변수 분석
    - DOM 속성/패턴 분석

    Attributes:
        name: 모듈 이름 ("tech_fingerprint")
        profiles: 지원하는 스캔 프로필 (STANDARD, FULL)
    """

    def __init__(self) -> None:
        """모듈 초기화."""
        self._header_matcher = HeaderMatcher()
        self._script_matcher = ScriptMatcher()
        self._global_variable_matcher = GlobalVariableMatcher()
        self._dom_signature_matcher = DomSignatureMatcher()

    @property
    def name(self) -> str:
        """모듈 고유 이름."""
        return "tech_fingerprint"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필."""
        return {ScanProfile.STANDARD, ScanProfile.FULL}

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """기술 스택 탐지 수행.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 기술 스택 자산
        """
        crawl_data = context.crawl_data
        target_url = context.target_url

        # 모든 시그니처 수집
        all_signatures: Dict[str, List[TechSignature]] = {}

        # 1. 헤더 분석
        responses = crawl_data.get("responses", [])
        for response_data in responses:
            headers = response_data.get("headers", {})
            header_sigs = self._header_matcher.match(headers)
            for sig in header_sigs:
                self._add_signature(all_signatures, sig)

        # 2. 스크립트 URL 분석
        scripts = crawl_data.get("scripts", [])
        script_sigs = self._script_matcher.match(scripts)
        for sig in script_sigs:
            self._add_signature(all_signatures, sig)

        # 3. 전역 변수 분석
        global_vars = crawl_data.get("global_variables", [])
        var_sigs = self._global_variable_matcher.match(global_vars)
        for sig in var_sigs:
            self._add_signature(all_signatures, sig)

        # 4. DOM 속성 분석
        html_content = crawl_data.get("html_content", "")
        dom_sigs = self._dom_signature_matcher.match(html_content)
        for sig in dom_sigs:
            self._add_signature(all_signatures, sig)

        # 시그니처 통합 및 자산 생성
        for tech_name, signatures in all_signatures.items():
            merged_sig = self._merge_signatures(signatures)

            yield DiscoveredAsset(
                url=target_url,
                asset_type="technology",
                source=self.name,
                metadata={
                    "technology_name": merged_sig.name,
                    "category": merged_sig.category,
                    "version": merged_sig.version,
                    "confidence": merged_sig.confidence,
                    "evidence": merged_sig.evidence,
                },
            )

    def _add_signature(
        self, signatures: Dict[str, List[TechSignature]], sig: TechSignature
    ) -> None:
        """시그니처를 딕셔너리에 추가.

        Args:
            signatures: 기술명 -> 시그니처 목록 딕셔너리
            sig: 추가할 시그니처
        """
        if sig.name not in signatures:
            signatures[sig.name] = []
        signatures[sig.name].append(sig)

    def _merge_signatures(self, signatures: List[TechSignature]) -> TechSignature:
        """여러 시그니처를 하나로 통합.

        다중 증거 소스가 있을 경우 신뢰도를 높이고,
        버전 정보를 우선적으로 보존합니다.

        Args:
            signatures: 같은 기술에 대한 시그니처 목록

        Returns:
            통합된 시그니처
        """
        if not signatures:
            raise ValueError("signatures list cannot be empty")

        if len(signatures) == 1:
            return signatures[0]

        # 기본 정보는 첫 번째 시그니처에서 가져옴
        name = signatures[0].name
        category = signatures[0].category

        # 버전: 버전 정보가 있는 것을 우선
        version: Optional[str] = None
        for sig in signatures:
            if sig.version:
                version = sig.version
                break

        # 증거 목록 통합 (중복 제거)
        evidence: List[str] = []
        for sig in signatures:
            for ev in sig.evidence:
                if ev not in evidence:
                    evidence.append(ev)

        # 신뢰도 계산: 다중 증거 시 신뢰도 상승
        base_confidence = max(sig.confidence for sig in signatures)
        evidence_count = len(evidence)

        # 증거가 많을수록 신뢰도 증가 (최대 0.99)
        confidence_boost = min(0.05 * (evidence_count - 1), 0.1)
        final_confidence = min(base_confidence + confidence_boost, 0.99)

        return TechSignature(
            name=name,
            category=category,
            version=version,
            confidence=round(final_confidence, 2),
            evidence=evidence,
        )
