from extensions import db
from models import Carga
from datetime import datetime
from pytz import UTC

def atualizar_numeracao():
    """Atualiza a numeração das cargas para começar em 5040"""
    try:
        # Buscar todas as cargas ordenadas por número
        cargas = Carga.query.order_by(Carga.numero_carga).all()
        
        if not cargas:
            print("Não há cargas para atualizar")
            return
        
        # Começar a contagem em 5040
        novo_numero = 5040
        
        # Atualizar cada carga
        for carga in cargas:
            carga.numero_carga = str(novo_numero)
            novo_numero += 1
            
        # Salvar as alterações
        db.session.commit()
        print(f"Numeração das cargas atualizada com sucesso! Agora começando em 5040")
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar numeração: {str(e)}")

if __name__ == "__main__":
    # Importar e criar o app Flask
    from app import create_app
    app = create_app()
    
    # Usar o contexto do app
    with app.app_context():
        atualizar_numeracao()
