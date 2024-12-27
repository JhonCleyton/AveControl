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
    print("\nColunas na tabela cargas:")
    for column in columns:
        print(f"Nome: {column[1]}, Tipo: {column[2]}, NotNull: {column[3]}, Default: {column[4]}")
except Exception as e:
    print(f"Erro ao verificar colunas: {e}")
finally:
    conn.close()
