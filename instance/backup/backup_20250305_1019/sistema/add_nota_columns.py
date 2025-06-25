import sqlite3
import os

def add_nota_columns():
    # Encontrar o banco de dados
    db_path = 'instance/sistema.db'
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em {db_path}")
        return

    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Adicionar novas colunas
        cursor.execute('ALTER TABLE cargas ADD COLUMN nota_aprovada BOOLEAN DEFAULT 0')
        cursor.execute('ALTER TABLE cargas ADD COLUMN aprovado_por_id INTEGER REFERENCES usuarios(id)')
        cursor.execute('ALTER TABLE cargas ADD COLUMN aprovado_em DATETIME')
        cursor.execute('ALTER TABLE cargas ADD COLUMN nota_autorizada BOOLEAN DEFAULT 0')
        cursor.execute('ALTER TABLE cargas ADD COLUMN autorizado_por_id INTEGER REFERENCES usuarios(id)')
        cursor.execute('ALTER TABLE cargas ADD COLUMN autorizado_em DATETIME')
        cursor.execute('ALTER TABLE cargas ADD COLUMN assinatura_autorizacao TEXT')
        
        # Commit das alterações
        conn.commit()
        print("Colunas adicionadas com sucesso!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("As colunas já existem.")
        else:
            print(f"Erro ao adicionar colunas: {e}")
    finally:
        # Fechar conexão
        conn.close()

if __name__ == '__main__':
    add_nota_columns()
