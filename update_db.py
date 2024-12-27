from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Drop and recreate the mensagens table with cascade delete
    with db.engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS mensagens'))
        conn.commit()
    db.create_all()  # This will recreate the mensagens table with the new cascade delete constraint
