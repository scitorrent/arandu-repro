"""add_quality_scores_table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-01-15 10:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM for quality score scope
    quality_score_scope_enum = postgresql.ENUM('paper', 'version', name='qualityscorescope')
    quality_score_scope_enum.create(op.get_bind(), checkfirst=True)
    
    op.create_table(
        'quality_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('paper_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope', quality_score_scope_enum, nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('signals', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('rationale', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('scoring_model_version', sa.String(length=20), nullable=False, server_default='v0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_version_id'], ['paper_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "(scope = 'paper' AND paper_id IS NOT NULL AND paper_version_id IS NULL) OR "
            "(scope = 'version' AND paper_version_id IS NOT NULL AND paper_id IS NULL)",
            name='check_quality_score_scope'
        ),
        sa.CheckConstraint('score >= 0 AND score <= 100', name='check_score_range'),
    )
    
    op.create_index('idx_quality_scores_paper_id', 'quality_scores', ['paper_id'])
    op.create_index('idx_quality_scores_paper_version_id', 'quality_scores', ['paper_version_id'])
    op.create_index('idx_quality_scores_scope', 'quality_scores', ['scope'])
    op.create_index('idx_quality_scores_created_at', 'quality_scores', ['created_at'])
    op.create_index('idx_quality_scores_score', 'quality_scores', ['score'])


def downgrade() -> None:
    op.drop_index('idx_quality_scores_score', table_name='quality_scores')
    op.drop_index('idx_quality_scores_created_at', table_name='quality_scores')
    op.drop_index('idx_quality_scores_scope', table_name='quality_scores')
    op.drop_index('idx_quality_scores_paper_version_id', table_name='quality_scores')
    op.drop_index('idx_quality_scores_paper_id', table_name='quality_scores')
    op.drop_table('quality_scores')
    
    # Drop ENUM
    quality_score_scope_enum = postgresql.ENUM('paper', 'version', name='qualityscorescope')
    quality_score_scope_enum.drop(op.get_bind(), checkfirst=True)

