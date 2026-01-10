"""
Safe JSON Parser utility.

Sprint 1.1: JSON 파싱 안정화

'Expecting value: line 1 column 1 (char 0)' 에러를 방지하기 위한
안전한 JSON 파싱 유틸리티입니다.

Usage:
    from app.core.utils.json_parser import SafeJsonParser

    result = SafeJsonParser.parse(json_string)
    if result.success:
        process(result.data)
    else:
        logger.warning(f"JSON parse failed: {result.error}")
"""
import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class JsonParseResult:
    """
    JSON 파싱 결과를 담는 데이터 클래스.

    Attributes:
        success: 파싱 성공 여부
        data: 파싱된 데이터 (성공 시) 또는 None (실패 시)
        error: 에러 메시지 (실패 시) 또는 None (성공 시)
        raw_input: 원본 입력 문자열
    """
    success: bool
    data: Optional[Any]
    error: Optional[str]
    raw_input: str


class SafeJsonParser:
    """
    안전한 JSON 파싱 유틸리티.

    예외를 발생시키지 않고 JsonParseResult를 반환합니다.
    빈 문자열, None, 잘못된 타입 등 모든 에지 케이스를 처리합니다.
    """

    @staticmethod
    def parse(json_str: Any) -> JsonParseResult:
        """
        JSON 문자열을 안전하게 파싱합니다.

        Args:
            json_str: 파싱할 JSON 문자열 (또는 잘못된 타입)

        Returns:
            JsonParseResult: 파싱 결과

        Examples:
            >>> result = SafeJsonParser.parse('{"id": "abc"}')
            >>> result.success
            True
            >>> result.data
            {'id': 'abc'}

            >>> result = SafeJsonParser.parse('')
            >>> result.success
            False
            >>> result.error
            'Empty string'
        """
        # None 체크
        if json_str is None:
            return JsonParseResult(
                success=False,
                data=None,
                error="Input is None",
                raw_input=""
            )

        # 타입 체크 - str만 허용
        if not isinstance(json_str, str):
            return JsonParseResult(
                success=False,
                data=None,
                error=f"Expected str type, got {type(json_str).__name__}",
                raw_input=str(json_str)[:200]  # 너무 긴 경우 잘라냄
            )

        # 빈 문자열 또는 공백만 있는 경우
        if not json_str.strip():
            return JsonParseResult(
                success=False,
                data=None,
                error="Empty string" if not json_str else "Whitespace only string",
                raw_input=json_str
            )

        # JSON 파싱 시도
        try:
            data = json.loads(json_str)
            return JsonParseResult(
                success=True,
                data=data,
                error=None,
                raw_input=json_str
            )
        except json.JSONDecodeError as e:
            return JsonParseResult(
                success=False,
                data=None,
                error=f"JSONDecodeError: {e}",
                raw_input=json_str
            )
        except Exception as e:
            # 예상치 못한 예외 처리
            return JsonParseResult(
                success=False,
                data=None,
                error=f"Unexpected error: {type(e).__name__}: {e}",
                raw_input=json_str
            )
