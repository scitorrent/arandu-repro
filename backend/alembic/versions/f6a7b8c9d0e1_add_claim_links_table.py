"""add_claim_links_table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2025-01-15 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM for claim relation
    claim_relation_enum = postgresql.ENUM(
        'equivalent', 'complementary', 'contradictory', 'unclear',
        name='claimrelation'
    )
    claim_relation_enum.create(op.get_bind(), checkfirst=True)
    
    op.create_table(
        'claim_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_paper_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_doc_id', sa.String(length=200), nullable=True),
        sa.Column('source_citation', sa.String(length=500), nullable=True),
        sa.Column('relation', claim_relation_enum, nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('context_excerpt', sa.String(length=2000), nullable=True),
        sa.Column('reasoning_ref', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_paper_id'], ['papers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "source_paper_id IS NOT NULL OR source_doc_id IS NOT NULL",
            name='check_source_exists'
        ),
        sa.CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name='check_confidence_range'
        ),
    )
    
    op.create_index('idx_claim_links_claim_id', 'claim_links', ['claim_id'])
    op.create_index('idx_claim_links_source_paper_id', 'claim_links', ['source_paper_id'])
    op.create_index('idx_claim_links_relation', 'claim_links', ['relation'])
    op.create_index('idx_claim_links_confidence', 'claim_links', ['confidence'])
    op.create_index('idx_claim_links_created_at', 'claim_links', ['created_at'])
    
    # Note: UNIQUE(claim_id, COALESCE(source_paper_id::text, source_doc_id), relation)
    # is complex and may need a functional index or application-level validation


def downgrade() -> None:
    op.drop_index('idx_claim_links_created_at', table_name='claim_links')
    op.drop_index('idx_claim_links_confidence', table_name='claim_links')
    op.drop_index('idx_claim_links_relation', table_name='claim_links')
    op.drop_index('idx_claim_links_source_paper_id', table_name='claim_links')
    op.drop_index('idx_claim_links_claim_id', table_name='claim_links')
    op.drop_table('claim_links')
    
    # Drop ENUM
    claim_relation_enum = postgresql.ENUM(
        'equivalent', 'complementary', 'contradictory', 'unclear',
        name='claimrelation'
    )
    claim_relation_enum.drop(op.get_bind(), checkfirst=True)

