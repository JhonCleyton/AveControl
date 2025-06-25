from app import create_app, db
from models.notificacao import Notificacao

def migrate_notificacoes():
    app = create_app()
    
    with app.app_context():
        try:
            # Criar a tabela de notificações
            db.create_all()
            print("Tabela de notificações criada com sucesso!")
                
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            raise

if __name__ == '__main__':
    migrate_notificacoes()
