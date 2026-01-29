"""change_asset_url_path_to_text

Revision ID: 371a28605bcb
Revises: 8afe47c82292
Create Date: 2026-01-28 00:38:57.754896

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "371a28605bcb"
down_revision: Union[str, Sequence[str], None] = "8afe47c82292"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Change url/path columns from VARCHAR(2048) to TEXT."""
    # Assets table: url and path columns
    op.alter_column(
        "assets",
        "url",
        existing_type=sa.VARCHAR(length=2048),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.alter_column(
        "assets",
        "path",
        existing_type=sa.VARCHAR(length=2048),
        type_=sa.Text(),
        existing_nullable=False,
    )

    # Tasks table: crawl_url column
    op.alter_column(
        "tasks",
        "crawl_url",
        existing_type=sa.VARCHAR(length=2048),
        type_=sa.Text(),
        existing_nullable=True,
    )

    # Targets table: url column
    op.alter_column(
        "targets",
        "url",
        existing_type=sa.VARCHAR(length=2048),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema: Revert url/path columns from TEXT to VARCHAR(2048)."""
    # Targets table: url column
    op.alter_column(
        "targets",
        "url",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=2048),
        existing_nullable=False,
    )

    # Tasks table: crawl_url column
    op.alter_column(
        "tasks",
        "crawl_url",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=2048),
        existing_nullable=True,
    )

    # Assets table: url and path columns
    op.alter_column(
        "assets",
        "path",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=2048),
        existing_nullable=False,
    )
    op.alter_column(
        "assets",
        "url",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=2048),
        existing_nullable=False,
    )
