"""Adiciona tabela de documentos

Revision ID: add_documentos_table
Revises: previous_revision
Create Date: 2025-01-14 15:48:19.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from pytz import UTC

# revision identifiers, used by Alembic.
revision = 'add_documentos_table'
down_revision = None  # Ajuste para a última revisão do seu banco
branch_labels = None
depends_on = None

def upgrade():
    # Criar tabela de documentos
    op.create_table(
        'documentos_carga',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('carga_id', sa.Integer(), nullable=False),
        sa.Column('tipo_documento', sa.String(100), nullable=False),
        sa.Column('outro_tipo_descricao', sa.String(255)),
        sa.Column('nome_arquivo', sa.String(255), nullable=False),
        sa.Column('caminho_arquivo', sa.String(500), nullable=False),
        sa.Column('data_upload', sa.DateTime(), default=datetime.now(UTC)),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('ausente', sa.Boolean(), default=False),
        sa.Column('motivo_ausencia', sa.Text()),
        sa.Column('status_exclusao', sa.String(20)),
        sa.Column('solicitado_exclusao_por_id', sa.Integer()),
        sa.Column('data_solicitacao_exclusao', sa.DateTime()),
        sa.Column('aprovado_exclusao_por_id', sa.Integer()),
        sa.Column('data_aprovacao_exclusao', sa.DateTime()),
        sa.Column('motivo_exclusao', sa.Text()),
        sa.ForeignKeyConstraint(['carga_id'], ['cargas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['solicitado_exclusao_por_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['aprovado_exclusao_por_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Criar diretório para uploads
    import os
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'documentos')
    os.makedirs(upload_dir, exist_ok=True)

def downgrade():
    op.drop_table('documentos_carga')
