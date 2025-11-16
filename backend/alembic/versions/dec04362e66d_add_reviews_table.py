"""add_reviews_table

Revision ID: dec04362e66d
Revises: 88227060e57c
Create Date: 2025-11-15 02:26:28.845719

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dec04362e66d'
down_revision: Union[str, None] = '88227060e57c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM for review status (idempotent)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reviewstatus AS ENUM ('pending', 'processing', 'completed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    review_status_enum = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed',
        name='reviewstatus', create_type=False
    )

    # Create reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('doi', sa.String(), nullable=True),
        sa.Column('pdf_file_path', sa.String(), nullable=True),
        sa.Column('repo_url', sa.String(), nullable=True),
        sa.Column('paper_meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', review_status_enum, nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('paper_text', sa.Text(), nullable=True),
        sa.Column('claims', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('citations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('checklist', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_score', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('badges', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('html_report_path', sa.String(), nullable=True),
        sa.Column('json_summary_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes
    op.create_index('idx_reviews_status', 'reviews', ['status'])
    op.create_index('idx_reviews_created_at', 'reviews', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_reviews_created_at', table_name='reviews')
    op.drop_index('idx_reviews_status', table_name='reviews')
    op.drop_table('reviews')

    # Drop ENUM
    review_status_enum = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed',
        name='reviewstatus'
    )
    review_status_enum.drop(op.get_bind(), checkfirst=True)

