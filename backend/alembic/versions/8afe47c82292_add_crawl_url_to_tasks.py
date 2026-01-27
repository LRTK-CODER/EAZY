"""add crawl_url to tasks

Revision ID: 8afe47c82292
Revises: 603d3a60dd6f
Create Date: 2026-01-27 22:24:44.830010

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8afe47c82292"
down_revision: Union[str, Sequence[str], None] = "603d3a60dd6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 재귀 크롤링용 URL 컬럼 추가
    op.add_column(
        "tasks", sa.Column("crawl_url", sa.VARCHAR(length=2048), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "crawl_url")
