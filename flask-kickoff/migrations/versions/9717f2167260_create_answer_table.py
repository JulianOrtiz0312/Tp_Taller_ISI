"""create answer table

Revision ID: 9717f2167260
Revises: 33ec7381e451
Create Date: 2026-11-26 07:04:28.706117

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9717f2167260"
down_revision: str | Sequence[str] | None = "33ec7381e451"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "answer",
        sa.Column("id_answer", sa.Integer(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "fecha",
            sa.Date(),
            server_default=sa.text("(CURRENT_DATE)"),
            nullable=False,
        ),
        sa.Column("accept", sa.Boolean(), nullable=False),
        sa.Column("id_Autor", sa.Integer(), nullable=True),
        sa.Column("id_Question", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_Autor"],
            ["user.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["id_Question"],
            ["question.id"],
            ondelete="NO ACTION",
        ),
        sa.PrimaryKeyConstraint("id_answer"),
    )


def downgrade() -> None:
    op.drop_table("answer")
