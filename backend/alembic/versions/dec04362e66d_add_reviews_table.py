"""add_reviews_table

Revision ID: dec04362e66d
Revises: 88227060e57c
Create Date: 2025-11-15 02:26:28.845719

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dec04362e66d'
down_revision: Union[str, None] = '88227060e57c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

