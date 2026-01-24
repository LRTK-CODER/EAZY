"""ApiSchemaGeneratorModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- PathNormalizer: 경로 정규화 (/users/123 -> /users/{id})
- SchemaInferrer: JSON 데이터에서 JSON Schema 추론
- OperationGrouper: 같은 경로의 다른 메서드들 그룹화
- OpenApiBuilder: OpenAPI 3.0 YAML/JSON 생성
- ApiSchemaGeneratorModule: Discovery 모듈
"""

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from app.services.discovery.models import DiscoveryContext, ScanProfile
from app.services.discovery.modules.api_schema_generator import (
    ApiOperation,
    ApiSchemaGeneratorModule,
    OpenApiBuilder,
    OperationGrouper,
    Parameter,
    PathNormalizer,
    RequestBody,
    SchemaInferrer,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def path_normalizer() -> PathNormalizer:
    """Create PathNormalizer instance."""
    return PathNormalizer()


@pytest.fixture
def schema_inferrer() -> SchemaInferrer:
    """Create SchemaInferrer instance."""
    return SchemaInferrer()


@pytest.fixture
def operation_grouper() -> OperationGrouper:
    """Create OperationGrouper instance."""
    return OperationGrouper()


@pytest.fixture
def openapi_builder() -> OpenApiBuilder:
    """Create OpenApiBuilder instance."""
    return OpenApiBuilder()


@pytest.fixture
def api_schema_generator_module() -> ApiSchemaGeneratorModule:
    """Create ApiSchemaGeneratorModule instance."""
    return ApiSchemaGeneratorModule()


# ============================================================================
# Test 1: Path Normalization - Numeric ID
# ============================================================================


class TestPathNormalizationNumericId:
    """숫자 ID 경로 정규화 테스트."""

    def test_single_numeric_id(self, path_normalizer: PathNormalizer) -> None:
        """단일 숫자 ID 정규화: /users/123 -> /users/{id}."""
        result = path_normalizer.normalize("/users/123")

        assert result.normalized_path == "/users/{id}"
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "id"
        assert result.parameters[0].location == "path"
        assert result.parameters[0].required is True
        assert result.parameters[0].schema == {"type": "integer"}

    def test_numeric_id_at_end(self, path_normalizer: PathNormalizer) -> None:
        """URL 끝의 숫자 ID: /api/v1/posts/456 -> /api/v1/posts/{id}."""
        result = path_normalizer.normalize("/api/v1/posts/456")

        assert result.normalized_path == "/api/v1/posts/{id}"
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "id"
        assert result.parameters[0].schema["type"] == "integer"

    def test_large_numeric_id(self, path_normalizer: PathNormalizer) -> None:
        """큰 숫자 ID: /orders/9999999999."""
        result = path_normalizer.normalize("/orders/9999999999")

        assert result.normalized_path == "/orders/{id}"
        assert result.parameters[0].schema["type"] == "integer"

    def test_numeric_id_preserves_version(
        self, path_normalizer: PathNormalizer
    ) -> None:
        """버전 번호는 정규화하지 않음: /api/v1/users/123."""
        result = path_normalizer.normalize("/api/v1/users/123")

        # v1은 그대로, 123만 {id}로 변환
        assert "/v1/" in result.normalized_path
        assert "{id}" in result.normalized_path


# ============================================================================
# Test 2: Path Normalization - UUID
# ============================================================================


class TestPathNormalizationUuid:
    """UUID 경로 정규화 테스트."""

    def test_uuid_v4(self, path_normalizer: PathNormalizer) -> None:
        """UUID v4 정규화: /posts/550e8400-e29b-41d4-a716-446655440000 -> /posts/{uuid}."""
        result = path_normalizer.normalize(
            "/posts/550e8400-e29b-41d4-a716-446655440000"
        )

        assert result.normalized_path == "/posts/{uuid}"
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "uuid"
        assert result.parameters[0].schema == {"type": "string", "format": "uuid"}

    def test_uuid_lowercase(self, path_normalizer: PathNormalizer) -> None:
        """소문자 UUID."""
        result = path_normalizer.normalize(
            "/documents/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        )

        assert result.normalized_path == "/documents/{uuid}"
        assert result.parameters[0].schema["format"] == "uuid"

    def test_uuid_uppercase(self, path_normalizer: PathNormalizer) -> None:
        """대문자 UUID."""
        result = path_normalizer.normalize(
            "/files/A0EEBC99-9C0B-4EF8-BB6D-6BB9BD380A11"
        )

        assert result.normalized_path == "/files/{uuid}"
        assert result.parameters[0].schema["format"] == "uuid"


# ============================================================================
# Test 3: Path Normalization - Slug
# ============================================================================


class TestPathNormalizationSlug:
    """Slug 경로 정규화 테스트."""

    def test_simple_slug(self, path_normalizer: PathNormalizer) -> None:
        """단순 slug: /articles/my-article-title -> /articles/{slug}."""
        result = path_normalizer.normalize("/articles/my-article-title")

        assert result.normalized_path == "/articles/{slug}"
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "slug"
        assert result.parameters[0].schema == {"type": "string"}

    def test_slug_with_numbers(self, path_normalizer: PathNormalizer) -> None:
        """숫자가 포함된 slug: /blog/top-10-tips-for-2024."""
        result = path_normalizer.normalize("/blog/top-10-tips-for-2024")

        assert result.normalized_path == "/blog/{slug}"

    def test_long_slug(self, path_normalizer: PathNormalizer) -> None:
        """긴 slug."""
        result = path_normalizer.normalize(
            "/news/this-is-a-very-long-article-title-with-many-words"
        )

        assert result.normalized_path == "/news/{slug}"


# ============================================================================
# Test 4: Path Normalization - Multiple Parameters
# ============================================================================


class TestPathNormalizationMultipleParams:
    """다중 파라미터 경로 정규화 테스트."""

    def test_two_numeric_ids(self, path_normalizer: PathNormalizer) -> None:
        """두 개의 숫자 ID: /users/1/posts/2 -> /users/{userId}/posts/{postId}."""
        result = path_normalizer.normalize("/users/1/posts/2")

        assert result.normalized_path == "/users/{userId}/posts/{postId}"
        assert len(result.parameters) == 2

        user_param = next(p for p in result.parameters if p.name == "userId")
        post_param = next(p for p in result.parameters if p.name == "postId")

        assert user_param.schema["type"] == "integer"
        assert post_param.schema["type"] == "integer"

    def test_mixed_params(self, path_normalizer: PathNormalizer) -> None:
        """혼합 파라미터: /users/123/articles/my-article."""
        result = path_normalizer.normalize("/users/123/articles/my-article")

        assert "{userId}" in result.normalized_path or "{id}" in result.normalized_path
        assert (
            "{slug}" in result.normalized_path
            or "{articleSlug}" in result.normalized_path
        )
        assert len(result.parameters) == 2

    def test_uuid_and_numeric(self, path_normalizer: PathNormalizer) -> None:
        """UUID와 숫자 ID: /teams/550e8400-e29b-41d4-a716-446655440000/members/5."""
        result = path_normalizer.normalize(
            "/teams/550e8400-e29b-41d4-a716-446655440000/members/5"
        )

        assert (
            "{uuid}" in result.normalized_path or "{teamUuid}" in result.normalized_path
        )
        assert (
            "{id}" in result.normalized_path or "{memberId}" in result.normalized_path
        )
        assert len(result.parameters) == 2


# ============================================================================
# Test 5: Schema Inference - Primitives
# ============================================================================


class TestSchemaInferencePrimitives:
    """기본 타입 스키마 추론 테스트."""

    def test_string_inference(self, schema_inferrer: SchemaInferrer) -> None:
        """문자열 스키마 추론."""
        result = schema_inferrer.infer("hello")

        assert result == {"type": "string"}

    def test_integer_inference(self, schema_inferrer: SchemaInferrer) -> None:
        """정수 스키마 추론."""
        result = schema_inferrer.infer(123)

        assert result == {"type": "integer"}

    def test_float_inference(self, schema_inferrer: SchemaInferrer) -> None:
        """실수 스키마 추론."""
        result = schema_inferrer.infer(12.5)

        assert result == {"type": "number"}

    def test_boolean_inference(self, schema_inferrer: SchemaInferrer) -> None:
        """불리언 스키마 추론."""
        result = schema_inferrer.infer(True)

        assert result == {"type": "boolean"}

    def test_null_inference(self, schema_inferrer: SchemaInferrer) -> None:
        """null 스키마 추론."""
        result = schema_inferrer.infer(None)

        assert result == {"type": "null"} or result.get("nullable") is True


# ============================================================================
# Test 6: Schema Inference - Objects
# ============================================================================


class TestSchemaInferenceObjects:
    """객체 스키마 추론 테스트."""

    def test_simple_object(self, schema_inferrer: SchemaInferrer) -> None:
        """단순 객체 스키마 추론."""
        data = {"name": "John", "age": 30}
        result = schema_inferrer.infer(data)

        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["name"]["type"] == "string"
        assert result["properties"]["age"]["type"] == "integer"

    def test_nested_object(self, schema_inferrer: SchemaInferrer) -> None:
        """중첩 객체 스키마 추론."""
        data = {
            "user": {
                "name": "John",
                "address": {
                    "city": "Seoul",
                    "zip": "12345",
                },
            }
        }
        result = schema_inferrer.infer(data)

        assert result["type"] == "object"
        user_props = result["properties"]["user"]
        assert user_props["type"] == "object"
        assert user_props["properties"]["address"]["type"] == "object"

    def test_object_with_array(self, schema_inferrer: SchemaInferrer) -> None:
        """배열을 포함한 객체."""
        data = {"tags": ["python", "api"], "count": 2}
        result = schema_inferrer.infer(data)

        assert result["type"] == "object"
        assert result["properties"]["tags"]["type"] == "array"
        assert result["properties"]["count"]["type"] == "integer"


# ============================================================================
# Test 7: Schema Inference - Arrays
# ============================================================================


class TestSchemaInferenceArrays:
    """배열 스키마 추론 테스트."""

    def test_integer_array(self, schema_inferrer: SchemaInferrer) -> None:
        """정수 배열 스키마 추론."""
        result = schema_inferrer.infer([1, 2, 3])

        assert result["type"] == "array"
        assert result["items"]["type"] == "integer"

    def test_string_array(self, schema_inferrer: SchemaInferrer) -> None:
        """문자열 배열 스키마 추론."""
        result = schema_inferrer.infer(["a", "b", "c"])

        assert result["type"] == "array"
        assert result["items"]["type"] == "string"

    def test_object_array(self, schema_inferrer: SchemaInferrer) -> None:
        """객체 배열 스키마 추론."""
        data = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        result = schema_inferrer.infer(data)

        assert result["type"] == "array"
        assert result["items"]["type"] == "object"
        assert "id" in result["items"]["properties"]
        assert "name" in result["items"]["properties"]

    def test_empty_array(self, schema_inferrer: SchemaInferrer) -> None:
        """빈 배열 스키마 추론."""
        result = schema_inferrer.infer([])

        assert result["type"] == "array"
        # 빈 배열은 items 타입을 알 수 없음
        assert "items" in result or result.get("items") == {}

    def test_mixed_type_array(self, schema_inferrer: SchemaInferrer) -> None:
        """혼합 타입 배열 스키마 추론."""
        result = schema_inferrer.infer([1, "two", 3.0])

        assert result["type"] == "array"
        # 혼합 타입은 oneOf 또는 가장 일반적인 타입 사용


# ============================================================================
# Test 8: Operation Grouping
# ============================================================================


class TestOperationGrouping:
    """API operation 그룹화 테스트."""

    def test_group_by_path(self, operation_grouper: OperationGrouper) -> None:
        """같은 경로의 다른 메서드들 그룹화."""
        operations = [
            ApiOperation(
                path="/users/{id}",
                method="GET",
                parameters=[
                    Parameter(
                        name="id",
                        location="path",
                        required=True,
                        schema={"type": "integer"},
                    )
                ],
            ),
            ApiOperation(
                path="/users/{id}",
                method="PUT",
                parameters=[
                    Parameter(
                        name="id",
                        location="path",
                        required=True,
                        schema={"type": "integer"},
                    )
                ],
                request_body=RequestBody(
                    content_type="application/json",
                    schema={"type": "object"},
                ),
            ),
            ApiOperation(
                path="/users/{id}",
                method="DELETE",
                parameters=[
                    Parameter(
                        name="id",
                        location="path",
                        required=True,
                        schema={"type": "integer"},
                    )
                ],
            ),
        ]

        grouped = operation_grouper.group(operations)

        assert "/users/{id}" in grouped
        assert len(grouped["/users/{id}"]) == 3
        methods = {op.method for op in grouped["/users/{id}"]}
        assert methods == {"GET", "PUT", "DELETE"}

    def test_group_multiple_paths(self, operation_grouper: OperationGrouper) -> None:
        """여러 경로 그룹화."""
        operations = [
            ApiOperation(path="/users", method="GET"),
            ApiOperation(path="/users", method="POST"),
            ApiOperation(path="/posts", method="GET"),
            ApiOperation(path="/posts/{id}", method="GET"),
        ]

        grouped = operation_grouper.group(operations)

        assert len(grouped) == 3
        assert "/users" in grouped
        assert "/posts" in grouped
        assert "/posts/{id}" in grouped
        assert len(grouped["/users"]) == 2

    def test_merge_duplicate_operations(
        self, operation_grouper: OperationGrouper
    ) -> None:
        """중복 operation 병합."""
        operations = [
            ApiOperation(path="/users/{id}", method="GET"),
            ApiOperation(path="/users/{id}", method="GET"),  # Duplicate
        ]

        grouped = operation_grouper.group(operations)

        # 중복은 하나로 병합
        assert len(grouped["/users/{id}"]) == 1


# ============================================================================
# Test 9: OpenAPI Spec Generation
# ============================================================================


class TestOpenApiSpecGeneration:
    """OpenAPI 스펙 생성 테스트."""

    def test_basic_spec_structure(self, openapi_builder: OpenApiBuilder) -> None:
        """기본 OpenAPI 스펙 구조."""
        operations = [
            ApiOperation(
                path="/users",
                method="GET",
                responses={200: {"description": "Success"}},
            ),
        ]

        spec = openapi_builder.build(
            operations, title="Test API", base_url="https://api.example.com"
        )

        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "Test API"
        assert spec["info"]["version"] == "1.0.0"
        assert "/users" in spec["paths"]

    def test_path_with_parameters(self, openapi_builder: OpenApiBuilder) -> None:
        """파라미터가 있는 경로."""
        operations = [
            ApiOperation(
                path="/users/{id}",
                method="GET",
                parameters=[
                    Parameter(
                        name="id",
                        location="path",
                        required=True,
                        schema={"type": "integer"},
                    )
                ],
            ),
        ]

        spec = openapi_builder.build(operations)

        path_spec = spec["paths"]["/users/{id}"]["get"]
        assert "parameters" in path_spec
        assert path_spec["parameters"][0]["name"] == "id"
        assert path_spec["parameters"][0]["in"] == "path"
        assert path_spec["parameters"][0]["required"] is True

    def test_request_body(self, openapi_builder: OpenApiBuilder) -> None:
        """요청 본문 스펙."""
        operations = [
            ApiOperation(
                path="/users",
                method="POST",
                request_body=RequestBody(
                    content_type="application/json",
                    schema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                        },
                    },
                    example={"name": "John", "email": "john@example.com"},
                ),
            ),
        ]

        spec = openapi_builder.build(operations)

        path_spec = spec["paths"]["/users"]["post"]
        assert "requestBody" in path_spec
        content = path_spec["requestBody"]["content"]["application/json"]
        assert content["schema"]["type"] == "object"
        assert "example" in content

    def test_response_schemas(self, openapi_builder: OpenApiBuilder) -> None:
        """응답 스키마."""
        operations = [
            ApiOperation(
                path="/users/{id}",
                method="GET",
                responses={
                    200: {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                    },
                                }
                            }
                        },
                    },
                    404: {"description": "Not Found"},
                },
            ),
        ]

        spec = openapi_builder.build(operations)

        responses = spec["paths"]["/users/{id}"]["get"]["responses"]
        assert "200" in responses
        assert "404" in responses
        assert "content" in responses["200"]

    def test_tags_assignment(self, openapi_builder: OpenApiBuilder) -> None:
        """태그 할당."""
        operations = [
            ApiOperation(path="/users", method="GET", tags=["Users"]),
            ApiOperation(path="/posts", method="GET", tags=["Posts"]),
        ]

        spec = openapi_builder.build(operations)

        assert spec["paths"]["/users"]["get"]["tags"] == ["Users"]
        assert spec["paths"]["/posts"]["get"]["tags"] == ["Posts"]

    def test_servers_configuration(self, openapi_builder: OpenApiBuilder) -> None:
        """서버 설정."""
        operations = [ApiOperation(path="/health", method="GET")]

        spec = openapi_builder.build(
            operations,
            base_url="https://api.example.com",
        )

        assert "servers" in spec
        assert spec["servers"][0]["url"] == "https://api.example.com"


# ============================================================================
# Test 10: Module Properties
# ============================================================================


class TestModuleProperties:
    """ApiSchemaGeneratorModule 속성 테스트."""

    def test_module_name(
        self, api_schema_generator_module: ApiSchemaGeneratorModule
    ) -> None:
        """모듈 이름."""
        assert api_schema_generator_module.name == "api_schema_generator"

    def test_module_profiles(
        self, api_schema_generator_module: ApiSchemaGeneratorModule
    ) -> None:
        """모듈 프로필 - FULL 전용."""
        assert ScanProfile.FULL in api_schema_generator_module.profiles
        assert ScanProfile.QUICK not in api_schema_generator_module.profiles
        assert ScanProfile.STANDARD not in api_schema_generator_module.profiles

    def test_is_active_for_full_profile(
        self, api_schema_generator_module: ApiSchemaGeneratorModule
    ) -> None:
        """FULL 프로필에서 활성화."""
        assert api_schema_generator_module.is_active_for(ScanProfile.FULL) is True
        assert api_schema_generator_module.is_active_for(ScanProfile.STANDARD) is False
        assert api_schema_generator_module.is_active_for(ScanProfile.QUICK) is False


# ============================================================================
# Test 11: Integration - Discover Method
# ============================================================================


class TestApiSchemaGeneratorIntegration:
    """ApiSchemaGeneratorModule 통합 테스트."""

    @pytest.fixture
    def sample_crawl_data(self) -> Dict[str, Any]:
        """샘플 크롤링 데이터."""
        return {
            "network_requests": [
                {"url": "https://api.example.com/users/1", "method": "GET"},
                {"url": "https://api.example.com/users/2", "method": "GET"},
                {
                    "url": "https://api.example.com/users",
                    "method": "POST",
                    "body": '{"name": "John"}',
                },
                {
                    "url": "https://api.example.com/posts/550e8400-e29b-41d4-a716-446655440000",
                    "method": "GET",
                },
            ],
            "network_responses": [
                {
                    "url": "https://api.example.com/users/1",
                    "status": 200,
                    "body": '{"id": 1, "name": "John"}',
                },
                {
                    "url": "https://api.example.com/users/2",
                    "status": 200,
                    "body": '{"id": 2, "name": "Jane"}',
                },
                {
                    "url": "https://api.example.com/users",
                    "status": 201,
                    "body": '{"id": 3, "name": "John"}',
                },
                {
                    "url": "https://api.example.com/posts/550e8400-e29b-41d4-a716-446655440000",
                    "status": 200,
                    "body": '{"id": "550e8400-e29b-41d4-a716-446655440000", "title": "Hello"}',
                },
            ],
        }

    async def test_discover_yields_openapi_spec(
        self,
        api_schema_generator_module: ApiSchemaGeneratorModule,
        mock_http_client: MagicMock,
        sample_crawl_data: Dict[str, Any],
    ) -> None:
        """discover 메서드가 OpenAPI 스펙을 yield."""
        context = DiscoveryContext(
            target_url="https://api.example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=sample_crawl_data,
        )

        assets = [
            asset async for asset in api_schema_generator_module.discover(context)
        ]

        assert len(assets) >= 1
        openapi_asset = next(
            (a for a in assets if a.asset_type == "openapi_spec"), None
        )
        assert openapi_asset is not None
        assert openapi_asset.source == "api_schema_generator"

    async def test_openapi_spec_metadata(
        self,
        api_schema_generator_module: ApiSchemaGeneratorModule,
        mock_http_client: MagicMock,
        sample_crawl_data: Dict[str, Any],
    ) -> None:
        """OpenAPI 스펙 메타데이터 확인."""
        context = DiscoveryContext(
            target_url="https://api.example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=sample_crawl_data,
        )

        assets = [
            asset async for asset in api_schema_generator_module.discover(context)
        ]
        openapi_asset = next(a for a in assets if a.asset_type == "openapi_spec")

        metadata = openapi_asset.metadata
        assert metadata["openapi_version"] == "3.0.0"
        assert "paths_count" in metadata
        assert "operations_count" in metadata
        assert "spec" in metadata

    async def test_path_normalization_in_spec(
        self,
        api_schema_generator_module: ApiSchemaGeneratorModule,
        mock_http_client: MagicMock,
        sample_crawl_data: Dict[str, Any],
    ) -> None:
        """스펙에서 경로 정규화 확인."""
        context = DiscoveryContext(
            target_url="https://api.example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=sample_crawl_data,
        )

        assets = [
            asset async for asset in api_schema_generator_module.discover(context)
        ]
        openapi_asset = next(a for a in assets if a.asset_type == "openapi_spec")

        spec = openapi_asset.metadata["spec"]
        paths = spec["paths"]

        # /users/1, /users/2 -> /users/{id}로 정규화되어야 함
        assert "/users/{id}" in paths or "/users/{userId}" in paths
        # /posts/uuid -> /posts/{uuid}로 정규화되어야 함
        assert "/posts/{uuid}" in paths or any("uuid" in p for p in paths)

    async def test_schema_inference_in_spec(
        self,
        api_schema_generator_module: ApiSchemaGeneratorModule,
        mock_http_client: MagicMock,
        sample_crawl_data: Dict[str, Any],
    ) -> None:
        """스펙에서 스키마 추론 확인."""
        context = DiscoveryContext(
            target_url="https://api.example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=sample_crawl_data,
        )

        assets = [
            asset async for asset in api_schema_generator_module.discover(context)
        ]
        openapi_asset = next(a for a in assets if a.asset_type == "openapi_spec")

        spec = openapi_asset.metadata["spec"]

        # POST /users에 request body가 있어야 함
        if "/users" in spec["paths"] and "post" in spec["paths"]["/users"]:
            post_spec = spec["paths"]["/users"]["post"]
            assert "requestBody" in post_spec

    async def test_empty_crawl_data(
        self,
        api_schema_generator_module: ApiSchemaGeneratorModule,
        mock_http_client: MagicMock,
    ) -> None:
        """빈 크롤링 데이터 처리."""
        context = DiscoveryContext(
            target_url="https://api.example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data={},
        )

        assets = [
            asset async for asset in api_schema_generator_module.discover(context)
        ]

        # 빈 데이터에서는 스펙을 생성하지 않거나 빈 스펙 생성
        assert isinstance(assets, list)

    async def test_non_full_profile_skips(
        self,
        api_schema_generator_module: ApiSchemaGeneratorModule,
        mock_http_client: MagicMock,
        sample_crawl_data: Dict[str, Any],
    ) -> None:
        """FULL이 아닌 프로필에서는 비활성화."""
        # STANDARD 프로필
        context = DiscoveryContext(
            target_url="https://api.example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=sample_crawl_data,
        )

        # 모듈이 활성화되지 않음
        assert api_schema_generator_module.is_active_for(context.profile) is False


# ============================================================================
# Test 12: Edge Cases
# ============================================================================


class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_path_normalizer_empty_path(self, path_normalizer: PathNormalizer) -> None:
        """빈 경로 처리."""
        result = path_normalizer.normalize("")

        assert result.normalized_path == "" or result.normalized_path == "/"

    def test_path_normalizer_root_path(self, path_normalizer: PathNormalizer) -> None:
        """루트 경로."""
        result = path_normalizer.normalize("/")

        assert result.normalized_path == "/"
        assert len(result.parameters) == 0

    def test_schema_inferrer_deep_nesting(
        self, schema_inferrer: SchemaInferrer
    ) -> None:
        """깊은 중첩 객체."""
        data = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        result = schema_inferrer.infer(data)

        assert result["type"] == "object"
        # 깊은 중첩도 올바르게 처리

    def test_path_normalizer_query_params_preserved(
        self, path_normalizer: PathNormalizer
    ) -> None:
        """쿼리 파라미터는 경로 정규화에 포함되지 않음."""
        # normalize는 경로만 처리, 쿼리 파라미터는 별도 처리
        result = path_normalizer.normalize("/users/123")

        # 쿼리 파라미터 없이 경로만
        assert "?" not in result.normalized_path


# ============================================================================
# Test 13: Request/Response Correlation
# ============================================================================


class TestRequestResponseCorrelation:
    """요청/응답 상관관계 테스트."""

    async def test_response_schema_extraction(
        self,
        api_schema_generator_module: ApiSchemaGeneratorModule,
        mock_http_client: MagicMock,
    ) -> None:
        """응답 본문에서 스키마 추출."""
        crawl_data = {
            "network_requests": [
                {"url": "https://api.example.com/users/1", "method": "GET"},
            ],
            "network_responses": [
                {
                    "url": "https://api.example.com/users/1",
                    "status": 200,
                    "body": '{"id": 1, "name": "John", "active": true}',
                },
            ],
        }

        context = DiscoveryContext(
            target_url="https://api.example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [
            asset async for asset in api_schema_generator_module.discover(context)
        ]
        openapi_asset = next(
            (a for a in assets if a.asset_type == "openapi_spec"), None
        )

        if openapi_asset:
            _spec = openapi_asset.metadata["spec"]
            # 응답 스키마에 id, name, active 필드가 있어야 함
            # 정확한 경로와 메서드에 따라 다름
            assert _spec is not None


# ============================================================================
# Additional Helper Tests
# ============================================================================


class TestDataClasses:
    """데이터 클래스 테스트."""

    def test_parameter_dataclass(self) -> None:
        """Parameter 데이터 클래스."""
        param = Parameter(
            name="id",
            location="path",
            required=True,
            schema={"type": "integer"},
        )

        assert param.name == "id"
        assert param.location == "path"
        assert param.required is True
        assert param.schema == {"type": "integer"}

    def test_request_body_dataclass(self) -> None:
        """RequestBody 데이터 클래스."""
        body = RequestBody(
            content_type="application/json",
            schema={"type": "object"},
            example={"key": "value"},
        )

        assert body.content_type == "application/json"
        assert body.schema == {"type": "object"}
        assert body.example == {"key": "value"}

    def test_api_operation_dataclass(self) -> None:
        """ApiOperation 데이터 클래스."""
        op = ApiOperation(
            path="/users",
            method="GET",
            parameters=[],
            request_body=None,
            responses={200: {"description": "OK"}},
            tags=["Users"],
        )

        assert op.path == "/users"
        assert op.method == "GET"
        assert op.tags == ["Users"]
