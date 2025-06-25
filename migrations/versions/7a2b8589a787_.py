"""empty message

Revision ID: 7a2b8589a787
Revises: 3eb117da8beb, rename_status_column
Create Date: 2025-01-21 16:30:02.607562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a2b8589a787'
down_revision = ('3eb117da8beb', 'rename_status_column')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
