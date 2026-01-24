"""Discovery 모듈 패키지.

Phase 2 기본 모듈:
- ConfigDiscoveryModule: robots.txt, sitemap.xml, well-known 파일 파싱
- HtmlElementParserModule: HTML 요소에서 URL 및 자산 추출
- ResponseAnalyzerModule: HTTP 응답 헤더 및 본문 분석

Phase 3 네트워크 캡처 모듈:
- NetworkCapturerModule: XHR/Fetch, CORS, GraphQL, WebSocket 분석

Phase 4 분석 모듈:
- JsAnalyzerAstModule: JavaScript AST 분석 (라우터 경로, 동적 URL, 설정 객체)
- JsAnalyzerRegexModule: JavaScript 정규식 분석 (URL, HTTP 클라이언트, 시크릿)

Phase 5 고급 모듈:
- InteractionEngineModule: 동적 상호작용으로 숨겨진 콘텐츠 및 API 발견
- TechFingerprintModule: 기술 스택 핑거프린팅 (React, Vue, nginx 등)
- ThirdPartyDetectorModule: 외부 서비스 탐지 (Analytics, Payment, Auth 등)
- ApiSchemaGeneratorModule: OpenAPI 3.0 스펙 자동 생성
"""

from app.services.discovery.modules.api_schema_generator import ApiSchemaGeneratorModule
from app.services.discovery.modules.config_discovery import ConfigDiscoveryModule
from app.services.discovery.modules.html_element_parser import HtmlElementParserModule
from app.services.discovery.modules.interaction_engine import InteractionEngineModule
from app.services.discovery.modules.js_analyzer_ast import JsAnalyzerAstModule
from app.services.discovery.modules.js_analyzer_regex import JsAnalyzerRegexModule
from app.services.discovery.modules.network_capturer import NetworkCapturerModule
from app.services.discovery.modules.response_analyzer import ResponseAnalyzerModule
from app.services.discovery.modules.tech_fingerprint import TechFingerprintModule
from app.services.discovery.modules.thirdparty_detector import ThirdPartyDetectorModule

__all__ = [
    "ApiSchemaGeneratorModule",
    "ConfigDiscoveryModule",
    "HtmlElementParserModule",
    "InteractionEngineModule",
    "JsAnalyzerAstModule",
    "JsAnalyzerRegexModule",
    "NetworkCapturerModule",
    "ResponseAnalyzerModule",
    "TechFingerprintModule",
    "ThirdPartyDetectorModule",
]
