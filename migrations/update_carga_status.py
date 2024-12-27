from app import create_app
from extensions import db
from models import Carga

def update_carga_status():
    app = create_app()
    with app.app_context():
        # Atualizar cargas existentes
        cargas = Carga.query.all()
        for carga in cargas:
            # Se a carga estiver incompleta, marcar como pendente
            if carga.status == 'incompleto':
                carga.status = 'pendente'
            # Se a carga estiver completa, marcar como concluída
            elif carga.status == 'completo':
                carga.status = 'concluida'
        
        db.session.commit()
        print("Status das cargas atualizado com sucesso!")

if __name__ == '__main__':
    update_carga_status()
