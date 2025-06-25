import sqlite3
from pathlib import Path

# Caminho para o banco de dados
db_path = Path('instance/banco.db')

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Adicionar a coluna status
    cursor.execute("ALTER TABLE cargas ADD COLUMN status VARCHAR(20) DEFAULT 'incompleto';")
    conn.commit()
    print("Coluna status adicionada com sucesso!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("A coluna status já existe.")
    else:
        print(f"Erro ao adicionar coluna: {e}")
finally:
    conn.close()
