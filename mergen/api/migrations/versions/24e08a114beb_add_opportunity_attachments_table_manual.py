"""add_opportunity_attachments_table_manual

Revision ID: 24e08a114beb
Revises: 
Create Date: 2025-11-16 17:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '24e08a114beb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'opportunities' not in existing_tables:
        op.create_table(
            'opportunities',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('opportunity_id', sa.String(length=255), nullable=False, index=True),
            sa.Column('notice_id', sa.String(length=100), nullable=True, index=True),
            sa.Column('solicitation_number', sa.String(length=100), nullable=True),
            sa.Column('title', sa.Text(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('posted_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('response_deadline', sa.DateTime(timezone=True), nullable=True),
            sa.Column('agency', sa.String(length=255), nullable=True),
            sa.Column('office', sa.String(length=255), nullable=True),
            sa.Column('naics_code', sa.String(length=100), nullable=True),
            sa.Column('psc_code', sa.String(length=100), nullable=True),
            sa.Column('status', sa.String(length=50), server_default='active', nullable=True),
            sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('cached_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        )

    # Create opportunity_attachments table
    op.create_table(
        'opportunity_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('attachment_type', sa.String(length=50), nullable=False, server_default='document'),
        sa.Column('mime_type', sa.String(length=255), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('local_path', sa.Text(), nullable=True),
        sa.Column('downloaded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('storage_path', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_opportunity_attachments_id', 'opportunity_attachments', ['id'], unique=False)
    op.create_index('ix_opportunity_attachments_opportunity_id', 'opportunity_attachments', ['opportunity_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_opportunity_attachments_opportunity_id', table_name='opportunity_attachments')
    op.drop_index('ix_opportunity_attachments_id', table_name='opportunity_attachments')
    
    # Drop table
    op.drop_table('opportunity_attachments')
