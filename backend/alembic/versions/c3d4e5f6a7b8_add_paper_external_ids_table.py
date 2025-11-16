"""add_paper_external_ids_table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-01-15 10:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM for external ID kind (idempotent)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE externalidkind AS ENUM ('doi', 'arxiv', 'pmid', 'url');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    external_id_kind_enum = postgresql.ENUM('doi', 'arxiv', 'pmid', 'url', name='externalidkind', create_type=False)
    
    op.create_table(
        'paper_external_ids',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', external_id_kind_enum, nullable=False),
        sa.Column('value', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id', 'kind', name='uq_paper_external_ids_paper_kind'),
    )
    
    op.create_index('idx_paper_external_ids_kind_value', 'paper_external_ids', ['kind', 'value'])


def downgrade() -> None:
    op.drop_index('idx_paper_external_ids_kind_value', table_name='paper_external_ids')
    op.drop_table('paper_external_ids')
    
    # Drop ENUM
    external_id_kind_enum = postgresql.ENUM('doi', 'arxiv', 'pmid', 'url', name='externalidkind')
    external_id_kind_enum.drop(op.get_bind(), checkfirst=True)

