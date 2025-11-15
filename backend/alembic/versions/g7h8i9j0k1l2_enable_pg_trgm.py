"""enable_pg_trgm

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2025-01-15 10:06:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'  # After claim_links table
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for full-text search (PostgreSQL only)
    # This is safe to run even if extension already exists
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")


def downgrade() -> None:
    # Note: We don't drop the extension as it might be used by other tables
    # If you need to drop it, uncomment the line below (use with caution)
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
    pass

