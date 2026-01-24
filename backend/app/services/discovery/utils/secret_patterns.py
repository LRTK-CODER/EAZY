"""Secret Patterns 유틸리티.

시크릿/API 키 패턴을 탐지합니다.
- AWS Access Key, Secret Key
- Stripe API Keys
- GitHub Tokens
- Generic API Keys, Passwords
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Pattern

from app.services.discovery.utils.entropy import EntropyCalculator


class SecretType(str, Enum):
    """시크릿 유형."""

    API_KEY = "api_key"
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    PRIVATE_KEY = "private_key"
    JWT = "jwt"
    OAUTH_TOKEN = "oauth_token"
    PASSWORD = "password"
    GENERIC_SECRET = "generic_secret"
    STRIPE_KEY = "stripe_key"
    GITHUB_TOKEN = "github_token"

    # Aliases for test compatibility
    @classmethod
    def _missing_(cls, value: object) -> Optional["SecretType"]:
        """Handle missing values for compatibility."""
        return None


@dataclass(frozen=True)
class SecretPattern:
    """시크릿 패턴 정의.

    Attributes:
        name: 패턴 이름
        pattern: 컴파일된 정규식 패턴
        secret_type: 시크릿 유형
        confidence: 신뢰도 (0.0-1.0)
        description: 패턴 설명
    """

    name: str
    pattern: Pattern[str]
    secret_type: SecretType
    confidence: float
    description: str


@dataclass
class SecretMatch:
    """시크릿 탐지 결과.

    Attributes:
        secret_type: 시크릿 유형
        matched_value: 매칭된 값
        pattern_name: 매칭된 패턴 이름
        confidence: 신뢰도
        line_number: 줄 번호 (optional)
        context: 주변 문맥 (optional)
        is_false_positive: False positive 여부
        entropy: 엔트로피 값 (optional)
    """

    secret_type: SecretType
    matched_value: str
    pattern_name: str
    confidence: float
    line_number: Optional[int] = None
    context: Optional[str] = None
    is_false_positive: bool = False
    entropy: Optional[float] = None


class SecretPatterns:
    """시크릿 패턴 매칭 엔진.

    Known secret patterns:
    - AWS: AKIA..., ASIA...
    - Stripe: sk_live_..., pk_live_...
    - GitHub: ghp_..., gho_..., ghu_...
    - Generic: api_key=, secret=, password=

    Example:
        >>> patterns = SecretPatterns()
        >>> matches = patterns.scan('const KEY = "AKIAIOSFODNN7EXAMPLE"')
        >>> print(matches[0].secret_type)
        SecretType.AWS_ACCESS_KEY
    """

    # 패턴 정의
    PATTERNS: List[SecretPattern] = [
        # AWS Access Key ID
        SecretPattern(
            name="aws_access_key",
            pattern=re.compile(
                r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"
            ),
            secret_type=SecretType.AWS_ACCESS_KEY,
            confidence=0.95,
            description="AWS Access Key ID",
        ),
        # AWS Secret Key (40 chars base64)
        SecretPattern(
            name="aws_secret_key",
            pattern=re.compile(
                r'(?:aws_secret_access_key|aws_secret_key|secret_key)\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?',
                re.IGNORECASE,
            ),
            secret_type=SecretType.AWS_SECRET_KEY,
            confidence=0.90,
            description="AWS Secret Access Key",
        ),
        # Stripe API Keys
        SecretPattern(
            name="stripe_secret_key",
            pattern=re.compile(r"sk_live_[a-zA-Z0-9]{24,}"),
            secret_type=SecretType.STRIPE_KEY,
            confidence=0.95,
            description="Stripe Secret Key",
        ),
        SecretPattern(
            name="stripe_publishable_key",
            pattern=re.compile(r"pk_live_[a-zA-Z0-9]{24,}"),
            secret_type=SecretType.STRIPE_KEY,
            confidence=0.90,
            description="Stripe Publishable Key",
        ),
        # GitHub Tokens
        SecretPattern(
            name="github_pat",
            pattern=re.compile(r"ghp_[a-zA-Z0-9]{36,255}"),
            secret_type=SecretType.GITHUB_TOKEN,
            confidence=0.95,
            description="GitHub Personal Access Token",
        ),
        SecretPattern(
            name="github_oauth",
            pattern=re.compile(r"gho_[a-zA-Z0-9]{36,255}"),
            secret_type=SecretType.GITHUB_TOKEN,
            confidence=0.95,
            description="GitHub OAuth Token",
        ),
        SecretPattern(
            name="github_user_to_server",
            pattern=re.compile(r"ghu_[a-zA-Z0-9]{36,255}"),
            secret_type=SecretType.GITHUB_TOKEN,
            confidence=0.95,
            description="GitHub User-to-Server Token",
        ),
        # Private Keys
        SecretPattern(
            name="private_key",
            pattern=re.compile(
                r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
            ),
            secret_type=SecretType.PRIVATE_KEY,
            confidence=0.99,
            description="Private Key Header",
        ),
        # JWT
        SecretPattern(
            name="jwt",
            pattern=re.compile(r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"),
            secret_type=SecretType.JWT,
            confidence=0.85,
            description="JSON Web Token",
        ),
        # Generic API Key patterns
        SecretPattern(
            name="generic_api_key",
            pattern=re.compile(
                r'(?:api_key|apikey|api-key)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
                re.IGNORECASE,
            ),
            secret_type=SecretType.API_KEY,
            confidence=0.70,
            description="Generic API Key",
        ),
        # Generic Secret patterns
        SecretPattern(
            name="generic_secret",
            pattern=re.compile(
                r'(?:secret|token|password|passwd|pwd)\s*[=:]\s*["\']?([a-zA-Z0-9_\-!@#$%^&*]{8,})["\']?',
                re.IGNORECASE,
            ),
            secret_type=SecretType.GENERIC_SECRET,
            confidence=0.60,
            description="Generic Secret",
        ),
        # Password in URL
        SecretPattern(
            name="password_in_url",
            pattern=re.compile(
                r"(?:https?://)[^:]+:([^@]+)@",
                re.IGNORECASE,
            ),
            secret_type=SecretType.PASSWORD,
            confidence=0.85,
            description="Password in URL",
        ),
    ]

    # False positive 필터
    FALSE_POSITIVE_PATTERNS: List[Pattern[str]] = [
        re.compile(
            r"example|placeholder|dummy|test|fake|xxx+|your[-_]?", re.IGNORECASE
        ),
        re.compile(r"^[A-Z_]+$"),  # 상수 이름만
        re.compile(r"^[0]+$"),  # 모두 0
        re.compile(r"^\*+$"),  # 모두 *
        re.compile(r"<[^>]+>"),  # HTML 태그
        re.compile(r"\$\{[^}]+\}"),  # 템플릿 변수
    ]

    def __init__(self, entropy_calculator: Optional[EntropyCalculator] = None) -> None:
        """Initialize SecretPatterns.

        Args:
            entropy_calculator: EntropyCalculator 인스턴스 (optional)
        """
        self.entropy_calculator = entropy_calculator or EntropyCalculator()

    def scan(self, content: str) -> List[SecretMatch]:
        """콘텐츠에서 시크릿 스캔.

        Args:
            content: 스캔할 콘텐츠

        Returns:
            탐지된 SecretMatch 목록
        """
        matches: List[SecretMatch] = []

        for pattern_def in self.PATTERNS:
            for match in pattern_def.pattern.finditer(content):
                # 매칭된 값 추출
                if match.groups():
                    matched_value = match.group(1)
                else:
                    matched_value = match.group(0)

                # False positive 체크
                is_fp = self.is_false_positive(matched_value, content)

                # 엔트로피 계산
                entropy = self.entropy_calculator.calculate(matched_value).value

                # 신뢰도 조정 (엔트로피 기반)
                adjusted_confidence = pattern_def.confidence
                if entropy < 3.0:  # 낮은 엔트로피 → 신뢰도 감소
                    adjusted_confidence *= 0.7
                elif entropy > 4.5:  # 높은 엔트로피 → 신뢰도 유지/증가
                    adjusted_confidence = min(1.0, adjusted_confidence * 1.1)

                matches.append(
                    SecretMatch(
                        secret_type=pattern_def.secret_type,
                        matched_value=matched_value,
                        pattern_name=pattern_def.name,
                        confidence=adjusted_confidence,
                        is_false_positive=is_fp,
                        entropy=entropy,
                    )
                )

        return matches

    def scan_with_context(
        self, content: str, context_lines: int = 2
    ) -> List[SecretMatch]:
        """주변 컨텍스트와 함께 시크릿 스캔.

        Args:
            content: 스캔할 콘텐츠
            context_lines: 컨텍스트로 포함할 줄 수

        Returns:
            컨텍스트가 포함된 SecretMatch 목록
        """
        lines = content.split("\n")
        matches: List[SecretMatch] = []

        for line_num, line in enumerate(lines, start=1):
            line_matches = self.scan(line)

            for match in line_matches:
                # 컨텍스트 추출
                start_line = max(0, line_num - context_lines - 1)
                end_line = min(len(lines), line_num + context_lines)
                context = "\n".join(lines[start_line:end_line])

                match.line_number = line_num
                match.context = context
                matches.append(match)

        return matches

    def is_false_positive(self, matched_value: str, context: str = "") -> bool:
        """False positive 여부 판단.

        Args:
            matched_value: 매칭된 값
            context: 주변 문맥

        Returns:
            True if false positive, False otherwise
        """
        # 패턴 기반 필터링
        for fp_pattern in self.FALSE_POSITIVE_PATTERNS:
            if fp_pattern.search(matched_value):
                return True

        # 길이 기반 필터링
        if len(matched_value) < 8:
            return True

        # 반복 문자 체크
        if len(set(matched_value)) < 4:
            return True

        return False
