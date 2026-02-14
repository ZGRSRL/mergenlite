"""v2_0_unified_schema

Revision ID: 7fda53160d19
Revises: ad66300dda81
Create Date: 2026-02-14 16:23:59.916129

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

try:
    import pgvector.sqlalchemy.vector
except ImportError:
    pgvector = None

# revision identifiers, used by Alembic.
revision = '7fda53160d19'
down_revision = 'ad66300dda81'
branch_labels = None
depends_on = None


_sp_counter = 0


def _safe(fn, *args, **kwargs):
    """Execute an op safely with a savepoint — skip if it fails."""
    global _sp_counter
    _sp_counter += 1
    sp_name = f"sp_{_sp_counter}"
    conn = op.get_bind()
    try:
        conn.execute(sa.text(f"SAVEPOINT {sp_name}"))
        fn(*args, **kwargs)
        conn.execute(sa.text(f"RELEASE SAVEPOINT {sp_name}"))
    except Exception as e:
        print(f"  [migration] Skipping: {e}")
        conn.execute(sa.text(f"ROLLBACK TO SAVEPOINT {sp_name}"))


def upgrade() -> None:
    # --- Drop deprecated tables (safe) ---
    _safe(op.drop_index, op.f('idx_sessions_start'), table_name='system_sessions')
    _safe(op.drop_index, op.f('idx_sessions_user'), table_name='system_sessions')
    _safe(op.drop_table, 'system_sessions')
    _safe(op.drop_index, op.f('idx_manual_docs_upload_date'), table_name='manual_documents')
    _safe(op.drop_table, 'manual_documents')

    # --- Add missing indexes ---
    _safe(op.create_index, op.f('ix_agent_messages_created_at'), 'agent_messages', ['created_at'], unique=False)
    _safe(op.create_index, op.f('ix_agent_messages_id'), 'agent_messages', ['id'], unique=False)
    _safe(op.create_index, op.f('ix_agent_runs_id'), 'agent_runs', ['id'], unique=False)
    _safe(op.create_index, op.f('ix_ai_analysis_results_id'), 'ai_analysis_results', ['id'], unique=False)
    _safe(op.create_index, op.f('ix_ai_analysis_results_opportunity_id'), 'ai_analysis_results', ['opportunity_id'], unique=False)
    _safe(op.create_index, op.f('ix_decision_cache_id'), 'decision_cache', ['id'], unique=False)
    _safe(op.create_index, op.f('ix_email_log_id'), 'email_log', ['id'], unique=False)
    _safe(op.create_index, op.f('ix_llm_calls_id'), 'llm_calls', ['id'], unique=False)
    _safe(op.create_index, op.f('ix_opportunities_id'), 'opportunities', ['id'], unique=False)
    _safe(op.create_index, op.f('ix_opportunities_opportunity_id'), 'opportunities', ['opportunity_id'], unique=False)
    _safe(op.create_index, op.f('ix_opportunity_attachments_opportunity_id'), 'opportunity_attachments', ['opportunity_id'], unique=False)
    _safe(op.create_index, op.f('ix_opportunity_history_id'), 'opportunity_history', ['id'], unique=False)
    _safe(op.create_index, op.f('ix_training_examples_id'), 'training_examples', ['id'], unique=False)

    # --- Column type changes (safe) ---
    _safe(op.alter_column, 'opportunities', 'opportunity_id',
          existing_type=sa.VARCHAR(length=50),
          type_=sa.String(length=255),
          existing_nullable=False)
    _safe(op.alter_column, 'opportunities', 'title',
          existing_type=sa.VARCHAR(length=512),
          type_=sa.Text(),
          existing_nullable=False)

    _safe(op.alter_column, 'opportunity_attachments', 'name',
          existing_type=sa.TEXT(),
          type_=sa.String(length=512),
          existing_nullable=False)
    _safe(op.alter_column, 'opportunity_attachments', 'source_url',
          existing_type=sa.TEXT(),
          type_=sa.String(length=1024),
          existing_nullable=True)
    _safe(op.alter_column, 'opportunity_attachments', 'local_path',
          existing_type=sa.TEXT(),
          type_=sa.String(length=1024),
          existing_nullable=True)
    _safe(op.alter_column, 'opportunity_attachments', 'storage_path',
          existing_type=sa.TEXT(),
          type_=sa.String(length=1024),
          existing_nullable=True)

    # --- Drop deprecated columns from ai_analysis_results ---
    _safe(op.drop_index, op.f('idx_ai_results_start_time'), table_name='ai_analysis_results')
    _safe(op.drop_index, op.f('idx_ai_results_status'), table_name='ai_analysis_results')
    _safe(op.drop_column, 'ai_analysis_results', 'start_time')
    _safe(op.drop_column, 'ai_analysis_results', 'analysis_status')
    _safe(op.drop_column, 'ai_analysis_results', 'end_time')
    _safe(op.drop_column, 'ai_analysis_results', 'analysis_version')
    _safe(op.drop_column, 'ai_analysis_results', 'analysis_duration_seconds')
    _safe(op.drop_column, 'ai_analysis_results', 'consolidated_output')

    # --- Drop table comments (cosmetic) ---
    _safe(op.drop_table_comment, 'ai_analysis_results',
          existing_comment='Konsolide AI analiz sonuçları - tüm ajan çıktıları JSONB formatında',
          schema=None)
    _safe(op.drop_table_comment, 'opportunities',
          existing_comment='SAM.gov fırsatları - temel ilan bilgileri',
          schema=None)

    # --- vector_chunks: add token_count, convert to pgvector ---
    _safe(op.add_column, 'vector_chunks', sa.Column('token_count', sa.Integer(), nullable=True))

    # Convert embedding column to native vector type using raw SQL + savepoint
    # (so failure doesn't abort the entire migration transaction)
    conn = op.get_bind()
    try:
        conn.execute(sa.text("SAVEPOINT sp_vector"))
        conn.execute(sa.text(
            "ALTER TABLE vector_chunks ALTER COLUMN embedding "
            "TYPE vector(1536) USING embedding::vector(1536)"
        ))
        conn.execute(sa.text("RELEASE SAVEPOINT sp_vector"))
    except Exception as e:
        print(f"  [migration] pgvector conversion skipped: {e}")
        conn.execute(sa.text("ROLLBACK TO SAVEPOINT sp_vector"))


def downgrade() -> None:
    # Downgrade is best-effort; data loss may occur
    _safe(op.drop_index, op.f('ix_training_examples_id'), table_name='training_examples')
    _safe(op.drop_index, op.f('ix_opportunity_history_id'), table_name='opportunity_history')
    _safe(op.drop_index, op.f('ix_opportunity_attachments_opportunity_id'), table_name='opportunity_attachments')
    _safe(op.drop_index, op.f('ix_opportunities_opportunity_id'), table_name='opportunities')
    _safe(op.drop_index, op.f('ix_opportunities_id'), table_name='opportunities')
    _safe(op.drop_index, op.f('ix_llm_calls_id'), table_name='llm_calls')
    _safe(op.drop_index, op.f('ix_email_log_id'), table_name='email_log')
    _safe(op.drop_index, op.f('ix_decision_cache_id'), table_name='decision_cache')
    _safe(op.drop_index, op.f('ix_ai_analysis_results_opportunity_id'), table_name='ai_analysis_results')
    _safe(op.drop_index, op.f('ix_ai_analysis_results_id'), table_name='ai_analysis_results')
    _safe(op.drop_index, op.f('ix_agent_runs_id'), table_name='agent_runs')
    _safe(op.drop_index, op.f('ix_agent_messages_id'), table_name='agent_messages')
    _safe(op.drop_index, op.f('ix_agent_messages_created_at'), table_name='agent_messages')
    _safe(op.drop_column, 'vector_chunks', 'token_count')
