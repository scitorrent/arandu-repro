"""add_paper_versions_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-01-15 10:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'paper_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aid', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('pdf_path', sa.String(length=1000), nullable=False),
        sa.Column('meta_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['aid'], ['papers.aid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('aid', 'version', name='uq_paper_versions_aid_version'),
        sa.CheckConstraint('version >= 1', name='check_version_positive'),
    )
    
    op.create_index('idx_paper_versions_aid', 'paper_versions', ['aid'])
    op.create_index('idx_paper_versions_created_at', 'paper_versions', ['created_at'])
    op.create_index('idx_paper_versions_deleted_at', 'paper_versions', ['deleted_at'])


def downgrade() -> None:
    op.drop_index('idx_paper_versions_deleted_at', table_name='paper_versions')
    op.drop_index('idx_paper_versions_created_at', table_name='paper_versions')
    op.drop_index('idx_paper_versions_aid', table_name='paper_versions')
    op.drop_table('paper_versions')

