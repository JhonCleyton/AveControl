import os
from app import create_app, db

def recreate_database():
    # Remover o banco de dados existente
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Banco de dados removido: {db_path}")
    
    # Criar o banco de dados novamente
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Tabelas criadas com sucesso!")

if __name__ == '__main__':
    recreate_database()
