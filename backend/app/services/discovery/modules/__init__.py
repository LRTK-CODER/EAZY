"""Discovery 모듈 패키지.

Phase 2 기본 모듈:
- ConfigDiscoveryModule: robots.txt, sitemap.xml, well-known 파일 파싱
- HtmlElementParserModule: HTML 요소에서 URL 및 자산 추출
- ResponseAnalyzerModule: HTTP 응답 헤더 및 본문 분석

Phase 3 네트워크 캡처 모듈:
- NetworkCapturerModule: XHR/Fetch, CORS, GraphQL, WebSocket 분석

Phase 4 고급 모듈:
- JsAnalyzerAstModule: JavaScript AST 분석 (라우터 경로, 동적 URL, 설정 객체)
- JsAnalyzerRegexModule: JavaScript 정규식 분석 (URL, HTTP 클라이언트, 시크릿)
"""

from app.services.discovery.modules.config_discovery import ConfigDiscoveryModule
from app.services.discovery.modules.html_element_parser import HtmlElementParserModule
from app.services.discovery.modules.js_analyzer_ast import JsAnalyzerAstModule
from app.services.discovery.modules.js_analyzer_regex import JsAnalyzerRegexModule
from app.services.discovery.modules.network_capturer import NetworkCapturerModule
from app.services.discovery.modules.response_analyzer import ResponseAnalyzerModule

__all__ = [
    "ConfigDiscoveryModule",
    "HtmlElementParserModule",
    "JsAnalyzerAstModule",
    "JsAnalyzerRegexModule",
    "NetworkCapturerModule",
    "ResponseAnalyzerModule",
]
