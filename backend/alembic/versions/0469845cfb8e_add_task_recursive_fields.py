"""add_task_recursive_fields

Revision ID: 0469845cfb8e
Revises: 1fbc4ba81531
Create Date: 2026-01-19 00:59:58.879048

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0469845cfb8e"
down_revision: Union[str, Sequence[str], None] = "1fbc4ba81531"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add recursive task support with depth tracking and parent relationship."""
    # 1. depth 컬럼 추가 (기존 데이터는 0으로 설정)
    op.add_column(
        "tasks", sa.Column("depth", sa.Integer(), nullable=False, server_default="0")
    )

    # 2. max_depth 컬럼 추가 (기존 데이터는 3으로 설정)
    op.add_column(
        "tasks",
        sa.Column("max_depth", sa.Integer(), nullable=False, server_default="3"),
    )

    # 3. parent_task_id 컬럼 추가 (root task는 NULL)
    op.add_column("tasks", sa.Column("parent_task_id", sa.Integer(), nullable=True))

    # 4. Self-referencing FK 생성 (부모 삭제 시 SET NULL)
    op.create_foreign_key(
        "fk_tasks_parent_task_id",
        "tasks",
        "tasks",
        ["parent_task_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 5. parent_task_id 인덱스 (FK 성능 최적화)
    op.create_index("ix_tasks_parent_task_id", "tasks", ["parent_task_id"])

    # 6. target + depth 복합 인덱스
    op.create_index("ix_tasks_target_depth", "tasks", ["target_id", "depth"])


def downgrade() -> None:
    """Remove recursive task fields.

    WARNING: Task hierarchy information will be permanently deleted.
    """
    # 1. 인덱스 삭제
    op.drop_index("ix_tasks_target_depth", table_name="tasks")
    op.drop_index("ix_tasks_parent_task_id", table_name="tasks")

    # 2. FK 삭제
    op.drop_constraint("fk_tasks_parent_task_id", "tasks", type_="foreignkey")

    # 3. 컬럼 삭제
    op.drop_column("tasks", "parent_task_id")
    op.drop_column("tasks", "max_depth")
    op.drop_column("tasks", "depth")
