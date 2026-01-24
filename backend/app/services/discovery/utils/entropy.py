"""Entropy Calculator 유틸리티.

Shannon entropy를 계산하여 랜덤 문자열(API 키, 시크릿 등)을 탐지합니다.

Shannon Entropy:
- 문자열의 무작위성을 측정 (0 ~ 8 비트)
- 높은 entropy = 높은 무작위성 = 잠재적 시크릿
- 일반 텍스트: ~3.5 bits
- 랜덤 문자열: ~4.5+ bits
"""

import math
from collections import Counter
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class EntropyResult:
    """엔트로피 계산 결과.

    Attributes:
        value: Shannon entropy 값 (0-8 비트)
        is_high_entropy: threshold 초과 여부
        character_distribution: 각 문자의 출현 횟수
    """

    value: float
    is_high_entropy: bool
    character_distribution: Dict[str, int]


class EntropyCalculator:
    """Shannon Entropy 계산기.

    문자열의 무작위성을 측정하여 잠재적인 시크릿/API 키를 탐지합니다.

    Example:
        >>> calculator = EntropyCalculator()
        >>> result = calculator.calculate("sk_live_abc123xyz789")
        >>> print(f"Entropy: {result.value:.2f}, High: {result.is_high_entropy}")
        Entropy: 4.58, High: True

        >>> calculator.is_high_entropy("normal text")
        False
    """

    DEFAULT_THRESHOLD: float = 4.5

    def __init__(self, threshold: float = DEFAULT_THRESHOLD) -> None:
        """Initialize EntropyCalculator.

        Args:
            threshold: High entropy 판단 기준값 (기본값: 4.5)
        """
        self.threshold = threshold

    def calculate(self, text: str) -> EntropyResult:
        """문자열의 Shannon entropy 계산.

        Shannon Entropy 공식:
            H = -sum(p(x) * log2(p(x))) for each character x

        Args:
            text: 분석할 문자열

        Returns:
            EntropyResult: entropy 값, high entropy 여부, 문자 분포
        """
        if not text:
            return EntropyResult(
                value=0.0,
                is_high_entropy=False,
                character_distribution={},
            )

        # 문자 빈도 계산
        char_counts = Counter(text)
        length = len(text)

        # Shannon entropy 계산
        entropy = 0.0
        for count in char_counts.values():
            if count > 0:
                probability = count / length
                entropy -= probability * math.log2(probability)

        # High entropy 판단
        is_high = entropy > self.threshold

        return EntropyResult(
            value=entropy,
            is_high_entropy=is_high,
            character_distribution=dict(char_counts),
        )

    def is_high_entropy(self, text: str) -> bool:
        """문자열이 high entropy인지 빠르게 확인.

        Args:
            text: 분석할 문자열

        Returns:
            True if entropy > threshold, False otherwise
        """
        return self.calculate(text).is_high_entropy
