"""add_task_target_created_index

Revision ID: 6e9dfb6131e4
Revises: 0469845cfb8e
Create Date: 2026-01-20 23:28:38.614616

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6e9dfb6131e4"
down_revision: Union[str, Sequence[str], None] = "0469845cfb8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite index for task list query optimization."""
    op.create_index(
        "ix_tasks_target_created", "tasks", ["target_id", "created_at"], unique=False
    )


def downgrade() -> None:
    """Remove composite index."""
    op.drop_index("ix_tasks_target_created", table_name="tasks")
