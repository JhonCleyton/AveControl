"""merge multiple heads

Revision ID: 3eb117da8beb
Revises: add_user_preferences, add_usuario_column
Create Date: 2025-01-15 09:35:42.960406

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3eb117da8beb'
down_revision = ('add_user_preferences', 'add_usuario_column')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
