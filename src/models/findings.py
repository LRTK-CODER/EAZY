"""취약점 모델 스텁.

Stage SPEC에서 필드를 채워나간다.
"""

from pydantic import BaseModel


class Vulnerability(BaseModel):
    """취약점 정답 스텁."""
