"""Adiciona tabela de perfis do chat

Revision ID: add_perfil_chat
Revises: None
Create Date: 2025-01-10 14:56:44.000000

"""
from extensions import db
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_perfil_chat'
down_revision = None

def upgrade():
    # Cria a tabela de perfis do chat
    db.session.execute(text("""
        CREATE TABLE perfis_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL UNIQUE,
            nome_exibicao VARCHAR(100),
            descricao TEXT,
            foto_perfil VARCHAR(255),
            icone_perfil VARCHAR(100),
            ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """))
    db.session.commit()

def downgrade():
    # Remove a tabela de perfis do chat
    db.session.execute(text("DROP TABLE IF EXISTS perfis_chat"))
    db.session.commit()
