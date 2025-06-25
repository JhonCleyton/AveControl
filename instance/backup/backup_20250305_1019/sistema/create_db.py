from app import create_app, db, create_default_users
from models import *

app = create_app()

with app.app_context():
    # Remover todas as tabelas existentes
    db.drop_all()
    
    # Criar todas as tabelas
    db.create_all()
    
    # Criar usuários padrão
    create_default_users()
    
print("Banco de dados criado com sucesso!")
