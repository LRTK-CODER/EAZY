"""HTML Element Parser Module.

HTML 문서에서 URL 및 자산을 추출하는 Discovery 모듈입니다.
- form 요소 파싱 (action, method, hidden inputs, CSRF)
- script 요소 파싱 (src, inline URL)
- link 요소 파싱 (href, rel types)
- media 요소 파싱 (img, video, audio, source)
- meta 요소 파싱 (refresh, Open Graph)
- data-* 속성 URL 파싱
- base href URL 해결
"""

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class FormInfo:
    """Form 정보."""

    action: str
    method: str
    hidden_inputs: Dict[str, str] = field(default_factory=dict)
    has_csrf_token: bool = False
    csrf_tokens: Dict[str, str] = field(default_factory=dict)
    inputs: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class FormParseResult:
    """Form 파싱 결과."""

    forms: List[FormInfo] = field(default_factory=list)


@dataclass
class ScriptInfo:
    """Script 정보."""

    src: str
    integrity: Optional[str] = None
    crossorigin: Optional[str] = None
    defer: bool = False
    async_: bool = False
    type_: Optional[str] = None


@dataclass
class ScriptParseResult:
    """Script 파싱 결과."""

    scripts: List[ScriptInfo] = field(default_factory=list)
    inline_urls: List[str] = field(default_factory=list)


@dataclass
class LinkInfo:
    """Link 정보."""

    href: str
    rel: str
    as_type: Optional[str] = None
    type_: Optional[str] = None
    crossorigin: Optional[str] = None


@dataclass
class LinkParseResult:
    """Link 파싱 결과."""

    links: List[LinkInfo] = field(default_factory=list)


@dataclass
class ImageInfo:
    """Image 정보."""

    src: Optional[str] = None
    srcset: List[str] = field(default_factory=list)
    alt: Optional[str] = None


@dataclass
class VideoInfo:
    """Video 정보."""

    src: Optional[str] = None
    poster: Optional[str] = None
    sources: List[str] = field(default_factory=list)


@dataclass
class AudioInfo:
    """Audio 정보."""

    src: Optional[str] = None
    sources: List[str] = field(default_factory=list)


@dataclass
class MediaParseResult:
    """Media 파싱 결과."""

    images: List[ImageInfo] = field(default_factory=list)
    videos: List[VideoInfo] = field(default_factory=list)
    audios: List[AudioInfo] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    tracks: List[str] = field(default_factory=list)

    def get_all_urls(self) -> List[str]:
        """모든 URL 반환."""
        urls: List[str] = []

        for img in self.images:
            if img.src:
                urls.append(img.src)
            urls.extend(img.srcset)

        for video in self.videos:
            if video.src:
                urls.append(video.src)
            if video.poster:
                urls.append(video.poster)
            urls.extend(video.sources)

        for audio in self.audios:
            if audio.src:
                urls.append(audio.src)
            urls.extend(audio.sources)

        urls.extend(self.sources)
        urls.extend(self.tracks)

        return urls


@dataclass
class MetaParseResult:
    """Meta 파싱 결과."""

    refresh_urls: List[str] = field(default_factory=list)
    og_data: Dict[str, str] = field(default_factory=dict)
    og_urls: List[str] = field(default_factory=list)
    twitter_urls: List[str] = field(default_factory=list)


@dataclass
class DataAttrParseResult:
    """Data 속성 파싱 결과."""

    urls: List[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """전체 파싱 결과."""

    forms: List[FormInfo] = field(default_factory=list)
    scripts: List[ScriptInfo] = field(default_factory=list)
    inline_urls: List[str] = field(default_factory=list)
    links: List[LinkInfo] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)
    videos: List[VideoInfo] = field(default_factory=list)
    audios: List[AudioInfo] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    tracks: List[str] = field(default_factory=list)
    refresh_urls: List[str] = field(default_factory=list)
    og_urls: List[str] = field(default_factory=list)
    twitter_urls: List[str] = field(default_factory=list)
    data_attr_urls: List[str] = field(default_factory=list)

    def get_all_urls(self) -> List[str]:
        """모든 URL 반환."""
        urls: List[str] = []

        for form in self.forms:
            urls.append(form.action)

        for script in self.scripts:
            urls.append(script.src)

        urls.extend(self.inline_urls)

        for link in self.links:
            urls.append(link.href)

        for img in self.images:
            if img.src:
                urls.append(img.src)
            urls.extend(img.srcset)

        for video in self.videos:
            if video.src:
                urls.append(video.src)
            if video.poster:
                urls.append(video.poster)
            urls.extend(video.sources)

        for audio in self.audios:
            if audio.src:
                urls.append(audio.src)
            urls.extend(audio.sources)

        urls.extend(self.sources)
        urls.extend(self.tracks)
        urls.extend(self.refresh_urls)
        urls.extend(self.og_urls)
        urls.extend(self.twitter_urls)
        urls.extend(self.data_attr_urls)

        return urls


# ============================================================================
# Parsers
# ============================================================================


class FormParser:
    """Form 요소 파서."""

    # 일반적인 CSRF 토큰 이름
    CSRF_TOKEN_NAMES = {
        "_csrf",
        "csrf_token",
        "csrf",
        "_token",
        "authenticity_token",
        "csrfmiddlewaretoken",
        "__requestverificationtoken",
        "anticsrf",
        "xsrf_token",
        "_xsrf",
    }

    def __init__(self, base_url: str) -> None:
        """Initialize FormParser.

        Args:
            base_url: 기본 URL (상대 URL 해결용)
        """
        self.base_url = base_url

    def parse(self, html: str) -> FormParseResult:
        """HTML에서 form 요소 파싱.

        Args:
            html: HTML 문자열

        Returns:
            FormParseResult
        """
        soup = BeautifulSoup(html, "html.parser")
        forms: List[FormInfo] = []

        for form_tag in soup.find_all("form"):
            form_info = self._parse_form(form_tag)
            forms.append(form_info)

        return FormParseResult(forms=forms)

    def _parse_form(self, form_tag: Tag) -> FormInfo:
        """단일 form 태그 파싱."""
        # Action URL 추출 및 해결
        action = form_tag.get("action", "")
        if action == "" or action is None:
            action = self.base_url
        else:
            action = urljoin(self.base_url, str(action))

        # Method 추출 (기본값 GET)
        method = form_tag.get("method", "GET")
        method = str(method).upper()

        # Hidden inputs 추출
        hidden_inputs: Dict[str, str] = {}
        csrf_tokens: Dict[str, str] = {}
        has_csrf_token = False

        for input_tag in form_tag.find_all("input", type="hidden"):
            name = input_tag.get("name", "")
            value = input_tag.get("value", "")

            if name:
                name = str(name)
                value = str(value) if value else ""
                hidden_inputs[name] = value

                # CSRF 토큰 확인
                if name.lower() in self.CSRF_TOKEN_NAMES:
                    has_csrf_token = True
                    csrf_tokens[name] = value

        return FormInfo(
            action=action,
            method=method,
            hidden_inputs=hidden_inputs,
            has_csrf_token=has_csrf_token,
            csrf_tokens=csrf_tokens,
        )


class ScriptParser:
    """Script 요소 파서."""

    # URL 패턴 (인라인 스크립트 내)
    URL_PATTERNS = [
        # 문자열 내 URL
        r'["\']((https?://|wss?://)[^"\']+)["\']',
        # 상대 URL (경로로 시작)
        r'["\'](/[a-zA-Z0-9_\-./]+)["\']',
    ]

    def __init__(self, base_url: str) -> None:
        """Initialize ScriptParser.

        Args:
            base_url: 기본 URL (상대 URL 해결용)
        """
        self.base_url = base_url
        self._url_patterns = [re.compile(p) for p in self.URL_PATTERNS]

    def parse(self, html: str) -> ScriptParseResult:
        """HTML에서 script 요소 파싱.

        Args:
            html: HTML 문자열

        Returns:
            ScriptParseResult
        """
        soup = BeautifulSoup(html, "html.parser")
        scripts: List[ScriptInfo] = []
        inline_urls: List[str] = []

        for script_tag in soup.find_all("script"):
            src = script_tag.get("src")

            if src:
                # 외부 스크립트
                script_info = self._parse_external_script(script_tag)
                scripts.append(script_info)
            else:
                # 인라인 스크립트
                content = script_tag.string
                if content:
                    urls = self._extract_inline_urls(str(content))
                    inline_urls.extend(urls)

        return ScriptParseResult(scripts=scripts, inline_urls=inline_urls)

    def _parse_external_script(self, script_tag: Tag) -> ScriptInfo:
        """외부 스크립트 태그 파싱."""
        src = script_tag.get("src", "")
        src = urljoin(self.base_url, str(src))

        integrity = script_tag.get("integrity")
        crossorigin = script_tag.get("crossorigin")
        type_ = script_tag.get("type")

        return ScriptInfo(
            src=src,
            integrity=str(integrity) if integrity else None,
            crossorigin=str(crossorigin) if crossorigin else None,
            defer=script_tag.has_attr("defer"),
            async_=script_tag.has_attr("async"),
            type_=str(type_) if type_ else None,
        )

    def _extract_inline_urls(self, content: str) -> List[str]:
        """인라인 스크립트에서 URL 추출."""
        urls: List[str] = []

        for pattern in self._url_patterns:
            matches = pattern.findall(content)
            for match in matches:
                if isinstance(match, tuple):
                    url = match[0]
                else:
                    url = match

                # 유효한 URL인지 확인
                if url and not url.startswith("//"):
                    urls.append(url)

        return urls


class LinkParser:
    """Link 요소 파서."""

    def __init__(self, base_url: str) -> None:
        """Initialize LinkParser.

        Args:
            base_url: 기본 URL (상대 URL 해결용)
        """
        self.base_url = base_url

    def parse(self, html: str) -> LinkParseResult:
        """HTML에서 link 요소 파싱.

        Args:
            html: HTML 문자열

        Returns:
            LinkParseResult
        """
        soup = BeautifulSoup(html, "html.parser")
        links: List[LinkInfo] = []

        for link_tag in soup.find_all("link"):
            href = link_tag.get("href")
            if href:
                link_info = self._parse_link(link_tag)
                links.append(link_info)

        return LinkParseResult(links=links)

    def _parse_link(self, link_tag: Tag) -> LinkInfo:
        """단일 link 태그 파싱."""
        href = link_tag.get("href", "")
        href = urljoin(self.base_url, str(href))

        rel_attr = link_tag.get("rel")
        if rel_attr is None:
            rel = ""
        elif isinstance(rel_attr, list):
            rel = rel_attr[0] if rel_attr else ""
        else:
            rel = str(rel_attr)

        as_type = link_tag.get("as")
        type_ = link_tag.get("type")
        crossorigin = link_tag.get("crossorigin")

        return LinkInfo(
            href=href,
            rel=str(rel),
            as_type=str(as_type) if as_type else None,
            type_=str(type_) if type_ else None,
            crossorigin=str(crossorigin) if crossorigin else None,
        )


class MediaParser:
    """Media 요소 파서 (img, video, audio, source, track)."""

    def __init__(self, base_url: str) -> None:
        """Initialize MediaParser.

        Args:
            base_url: 기본 URL (상대 URL 해결용)
        """
        self.base_url = base_url

    def parse(self, html: str) -> MediaParseResult:
        """HTML에서 media 요소 파싱.

        Args:
            html: HTML 문자열

        Returns:
            MediaParseResult
        """
        soup = BeautifulSoup(html, "html.parser")

        images = self._parse_images(soup)
        videos = self._parse_videos(soup)
        audios = self._parse_audios(soup)
        sources = self._parse_standalone_sources(soup)
        tracks = self._parse_tracks(soup)

        return MediaParseResult(
            images=images,
            videos=videos,
            audios=audios,
            sources=sources,
            tracks=tracks,
        )

    def _parse_images(self, soup: BeautifulSoup) -> List[ImageInfo]:
        """img 태그 파싱."""
        images: List[ImageInfo] = []

        for img_tag in soup.find_all("img"):
            src_attr = img_tag.get("src")
            src: Optional[str] = None
            if src_attr:
                src = urljoin(self.base_url, str(src_attr))

            srcset = img_tag.get("srcset")
            srcset_urls: List[str] = []
            if srcset:
                srcset_urls = self._parse_srcset(str(srcset))

            alt_attr = img_tag.get("alt")
            alt = str(alt_attr) if alt_attr else None

            images.append(ImageInfo(src=src, srcset=srcset_urls, alt=alt))

        # picture > source 도 처리
        for picture in soup.find_all("picture"):
            for source in picture.find_all("source"):
                srcset = source.get("srcset")
                if srcset:
                    srcset_urls = self._parse_srcset(str(srcset))
                    images.append(ImageInfo(srcset=srcset_urls))

        return images

    def _parse_srcset(self, srcset: str) -> List[str]:
        """srcset 속성 파싱."""
        urls: List[str] = []

        # srcset 형식: "url1 1x, url2 2x" 또는 "url1 100w, url2 200w"
        parts = srcset.split(",")
        for part in parts:
            part = part.strip()
            if part:
                # URL과 디스크립터 분리
                tokens = part.split()
                if tokens:
                    url = urljoin(self.base_url, tokens[0])
                    urls.append(url)

        return urls

    def _parse_videos(self, soup: BeautifulSoup) -> List[VideoInfo]:
        """video 태그 파싱."""
        videos: List[VideoInfo] = []

        for video_tag in soup.find_all("video"):
            src_attr = video_tag.get("src")
            src: Optional[str] = None
            if src_attr:
                src = urljoin(self.base_url, str(src_attr))

            poster_attr = video_tag.get("poster")
            poster: Optional[str] = None
            if poster_attr:
                poster = urljoin(self.base_url, str(poster_attr))

            sources: List[str] = []
            for source in video_tag.find_all("source"):
                source_src = source.get("src")
                if source_src:
                    sources.append(urljoin(self.base_url, str(source_src)))

            videos.append(VideoInfo(src=src, poster=poster, sources=sources))

        return videos

    def _parse_audios(self, soup: BeautifulSoup) -> List[AudioInfo]:
        """audio 태그 파싱."""
        audios: List[AudioInfo] = []

        for audio_tag in soup.find_all("audio"):
            src_attr = audio_tag.get("src")
            src: Optional[str] = None
            if src_attr:
                src = urljoin(self.base_url, str(src_attr))

            sources: List[str] = []
            for source in audio_tag.find_all("source"):
                source_src = source.get("src")
                if source_src:
                    sources.append(urljoin(self.base_url, str(source_src)))

            audios.append(AudioInfo(src=src, sources=sources))

        return audios

    def _parse_standalone_sources(self, soup: BeautifulSoup) -> List[str]:
        """video/audio 외부의 source 태그 파싱."""
        sources: List[str] = []

        # picture 내의 source는 _parse_images에서 처리
        # video/audio 내의 source는 각각의 메서드에서 처리
        # 여기서는 독립적인 source만 처리 (거의 없지만 방어적 코드)

        return sources

    def _parse_tracks(self, soup: BeautifulSoup) -> List[str]:
        """track 태그 파싱."""
        tracks: List[str] = []

        for track_tag in soup.find_all("track"):
            src = track_tag.get("src")
            if src:
                tracks.append(urljoin(self.base_url, str(src)))

        return tracks

    def get_all_urls(self) -> List[str]:
        """모든 URL 반환 (parse 결과에서 호출)."""
        # 이 메서드는 parse 결과의 MediaParseResult에서 사용
        return []


class MetaParser:
    """Meta 요소 파서."""

    # meta refresh URL 패턴
    REFRESH_URL_PATTERN = re.compile(
        r"(?:url\s*=\s*['\"]?)([^'\">\s]+)",
        re.IGNORECASE,
    )

    # OG URL 속성들
    OG_URL_PROPERTIES = {"og:image", "og:url", "og:video", "og:audio", "og:image:url"}

    # Twitter URL 속성들
    TWITTER_URL_NAMES = {"twitter:image", "twitter:player", "twitter:image:src"}

    def __init__(self, base_url: str) -> None:
        """Initialize MetaParser.

        Args:
            base_url: 기본 URL (상대 URL 해결용)
        """
        self.base_url = base_url

    def parse(self, html: str) -> MetaParseResult:
        """HTML에서 meta 요소 파싱.

        Args:
            html: HTML 문자열

        Returns:
            MetaParseResult
        """
        soup = BeautifulSoup(html, "html.parser")

        refresh_urls = self._parse_refresh(soup)
        og_data, og_urls = self._parse_og(soup)
        twitter_urls = self._parse_twitter(soup)

        return MetaParseResult(
            refresh_urls=refresh_urls,
            og_data=og_data,
            og_urls=og_urls,
            twitter_urls=twitter_urls,
        )

    def _parse_refresh(self, soup: BeautifulSoup) -> List[str]:
        """meta refresh URL 파싱."""
        urls: List[str] = []

        for meta in soup.find_all(
            "meta", attrs={"http-equiv": re.compile("refresh", re.I)}
        ):
            content = meta.get("content", "")
            if content:
                match = self.REFRESH_URL_PATTERN.search(str(content))
                if match:
                    url = match.group(1)
                    url = urljoin(self.base_url, url)
                    urls.append(url)

        return urls

    def _parse_og(self, soup: BeautifulSoup) -> tuple[Dict[str, str], List[str]]:
        """Open Graph 태그 파싱."""
        og_data: Dict[str, str] = {}
        og_urls: List[str] = []

        for meta in soup.find_all("meta", attrs={"property": re.compile("^og:", re.I)}):
            property_name = meta.get("property", "")
            content = meta.get("content", "")

            if property_name and content:
                property_name = str(property_name)
                content = str(content)
                og_data[property_name] = content

                # URL 속성인 경우
                if property_name.lower() in {p.lower() for p in self.OG_URL_PROPERTIES}:
                    og_urls.append(content)

        return og_data, og_urls

    def _parse_twitter(self, soup: BeautifulSoup) -> List[str]:
        """Twitter Card 태그 파싱."""
        twitter_urls: List[str] = []

        for meta in soup.find_all(
            "meta", attrs={"name": re.compile("^twitter:", re.I)}
        ):
            name = meta.get("name", "")
            content = meta.get("content", "")

            if name and content:
                name = str(name)
                content = str(content)

                if name.lower() in {n.lower() for n in self.TWITTER_URL_NAMES}:
                    twitter_urls.append(content)

        return twitter_urls


class DataAttrParser:
    """Data 속성 파서."""

    # URL로 보이는 data 속성 이름 패턴
    URL_ATTR_PATTERNS = [
        re.compile(r"^data-.*url.*$", re.I),
        re.compile(r"^data-.*href.*$", re.I),
        re.compile(r"^data-.*src.*$", re.I),
        re.compile(r"^data-.*endpoint.*$", re.I),
        re.compile(r"^data-.*api.*$", re.I),
        re.compile(r"^data-.*callback.*$", re.I),
    ]

    # URL 패턴 (값 내에서)
    URL_VALUE_PATTERN = re.compile(r'(https?://[^\s"\'<>]+|/[a-zA-Z0-9_\-./]+)')

    def __init__(self, base_url: str) -> None:
        """Initialize DataAttrParser.

        Args:
            base_url: 기본 URL (상대 URL 해결용)
        """
        self.base_url = base_url

    def parse(self, html: str) -> DataAttrParseResult:
        """HTML에서 data 속성 파싱.

        Args:
            html: HTML 문자열

        Returns:
            DataAttrParseResult
        """
        soup = BeautifulSoup(html, "html.parser")
        urls: List[str] = []

        for tag in soup.find_all(True):  # 모든 태그
            if not hasattr(tag, "attrs"):
                continue

            for attr_name, attr_value in tag.attrs.items():
                if not attr_name.startswith("data-"):
                    continue

                # URL 속성 이름 패턴 확인
                is_url_attr = any(p.match(attr_name) for p in self.URL_ATTR_PATTERNS)

                if is_url_attr and attr_value:
                    value = str(attr_value)
                    # 절대 또는 상대 URL인 경우
                    if value.startswith(("http://", "https://", "/")):
                        urls.append(urljoin(self.base_url, value))
                    # JSON 값인 경우
                    elif value.startswith("{") or value.startswith("["):
                        json_urls = self._extract_urls_from_json(value)
                        urls.extend(json_urls)

        # JSON 데이터가 있는 script 태그도 처리
        for script in soup.find_all("script", type="application/json"):
            content = script.string
            if content:
                json_urls = self._extract_urls_from_json(str(content))
                urls.extend(json_urls)

        # data-config 같은 JSON 속성도 처리
        for tag in soup.find_all(True):
            if not hasattr(tag, "attrs"):
                continue

            for attr_name, attr_value in tag.attrs.items():
                if not attr_name.startswith("data-"):
                    continue

                if attr_value and isinstance(attr_value, str):
                    if attr_value.startswith("{") or attr_value.startswith("["):
                        json_urls = self._extract_urls_from_json(attr_value)
                        urls.extend(json_urls)

        return DataAttrParseResult(urls=list(set(urls)))  # 중복 제거

    def _extract_urls_from_json(self, json_str: str) -> List[str]:
        """JSON 문자열에서 URL 추출."""
        urls: List[str] = []

        try:
            data = json.loads(json_str)
            urls = self._extract_urls_from_value(data)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 정규식으로 추출
            matches = self.URL_VALUE_PATTERN.findall(json_str)
            for match in matches:
                urls.append(urljoin(self.base_url, match))

        return urls

    def _extract_urls_from_value(self, value: Any) -> List[str]:
        """값에서 재귀적으로 URL 추출."""
        urls: List[str] = []

        if isinstance(value, str):
            if value.startswith(("http://", "https://", "/")):
                urls.append(urljoin(self.base_url, value))
        elif isinstance(value, dict):
            for v in value.values():
                urls.extend(self._extract_urls_from_value(v))
        elif isinstance(value, list):
            for item in value:
                urls.extend(self._extract_urls_from_value(item))

        return urls


# ============================================================================
# Main Module
# ============================================================================


class HtmlElementParserModule(BaseDiscoveryModule):
    """HTML Element Parser Discovery 모듈.

    HTML 문서에서 다양한 요소들을 파싱하여 URL과 자산을 추출합니다.
    """

    @property
    def name(self) -> str:
        """모듈 고유 이름."""
        return "html_element_parser"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필 집합."""
        return {ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL}

    def parse_with_base(self, html: str, page_url: str) -> ParseResult:
        """base href를 고려하여 HTML 파싱.

        Args:
            html: HTML 문자열
            page_url: 현재 페이지 URL

        Returns:
            ParseResult
        """
        soup = BeautifulSoup(html, "html.parser")

        # base href 확인
        base_tag = soup.find("base", href=True)
        if base_tag:
            base_href = base_tag.get("href", "")
            base_url = urljoin(page_url, str(base_href))
        else:
            base_url = page_url

        # 각 파서로 파싱
        form_result = FormParser(base_url).parse(html)
        script_result = ScriptParser(base_url).parse(html)
        link_result = LinkParser(base_url).parse(html)
        media_result = MediaParser(base_url).parse(html)
        meta_result = MetaParser(base_url).parse(html)
        data_result = DataAttrParser(base_url).parse(html)

        return ParseResult(
            forms=form_result.forms,
            scripts=script_result.scripts,
            inline_urls=script_result.inline_urls,
            links=link_result.links,
            images=media_result.images,
            videos=media_result.videos,
            audios=media_result.audios,
            sources=media_result.sources,
            tracks=media_result.tracks,
            refresh_urls=meta_result.refresh_urls,
            og_urls=meta_result.og_urls,
            twitter_urls=meta_result.twitter_urls,
            data_attr_urls=data_result.urls,
        )

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """자산 발견 수행.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 자산
        """
        html_content = context.crawl_data.get("html_content", "")
        base_url = context.crawl_data.get("base_url", context.target_url)

        if not html_content:
            return

        # HTML 파싱
        result = self.parse_with_base(html_content, base_url)

        # Forms
        for form in result.forms:
            metadata = {
                "method": form.method,
                "has_csrf_token": form.has_csrf_token,
                "hidden_inputs_count": len(form.hidden_inputs),
            }
            if form.csrf_tokens:
                metadata["csrf_token_names"] = list(form.csrf_tokens.keys())

            yield DiscoveredAsset(
                url=form.action,
                asset_type="form",
                source=self.name,
                metadata=metadata,
            )

        # Scripts
        for script in result.scripts:
            yield DiscoveredAsset(
                url=script.src,
                asset_type="script",
                source=self.name,
                metadata={
                    "integrity": script.integrity,
                    "defer": script.defer,
                    "async": script.async_,
                },
            )

        # Links
        for link in result.links:
            asset_type = (
                "stylesheet" if link.rel == "stylesheet" else f"link_{link.rel}"
            )
            yield DiscoveredAsset(
                url=link.href,
                asset_type=asset_type,
                source=self.name,
                metadata={"rel": link.rel, "as": link.as_type},
            )

        # Images
        for image in result.images:
            if image.src:
                yield DiscoveredAsset(
                    url=image.src,
                    asset_type="image",
                    source=self.name,
                    metadata={"alt": image.alt, "srcset_count": len(image.srcset)},
                )
            for srcset_url in image.srcset:
                yield DiscoveredAsset(
                    url=srcset_url,
                    asset_type="image",
                    source=self.name,
                    metadata={"from_srcset": True},
                )

        # Videos
        for video in result.videos:
            if video.src:
                yield DiscoveredAsset(
                    url=video.src,
                    asset_type="video",
                    source=self.name,
                    metadata={"poster": video.poster},
                )
            for source_url in video.sources:
                yield DiscoveredAsset(
                    url=source_url,
                    asset_type="video",
                    source=self.name,
                    metadata={"from_source": True},
                )

        # Audios
        for audio in result.audios:
            if audio.src:
                yield DiscoveredAsset(
                    url=audio.src,
                    asset_type="audio",
                    source=self.name,
                )
            for source_url in audio.sources:
                yield DiscoveredAsset(
                    url=source_url,
                    asset_type="audio",
                    source=self.name,
                    metadata={"from_source": True},
                )

        # Tracks
        for track_url in result.tracks:
            yield DiscoveredAsset(
                url=track_url,
                asset_type="track",
                source=self.name,
            )

        # Meta refresh URLs
        for refresh_url in result.refresh_urls:
            yield DiscoveredAsset(
                url=refresh_url,
                asset_type="redirect",
                source=self.name,
                metadata={"type": "meta_refresh"},
            )

        # OG URLs
        for og_url in result.og_urls:
            yield DiscoveredAsset(
                url=og_url,
                asset_type="og_resource",
                source=self.name,
            )

        # Twitter URLs
        for twitter_url in result.twitter_urls:
            yield DiscoveredAsset(
                url=twitter_url,
                asset_type="twitter_resource",
                source=self.name,
            )

        # Data attribute URLs
        for data_url in result.data_attr_urls:
            yield DiscoveredAsset(
                url=data_url,
                asset_type="data_attr",
                source=self.name,
            )
