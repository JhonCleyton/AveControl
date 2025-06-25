from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

def run_migration():
    with app.app_context():
        # Adiciona as colunas uma por uma
        commands = [
            'ALTER TABLE cargas ADD COLUMN aprovado_por VARCHAR(100);',
            'ALTER TABLE cargas ADD COLUMN aprovado_em DATETIME;',
            'ALTER TABLE cargas ADD COLUMN autorizado_por VARCHAR(100);',
            'ALTER TABLE cargas ADD COLUMN autorizado_em DATETIME;'
        ]
        
        for command in commands:
            try:
                db.session.execute(text(command))
                print(f"Executado: {command}")
            except Exception as e:
                print(f"Erro ao executar {command}: {str(e)}")
                continue
        
        db.session.commit()
        print("Migração concluída com sucesso!")

if __name__ == '__main__':
    run_migration()
