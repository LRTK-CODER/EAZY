"""JavaScript Analyzer AST Module.

JavaScript 코드를 AST로 파싱하여 라우터 경로, 동적 URL, 설정 객체를 분석합니다.
- React Router / Vue Router 경로 추출
- 동적 URL 구성 추적 (문자열 연결, 템플릿 리터럴)
- 설정 객체 내 URL 및 환경 변수 추출

pyjsparser를 사용하여 ES6+ JavaScript를 파싱합니다.
"""

import re
import signal
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class RouterPath:
    """라우터 경로 정보."""

    path: str
    component: Optional[str] = None
    is_dynamic: bool = False
    params: List[str] = field(default_factory=list)


@dataclass
class DynamicUrlConstruction:
    """동적 URL 구성 정보."""

    base_pattern: str
    variables: List[str] = field(default_factory=list)
    is_complete: bool = False


@dataclass
class ConfigUrl:
    """설정 객체 내 URL 정보."""

    url: str
    key_path: str
    is_environment_variable: bool = False
    env_var_name: Optional[str] = None


# ============================================================================
# Timeout Handler
# ============================================================================


class TimeoutError(Exception):
    """Timeout exception for parsing."""

    pass


def timeout_handler(signum: int, frame: Any) -> None:  # pragma: no cover
    """Signal handler for timeout."""
    raise TimeoutError("Parsing timeout")


# ============================================================================
# AstParser
# ============================================================================


class AstParser:
    """pyjsparser wrapper with safe parsing."""

    def __init__(self) -> None:
        """Initialize AstParser."""
        self._parser: Any = None
        self._init_parser()

    def _init_parser(self) -> None:
        """Initialize pyjsparser."""
        try:
            import pyjsparser

            self._parser = pyjsparser
        except ImportError:  # pragma: no cover
            self._parser = None

    def parse_safe(
        self, js_code: str, timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """JavaScript 코드를 안전하게 파싱.

        Args:
            js_code: JavaScript 소스 코드
            timeout: 파싱 타임아웃 (초)

        Returns:
            파싱된 AST (dict) 또는 None (실패 시)
        """
        if not js_code or not js_code.strip():
            return None

        if self._parser is None:
            return None

        try:
            # Set up signal-based timeout (Unix only)
            old_handler = None
            try:
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.setitimer(signal.ITIMER_REAL, timeout)
            except (AttributeError, ValueError):  # pragma: no cover
                # Windows or signal not available
                pass

            try:
                ast: Dict[str, Any] = self._parser.parse(js_code)
                return ast
            finally:
                # Restore signal handler
                try:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    if old_handler is not None:
                        signal.signal(signal.SIGALRM, old_handler)
                except (AttributeError, ValueError):  # pragma: no cover
                    pass

        except TimeoutError:
            return None
        except Exception:
            # pyjsparser가 JSX, TypeScript 등을 지원하지 않음
            return None


# ============================================================================
# RouterExtractor
# ============================================================================


class RouterExtractor:
    """React/Vue Router 경로 추출기."""

    # 동적 파라미터 패턴
    PARAM_PATTERNS = [
        re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)"),  # React Router :param
        re.compile(r"\[([a-zA-Z_][a-zA-Z0-9_]*)\]"),  # Next.js [param]
        re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"),  # Some frameworks {param}
    ]

    # 경로 추출 정규식 패턴
    PATH_PATTERNS = [
        # path: '/users' 또는 path: "/users"
        re.compile(r'path\s*:\s*["\']([^"\']+)["\']'),
        # Route path="/users"
        re.compile(r'<Route\s+[^>]*path\s*=\s*["\']([^"\']+)["\']'),
        # to="/users" (Link component)
        re.compile(r'to\s*=\s*["\']([^"\']+)["\']'),
    ]

    def extract(self, ast: Dict[str, Any]) -> List[RouterPath]:
        """AST에서 라우터 경로 추출.

        Args:
            ast: JavaScript AST

        Returns:
            추출된 RouterPath 목록
        """
        paths: List[RouterPath] = []
        visited: Set[int] = set()
        self._walk_ast(ast, paths, visited)
        return paths

    def _walk_ast(
        self,
        node: Any,
        paths: List[RouterPath],
        visited: Set[int],
        depth: int = 0,
    ) -> None:
        """AST 노드 순회.

        Args:
            node: 현재 노드
            paths: 수집된 경로 목록
            visited: 방문한 노드 ID 집합
            depth: 현재 깊이 (무한 루프 방지)
        """
        if depth > 100:  # 최대 깊이 제한
            return

        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)

        if isinstance(node, dict):
            # ObjectExpression에서 path 프로퍼티 찾기
            if node.get("type") == "ObjectExpression":
                self._extract_from_object(node, paths)

            # 모든 값 순회
            for value in node.values():
                self._walk_ast(value, paths, visited, depth + 1)

        elif isinstance(node, list):
            for item in node:
                self._walk_ast(item, paths, visited, depth + 1)

    def _extract_from_object(
        self,
        obj_node: Dict[str, Any],
        paths: List[RouterPath],
    ) -> None:
        """ObjectExpression에서 라우터 경로 추출."""
        properties = obj_node.get("properties", [])

        path_value: Optional[str] = None
        component_value: Optional[str] = None

        for prop in properties:
            if not isinstance(prop, dict):
                continue

            key = prop.get("key", {})
            value = prop.get("value", {})

            key_name = key.get("name") or key.get("value")

            if key_name == "path":
                # 문자열 값 추출
                if value.get("type") == "Literal":
                    path_value = str(value.get("value", ""))

            elif key_name == "component":
                # 컴포넌트 이름 추출
                if value.get("type") == "Identifier":
                    component_value = value.get("name")

        if path_value:
            is_dynamic, params = self._analyze_path(path_value)
            paths.append(
                RouterPath(
                    path=path_value,
                    component=component_value,
                    is_dynamic=is_dynamic,
                    params=params,
                )
            )

    def _analyze_path(self, path: str) -> tuple[bool, List[str]]:
        """경로의 동적 파라미터 분석.

        Args:
            path: 경로 문자열

        Returns:
            (is_dynamic, params) 튜플
        """
        params: List[str] = []
        is_dynamic = False

        for pattern in self.PARAM_PATTERNS:
            matches = pattern.findall(path)
            if matches:
                is_dynamic = True
                params.extend(matches)

        return is_dynamic, params

    def extract_from_source(self, js_code: str) -> List[RouterPath]:
        """소스 코드에서 라우터 경로 추출 (정규식 fallback).

        Args:
            js_code: JavaScript 소스 코드

        Returns:
            추출된 RouterPath 목록
        """
        paths: List[RouterPath] = []
        seen_paths: Set[str] = set()

        for pattern in self.PATH_PATTERNS:
            matches = pattern.findall(js_code)
            for match in matches:
                if match and match not in seen_paths:
                    seen_paths.add(match)
                    is_dynamic, params = self._analyze_path(match)
                    paths.append(
                        RouterPath(
                            path=match,
                            component=None,
                            is_dynamic=is_dynamic,
                            params=params,
                        )
                    )

        return paths


# ============================================================================
# UrlConstructionTracker
# ============================================================================


class UrlConstructionTracker:
    """동적 URL 구성 추적기."""

    # URL 구성 패턴
    URL_CONSTRUCTION_PATTERNS = [
        # 문자열 연결: '/api/' + endpoint
        re.compile(
            r'["\']([/a-zA-Z0-9_-]+)["\']' r"\s*\+\s*" r"([a-zA-Z_][a-zA-Z0-9_]*)"
        ),
        # 변수 + 문자열: baseUrl + '/users'
        re.compile(
            r"([a-zA-Z_][a-zA-Z0-9_]*)" r"\s*\+\s*" r'["\']([/a-zA-Z0-9_-]+)["\']'
        ),
        # 템플릿 리터럴: `/api/${var}`
        re.compile(r"`([^`]*\$\{[^}]+\}[^`]*)`"),
        # fetch/axios URL
        re.compile(
            r'(?:fetch|axios\.(?:get|post|put|delete|patch))\s*\(\s*["\']([^"\']+)["\']'
        ),
        # axios config
        re.compile(r'url\s*:\s*["\']([^"\']+)["\']'),
    ]

    # 템플릿 변수 추출
    TEMPLATE_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def track(self, ast: Dict[str, Any]) -> List[DynamicUrlConstruction]:
        """AST에서 동적 URL 구성 추적.

        Args:
            ast: JavaScript AST

        Returns:
            추적된 DynamicUrlConstruction 목록
        """
        constructions: List[DynamicUrlConstruction] = []
        visited: Set[int] = set()
        self._walk_ast(ast, constructions, visited)
        return constructions

    def _walk_ast(
        self,
        node: Any,
        constructions: List[DynamicUrlConstruction],
        visited: Set[int],
        depth: int = 0,
    ) -> None:
        """AST 노드 순회."""
        if depth > 100:
            return

        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)

        if isinstance(node, dict):
            node_type = node.get("type")

            # BinaryExpression (문자열 연결)
            if node_type == "BinaryExpression" and node.get("operator") == "+":
                self._extract_from_binary(node, constructions)

            # TemplateLiteral
            elif node_type == "TemplateLiteral":
                self._extract_from_template(node, constructions)

            # CallExpression (fetch, axios 등)
            elif node_type == "CallExpression":
                self._extract_from_call(node, constructions)

            for value in node.values():
                self._walk_ast(value, constructions, visited, depth + 1)

        elif isinstance(node, list):
            for item in node:
                self._walk_ast(item, constructions, visited, depth + 1)

    def _extract_from_binary(
        self,
        node: Dict[str, Any],
        constructions: List[DynamicUrlConstruction],
    ) -> None:
        """BinaryExpression에서 URL 구성 추출."""
        left = node.get("left", {})
        right = node.get("right", {})

        base_pattern = ""
        variables: List[str] = []

        # 왼쪽이 문자열
        if left.get("type") == "Literal" and isinstance(left.get("value"), str):
            value = left.get("value", "")
            if "/" in value or "api" in value.lower():
                base_pattern = value

        # 오른쪽이 식별자 (변수)
        if right.get("type") == "Identifier":
            variables.append(right.get("name", ""))

        # 오른쪽이 문자열
        if right.get("type") == "Literal" and isinstance(right.get("value"), str):
            value = right.get("value", "")
            if "/" in value or "api" in value.lower():
                base_pattern = base_pattern + value if base_pattern else value

        # 왼쪽이 식별자
        if left.get("type") == "Identifier":
            variables.append(left.get("name", ""))

        if base_pattern or variables:
            constructions.append(
                DynamicUrlConstruction(
                    base_pattern=base_pattern,
                    variables=variables,
                    is_complete=bool(base_pattern and not variables),
                )
            )

    def _extract_from_template(
        self,
        node: Dict[str, Any],
        constructions: List[DynamicUrlConstruction],
    ) -> None:
        """TemplateLiteral에서 URL 구성 추출."""
        quasis = node.get("quasis", [])
        expressions = node.get("expressions", [])

        base_parts: List[str] = []
        variables: List[str] = []

        for quasi in quasis:
            if quasi.get("type") == "TemplateElement":
                value = quasi.get("value", {})
                raw = value.get("raw", "")
                base_parts.append(raw)

        for expr in expressions:
            if expr.get("type") == "Identifier":
                variables.append(expr.get("name", ""))
            elif expr.get("type") == "MemberExpression":
                # 예: obj.prop
                obj = expr.get("object", {})
                prop = expr.get("property", {})
                var_name = f"{obj.get('name', '')}.{prop.get('name', '')}"
                variables.append(var_name)

        base_pattern = "".join(base_parts)
        if "/" in base_pattern or "api" in base_pattern.lower():
            constructions.append(
                DynamicUrlConstruction(
                    base_pattern=base_pattern,
                    variables=variables,
                    is_complete=len(variables) == 0,
                )
            )

    def _extract_from_call(
        self,
        node: Dict[str, Any],
        constructions: List[DynamicUrlConstruction],
    ) -> None:
        """CallExpression에서 URL 추출 (fetch, axios)."""
        callee = node.get("callee", {})
        arguments = node.get("arguments", [])

        # fetch(url) 또는 axios.get(url) 확인
        is_http_call = False

        if callee.get("type") == "Identifier":
            if callee.get("name") == "fetch":
                is_http_call = True
        elif callee.get("type") == "MemberExpression":
            obj = callee.get("object", {})
            prop = callee.get("property", {})
            if obj.get("name") == "axios" and prop.get("name") in {
                "get",
                "post",
                "put",
                "delete",
                "patch",
            }:
                is_http_call = True

        if is_http_call and arguments:
            first_arg = arguments[0]
            if first_arg.get("type") == "Literal":
                url = first_arg.get("value", "")
                if isinstance(url, str) and "/" in url:
                    constructions.append(
                        DynamicUrlConstruction(
                            base_pattern=url,
                            variables=[],
                            is_complete=True,
                        )
                    )

    def track_from_source(self, js_code: str) -> List[DynamicUrlConstruction]:
        """소스 코드에서 URL 구성 추적 (정규식 fallback).

        Args:
            js_code: JavaScript 소스 코드

        Returns:
            추적된 DynamicUrlConstruction 목록
        """
        constructions: List[DynamicUrlConstruction] = []
        seen_patterns: Set[str] = set()

        for pattern in self.URL_CONSTRUCTION_PATTERNS:
            matches = pattern.findall(js_code)
            for match in matches:
                if isinstance(match, tuple):
                    # 문자열 연결 패턴
                    parts = [p for p in match if p]
                    base_pattern = ""
                    variables: List[str] = []

                    for part in parts:
                        if part.startswith("/") or "api" in part.lower():
                            base_pattern += part
                        elif not part.startswith('"') and not part.startswith("'"):
                            variables.append(part)

                    if base_pattern and base_pattern not in seen_patterns:
                        seen_patterns.add(base_pattern)
                        constructions.append(
                            DynamicUrlConstruction(
                                base_pattern=base_pattern,
                                variables=variables,
                                is_complete=len(variables) == 0,
                            )
                        )
                else:
                    # 단일 매치 (템플릿 리터럴, fetch URL 등)
                    if match and match not in seen_patterns:
                        seen_patterns.add(match)

                        # 템플릿 변수 추출
                        template_vars = self.TEMPLATE_VAR_PATTERN.findall(match)

                        constructions.append(
                            DynamicUrlConstruction(
                                base_pattern=match,
                                variables=template_vars,
                                is_complete=len(template_vars) == 0,
                            )
                        )

        return constructions


# ============================================================================
# ConfigObjectAnalyzer
# ============================================================================


class ConfigObjectAnalyzer:
    """설정 객체 내 URL 및 환경 변수 분석기."""

    # URL 패턴
    URL_PATTERN = re.compile(r'(https?://[^\s"\'<>]+|wss?://[^\s"\'<>]+)')

    # 환경 변수 패턴
    ENV_VAR_PATTERNS = [
        # process.env.VAR_NAME
        re.compile(r"process\.env\.([A-Z_][A-Z0-9_]*)"),
        # import.meta.env.VAR_NAME
        re.compile(r"import\.meta\.env\.([A-Z_][A-Z0-9_]*)"),
    ]

    # 설정 키 패턴 (URL을 포함할 가능성이 높은)
    CONFIG_KEY_PATTERNS = [
        re.compile(
            r'([a-zA-Z_][a-zA-Z0-9_]*(?:Url|URL|Uri|URI|Endpoint|Host|Base))\s*:\s*["\']([^"\']+)["\']'
        ),
        re.compile(
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*["\']((https?|wss?)://[^"\']+)["\']'
        ),
    ]

    def analyze(self, ast: Dict[str, Any]) -> List[ConfigUrl]:
        """AST에서 설정 URL 분석.

        Args:
            ast: JavaScript AST

        Returns:
            분석된 ConfigUrl 목록
        """
        configs: List[ConfigUrl] = []
        visited: Set[int] = set()
        self._walk_ast(ast, configs, visited, "")
        return configs

    def _walk_ast(
        self,
        node: Any,
        configs: List[ConfigUrl],
        visited: Set[int],
        key_path: str,
        depth: int = 0,
    ) -> None:
        """AST 노드 순회."""
        if depth > 100:
            return

        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)

        if isinstance(node, dict):
            node_type = node.get("type")

            # VariableDeclarator
            if node_type == "VariableDeclarator":
                var_id = node.get("id", {})
                var_name = var_id.get("name", "")
                init = node.get("init")
                if init:
                    self._walk_ast(init, configs, visited, var_name, depth + 1)

            # Property (객체 프로퍼티)
            elif node_type == "Property":
                key = node.get("key", {})
                key_name = key.get("name") or key.get("value", "")
                value = node.get("value", {})

                new_key_path = f"{key_path}.{key_name}" if key_path else key_name
                self._extract_from_property(value, configs, new_key_path)
                self._walk_ast(value, configs, visited, new_key_path, depth + 1)

            # MemberExpression (process.env, import.meta.env)
            elif node_type == "MemberExpression":
                env_var = self._extract_env_var(node)
                if env_var:
                    configs.append(
                        ConfigUrl(
                            url="",
                            key_path=key_path,
                            is_environment_variable=True,
                            env_var_name=env_var,
                        )
                    )

            else:
                for key, value in node.items():
                    self._walk_ast(value, configs, visited, key_path, depth + 1)

        elif isinstance(node, list):
            for item in node:
                self._walk_ast(item, configs, visited, key_path, depth + 1)

    def _extract_from_property(
        self,
        value_node: Dict[str, Any],
        configs: List[ConfigUrl],
        key_path: str,
    ) -> None:
        """프로퍼티 값에서 URL 추출."""
        if value_node.get("type") == "Literal":
            value = value_node.get("value")
            if isinstance(value, str):
                # URL인지 확인
                if self.URL_PATTERN.match(value):
                    configs.append(
                        ConfigUrl(
                            url=value,
                            key_path=key_path,
                            is_environment_variable=False,
                            env_var_name=None,
                        )
                    )
                # 상대 경로 API 엔드포인트
                elif value.startswith("/api/") or value.startswith("/v1/"):
                    configs.append(
                        ConfigUrl(
                            url=value,
                            key_path=key_path,
                            is_environment_variable=False,
                            env_var_name=None,
                        )
                    )

    def _extract_env_var(self, node: Dict[str, Any]) -> Optional[str]:
        """MemberExpression에서 환경 변수 이름 추출."""
        obj = node.get("object", {})
        prop = node.get("property", {})

        # process.env.VAR_NAME
        if obj.get("type") == "MemberExpression":
            inner_obj = obj.get("object", {})
            inner_prop = obj.get("property", {})

            if inner_obj.get("name") == "process" and inner_prop.get("name") == "env":
                prop_name = prop.get("name")
                return str(prop_name) if prop_name else None

            # import.meta.env.VAR_NAME
            if inner_obj.get("type") == "MetaProperty":
                meta = inner_obj.get("meta", {})
                property_ = inner_obj.get("property", {})
                if meta.get("name") == "import" and property_.get("name") == "meta":
                    if inner_prop.get("name") == "env":
                        prop_name = prop.get("name")
                        return str(prop_name) if prop_name else None

        return None

    def analyze_from_source(self, js_code: str) -> List[ConfigUrl]:
        """소스 코드에서 설정 URL 분석 (정규식 fallback).

        Args:
            js_code: JavaScript 소스 코드

        Returns:
            분석된 ConfigUrl 목록
        """
        configs: List[ConfigUrl] = []
        seen_urls: Set[str] = set()

        # 설정 키에서 URL 추출
        for pattern in self.CONFIG_KEY_PATTERNS:
            matches = pattern.findall(js_code)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    key_name = match[0]
                    url = match[1]
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        configs.append(
                            ConfigUrl(
                                url=url,
                                key_path=key_name,
                                is_environment_variable=False,
                                env_var_name=None,
                            )
                        )

        # 일반 URL 추출
        url_matches = self.URL_PATTERN.findall(js_code)
        for url in url_matches:
            if url and url not in seen_urls:
                seen_urls.add(url)
                configs.append(
                    ConfigUrl(
                        url=url,
                        key_path="",
                        is_environment_variable=False,
                        env_var_name=None,
                    )
                )

        # 환경 변수 참조 추출
        for pattern in self.ENV_VAR_PATTERNS:
            matches = pattern.findall(js_code)
            for env_var in matches:
                configs.append(
                    ConfigUrl(
                        url="",
                        key_path="",
                        is_environment_variable=True,
                        env_var_name=env_var,
                    )
                )

        return configs


# ============================================================================
# Main Module
# ============================================================================


class JsAnalyzerAstModule(BaseDiscoveryModule):
    """JavaScript AST Analyzer Discovery 모듈.

    JavaScript 코드를 AST로 분석하여 라우터 경로, 동적 URL,
    설정 객체를 추출합니다.

    FULL 프로필에서만 활성화됩니다 (성능 고려).
    """

    def __init__(self) -> None:
        """Initialize JsAnalyzerAstModule."""
        self._ast_parser = AstParser()
        self._router_extractor = RouterExtractor()
        self._url_tracker = UrlConstructionTracker()
        self._config_analyzer = ConfigObjectAnalyzer()

    @property
    def name(self) -> str:
        """모듈 고유 이름."""
        return "js_analyzer_ast"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필 집합."""
        return {ScanProfile.FULL}

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

        for js_item in js_contents:
            js_url = js_item.get("url", "")
            js_code = js_item.get("content", "")

            if not js_code:
                continue

            # AST 파싱 시도
            ast = self._ast_parser.parse_safe(js_code)

            # 라우터 경로 추출
            if ast:
                router_paths = self._router_extractor.extract(ast)
            else:
                router_paths = self._router_extractor.extract_from_source(js_code)

            for router_path in router_paths:
                yield DiscoveredAsset(
                    url=router_path.path,
                    asset_type="router_path",
                    source=self.name,
                    metadata={
                        "component": router_path.component,
                        "is_dynamic": router_path.is_dynamic,
                        "params": router_path.params,
                        "source_file": js_url,
                    },
                )

            # 동적 URL 구성 추출
            if ast:
                url_constructions = self._url_tracker.track(ast)
            else:
                url_constructions = self._url_tracker.track_from_source(js_code)

            for construction in url_constructions:
                if construction.base_pattern:
                    yield DiscoveredAsset(
                        url=construction.base_pattern,
                        asset_type="dynamic_url",
                        source=self.name,
                        metadata={
                            "variables": construction.variables,
                            "is_complete": construction.is_complete,
                            "source_file": js_url,
                        },
                    )

            # 설정 URL 추출
            if ast:
                config_urls = self._config_analyzer.analyze(ast)
            else:
                config_urls = self._config_analyzer.analyze_from_source(js_code)

            for config_url in config_urls:
                if config_url.url:
                    yield DiscoveredAsset(
                        url=config_url.url,
                        asset_type="config_url",
                        source=self.name,
                        metadata={
                            "key_path": config_url.key_path,
                            "is_environment_variable": config_url.is_environment_variable,
                            "env_var_name": config_url.env_var_name,
                            "source_file": js_url,
                        },
                    )
                elif config_url.is_environment_variable:
                    yield DiscoveredAsset(
                        url=f"env://{config_url.env_var_name}",
                        asset_type="env_variable",
                        source=self.name,
                        metadata={
                            "key_path": config_url.key_path,
                            "env_var_name": config_url.env_var_name,
                            "source_file": js_url,
                        },
                    )
