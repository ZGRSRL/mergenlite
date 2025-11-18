"""history and agent logging tables

Revision ID: 0005
Revises: 0004
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # opportunity_history
    op.create_table(
        'opportunity_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('old_status', sa.String(length=100), nullable=True),
        sa.Column('new_status', sa.String(length=100), nullable=False),
        sa.Column('changed_by', sa.String(length=255), nullable=False),
        sa.Column('change_source', sa.String(length=100), nullable=True),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_opportunity_history_opportunity_id'), 'opportunity_history', ['opportunity_id'], unique=False)

    # agent_runs
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=True),
        sa.Column('run_type', sa.String(length=100), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='started'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_runs_opportunity_id'), 'agent_runs', ['opportunity_id'], unique=False)

    # agent_messages
    op.create_table(
        'agent_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_run_id', sa.Integer(), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_messages_agent_run_id'), 'agent_messages', ['agent_run_id'], unique=False)

    # llm_calls
    op.create_table(
        'llm_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_run_id', sa.Integer(), nullable=True),
        sa.Column('agent_name', sa.String(length=100), nullable=True),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_calls_agent_run_id'), 'llm_calls', ['agent_run_id'], unique=False)

    # email_log (extended)
    op.create_table(
        'email_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=True),
        sa.Column('hotel_id', sa.Integer(), nullable=True),
        sa.Column('direction', sa.String(length=20), nullable=False),
        sa.Column('subject', sa.String(length=512), nullable=True),
        sa.Column('from_address', sa.String(length=255), nullable=True),
        sa.Column('to_address', sa.String(length=255), nullable=True),
        sa.Column('message_id', sa.String(length=255), nullable=True),
        sa.Column('in_reply_to', sa.String(length=255), nullable=True),
        sa.Column('raw_body', sa.Text(), nullable=True),
        sa.Column('parsed_summary', sa.Text(), nullable=True),
        sa.Column('related_agent_run_id', sa.Integer(), nullable=True),
        sa.Column('related_llm_call_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_agent_run_id'], ['agent_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_llm_call_id'], ['llm_calls.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_log_opportunity_id'), 'email_log', ['opportunity_id'], unique=False)

    # decision_cache
    op.create_table(
        'decision_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('pattern_desc', sa.Text(), nullable=True),
        sa.Column('recommended_hotels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decision_cache_key_hash'), 'decision_cache', ['key_hash'], unique=True)

    # training_examples
    op.create_table(
        'training_examples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=True),
        sa.Column('example_type', sa.String(length=100), nullable=False),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_training_examples_opportunity_id'), 'training_examples', ['opportunity_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_training_examples_opportunity_id'), table_name='training_examples')
    op.drop_table('training_examples')
    op.drop_index(op.f('ix_decision_cache_key_hash'), table_name='decision_cache')
    op.drop_table('decision_cache')
    op.drop_index(op.f('ix_email_log_opportunity_id'), table_name='email_log')
    op.drop_table('email_log')
    op.drop_index(op.f('ix_llm_calls_agent_run_id'), table_name='llm_calls')
    op.drop_table('llm_calls')
    op.drop_index(op.f('ix_agent_messages_agent_run_id'), table_name='agent_messages')
    op.drop_table('agent_messages')
    op.drop_index(op.f('ix_agent_runs_opportunity_id'), table_name='agent_runs')
    op.drop_table('agent_runs')
    op.drop_index(op.f('ix_opportunity_history_opportunity_id'), table_name='opportunity_history')
    op.drop_table('opportunity_history')
