import sqlite3
from pathlib import Path

# Caminho para o banco de dados
db_path = Path('instance/banco.db')

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tabelas encontradas:")
    for table in tables:
        print(table[0])
except Exception as e:
    print(f"Erro ao listar tabelas: {e}")
finally:
    conn.close()
