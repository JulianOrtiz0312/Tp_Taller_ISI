"""Merge migration heads

Revision ID: 74f7d87f562f
Revises: 613b9d3052f5, 7ab3adff9395
Create Date: 2026-11-24 16:32:08.828337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74f7d87f562f'
down_revision: Union[str, Sequence[str], None] = ('613b9d3052f5', '7ab3adff9395')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
