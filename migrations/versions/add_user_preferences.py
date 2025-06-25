"""add user preferences

Revision ID: add_user_preferences
Revises: e7a8ae4aec44
Create Date: 2025-01-14 17:28:44.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_preferences'
down_revision = 'e7a8ae4aec44'  # usando a revisão atual como base
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona novas colunas na tabela usuarios
    op.add_column('usuarios', sa.Column('tema', sa.String(20), nullable=True, server_default='claro'))
    op.add_column('usuarios', sa.Column('notif_email', sa.Boolean(), nullable=True, server_default='true'))

def downgrade():
    # Remove as colunas adicionadas
    op.drop_column('usuarios', 'tema')
    op.drop_column('usuarios', 'notif_email')
