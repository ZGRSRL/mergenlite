"""unified opportunity schema

Revision ID: 0002
Revises: 24e08a114beb
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '24e08a114beb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # Add missing columns to opportunities table if they don't exist
    if 'opportunities' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('opportunities')]
        
        # Add psc_code if missing
        if 'psc_code' not in existing_columns:
            op.add_column('opportunities', sa.Column('psc_code', sa.String(length=100), nullable=True))
        
        # Add status if missing
        if 'status' not in existing_columns:
            op.add_column('opportunities', sa.Column('status', sa.String(length=50), nullable=True, server_default='active'))
        
        # Add agency if missing
        if 'agency' not in existing_columns:
            op.add_column('opportunities', sa.Column('agency', sa.Text(), nullable=True))
        
        # Add office if missing
        if 'office' not in existing_columns:
            op.add_column('opportunities', sa.Column('office', sa.Text(), nullable=True))
        
        # Add organization_type if missing
        if 'organization_type' not in existing_columns:
            op.add_column('opportunities', sa.Column('organization_type', sa.String(length=100), nullable=True))
        
        # Add point_of_contact if missing
        if 'point_of_contact' not in existing_columns:
            op.add_column('opportunities', sa.Column('point_of_contact', sa.Text(), nullable=True))
        
        # Ensure raw_data column exists (might be named raw_json in old schema)
        if 'raw_data' not in existing_columns:
            if 'raw_json' in existing_columns:
                # Rename raw_json to raw_data
                op.alter_column('opportunities', 'raw_json', new_column_name='raw_data')
            else:
                op.add_column('opportunities', sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        
        # Ensure cached_data column exists
        if 'cached_data' not in existing_columns:
            op.add_column('opportunities', sa.Column('cached_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        
        # Ensure id column exists (primary key)
        if 'id' not in existing_columns:
            # Add id column as SERIAL
            op.execute("""
                ALTER TABLE opportunities 
                ADD COLUMN id SERIAL;
                ALTER TABLE opportunities 
                ADD PRIMARY KEY (id);
            """)


def downgrade() -> None:
    # Remove added columns from opportunities (optional - comment out if you want to keep them)
    # op.drop_column('opportunities', 'psc_code')
    # op.drop_column('opportunities', 'status')
    # op.drop_column('opportunities', 'agency')
    # op.drop_column('opportunities', 'office')
    # op.drop_column('opportunities', 'cached_data')
    pass

