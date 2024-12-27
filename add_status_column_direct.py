import sqlite3
from pathlib import Path

# Caminho para o banco de dados
db_path = Path('instance/sistema.db')

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Adicionar a coluna status
    cursor.execute("ALTER TABLE cargas ADD COLUMN status VARCHAR(20) DEFAULT 'incompleto';")
    conn.commit()
    print("Coluna status adicionada com sucesso!")
    
    # Atualizar todos os registros existentes para ter status='incompleto'
    cursor.execute("UPDATE cargas SET status = 'incompleto' WHERE status IS NULL;")
    conn.commit()
    print("Registros existentes atualizados com status='incompleto'")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("A coluna status já existe na tabela.")
    else:
        print(f"Erro ao adicionar coluna: {e}")
finally:
    conn.close()
