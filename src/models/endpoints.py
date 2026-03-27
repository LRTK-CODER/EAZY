"""엔드포인트 모델 스텁.

Stage SPEC에서 필드를 채워나간다.
"""

from pydantic import BaseModel


class Endpoint(BaseModel):
    """엔드포인트 정답 스텁."""
