"""empty message

Revision ID: 2d64b79598cb
Revises: 622200274f91, fix_migrations
Create Date: 2025-01-23 10:16:42.959330

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d64b79598cb'
down_revision = ('622200274f91', 'fix_migrations')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
