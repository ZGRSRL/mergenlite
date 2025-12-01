"""rename_metadata_to_extra_metadata

Revision ID: 5f53d9336658
Revises: 0005
Create Date: 2025-11-27 12:46:09.103259

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f53d9336658'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('agent_runs', 'metadata', new_column_name='extra_metadata')
    op.alter_column('decision_cache', 'metadata', new_column_name='extra_metadata')


def downgrade() -> None:
    op.alter_column('agent_runs', 'extra_metadata', new_column_name='metadata')
    op.alter_column('decision_cache', 'extra_metadata', new_column_name='metadata')



