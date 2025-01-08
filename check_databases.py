import sqlite3
import os
from datetime import datetime

def get_db_info(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar número de registros em tabelas principais
        tables = ['cargas', 'usuarios', 'solicitacoes']
        counts = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                counts[table] = count
            except sqlite3.OperationalError:
                counts[table] = "Tabela não existe"
        
        # Verificar última modificação do arquivo
        mod_time = os.path.getmtime(db_path)
        mod_date = datetime.fromtimestamp(mod_time)
        
        # Verificar tamanho do arquivo
        size = os.path.getsize(db_path)
        
        return {
            'path': db_path,
            'size': size,
            'last_modified': mod_date,
            'table_counts': counts
        }
    except Exception as e:
        return {
            'path': db_path,
            'error': str(e)
        }
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    root_db = 'sistema.db'
    instance_db = 'instance/sistema.db'
    
    print("\n=== Comparação dos Bancos de Dados ===\n")
    
    for db_path in [root_db, instance_db]:
        if os.path.exists(db_path):
            info = get_db_info(db_path)
            print(f"\nBanco de dados: {db_path}")
            if 'error' in info:
                print(f"Erro ao acessar: {info['error']}")
            else:
                print(f"Tamanho: {info['size']/1024:.2f} KB")
                print(f"Última modificação: {info['last_modified']}")
                print("\nContagem de registros:")
                for table, count in info['table_counts'].items():
                    print(f"  {table}: {count}")
        else:
            print(f"\nBanco de dados {db_path} não existe")

if __name__ == '__main__':
    main()
