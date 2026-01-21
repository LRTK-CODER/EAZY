"""add_target_search_indexes

Revision ID: 603d3a60dd6f
Revises: 6e9dfb6131e4
Create Date: 2026-01-21 22:48:57.929744

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "603d3a60dd6f"
down_revision: Union[str, Sequence[str], None] = "6e9dfb6131e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for target search optimization."""
    # P0: project_id index (critical for filtering)
    op.create_index(
        "ix_targets_project_id",
        "targets",
        ["project_id"],
        unique=False,
    )

    # P0: Composite index for search results ordering
    op.create_index(
        "ix_targets_project_created",
        "targets",
        ["project_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove target search indexes."""
    op.drop_index("ix_targets_project_created", table_name="targets")
    op.drop_index("ix_targets_project_id", table_name="targets")
