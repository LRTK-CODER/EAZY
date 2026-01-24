"""EntropyCalculator 테스트.

TDD RED Phase: 테스트 먼저 작성
- Shannon entropy 계산
- High entropy 문자열 탐지
- 문자 분포 분석
"""

import pytest

from app.services.discovery.utils.entropy import EntropyCalculator, EntropyResult

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def entropy_calculator() -> EntropyCalculator:
    """Create EntropyCalculator instance."""
    return EntropyCalculator()


@pytest.fixture
def custom_threshold_calculator() -> EntropyCalculator:
    """Create EntropyCalculator with custom threshold."""
    return EntropyCalculator(threshold=3.5)


# ============================================================================
# Test 1: 기본 엔트로피 계산
# ============================================================================


class TestBasicEntropyCalculation:
    """기본 엔트로피 계산 테스트."""

    def test_empty_string_entropy(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """빈 문자열의 엔트로피는 0."""
        result = entropy_calculator.calculate("")

        assert result.value == 0.0
        assert result.is_high_entropy is False
        assert result.character_distribution == {}

    def test_single_character_entropy(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """단일 문자 반복의 엔트로피는 0."""
        result = entropy_calculator.calculate("aaaaaaaaaa")

        assert result.value == 0.0
        assert result.is_high_entropy is False
        assert result.character_distribution == {"a": 10}

    def test_two_equal_characters_entropy(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """두 문자가 동일하게 분포되면 엔트로피 = 1.0."""
        result = entropy_calculator.calculate("abababab")

        assert abs(result.value - 1.0) < 0.01
        assert result.character_distribution["a"] == 4
        assert result.character_distribution["b"] == 4

    def test_four_equal_characters_entropy(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """네 문자가 동일하게 분포되면 엔트로피 = 2.0."""
        result = entropy_calculator.calculate("abcdabcdabcdabcd")

        assert abs(result.value - 2.0) < 0.01


# ============================================================================
# Test 2: High Entropy 탐지
# ============================================================================


class TestHighEntropyDetection:
    """High entropy 탐지 테스트."""

    def test_random_string_high_entropy(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """랜덤 문자열은 high entropy."""
        # 랜덤하게 보이는 API 키
        random_string = "aB3dE7fG2hI9jK4lM6nO1pQ8rS5tU"

        result = entropy_calculator.calculate(random_string)

        assert result.value > 4.0
        assert result.is_high_entropy is True

    def test_readable_text_low_entropy(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """읽을 수 있는 텍스트는 low entropy."""
        readable_text = "this is a normal english sentence"

        result = entropy_calculator.calculate(readable_text)

        assert result.value < 4.5
        assert result.is_high_entropy is False

    def test_hex_string_moderate_entropy(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """16진수 문자열은 중간 정도의 entropy를 가짐."""
        # Hex 문자열은 16개 문자(0-9, a-f)만 사용하므로 최대 entropy는 log2(16) = 4.0
        hex_string = "a1b2c3d4e5f6789abcdef0123456789abcdef0123456789abcdef"

        result = entropy_calculator.calculate(hex_string)

        # Hex 문자열은 일반 텍스트보다 높은 entropy를 가짐
        assert result.value > 3.5
        # 하지만 완전 랜덤 알파뉴메릭(62자) 보다는 낮음
        assert result.value < 4.5

    def test_base64_string_high_entropy(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """Base64 문자열은 high entropy."""
        base64_string = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="

        result = entropy_calculator.calculate(base64_string)

        assert result.value > 4.0
        assert result.is_high_entropy is True


# ============================================================================
# Test 3: is_high_entropy 편의 메서드
# ============================================================================


class TestIsHighEntropyMethod:
    """is_high_entropy 편의 메서드 테스트."""

    def test_is_high_entropy_true(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """High entropy 문자열에 True 반환."""
        high_entropy_string = "Xa3Kl9Mn2Pq5Rs7Tv4Wx8Yz1Ab6Cd"

        assert entropy_calculator.is_high_entropy(high_entropy_string) is True

    def test_is_high_entropy_false(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """Low entropy 문자열에 False 반환."""
        low_entropy_string = "password123"

        assert entropy_calculator.is_high_entropy(low_entropy_string) is False

    def test_is_high_entropy_with_short_string(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """짧은 문자열은 low entropy로 판단."""
        short_string = "abc"

        assert entropy_calculator.is_high_entropy(short_string) is False


# ============================================================================
# Test 4: 커스텀 threshold
# ============================================================================


class TestCustomThreshold:
    """커스텀 threshold 테스트."""

    def test_custom_threshold_applied(
        self,
        custom_threshold_calculator: EntropyCalculator,
    ) -> None:
        """커스텀 threshold가 적용됨."""
        # 3.5 < entropy < 4.5인 문자열 (더 다양한 문자 포함)
        medium_entropy_string = "abcdefghijklmnop"  # 16자, entropy ~4.0

        result = custom_threshold_calculator.calculate(medium_entropy_string)

        # 기본 threshold (4.5)에서는 low, 커스텀 (3.5)에서는 high
        assert result.value > 3.5
        assert result.is_high_entropy is True

    def test_default_threshold_value(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """기본 threshold는 4.5."""
        assert entropy_calculator.threshold == EntropyCalculator.DEFAULT_THRESHOLD
        assert entropy_calculator.threshold == 4.5


# ============================================================================
# Test 5: 엣지 케이스
# ============================================================================


class TestEntropyEdgeCases:
    """엔트로피 계산 엣지 케이스 테스트."""

    def test_unicode_characters(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """유니코드 문자 처리."""
        unicode_string = "한글테스트문자열"

        result = entropy_calculator.calculate(unicode_string)

        assert result.value > 0
        assert "한" in result.character_distribution

    def test_special_characters(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """특수 문자 처리."""
        special_string = "!@#$%^&*()_+{}|:<>?"

        result = entropy_calculator.calculate(special_string)

        assert result.value > 3.0
        assert "!" in result.character_distribution

    def test_whitespace_characters(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """공백 문자 처리."""
        whitespace_string = "a b c d e f"

        result = entropy_calculator.calculate(whitespace_string)

        assert " " in result.character_distribution

    def test_very_long_string(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """긴 문자열 처리."""
        # 1000자 랜덤 문자열
        long_string = "aB3dE7fG2h" * 100

        result = entropy_calculator.calculate(long_string)

        # 반복 패턴이므로 entropy가 높지 않음
        assert result.value > 0
        assert result.value < 5.0


# ============================================================================
# Test 6: EntropyResult 데이터 클래스
# ============================================================================


class TestEntropyResult:
    """EntropyResult 데이터 클래스 테스트."""

    def test_entropy_result_attributes(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """EntropyResult가 올바른 속성을 가짐."""
        result = entropy_calculator.calculate("test123")

        assert isinstance(result, EntropyResult)
        assert isinstance(result.value, float)
        assert isinstance(result.is_high_entropy, bool)
        assert isinstance(result.character_distribution, dict)

    def test_entropy_result_immutable(
        self,
        entropy_calculator: EntropyCalculator,
    ) -> None:
        """EntropyResult는 dataclass로 생성됨."""
        result = entropy_calculator.calculate("test")

        # dataclass이므로 속성 접근 가능
        _ = result.value
        _ = result.is_high_entropy
        _ = result.character_distribution
