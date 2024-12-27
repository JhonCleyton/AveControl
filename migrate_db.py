from app import create_app, db
from models.usuario import Usuario
from models.carga import Carga
from sqlalchemy import text

def migrate_database():
    # Criar a aplicação
    app = create_app()
    
    with app.app_context():
        try:
            # Adicionar novas colunas
            with db.engine.connect() as conn:
                # Verificar se as colunas existem
                result = conn.execute(text("PRAGMA table_info(cargas)"))
                colunas = {row[1] for row in result.fetchall()}
                
                # Adicionar coluna nota_autorizada se não existir
                if 'nota_autorizada' not in colunas:
                    conn.execute(text('ALTER TABLE cargas ADD COLUMN nota_autorizada BOOLEAN DEFAULT 0'))
                    print("Coluna nota_autorizada adicionada")
                
                # Adicionar coluna autorizado_por_id se não existir
                if 'autorizado_por_id' not in colunas:
                    conn.execute(text('ALTER TABLE cargas ADD COLUMN autorizado_por_id INTEGER REFERENCES usuarios(id)'))
                    print("Coluna autorizado_por_id adicionada")
                
                # Adicionar coluna autorizado_em se não existir
                if 'autorizado_em' not in colunas:
                    conn.execute(text('ALTER TABLE cargas ADD COLUMN autorizado_em DATETIME'))
                    print("Coluna autorizado_em adicionada")
                
                # Adicionar coluna assinatura_autorizacao se não existir
                if 'assinatura_autorizacao' not in colunas:
                    conn.execute(text('ALTER TABLE cargas ADD COLUMN assinatura_autorizacao TEXT'))
                    print("Coluna assinatura_autorizacao adicionada")
                
                conn.commit()
                print("Migração concluída com sucesso!")
                
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            raise

if __name__ == '__main__':
    migrate_database()
