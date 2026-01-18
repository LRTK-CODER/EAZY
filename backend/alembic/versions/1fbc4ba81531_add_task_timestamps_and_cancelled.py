"""add_task_timestamps_and_cancelled

Revision ID: 1fbc4ba81531
Revises: 4052f2d0b97d
Create Date: 2026-01-08 20:42:55.085820

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1fbc4ba81531"
down_revision: Union[str, Sequence[str], None] = "4052f2d0b97d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timestamp columns and CANCELLED enum value to tasks table."""
    # Add timestamp columns
    op.add_column("tasks", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("tasks", sa.Column("completed_at", sa.DateTime(), nullable=True))

    # Add CANCELLED to TaskStatus enum
    op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade() -> None:
    """Remove timestamp columns from tasks table."""
    op.drop_column("tasks", "completed_at")
    op.drop_column("tasks", "started_at")
    # Note: PostgreSQL doesn't support removing enum values
    # CANCELLED will remain but be unused after downgrade
