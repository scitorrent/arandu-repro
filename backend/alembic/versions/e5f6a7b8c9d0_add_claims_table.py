"""add_claims_table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-01-15 10:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'claims',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('text', sa.String(length=5000), nullable=False),
        sa.Column('span_start', sa.Integer(), nullable=True),
        sa.Column('span_end', sa.Integer(), nullable=True),
        sa.Column('page', sa.Integer(), nullable=True),
        sa.Column('bbox', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('section', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('extraction_model_version', sa.String(length=50), nullable=True),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('text_hash', sa.String(length=64), nullable=True),  # Hash do documento base
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['paper_version_id'], ['paper_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hash', name='uq_claims_hash'),
        sa.CheckConstraint(
            "(span_start IS NULL AND span_end IS NULL) OR "
            "(span_start IS NOT NULL AND span_end IS NOT NULL)",
            name='check_span_consistency'
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name='check_confidence_range'
        ),
    )
    
    op.create_index('idx_claims_paper_version_id', 'claims', ['paper_version_id'])
    op.create_index('idx_claims_paper_version_section', 'claims', ['paper_version_id', 'section'])
    # Composite index with DESC (PostgreSQL syntax)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_claims_paper_version_section_created 
        ON claims(paper_version_id, section, created_at DESC);
    """)
    op.create_index('idx_claims_paper_id', 'claims', ['paper_id'])
    op.create_index('idx_claims_section', 'claims', ['section'])
    op.create_index('idx_claims_hash', 'claims', ['hash'], unique=True)
    op.create_index('idx_claims_created_at', 'claims', ['created_at'])
    op.create_index('idx_claims_text_hash', 'claims', ['text_hash'])
    
    # Create GIN index for full-text search (PostgreSQL only)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_claims_text_gin 
        ON claims USING gin(to_tsvector('english', text));
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_claims_text_gin;")
    op.drop_index('idx_claims_text_hash', table_name='claims')
    op.drop_index('idx_claims_created_at', table_name='claims')
    op.drop_index('idx_claims_hash', table_name='claims')
    op.drop_index('idx_claims_section', table_name='claims')
    op.drop_index('idx_claims_paper_id', table_name='claims')
    op.execute("DROP INDEX IF EXISTS idx_claims_paper_version_section_created;")
    op.drop_index('idx_claims_paper_version_section', table_name='claims')
    op.drop_index('idx_claims_paper_version_id', table_name='claims')
    op.drop_table('claims')

