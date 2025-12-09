"""add_missing_notice_id

Revision ID: a0e089ab5334
Revises: 35fa6f5a770b
Create Date: 2025-12-08 13:55:05.803518

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0e089ab5334'
down_revision = '35fa6f5a770b'
branch_labels = None
depends_on = None


def check_and_add_columns(table_name, col_specs, inspector):
    columns = [col['name'] for col in inspector.get_columns(table_name)] # Re-fetch per table
    for col_name, col_type, create_idx in col_specs:
        if col_name not in columns:
            op.add_column(table_name, sa.Column(col_name, col_type, nullable=True))
            if create_idx:
                op.create_index(f'ix_{table_name}_{col_name}', table_name, [col_name])

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # 1. Opportunities
    opp_cols = [
        ('notice_id', sa.String(length=100), True),
        ('solicitation_number', sa.String(length=100), True),
        ('description', sa.Text(), False),
        ('posted_date', sa.DateTime(timezone=True), True),
        ('response_deadline', sa.DateTime(timezone=True), False),
        ('agency', sa.String(length=255), False),
        ('office', sa.String(length=255), False),
        ('organization_type', sa.String(length=100), False),
        ('point_of_contact', sa.Text(), False),
        ('naics_code', sa.String(length=100), True),
        ('psc_code', sa.String(length=100), False),
        ('classification_code', sa.String(length=100), False),
        ('set_aside', sa.String(length=100), False),
        ('contract_type', sa.String(length=100), False),
        ('notice_type', sa.String(length=100), False),
        ('place_of_performance', sa.Text(), False),
        ('estimated_value', sa.Float(), False),
        ('status', sa.String(length=50), False),
        ('sam_gov_link', sa.String(length=512), False),
        ('raw_data', sa.JSON(), False),
        ('cached_data', sa.JSON(), False),
        ('cache_updated_at', sa.DateTime(timezone=True), False),
        ('created_at', sa.DateTime(timezone=True), False),
        ('updated_at', sa.DateTime(timezone=True), False),
    ]
    check_and_add_columns('opportunities', opp_cols, inspector)
    
    # Ensure title is present (opportunities)
    opp_columns_curr = [col['name'] for col in inspector.get_columns('opportunities')]
    if 'title' not in opp_columns_curr:
         op.add_column('opportunities', sa.Column('title', sa.Text(), nullable=True))

    # 2. AI Analysis Results
    if inspector.has_table("ai_analysis_results"):
        analysis_columns = [col['name'] for col in inspector.get_columns("ai_analysis_results")]
        
        # Check ID first
        if 'id' not in analysis_columns:
            op.add_column('ai_analysis_results', sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False))
            # Note: adding PK constraint explicitly might be needed depending on dialect, 
            # but sa.Column(primary_key=True) usually works for add_column if table empty.
            # If not empty, we might need multiple steps (add col, fill, add pk). 
            # Assuming empty/dev.
        
        analysis_cols = [
            ('analysis_type', sa.String(length=100), True),
            ('status', sa.String(length=50), True),
            ('result_json', sa.JSON(), False),
            ('confidence', sa.Float(), False),
            ('pdf_path', sa.String(length=1024), False),
            ('json_path', sa.String(length=1024), False),
            ('markdown_path', sa.String(length=1024), False),
            ('agent_name', sa.String(length=100), False),
            ('pipeline_version', sa.String(length=50), False),
            ('created_at', sa.DateTime(timezone=True), False),
            ('updated_at', sa.DateTime(timezone=True), False),
            ('completed_at', sa.DateTime(timezone=True), False),
        ]
        check_and_add_columns('ai_analysis_results', analysis_cols, inspector)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # helper for downgrade
    def safe_drop(table_name, cols_to_remove):
        if not inspector.has_table(table_name): return
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
        
        for col_name in cols_to_remove:
            if col_name in columns:
                idx_name = f'ix_{table_name}_{col_name}'
                # Check for special naming if needed, but generic pattern used in upgrade
                if idx_name in indexes:
                    op.drop_index(idx_name, table_name=table_name)
                
                # Special cases 
                if table_name == 'opportunities' and col_name == 'notice_id':
                     if 'ix_opportunities_notice_id' in indexes:
                         op.drop_index('ix_opportunities_notice_id', table_name='opportunities')
                
                op.drop_column(table_name, col_name)

    safe_drop('opportunities', [
        'notice_id', 'solicitation_number', 'description', 'posted_date', 'response_deadline',
        'agency', 'office', 'organization_type', 'point_of_contact', 'naics_code',
        'psc_code', 'classification_code', 'set_aside', 'contract_type', 'notice_type',
        'place_of_performance', 'estimated_value', 'status', 'sam_gov_link', 'raw_data',
        'cached_data', 'cache_updated_at', 'created_at', 'updated_at'
    ])
    
    if inspector.has_table("ai_analysis_results"):
        safe_drop('ai_analysis_results', [
            'id', 'analysis_type', 'status', 'result_json', 'confidence', 'pdf_path', 
            'json_path', 'markdown_path', 'agent_name', 'pipeline_version',
            'created_at', 'updated_at', 'completed_at'
        ])



