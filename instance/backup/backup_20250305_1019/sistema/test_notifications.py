from app import create_app, db
from models import Notificacao

app = create_app()
with app.app_context():
    print(f"Total de notificações: {Notificacao.query.count()}")
