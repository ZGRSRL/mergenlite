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
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Check agent_runs
    columns = [col['name'] for col in inspector.get_columns('agent_runs')]
    if 'extra_metadata' not in columns:
        op.add_column('agent_runs', sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))

    # Check decision_cache
    columns = [col['name'] for col in inspector.get_columns('decision_cache')]
    if 'extra_metadata' not in columns:
        op.add_column('decision_cache', sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('agent_runs', 'extra_metadata')
    op.drop_column('decision_cache', 'extra_metadata')



