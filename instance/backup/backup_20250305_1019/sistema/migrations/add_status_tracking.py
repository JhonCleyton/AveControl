import sqlite3
import os

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'sistema.db')

def add_status_tracking_columns():
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Adiciona as novas colunas
        cursor.execute('''
            ALTER TABLE cargas 
            ADD COLUMN status_atualizado_em DATETIME;
        ''')
        
        cursor.execute('''
            ALTER TABLE cargas 
            ADD COLUMN status_atualizado_por_id INTEGER 
            REFERENCES usuarios(id);
        ''')
        
        # Commit das alterações
        conn.commit()
        print("Colunas de tracking de status adicionadas com sucesso!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("As colunas já existem. Continuando...")
        else:
            print(f"Erro ao adicionar colunas: {str(e)}")
    except Exception as e:
        print(f"Erro: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_status_tracking_columns()
