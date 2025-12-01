"""add_extra_metadata_column

Revision ID: 435eef02c8f3
Revises: 5f53d9336658
Create Date: 2025-11-27 12:51:32.382585

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '435eef02c8f3'
down_revision = '5f53d9336658'
branch_labels = None
depends_on = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    # Check if column exists before adding to avoid errors if it was partially applied
    # But alembic doesn't support 'if not exists' easily in op.add_column without raw SQL
    # We will just try to add it. If it fails, we might need to handle it manually.
    # However, since 'rename' failed (likely because 'metadata' didn't exist), 'add' should work.
    op.add_column('agent_runs', sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('decision_cache', sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('agent_runs', 'extra_metadata')
    op.drop_column('decision_cache', 'extra_metadata')



