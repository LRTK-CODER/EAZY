"""API Schema Generator 모듈.

네트워크 요청/응답을 분석하여 OpenAPI 3.0 스펙을 자동 생성합니다.

Components:
    - PathNormalizer: 경로 정규화 (/users/123 -> /users/{id})
    - SchemaInferrer: JSON 데이터에서 JSON Schema 추론
    - OperationGrouper: 같은 경로의 다른 메서드들 그룹화
    - OpenApiBuilder: OpenAPI 3.0 스펙 생성
    - ApiSchemaGeneratorModule: Discovery 모듈 (FULL 프로필 전용)
"""

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class Parameter:
    """API 파라미터 정보."""

    name: str
    location: str  # "path", "query", "header"
    required: bool = True
    schema: Dict[str, Any] = field(default_factory=lambda: {"type": "string"})
    description: Optional[str] = None


@dataclass
class RequestBody:
    """요청 본문 정보."""

    content_type: str = "application/json"
    schema: Dict[str, Any] = field(default_factory=dict)
    example: Optional[Dict[str, Any]] = None
    required: bool = True


@dataclass
class ApiOperation:
    """API 작업 정보."""

    path: str
    method: str
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = None


@dataclass
class NormalizationResult:
    """경로 정규화 결과."""

    normalized_path: str
    parameters: List[Parameter] = field(default_factory=list)


# 별칭 for backward compatibility
NormalizedPath = NormalizationResult


# ============================================================================
# Path Normalizer
# ============================================================================


class PathNormalizer:
    """URL 경로를 OpenAPI 스타일로 정규화.

    /users/123 -> /users/{id}
    /posts/550e8400-e29b-41d4-a716-446655440000 -> /posts/{uuid}
    /articles/my-article-title -> /articles/{slug}
    """

    # UUID v4 패턴
    UUID_PATTERN = re.compile(
        r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"
    )

    # 순수 숫자 ID 패턴 (v1, v2 등 버전은 제외)
    NUMERIC_ID_PATTERN = re.compile(r"^\d+$")

    # API 버전 패턴 (보존해야 함)
    VERSION_PATTERN = re.compile(r"^v\d+$", re.IGNORECASE)

    # Slug 패턴 (하이픈 포함, 최소 2개 세그먼트)
    SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+$")

    def normalize(self, path: str) -> NormalizationResult:
        """경로를 정규화하고 파라미터 정보 추출.

        Args:
            path: 원본 URL 경로

        Returns:
            정규화된 경로와 파라미터 정보
        """
        if not path or path == "/":
            return NormalizationResult(normalized_path=path or "/", parameters=[])

        segments = path.strip("/").split("/")
        normalized_segments = []
        parameters: List[Parameter] = []

        # 먼저 전체 파라미터 개수를 파악
        total_params = self._count_params(segments)

        # 이전 세그먼트 정보 (컨텍스트 파라미터 이름 결정용)
        prev_segment = None
        # 파라미터 개수 추적 (다중 파라미터일 때 컨텍스트 기반 이름 사용)
        param_count = 0

        for segment in segments:
            if not segment:
                continue

            # 버전 번호는 그대로 유지
            if self.VERSION_PATTERN.match(segment):
                normalized_segments.append(segment)
                prev_segment = segment
                continue

            # UUID 감지
            if self.UUID_PATTERN.match(segment):
                param_count += 1
                param_name = self._get_param_name(prev_segment, "uuid", total_params)
                normalized_segments.append(f"{{{param_name}}}")
                parameters.append(
                    Parameter(
                        name=param_name,
                        location="path",
                        required=True,
                        schema={"type": "string", "format": "uuid"},
                    )
                )
                prev_segment = segment
                continue

            # 순수 숫자 ID 감지
            if self.NUMERIC_ID_PATTERN.match(segment):
                param_count += 1
                param_name = self._get_param_name(prev_segment, "id", total_params)
                normalized_segments.append(f"{{{param_name}}}")
                parameters.append(
                    Parameter(
                        name=param_name,
                        location="path",
                        required=True,
                        schema={"type": "integer"},
                    )
                )
                prev_segment = segment
                continue

            # Slug 감지
            if self.SLUG_PATTERN.match(segment):
                param_count += 1
                param_name = self._get_param_name(prev_segment, "slug", total_params)
                normalized_segments.append(f"{{{param_name}}}")
                parameters.append(
                    Parameter(
                        name=param_name,
                        location="path",
                        required=True,
                        schema={"type": "string"},
                    )
                )
                prev_segment = segment
                continue

            # 일반 세그먼트는 그대로 유지
            normalized_segments.append(segment)
            prev_segment = segment

        normalized_path = (
            "/" + "/".join(normalized_segments) if normalized_segments else "/"
        )
        return NormalizationResult(
            normalized_path=normalized_path, parameters=parameters
        )

    def _count_params(self, segments: List[str]) -> int:
        """경로 세그먼트에서 파라미터 개수 계산.

        Args:
            segments: 경로 세그먼트 리스트

        Returns:
            파라미터 개수
        """
        count = 0
        for segment in segments:
            if not segment or self.VERSION_PATTERN.match(segment):
                continue
            if (
                self.UUID_PATTERN.match(segment)
                or self.NUMERIC_ID_PATTERN.match(segment)
                or self.SLUG_PATTERN.match(segment)
            ):
                count += 1
        return count

    def _get_param_name(
        self, prev_segment: Optional[str], default_type: str, total_params: int
    ) -> str:
        """파라미터 이름 결정.

        단일 파라미터: 간단한 이름 (id, uuid, slug)
        다중 파라미터: 컨텍스트 기반 이름 (userId, postId)

        Args:
            prev_segment: 이전 경로 세그먼트
            default_type: 기본 파라미터 타입 (id, uuid, slug)
            total_params: 전체 파라미터 개수

        Returns:
            파라미터 이름
        """
        # 단일 파라미터는 간단한 이름 사용
        if total_params == 1:
            return default_type

        # 다중 파라미터: 컨텍스트 기반 이름
        if not prev_segment:
            return default_type

        # 복수형 -> 단수형 + 타입
        singular = self._singularize(prev_segment)

        if default_type == "id":
            return f"{singular}Id"
        elif default_type == "uuid":
            return f"{singular}Uuid" if singular != prev_segment else "uuid"
        elif default_type == "slug":
            return f"{singular}Slug" if singular != prev_segment else "slug"

        return default_type

    def _singularize(self, word: str) -> str:
        """간단한 단수화 (복수형 -> 단수형).

        Args:
            word: 복수형 단어

        Returns:
            단수형 단어
        """
        if word.endswith("ies"):
            return word[:-3] + "y"
        elif word.endswith("ses") or word.endswith("xes") or word.endswith("zes"):
            return word[:-2]
        elif word.endswith("ches") or word.endswith("shes"):
            return word[:-2]
        elif word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word


# ============================================================================
# Schema Inferrer
# ============================================================================


class SchemaInferrer:
    """JSON 데이터에서 JSON Schema 추론."""

    def infer(self, data: Any) -> Dict[str, Any]:
        """데이터에서 JSON Schema 추론.

        Args:
            data: 분석할 JSON 데이터

        Returns:
            추론된 JSON Schema
        """
        if data is None:
            return {"type": "null"}

        if isinstance(data, bool):
            return {"type": "boolean"}

        if isinstance(data, int):
            return {"type": "integer"}

        if isinstance(data, float):
            return {"type": "number"}

        if isinstance(data, str):
            return {"type": "string"}

        if isinstance(data, list):
            return self._infer_array_schema(data)

        if isinstance(data, dict):
            return self._infer_object_schema(data)

        return {"type": "string"}

    def _infer_array_schema(self, data: List[Any]) -> Dict[str, Any]:
        """배열 스키마 추론.

        Args:
            data: 배열 데이터

        Returns:
            배열 JSON Schema
        """
        if not data:
            return {"type": "array", "items": {}}

        # 첫 번째 요소로 아이템 스키마 추론
        first_item_schema = self.infer(data[0])

        # 여러 요소가 있으면 스키마 병합 시도
        if len(data) > 1:
            merged_schema = first_item_schema.copy()
            for item in data[1:]:
                item_schema = self.infer(item)
                merged_schema = self._merge_schemas(merged_schema, item_schema)
            return {"type": "array", "items": merged_schema}

        return {"type": "array", "items": first_item_schema}

    def _infer_object_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """객체 스키마 추론.

        Args:
            data: 객체 데이터

        Returns:
            객체 JSON Schema
        """
        properties = {}
        for key, value in data.items():
            properties[key] = self.infer(value)

        return {"type": "object", "properties": properties}

    def _merge_schemas(
        self, schema1: Dict[str, Any], schema2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """두 스키마 병합.

        Args:
            schema1: 첫 번째 스키마
            schema2: 두 번째 스키마

        Returns:
            병합된 스키마
        """
        if schema1.get("type") != schema2.get("type"):
            # 타입이 다르면 oneOf 사용
            return {"oneOf": [schema1, schema2]}

        if schema1.get("type") == "object":
            # 객체면 프로퍼티 병합
            merged_props = schema1.get("properties", {}).copy()
            for key, value in schema2.get("properties", {}).items():
                if key in merged_props:
                    merged_props[key] = self._merge_schemas(merged_props[key], value)
                else:
                    merged_props[key] = value
            return {"type": "object", "properties": merged_props}

        return schema1


# ============================================================================
# Operation Grouper
# ============================================================================


class OperationGrouper:
    """API Operation을 경로별로 그룹화."""

    def group(self, operations: List[ApiOperation]) -> Dict[str, List[ApiOperation]]:
        """Operation들을 경로별로 그룹화.

        Args:
            operations: API Operation 리스트

        Returns:
            경로를 키로 하는 Operation 그룹 딕셔너리
        """
        grouped: Dict[str, List[ApiOperation]] = {}
        seen: Set[Tuple[str, str]] = set()  # (path, method) 중복 체크용

        for op in operations:
            key = (op.path, op.method)
            if key in seen:
                continue
            seen.add(key)

            if op.path not in grouped:
                grouped[op.path] = []
            grouped[op.path].append(op)

        return grouped


# ============================================================================
# OpenAPI Builder
# ============================================================================


class OpenApiBuilder:
    """OpenAPI 3.0 스펙 빌더."""

    def build(
        self,
        operations: List[ApiOperation],
        title: str = "API Specification",
        version: str = "1.0.0",
        description: str = "",
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """OpenAPI 3.0 스펙 생성.

        Args:
            operations: API Operation 리스트
            title: API 제목
            version: API 버전
            description: API 설명
            base_url: 기본 서버 URL

        Returns:
            OpenAPI 3.0 스펙 딕셔너리
        """
        spec: Dict[str, Any] = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version,
            },
            "paths": {},
        }

        if description:
            spec["info"]["description"] = description

        if base_url:
            spec["servers"] = [{"url": base_url}]

        # Operation 그룹화
        grouper = OperationGrouper()
        grouped = grouper.group(operations)

        # 경로별 스펙 생성
        for path, ops in grouped.items():
            spec["paths"][path] = self._build_path_item(ops)

        return spec

    def _build_path_item(self, operations: List[ApiOperation]) -> Dict[str, Any]:
        """경로 아이템 생성.

        Args:
            operations: 같은 경로의 Operation 리스트

        Returns:
            경로 아이템 딕셔너리
        """
        path_item: Dict[str, Any] = {}

        for op in operations:
            method = op.method.lower()
            operation_spec = self._build_operation(op)
            path_item[method] = operation_spec

        return path_item

    def _build_operation(self, op: ApiOperation) -> Dict[str, Any]:
        """Operation 스펙 생성.

        Args:
            op: API Operation

        Returns:
            Operation 스펙 딕셔너리
        """
        operation: Dict[str, Any] = {}

        if op.tags:
            operation["tags"] = op.tags

        if op.summary:
            operation["summary"] = op.summary

        if op.description:
            operation["description"] = op.description

        if op.operation_id:
            operation["operationId"] = op.operation_id

        # 파라미터
        if op.parameters:
            operation["parameters"] = [
                self._build_parameter(param) for param in op.parameters
            ]

        # Request Body
        if op.request_body:
            operation["requestBody"] = self._build_request_body(op.request_body)

        # Responses
        if op.responses:
            operation["responses"] = {
                str(code): self._build_response(resp)
                for code, resp in op.responses.items()
            }
        else:
            # 기본 응답
            operation["responses"] = {"200": {"description": "Successful response"}}

        return operation

    def _build_parameter(self, param: Parameter) -> Dict[str, Any]:
        """파라미터 스펙 생성.

        Args:
            param: Parameter 객체

        Returns:
            파라미터 스펙 딕셔너리
        """
        spec: Dict[str, Any] = {
            "name": param.name,
            "in": param.location,
            "required": param.required,
            "schema": param.schema,
        }

        if param.description:
            spec["description"] = param.description

        return spec

    def _build_request_body(self, body: RequestBody) -> Dict[str, Any]:
        """Request Body 스펙 생성.

        Args:
            body: RequestBody 객체

        Returns:
            Request Body 스펙 딕셔너리
        """
        content: Dict[str, Any] = {"schema": body.schema}

        if body.example:
            content["example"] = body.example

        return {
            "required": body.required,
            "content": {body.content_type: content},
        }

    def _build_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Response 스펙 생성.

        Args:
            response: 응답 정보 딕셔너리

        Returns:
            Response 스펙 딕셔너리
        """
        spec: Dict[str, Any] = {
            "description": response.get("description", "Response"),
        }

        if "content" in response:
            spec["content"] = response["content"]

        return spec


# ============================================================================
# API Schema Generator Module
# ============================================================================


class ApiSchemaGeneratorModule(BaseDiscoveryModule):
    """API 스키마 생성 모듈.

    네트워크 요청/응답을 분석하여 OpenAPI 3.0 스펙을 생성합니다.
    FULL 프로필에서만 활성화됩니다.
    """

    def __init__(self) -> None:
        """모듈 초기화."""
        self._path_normalizer = PathNormalizer()
        self._schema_inferrer = SchemaInferrer()
        self._openapi_builder = OpenApiBuilder()

    @property
    def name(self) -> str:
        """모듈 이름."""
        return "api_schema_generator"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원 프로필 - FULL 전용."""
        return {ScanProfile.FULL}

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """크롤링 데이터에서 OpenAPI 스펙 생성.

        Args:
            context: Discovery 컨텍스트

        Yields:
            OpenAPI 스펙 자산
        """
        crawl_data = getattr(context, "crawl_data", {}) or {}
        network_requests = crawl_data.get("network_requests", [])
        network_responses = crawl_data.get("network_responses", [])

        if not network_requests:
            return

        # 응답을 URL 기준으로 인덱싱
        response_map = {resp.get("url"): resp for resp in network_responses}

        # Operation 리스트 생성
        operations: List[ApiOperation] = []

        for request in network_requests:
            url = request.get("url", "")
            method = request.get("method", "GET").upper()

            # URL 파싱
            parsed = urlparse(url)
            path = parsed.path

            # 경로 정규화
            norm_result = self._path_normalizer.normalize(path)

            # Request Body 파싱
            request_body = None
            if method in ("POST", "PUT", "PATCH") and request.get("body"):
                try:
                    body_data = json.loads(request["body"])
                    request_body = RequestBody(
                        content_type="application/json",
                        schema=self._schema_inferrer.infer(body_data),
                        example=body_data,
                    )
                except (json.JSONDecodeError, TypeError):
                    pass

            # Response 스키마 추론
            responses: Dict[int, Dict[str, Any]] = {}
            if url in response_map:
                resp = response_map[url]
                status = resp.get("status", 200)
                try:
                    body_data = json.loads(resp.get("body", "{}"))
                    responses[status] = {
                        "description": self._get_status_description(status),
                        "content": {
                            "application/json": {
                                "schema": self._schema_inferrer.infer(body_data),
                            }
                        },
                    }
                except (json.JSONDecodeError, TypeError):
                    responses[status] = {
                        "description": self._get_status_description(status),
                    }

            # 태그 결정 (첫 번째 경로 세그먼트)
            tags = self._extract_tags(norm_result.normalized_path)

            operations.append(
                ApiOperation(
                    path=norm_result.normalized_path,
                    method=method,
                    parameters=norm_result.parameters,
                    request_body=request_body,
                    responses=responses,
                    tags=tags,
                )
            )

        if not operations:
            return

        # OpenAPI 스펙 생성
        spec = self._openapi_builder.build(
            operations,
            title=f"{context.target_url} API",
            base_url=context.target_url,
        )

        # Operation/Path 카운트
        paths_count = len(spec.get("paths", {}))
        operations_count = sum(
            len(methods) for methods in spec.get("paths", {}).values()
        )

        yield DiscoveredAsset(
            url=context.target_url,
            asset_type="openapi_spec",
            source=self.name,
            metadata={
                "openapi_version": "3.0.0",
                "paths_count": paths_count,
                "operations_count": operations_count,
                "spec": spec,
            },
        )

    def _get_status_description(self, status: int) -> str:
        """HTTP 상태 코드 설명.

        Args:
            status: HTTP 상태 코드

        Returns:
            상태 설명
        """
        descriptions = {
            200: "Successful response",
            201: "Created",
            204: "No Content",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
        }
        return descriptions.get(status, "Response")

    def _extract_tags(self, path: str) -> List[str]:
        """경로에서 태그 추출.

        Args:
            path: API 경로

        Returns:
            태그 리스트
        """
        segments = path.strip("/").split("/")
        for segment in segments:
            if segment and not segment.startswith("{"):
                # 첫 번째 정적 세그먼트를 태그로 사용
                return [segment.capitalize()]
        return []
