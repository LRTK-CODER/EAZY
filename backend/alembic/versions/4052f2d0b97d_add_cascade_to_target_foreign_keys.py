"""add_cascade_to_target_foreign_keys

Revision ID: 4052f2d0b97d
Revises: 03d37afa12f2
Create Date: 2026-01-05 21:23:59.905626

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4052f2d0b97d"
down_revision: Union[str, Sequence[str], None] = "03d37afa12f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Target 삭제 시 관련 데이터 자동 삭제를 위한 CASCADE 추가"""

    # 1. tasks.target_id FK 재생성 (CASCADE 추가)
    op.drop_constraint("tasks_target_id_fkey", "tasks", type_="foreignkey")
    op.create_foreign_key(
        "tasks_target_id_fkey",
        "tasks",
        "targets",
        ["target_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 2. assets.target_id FK 재생성 (CASCADE 추가)
    op.drop_constraint("assets_target_id_fkey", "assets", type_="foreignkey")
    op.create_foreign_key(
        "assets_target_id_fkey",
        "assets",
        "targets",
        ["target_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 3. asset_discoveries.task_id FK 재생성 (CASCADE 추가)
    op.drop_constraint(
        "asset_discoveries_task_id_fkey", "asset_discoveries", type_="foreignkey"
    )
    op.create_foreign_key(
        "asset_discoveries_task_id_fkey",
        "asset_discoveries",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. asset_discoveries.asset_id FK 재생성 (CASCADE 추가)
    op.drop_constraint(
        "asset_discoveries_asset_id_fkey", "asset_discoveries", type_="foreignkey"
    )
    op.create_foreign_key(
        "asset_discoveries_asset_id_fkey",
        "asset_discoveries",
        "assets",
        ["asset_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 5. asset_discoveries.parent_asset_id FK 재생성 (CASCADE 추가)
    op.drop_constraint(
        "asset_discoveries_parent_asset_id_fkey",
        "asset_discoveries",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "asset_discoveries_parent_asset_id_fkey",
        "asset_discoveries",
        "assets",
        ["parent_asset_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """CASCADE 제거 (원래 상태로 복원)"""

    # 1. tasks.target_id FK 복원 (ondelete 제거)
    op.drop_constraint("tasks_target_id_fkey", "tasks", type_="foreignkey")
    op.create_foreign_key(
        "tasks_target_id_fkey", "tasks", "targets", ["target_id"], ["id"]
    )

    # 2. assets.target_id FK 복원 (ondelete 제거)
    op.drop_constraint("assets_target_id_fkey", "assets", type_="foreignkey")
    op.create_foreign_key(
        "assets_target_id_fkey", "assets", "targets", ["target_id"], ["id"]
    )

    # 3. asset_discoveries.task_id FK 복원 (ondelete 제거)
    op.drop_constraint(
        "asset_discoveries_task_id_fkey", "asset_discoveries", type_="foreignkey"
    )
    op.create_foreign_key(
        "asset_discoveries_task_id_fkey",
        "asset_discoveries",
        "tasks",
        ["task_id"],
        ["id"],
    )

    # 4. asset_discoveries.asset_id FK 복원 (ondelete 제거)
    op.drop_constraint(
        "asset_discoveries_asset_id_fkey", "asset_discoveries", type_="foreignkey"
    )
    op.create_foreign_key(
        "asset_discoveries_asset_id_fkey",
        "asset_discoveries",
        "assets",
        ["asset_id"],
        ["id"],
    )

    # 5. asset_discoveries.parent_asset_id FK 복원 (ondelete 제거)
    op.drop_constraint(
        "asset_discoveries_parent_asset_id_fkey",
        "asset_discoveries",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "asset_discoveries_parent_asset_id_fkey",
        "asset_discoveries",
        "assets",
        ["parent_asset_id"],
        ["id"],
    )
