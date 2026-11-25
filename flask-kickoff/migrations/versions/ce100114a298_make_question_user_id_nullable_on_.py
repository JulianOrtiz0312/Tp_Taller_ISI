"""make question user_id nullable on delete set null

Revision ID: ce100114a298
Revises: 319fd0d84f8d
Create Date: 2026-11-25 07:53:40.386822

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ce100114a298"
down_revision: str | Sequence[str] | None = "319fd0d84f8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    naming_convention = {
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
    with op.batch_alter_table(
        "question", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_question_user_id_user", type_="foreignkey")
        batch_op.alter_column(
            "user_id",
            existing_type=sa.INTEGER(),
            nullable=True,
        )
        batch_op.create_foreign_key(
            "fk_question_user_id_user",
            "user",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    naming_convention = {
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
    with op.batch_alter_table(
        "question", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_question_user_id_user", type_="foreignkey")
        batch_op.alter_column(
            "user_id",
            existing_type=sa.INTEGER(),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_question_user_id_user",
            "user",
            ["user_id"],
            ["id"],
        )
