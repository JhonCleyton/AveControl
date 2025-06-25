from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Renomear a coluna status para _status
    db.session.execute(text('ALTER TABLE cargas RENAME COLUMN status TO _status'))
    db.session.commit()
    print("Coluna renomeada com sucesso!")
