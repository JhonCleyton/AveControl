from app import create_app
from extensions import db
from models.carga import Carga
from sqlalchemy import func

def check_status():
    app = create_app()
    with app.app_context():
        # Total de cargas
        total = Carga.query.count()
        print(f"\nTotal de cargas: {total}")
        
        # Status por grupo
        result = db.session.query(Carga._status, func.count(Carga.id)).group_by(Carga._status).all()
        print("\nStatus das cargas:")
        for status, count in result:
            print(f"- {status}: {count}")
        
        # Verificar cargas com status vazio ou nulo
        cargas_sem_status = Carga.query.filter(
            (Carga._status == None) | (Carga._status == '')
        ).all()
        if cargas_sem_status:
            print("\nCargas sem status:")
            for carga in cargas_sem_status:
                print(f"- Carga {carga.numero_carga}: status='{carga._status}'")

if __name__ == '__main__':
    check_status()
