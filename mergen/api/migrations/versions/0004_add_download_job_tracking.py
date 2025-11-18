"""add download job tracking

Revision ID: 0004
Revises: 0003
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create download_jobs table
    op.create_table(
        'download_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_attachments', sa.Integer(), server_default='0', nullable=True),
        sa.Column('downloaded_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('failed_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_download_jobs_job_id'), 'download_jobs', ['job_id'], unique=True)
    op.create_index(op.f('ix_download_jobs_id'), 'download_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_download_jobs_opportunity_id'), 'download_jobs', ['opportunity_id'], unique=False)
    
    # Create download_logs table
    op.create_table(
        'download_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('attachment_name', sa.String(length=512), nullable=True),
        sa.Column('step', sa.String(length=100), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['download_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_download_logs_job_id'), 'download_logs', ['job_id'], unique=False)
    op.create_index(op.f('ix_download_logs_level'), 'download_logs', ['level'], unique=False)
    op.create_index(op.f('ix_download_logs_timestamp'), 'download_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_download_logs_id'), 'download_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_download_logs_id'), table_name='download_logs')
    op.drop_index(op.f('ix_download_logs_timestamp'), table_name='download_logs')
    op.drop_index(op.f('ix_download_logs_level'), table_name='download_logs')
    op.drop_index(op.f('ix_download_logs_job_id'), table_name='download_logs')
    op.drop_table('download_logs')
    op.drop_index(op.f('ix_download_jobs_opportunity_id'), table_name='download_jobs')
    op.drop_index(op.f('ix_download_jobs_id'), table_name='download_jobs')
    op.drop_index(op.f('ix_download_jobs_job_id'), table_name='download_jobs')
    op.drop_table('download_jobs')

