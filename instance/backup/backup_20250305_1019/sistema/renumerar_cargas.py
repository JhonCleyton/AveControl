from app import create_app
from extensions import db
from models import Carga
from sqlalchemy import func
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s: %(message)s',
                    filename='renumerar_cargas.log',
                    filemode='w')

def parse_data_abate(data_str):
    """Converte string de data para objeto datetime."""
    try:
        return datetime.strptime(data_str, '%d/%m/%Y')
    except ValueError:
        logging.error(f"Erro ao converter data: {data_str}")
        return datetime.min

def renumerar_cargas():
    app = create_app()
    with app.app_context():
        try:
            logging.info("Iniciando processo de renumeração de cargas")
            
            # Buscar todas as cargas
            cargas = Carga.query.all()
            
            # Ordenar cargas com critérios mais precisos
            cargas_ordenadas = sorted(cargas, 
                key=lambda x: (
                    parse_data_abate(x.data_abate),  # Primeiro por data
                    x.id  # Depois pelo ID para manter a ordem original
                )
            )
            
            logging.info(f"Total de cargas encontradas: {len(cargas_ordenadas)}")
            
            # Começar a numeração a partir de 5040
            novo_numero = 5040
            
            # Primeiro, adicionar um prefixo temporário para evitar conflitos
            for carga in cargas_ordenadas:
                original_numero = carga.numero_carga
                carga.numero_carga = f"TEMP_{original_numero}"
                logging.info(f"Prefixo temporário adicionado à carga {original_numero}")
            db.session.commit()
            
            # Agora renumerar normalmente
            for carga in cargas_ordenadas:
                logging.info(f"Atualizando carga {carga.numero_carga} para {novo_numero}")
                carga.numero_carga = str(novo_numero)
                novo_numero += 1
            
            # Salvar as alterações no banco de dados
            db.session.commit()
            logging.info("\nTodas as cargas foram renumeradas com sucesso!")
            logging.info(f"Próxima carga começará com o número {novo_numero}")
            
            print("\nTodas as cargas foram renumeradas com sucesso!")
            print(f"A próxima carga começará com o número {novo_numero}")
            
        except Exception as e:
            logging.error(f"Erro durante a renumeração de cargas: {str(e)}")
            db.session.rollback()
            print(f"Erro ao renumerar cargas: {str(e)}")
            
            # Tentar reverter para os números originais se algo der errado
            try:
                for carga in Carga.query.all():
                    if carga.numero_carga.startswith("TEMP_"):
                        original_numero = carga.numero_carga.replace("TEMP_", "")
                        carga.numero_carga = original_numero
                        logging.info(f"Número original restaurado: {original_numero}")
                db.session.commit()
                logging.info("Números originais de cargas restaurados com sucesso.")
                print("Restauração dos números originais concluída.")
            except Exception as restore_error:
                logging.error(f"Erro durante a restauração dos números: {str(restore_error)}")
                db.session.rollback()
                print(f"Erro na restauração: {str(restore_error)}")

if __name__ == "__main__":
    renumerar_cargas()