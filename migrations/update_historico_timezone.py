import os
import sys

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models import db, HistoricoCarga
from config import Config
from extensions import db as _db
from utils.datetime_utils import get_current_time
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
_db.init_app(app)

def update_historico_timezone():
    with app.app_context():
        # Altera a coluna data_hora para suportar timezone
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE historico_carga RENAME TO historico_carga_old'))
            conn.commit()
        
        # Cria a nova tabela com suporte a timezone
        db.create_all()
        
        # Copia os dados da tabela antiga para a nova
        with db.engine.connect() as conn:
            conn.execute(text('''
                INSERT INTO historico_carga (id, carga_id, usuario_id, acao, data_hora)
                SELECT id, carga_id, usuario_id, acao, datetime(data_hora, 'localtime')
                FROM historico_carga_old
            '''))
            conn.commit()
        
        # Remove a tabela antiga
        with db.engine.connect() as conn:
            conn.execute(text('DROP TABLE historico_carga_old'))
            conn.commit()
        
        print("Migração concluída com sucesso!")

if __name__ == '__main__':
    update_historico_timezone()
