from flask import Flask
from config import Config
from extensions import db
import os

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)

# Garantir que o diretório instance existe
os.makedirs(app.instance_path, exist_ok=True)

db.init_app(app)

with app.app_context():
    try:
        # Tentar criar o banco de dados
        db.create_all()
        print("Banco de dados criado com sucesso!")
        
        # Tentar fazer uma consulta simples
        result = db.session.execute('SELECT 1').scalar()
        print("Conexão com o banco de dados testada com sucesso!")
        
    except Exception as e:
        print(f"Erro ao acessar o banco de dados: {str(e)}")
        print(f"Diretório instance: {app.instance_path}")
        print(f"URI do banco: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Diretório atual: {os.getcwd()}")
