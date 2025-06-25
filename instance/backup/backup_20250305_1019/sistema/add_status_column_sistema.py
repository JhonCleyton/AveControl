import sqlite3
from pathlib import Path

# Caminho para o banco de dados
db_path = Path('instance/sistema.db')

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(cargas);")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'status' not in column_names:
        # Adicionar a coluna status
        cursor.execute("ALTER TABLE cargas ADD COLUMN status VARCHAR(20) DEFAULT 'incompleto';")
        conn.commit()
        print("Coluna status adicionada com sucesso!")
    else:
        print("A coluna status já existe na tabela.")
except Exception as e:
    print(f"Erro ao adicionar coluna: {e}")
finally:
    conn.close()
