"""add_papers_table

Revision ID: a1b2c3d4e5f6
Revises: dec04362e66d
Create Date: 2025-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'dec04362e66d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM for paper visibility (using native_enum=False for compatibility)
    # Use String with CheckConstraint instead of native ENUM for easier evolution
    paper_visibility_enum = postgresql.ENUM(
        'private', 'unlisted', 'public', name='papervisibility', create_type=False
    )
    # Create as String with check constraint for better compatibility
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE papervisibility AS ENUM ('private', 'unlisted', 'public');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create papers table
    op.create_table(
        'papers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aid', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('repo_url', sa.String(length=1000), nullable=True),
        sa.Column('visibility', paper_visibility_enum, nullable=False, server_default='private'),
        sa.Column('license', sa.String(length=200), nullable=True),
        sa.Column('created_by', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_public_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index('idx_papers_aid', 'papers', ['aid'], unique=True)
    op.create_index('idx_papers_visibility', 'papers', ['visibility'])
    op.create_index('idx_papers_created_at', 'papers', ['created_at'])
    op.create_index('idx_papers_approved_public_at', 'papers', ['approved_public_at'])
    op.create_index('idx_papers_deleted_at', 'papers', ['deleted_at'])


def downgrade() -> None:
    op.drop_index('idx_papers_deleted_at', table_name='papers')
    op.drop_index('idx_papers_approved_public_at', table_name='papers')
    op.drop_index('idx_papers_created_at', table_name='papers')
    op.drop_index('idx_papers_visibility', table_name='papers')
    op.drop_index('idx_papers_aid', table_name='papers')
    op.drop_table('papers')
    
    # Drop ENUM
    paper_visibility_enum = postgresql.ENUM('private', 'unlisted', 'public', name='papervisibility')
    paper_visibility_enum.drop(op.get_bind(), checkfirst=True)

