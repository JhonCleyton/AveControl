"""rename status column

Revision ID: rename_status_column
Revises: add_user_preferences
Create Date: 2024-01-21 15:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_status_column'
down_revision = 'add_user_preferences'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
