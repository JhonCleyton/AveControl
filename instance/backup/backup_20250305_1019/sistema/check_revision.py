from app import create_app
from flask_migrate import current

app = create_app()
with app.app_context():
    print(f"Revisão atual: {current()}")
