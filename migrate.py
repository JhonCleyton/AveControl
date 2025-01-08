"""
Script para executar migrações do banco de dados
"""
from extensions import db
from app import create_app
import importlib.util
import os

def run_migration(migration_file):
    # Importar o módulo de migração
    spec = importlib.util.spec_from_file_location(
        "migration", 
        os.path.join("migrations", migration_file)
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    
    # Executar a migração
    print(f"Executando migração: {migration_file}")
    migration.upgrade()
    print("Migração concluída com sucesso!")

if __name__ == "__main__":
    # Criar aplicação
    app = create_app()
    
    # Executar dentro do contexto da aplicação
    with app.app_context():
        # Executar migrações
        run_migration("add_verificacao_solicitacao.py")
