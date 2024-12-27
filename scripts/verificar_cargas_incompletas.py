from app import create_app
from routes.notificacoes import notificar_cargas_incompletas

def main():
    app = create_app()
    with app.app_context():
        notificar_cargas_incompletas()

if __name__ == '__main__':
    main()
