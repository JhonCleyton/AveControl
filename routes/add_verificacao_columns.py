from extensions import db
from sqlalchemy import text

def add_columns():
    try:
        # Add verificado_por_id column
        db.session.execute(text('ALTER TABLE solicitacoes ADD COLUMN verificado_por_id INTEGER REFERENCES usuarios(id)'))
        # Add verificado_em column
        db.session.execute(text('ALTER TABLE solicitacoes ADD COLUMN verificado_em DATETIME'))
        
        db.session.commit()
        print("Colunas adicionadas com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao adicionar colunas: {str(e)}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    
    with app.app_context():
        add_columns()
