from app import create_app
from extensions import db
from models import Carga
from constants import NUMERO_INICIAL_CARGA

def renumerar_cargas():
    app = create_app()
    with app.app_context():
        try:
            # Buscar todas as cargas ordenadas por data_abate e id
            cargas = Carga.query.order_by(Carga.data_abate, Carga.id).all()
            
            # Começar a numeração a partir do NUMERO_INICIAL_CARGA
            novo_numero = NUMERO_INICIAL_CARGA
            
            # Atualizar o número de cada carga
            for carga in cargas:
                print(f"Atualizando carga {carga.numero_carga} para {novo_numero}")
                carga.numero_carga = str(novo_numero)
                novo_numero += 1
            
            # Salvar as alterações no banco de dados
            db.session.commit()
            print("\nTodas as cargas foram renumeradas com sucesso!")
            print(f"A próxima carga começará com o número {novo_numero}")
            
        except Exception as e:
            print(f"Erro ao renumerar cargas: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    renumerar_cargas()
