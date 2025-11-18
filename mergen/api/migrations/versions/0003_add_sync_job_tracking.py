"""add sync job tracking

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sync_jobs table
    op.create_table(
        'sync_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('sync_type', sa.String(length=50), nullable=False, server_default='sam'),
        sa.Column('params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('count_new', sa.Integer(), server_default='0', nullable=True),
        sa.Column('count_updated', sa.Integer(), server_default='0', nullable=True),
        sa.Column('count_attachments', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_processed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sync_jobs_job_id'), 'sync_jobs', ['job_id'], unique=True)
    op.create_index(op.f('ix_sync_jobs_id'), 'sync_jobs', ['id'], unique=False)
    
    # Create sync_logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('step', sa.String(length=100), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['sync_jobs.job_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sync_logs_job_id'), 'sync_logs', ['job_id'], unique=False)
    op.create_index(op.f('ix_sync_logs_level'), 'sync_logs', ['level'], unique=False)
    op.create_index(op.f('ix_sync_logs_timestamp'), 'sync_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_sync_logs_id'), 'sync_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sync_logs_id'), table_name='sync_logs')
    op.drop_index(op.f('ix_sync_logs_timestamp'), table_name='sync_logs')
    op.drop_index(op.f('ix_sync_logs_level'), table_name='sync_logs')
    op.drop_index(op.f('ix_sync_logs_job_id'), table_name='sync_logs')
    op.drop_table('sync_logs')
    op.drop_index(op.f('ix_sync_jobs_id'), table_name='sync_jobs')
    op.drop_index(op.f('ix_sync_jobs_job_id'), table_name='sync_jobs')
    op.drop_table('sync_jobs')

