"""ConfigDiscoveryModule - 설정 파일 기반 자산 발견.

robots.txt, sitemap.xml, well-known 파일, source map 등을 파싱하여
자산을 발견합니다.

주요 컴포넌트:
- RobotsTxtParser: robots.txt 파싱
- SitemapParser: sitemap.xml 파싱
- WellKnownParser: security.txt, openid-configuration 파싱
- SourceMapDetector: JavaScript source map 탐지
"""

import logging
import re
import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile

logger = logging.getLogger(__name__)


# ============================================================================
# RobotsTxtParser
# ============================================================================


@dataclass
class RobotsTxtParseResult:
    """robots.txt 파싱 결과."""

    disallowed_paths: List[str] = field(default_factory=list)
    sitemap_urls: List[str] = field(default_factory=list)


class RobotsTxtParser:
    """robots.txt 파서.

    User-agent: * 에 해당하는 Disallow 규칙과 Sitemap URL을 추출합니다.
    """

    def parse(self, content: str) -> RobotsTxtParseResult:
        """robots.txt 내용을 파싱합니다.

        Args:
            content: robots.txt 파일 내용

        Returns:
            파싱 결과 (disallowed_paths, sitemap_urls)
        """
        result = RobotsTxtParseResult()

        if not content:
            return result

        is_relevant_user_agent = False

        for line in content.split("\n"):
            # 주석 제거
            line = re.sub(r"#.*$", "", line).strip()
            if not line:
                continue

            # 지시문 파싱
            match = re.match(r"^(\S+):\s*(.*)$", line, re.IGNORECASE)
            if not match:
                continue

            directive = match.group(1).lower()
            value = match.group(2).strip()

            if directive == "user-agent":
                # User-agent: * 인 경우만 처리
                is_relevant_user_agent = value == "*"

            elif directive == "disallow" and is_relevant_user_agent:
                if value:  # 빈 Disallow는 무시
                    result.disallowed_paths.append(value)

            elif directive == "sitemap":
                # Sitemap은 User-agent와 무관하게 처리
                result.sitemap_urls.append(value)

        return result


# ============================================================================
# SitemapParser
# ============================================================================


@dataclass
class SitemapParseResult:
    """sitemap.xml 파싱 결과."""

    urls: List[str] = field(default_factory=list)
    url_metadata: Dict[str, Dict[str, str]] = field(default_factory=dict)
    is_index: bool = False
    child_sitemaps: List[str] = field(default_factory=list)


class SitemapParser:
    """sitemap.xml 파서.

    일반 sitemap과 sitemap index 모두 지원합니다.
    """

    # XML 네임스페이스
    SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

    def __init__(self, max_depth: int = 3) -> None:
        """SitemapParser 초기화.

        Args:
            max_depth: sitemap index 재귀 탐색 최대 깊이
        """
        self.max_depth = max_depth

    def parse(self, content: str) -> SitemapParseResult:
        """sitemap XML 내용을 파싱합니다.

        Args:
            content: sitemap.xml 파일 내용

        Returns:
            파싱 결과
        """
        result = SitemapParseResult()

        if not content:
            return result

        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            logger.warning("Failed to parse sitemap XML")
            return result

        # 네임스페이스 처리
        ns = {"sm": self.SITEMAP_NS}

        # sitemap index인지 확인
        if (
            root.tag == f"{{{self.SITEMAP_NS}}}sitemapindex"
            or root.tag == "sitemapindex"
        ):
            result.is_index = True
            self._parse_sitemap_index(root, result, ns)
        else:
            self._parse_urlset(root, result, ns)

        return result

    def _parse_sitemap_index(
        self, root: ET.Element, result: SitemapParseResult, ns: Dict[str, str]
    ) -> None:
        """sitemap index 파싱."""
        # 네임스페이스 있는 경우
        for sitemap in root.findall("sm:sitemap", ns):
            loc = sitemap.find("sm:loc", ns)
            if loc is not None and loc.text:
                result.child_sitemaps.append(loc.text.strip())

        # 네임스페이스 없는 경우
        for sitemap in root.findall("sitemap"):
            loc = sitemap.find("loc")
            if loc is not None and loc.text:
                result.child_sitemaps.append(loc.text.strip())

    def _parse_urlset(
        self, root: ET.Element, result: SitemapParseResult, ns: Dict[str, str]
    ) -> None:
        """urlset 파싱."""
        # 네임스페이스 있는 경우
        for url_elem in root.findall("sm:url", ns):
            self._extract_url_info(url_elem, result, ns, use_ns=True)

        # 네임스페이스 없는 경우
        for url_elem in root.findall("url"):
            self._extract_url_info(url_elem, result, ns, use_ns=False)

    def _extract_url_info(
        self,
        url_elem: ET.Element,
        result: SitemapParseResult,
        ns: Dict[str, str],
        use_ns: bool,
    ) -> None:
        """URL 정보 추출."""
        if use_ns:
            loc = url_elem.find("sm:loc", ns)
            lastmod = url_elem.find("sm:lastmod", ns)
            changefreq = url_elem.find("sm:changefreq", ns)
            priority = url_elem.find("sm:priority", ns)
        else:
            loc = url_elem.find("loc")
            lastmod = url_elem.find("lastmod")
            changefreq = url_elem.find("changefreq")
            priority = url_elem.find("priority")

        if loc is not None and loc.text:
            url = loc.text.strip()
            result.urls.append(url)

            # 메타데이터 추출
            metadata: Dict[str, str] = {}
            if lastmod is not None and lastmod.text:
                metadata["lastmod"] = lastmod.text.strip()
            if changefreq is not None and changefreq.text:
                metadata["changefreq"] = changefreq.text.strip()
            if priority is not None and priority.text:
                metadata["priority"] = priority.text.strip()

            if metadata:
                result.url_metadata[url] = metadata


# ============================================================================
# WellKnownParser
# ============================================================================


@dataclass
class SecurityTxtResult:
    """security.txt 파싱 결과."""

    contact: str = ""
    expires: str = ""
    encryption: str = ""
    acknowledgments: str = ""
    policy: str = ""
    hiring: str = ""
    has_pgp_signature: bool = False


@dataclass
class OpenIdConfigResult:
    """openid-configuration 파싱 결과."""

    issuer: str = ""
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    userinfo_endpoint: str = ""
    jwks_uri: str = ""


class WellKnownParser:
    """well-known 파일 파서.

    지원 파일:
    - /.well-known/security.txt
    - /.well-known/openid-configuration
    """

    def parse_security_txt(self, content: str) -> SecurityTxtResult:
        """security.txt 내용을 파싱합니다.

        Args:
            content: security.txt 파일 내용

        Returns:
            파싱 결과
        """
        result = SecurityTxtResult()

        if not content:
            return result

        # PGP 서명 확인
        if "-----BEGIN PGP SIGNED MESSAGE-----" in content:
            result.has_pgp_signature = True
            # PGP 서명 블록에서 실제 내용 추출
            content = self._extract_pgp_content(content)

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 지시문 파싱
            match = re.match(r"^(\S+):\s*(.*)$", line, re.IGNORECASE)
            if not match:
                continue

            directive = match.group(1).lower()
            value = match.group(2).strip()

            if directive == "contact":
                result.contact = value
            elif directive == "expires":
                result.expires = value
            elif directive == "encryption":
                result.encryption = value
            elif directive == "acknowledgments":
                result.acknowledgments = value
            elif directive == "policy":
                result.policy = value
            elif directive == "hiring":
                result.hiring = value

        return result

    def _extract_pgp_content(self, content: str) -> str:
        """PGP 서명된 메시지에서 실제 내용 추출."""
        lines = content.split("\n")
        result_lines = []
        in_content = False

        for line in lines:
            if line.startswith("-----BEGIN PGP SIGNATURE-----"):
                break
            if in_content:
                result_lines.append(line)
            if line.startswith("Hash:"):
                # Hash: 다음 빈 줄 이후부터 내용
                in_content = True

        # 첫 빈 줄 제거
        while result_lines and not result_lines[0].strip():
            result_lines.pop(0)

        return "\n".join(result_lines)

    def parse_openid_config(self, config: Dict[str, Any]) -> OpenIdConfigResult:
        """openid-configuration JSON을 파싱합니다.

        Args:
            config: openid-configuration JSON 딕셔너리

        Returns:
            파싱 결과
        """
        return OpenIdConfigResult(
            issuer=config.get("issuer", ""),
            authorization_endpoint=config.get("authorization_endpoint", ""),
            token_endpoint=config.get("token_endpoint", ""),
            userinfo_endpoint=config.get("userinfo_endpoint", ""),
            jwks_uri=config.get("jwks_uri", ""),
        )


# ============================================================================
# SourceMapDetector
# ============================================================================


@dataclass
class SourceMapResult:
    """source map 탐지 결과."""

    has_source_map: bool = False
    source_map_url: str = ""
    is_information_disclosure_risk: bool = False


class SourceMapDetector:
    """JavaScript source map 탐지기.

    //# sourceMappingURL= 주석을 탐지하여 source map 정보를 추출합니다.
    Source map은 잠재적인 정보 노출 위험으로 표시됩니다.
    """

    # Source map URL 패턴
    SOURCE_MAP_PATTERN = re.compile(
        r"//[#@]\s*sourceMappingURL\s*=\s*(\S+)", re.IGNORECASE
    )

    def detect(self, content: str) -> SourceMapResult:
        """JavaScript 내용에서 source map을 탐지합니다.

        Args:
            content: JavaScript 파일 내용

        Returns:
            탐지 결과
        """
        result = SourceMapResult()

        if not content:
            return result

        match = self.SOURCE_MAP_PATTERN.search(content)
        if match:
            result.has_source_map = True
            result.source_map_url = match.group(1)
            result.is_information_disclosure_risk = True

        return result


# ============================================================================
# ConfigDiscoveryModule
# ============================================================================


class ConfigDiscoveryModule(BaseDiscoveryModule):
    """설정 파일 기반 자산 발견 모듈.

    다음 파일들을 파싱하여 자산을 발견합니다:
    - robots.txt: Disallow 경로, Sitemap URL
    - sitemap.xml: 페이지 URL
    - /.well-known/security.txt: 보안 관련 URL
    - /.well-known/openid-configuration: OAuth 엔드포인트
    """

    def __init__(self) -> None:
        """ConfigDiscoveryModule 초기화."""
        self._robots_parser = RobotsTxtParser()
        self._sitemap_parser = SitemapParser()
        self._wellknown_parser = WellKnownParser()
        self._source_map_detector = SourceMapDetector()

    @property
    def name(self) -> str:
        """모듈 이름."""
        return "config_discovery"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필."""
        return {ScanProfile.STANDARD, ScanProfile.FULL}

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """설정 파일 기반 자산 발견 수행.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 자산
        """
        # robots.txt 처리
        async for asset in self._discover_from_robots(context):
            yield asset

        # sitemap.xml 처리
        async for asset in self._discover_from_sitemap(context):
            yield asset

        # well-known 파일 처리
        async for asset in self._discover_from_wellknown(context):
            yield asset

    async def _discover_from_robots(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """robots.txt에서 자산 발견."""
        robots_url = f"{context.target_url.rstrip('/')}/robots.txt"

        try:
            response = await context.http_client.get(robots_url)

            if response.status_code == 404:
                logger.warning("robots.txt not found", extra={"url": robots_url})
                return

            if response.status_code != 200:
                return

            content = response.text
            result = self._robots_parser.parse(content)

            # Disallow 경로를 자산으로 등록
            for path in result.disallowed_paths:
                # 와일드카드 패턴 제외
                if "*" not in path and "$" not in path:
                    full_url = f"{context.target_url.rstrip('/')}{path}"
                    yield DiscoveredAsset(
                        url=full_url,
                        asset_type="endpoint",
                        source="robots_txt",
                        metadata={
                            "disallowed": True,
                            "path": path,
                        },
                    )

            # Sitemap URL 저장 (나중에 처리)
            self._sitemap_urls = result.sitemap_urls

        except Exception as e:
            logger.warning(
                "Failed to fetch robots.txt",
                extra={"url": robots_url, "error": str(e)},
            )

    async def _discover_from_sitemap(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """sitemap.xml에서 자산 발견."""
        # robots.txt에서 발견된 sitemap URL 사용
        sitemap_urls = getattr(self, "_sitemap_urls", [])

        # 기본 sitemap URL 추가
        default_sitemap = f"{context.target_url.rstrip('/')}/sitemap.xml"
        if default_sitemap not in sitemap_urls:
            sitemap_urls = [default_sitemap] + sitemap_urls

        visited: Set[str] = set()

        async for asset in self._process_sitemaps(context, sitemap_urls, visited, 0):
            yield asset

    async def _process_sitemaps(
        self,
        context: DiscoveryContext,
        sitemap_urls: List[str],
        visited: Set[str],
        depth: int,
    ) -> AsyncIterator[DiscoveredAsset]:
        """sitemap URL 목록 처리."""
        max_depth = self._sitemap_parser.max_depth

        for sitemap_url in sitemap_urls:
            if sitemap_url in visited:
                continue
            visited.add(sitemap_url)

            try:
                response = await context.http_client.get(sitemap_url)

                if response.status_code != 200:
                    continue

                content = response.text
                result = self._sitemap_parser.parse(content)

                # 일반 URL 처리
                for url in result.urls:
                    yield DiscoveredAsset(
                        url=url,
                        asset_type="page",
                        source="sitemap",
                        metadata=result.url_metadata.get(url, {}),
                    )

                # sitemap index인 경우 재귀 처리
                if result.is_index and depth < max_depth:
                    async for asset in self._process_sitemaps(
                        context, result.child_sitemaps, visited, depth + 1
                    ):
                        yield asset

            except Exception as e:
                logger.warning(
                    "Failed to fetch sitemap",
                    extra={"url": sitemap_url, "error": str(e)},
                )

    async def _discover_from_wellknown(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """well-known 파일에서 자산 발견."""
        base_url = context.target_url.rstrip("/")

        # security.txt 처리
        security_txt_url = f"{base_url}/.well-known/security.txt"
        try:
            response = await context.http_client.get(security_txt_url)
            if response.status_code == 200:
                result = self._wellknown_parser.parse_security_txt(response.text)
                if result.policy:
                    yield DiscoveredAsset(
                        url=result.policy,
                        asset_type="policy",
                        source="security_txt",
                        metadata={"type": "security_policy"},
                    )
                if result.hiring:
                    yield DiscoveredAsset(
                        url=result.hiring,
                        asset_type="page",
                        source="security_txt",
                        metadata={"type": "hiring"},
                    )
        except Exception as e:
            logger.debug(
                "Failed to fetch security.txt",
                extra={"url": security_txt_url, "error": str(e)},
            )

        # openid-configuration 처리
        openid_url = f"{base_url}/.well-known/openid-configuration"
        try:
            response = await context.http_client.get(openid_url)
            if response.status_code == 200:
                import json

                config = json.loads(response.text)
                openid_result = self._wellknown_parser.parse_openid_config(config)

                if openid_result.authorization_endpoint:
                    yield DiscoveredAsset(
                        url=openid_result.authorization_endpoint,
                        asset_type="endpoint",
                        source="openid_config",
                        metadata={"type": "authorization_endpoint"},
                    )
                if openid_result.token_endpoint:
                    yield DiscoveredAsset(
                        url=openid_result.token_endpoint,
                        asset_type="endpoint",
                        source="openid_config",
                        metadata={"type": "token_endpoint"},
                    )
                if openid_result.jwks_uri:
                    yield DiscoveredAsset(
                        url=openid_result.jwks_uri,
                        asset_type="endpoint",
                        source="openid_config",
                        metadata={"type": "jwks"},
                    )
        except Exception as e:
            logger.debug(
                "Failed to fetch openid-configuration",
                extra={"url": openid_url, "error": str(e)},
            )
