from config import Config
import sqlite3
import os

def create_documentos_table():
    # Conectar ao banco de dados
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Criar tabela de documentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentos_carga (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carga_id INTEGER NOT NULL,
                tipo_documento VARCHAR(100) NOT NULL,
                outro_tipo_descricao VARCHAR(255),
                nome_arquivo VARCHAR(255) NOT NULL,
                caminho_arquivo VARCHAR(500) NOT NULL,
                data_upload TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER NOT NULL,
                ausente BOOLEAN DEFAULT 0,
                motivo_ausencia TEXT,
                status_exclusao VARCHAR(20),
                solicitado_exclusao_por_id INTEGER,
                data_solicitacao_exclusao TIMESTAMP,
                aprovado_exclusao_por_id INTEGER,
                data_aprovacao_exclusao TIMESTAMP,
                motivo_exclusao TEXT,
                FOREIGN KEY (carga_id) REFERENCES cargas(id) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                FOREIGN KEY (solicitado_exclusao_por_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                FOREIGN KEY (aprovado_exclusao_por_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        ''')

        print("Tabela documentos_carga criada com sucesso!")
        conn.commit()

    except Exception as e:
        print(f"Erro ao criar tabela: {str(e)}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == '__main__':
    create_documentos_table()
