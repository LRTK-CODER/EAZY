"""체인 결과 모델 스텁.

Stage SPEC에서 필드를 채워나간다.
"""

from pydantic import BaseModel


class ChainResult(BaseModel):
    """공격 체인 결과 스텁."""
