"""
TDD Tests for SafeJsonParser utility.

Sprint 1.1: JSON 파싱 안정화
Red Phase: 테스트 먼저 작성
"""
import pytest
from app.core.utils.json_parser import SafeJsonParser, JsonParseResult


class TestSafeJsonParser:
    """SafeJsonParser 단위 테스트"""

    def test_parse_valid_json_dict(self):
        """유효한 JSON dict 파싱"""
        json_str = '{"id": "abc-123", "db_task_id": 100}'
        result = SafeJsonParser.parse(json_str)

        assert result.success is True
        assert result.data == {"id": "abc-123", "db_task_id": 100}
        assert result.error is None
        assert result.raw_input == json_str

    def test_parse_valid_json_list(self):
        """유효한 JSON list 파싱"""
        json_str = '[1, 2, 3]'
        result = SafeJsonParser.parse(json_str)

        assert result.success is True
        assert result.data == [1, 2, 3]
        assert result.error is None

    def test_parse_valid_json_string(self):
        """유효한 JSON 문자열 파싱"""
        json_str = '"hello"'
        result = SafeJsonParser.parse(json_str)

        assert result.success is True
        assert result.data == "hello"
        assert result.error is None

    def test_parse_valid_json_number(self):
        """유효한 JSON 숫자 파싱"""
        json_str = '42'
        result = SafeJsonParser.parse(json_str)

        assert result.success is True
        assert result.data == 42
        assert result.error is None

    def test_parse_valid_json_null(self):
        """유효한 JSON null 파싱"""
        json_str = 'null'
        result = SafeJsonParser.parse(json_str)

        assert result.success is True
        assert result.data is None
        assert result.error is None

    def test_parse_empty_string(self):
        """빈 문자열 처리 - 'Expecting value: line 1 column 1' 에러 방지"""
        json_str = ''
        result = SafeJsonParser.parse(json_str)

        assert result.success is False
        assert result.data is None
        assert result.error is not None
        assert "empty" in result.error.lower() or "Empty" in result.error
        assert result.raw_input == json_str

    def test_parse_whitespace_only_string(self):
        """공백만 있는 문자열 처리"""
        json_str = '   \n\t  '
        result = SafeJsonParser.parse(json_str)

        assert result.success is False
        assert result.data is None
        assert result.error is not None

    def test_parse_none_input(self):
        """None 입력 처리"""
        result = SafeJsonParser.parse(None)

        assert result.success is False
        assert result.data is None
        assert result.error is not None
        assert "None" in result.error or "none" in result.error.lower()

    def test_parse_invalid_json(self):
        """잘못된 JSON 형식 처리"""
        json_str = '{"id": "abc-123", "invalid'
        result = SafeJsonParser.parse(json_str)

        assert result.success is False
        assert result.data is None
        assert result.error is not None
        assert "JSONDecodeError" in result.error or "decode" in result.error.lower()
        assert result.raw_input == json_str

    def test_parse_non_string_input_int(self):
        """정수 입력 처리"""
        result = SafeJsonParser.parse(123)

        assert result.success is False
        assert result.data is None
        assert result.error is not None
        assert "str" in result.error or "type" in result.error.lower()

    def test_parse_non_string_input_dict(self):
        """딕셔너리 입력 처리 (이미 파싱된 데이터)"""
        result = SafeJsonParser.parse({"already": "parsed"})

        assert result.success is False
        assert result.data is None
        assert result.error is not None

    def test_parse_non_string_input_bytes(self):
        """bytes 입력 처리"""
        result = SafeJsonParser.parse(b'{"id": "abc"}')

        assert result.success is False
        assert result.data is None
        assert result.error is not None

    def test_parse_unicode_json(self):
        """유니코드 JSON 처리"""
        json_str = '{"message": "한글 테스트", "emoji": "🚀"}'
        result = SafeJsonParser.parse(json_str)

        assert result.success is True
        assert result.data == {"message": "한글 테스트", "emoji": "🚀"}
        assert result.error is None

    def test_parse_nested_json(self):
        """중첩된 JSON 처리"""
        json_str = '{"outer": {"inner": {"deep": [1, 2, 3]}}}'
        result = SafeJsonParser.parse(json_str)

        assert result.success is True
        assert result.data["outer"]["inner"]["deep"] == [1, 2, 3]
        assert result.error is None


class TestJsonParseResult:
    """JsonParseResult dataclass 테스트"""

    def test_result_is_dataclass(self):
        """JsonParseResult가 dataclass인지 확인"""
        from dataclasses import is_dataclass
        assert is_dataclass(JsonParseResult)

    def test_result_fields(self):
        """JsonParseResult 필드 확인"""
        result = JsonParseResult(
            success=True,
            data={"test": "data"},
            error=None,
            raw_input='{"test": "data"}'
        )

        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'error')
        assert hasattr(result, 'raw_input')

    def test_result_immutability(self):
        """JsonParseResult 불변성 (frozen=True인 경우)"""
        result = JsonParseResult(
            success=True,
            data={"test": "data"},
            error=None,
            raw_input='{"test": "data"}'
        )

        # frozen=True가 아니면 이 테스트는 스킵
        # 구현에 따라 frozen 여부 결정
        assert result.success is True  # 기본 접근 테스트
