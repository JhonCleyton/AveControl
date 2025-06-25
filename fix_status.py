from app import create_app
from extensions import db
from models.carga import Carga

def fix_status():
    app = create_app()
    with app.app_context():
        # Converter todos os status para minúsculas
        cargas = Carga.query.all()
        for carga in cargas:
            if carga.status:
                carga.status = carga.status.lower()
        db.session.commit()
        print("Status das cargas atualizados com sucesso!")

if __name__ == '__main__':
    fix_status()
