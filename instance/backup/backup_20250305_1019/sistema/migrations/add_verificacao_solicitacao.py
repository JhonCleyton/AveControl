"""
Script para adicionar colunas de verificação na tabela solicitacoes
"""
from extensions import db

def upgrade():
    # Adicionar colunas de verificação uma por vez
    db.session.execute("""
        ALTER TABLE solicitacoes 
        ADD COLUMN verificado_por_id INTEGER REFERENCES usuarios(id)
    """)
    
    db.session.execute("""
        ALTER TABLE solicitacoes 
        ADD COLUMN verificado_em TIMESTAMP
    """)
    
    db.session.commit()

def downgrade():
    # Remover colunas de verificação uma por vez
    db.session.execute("""
        ALTER TABLE solicitacoes 
        DROP COLUMN verificado_por_id
    """)
    
    db.session.execute("""
        ALTER TABLE solicitacoes 
        DROP COLUMN verificado_em
    """)
    
    db.session.commit()
