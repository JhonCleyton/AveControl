from app import create_app, db
from models.solicitacao import Solicitacao
from sqlalchemy import text

def migrate_solicitacoes():
    # Criar a aplicação
    app = create_app()
    
    with app.app_context():
        try:
            # Criar a tabela de solicitações
            db.create_all()
            print("Tabela de solicitações criada com sucesso!")
                
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            raise

if __name__ == '__main__':
    migrate_solicitacoes()
