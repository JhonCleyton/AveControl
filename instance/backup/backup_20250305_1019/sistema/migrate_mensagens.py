from app import create_app, db
from models.mensagem import Mensagem

def migrate_mensagens():
    app = create_app()
    
    with app.app_context():
        try:
            # Criar a tabela de mensagens
            db.create_all()
            print("Tabela de mensagens criada com sucesso!")
                
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            raise

if __name__ == '__main__':
    migrate_mensagens()
