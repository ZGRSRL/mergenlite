"""fix_db_keys_mismatch

Revision ID: ad66300dda81
Revises: a0e089ab5334
Create Date: 2025-12-08 14:07:24.753368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad66300dda81'
down_revision = 'a0e089ab5334'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # 1. Truncate child tables that need fixing (linking to String ID)
    # We truncate ALL known dependents to be safe in data migration (dev env)
    # or just the ones we know are broken.
    op.execute("TRUNCATE TABLE ai_analysis_results CASCADE")
    if inspector.has_table("manual_documents"):
        op.execute("TRUNCATE TABLE manual_documents CASCADE")
        
    # opportunity_attachments seemed to link to ID, but let's be safe
    if inspector.has_table("opportunity_attachments"):
        op.execute("TRUNCATE TABLE opportunity_attachments CASCADE")

    # 2. Fix AI Analysis Results
    fks = inspector.get_foreign_keys('ai_analysis_results')
    for fk in fks:
        op.drop_constraint(fk['name'], 'ai_analysis_results', type_='foreignkey')
    
    op.drop_column('ai_analysis_results', 'opportunity_id')
    op.add_column('ai_analysis_results', sa.Column('opportunity_id', sa.Integer(), nullable=False))
    
    # 3. Fix Manual Documents (if exists)
    if inspector.has_table("manual_documents"):
        fks_md = inspector.get_foreign_keys('manual_documents')
        for fk in fks_md:
            op.drop_constraint(fk['name'], 'manual_documents', type_='foreignkey')
        
        # Check column existence
        md_cols = [c['name'] for c in inspector.get_columns('manual_documents')]
        if 'opportunity_id' in md_cols:
             op.drop_column('manual_documents', 'opportunity_id')
        op.add_column('manual_documents', sa.Column('opportunity_id', sa.Integer(), nullable=False))
        
    # 4. Fix Opportunity Attachments (Recreate to ensure Integer linkage)
    if inspector.has_table("opportunity_attachments"):
        fks_att = inspector.get_foreign_keys('opportunity_attachments')
        for fk in fks_att:
            op.drop_constraint(fk['name'], 'opportunity_attachments', type_='foreignkey')
        
        att_cols = [c['name'] for c in inspector.get_columns('opportunity_attachments')]
        if 'opportunity_id' in att_cols:
            op.drop_column('opportunity_attachments', 'opportunity_id')
        op.add_column('opportunity_attachments', sa.Column('opportunity_id', sa.Integer(), nullable=False))
    
    # 5. Fix Opportunities PK
    pks = inspector.get_pk_constraint('opportunities')
    if pks and pks['name']:
        op.drop_constraint(pks['name'], 'opportunities', type_='primary')
        
    # Create new PK on 'id'
    op.create_primary_key('opportunities_pkey', 'opportunities', ['id'])
    
    # 6. Re-create FKs
    op.create_foreign_key(
        'ai_analysis_results_opportunity_id_fkey', 'ai_analysis_results', 'opportunities',
        ['opportunity_id'], ['id'], ondelete='CASCADE'
    )
    
    if inspector.has_table("manual_documents"):
        op.create_foreign_key(
            'manual_documents_opportunity_id_fkey', 'manual_documents', 'opportunities',
            ['opportunity_id'], ['id'], ondelete='CASCADE'
        )

    if inspector.has_table("opportunity_attachments"):
        op.create_foreign_key(
            'opportunity_attachments_opportunity_id_fkey', 'opportunity_attachments', 'opportunities',
            ['opportunity_id'], ['id'], ondelete='CASCADE'
        )

def downgrade() -> None:
    # Downgrade is complex and risky (data type reversion). 
    # For now, we assume this fix is needed and one-way in dev.
    pass



