import os
import sqlite3
from datetime import datetime

def reset_database():
    # Backup dos bancos antes de zerar
    backup_dir = os.path.join('instance', 'backup', 'pre_reset_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(backup_dir, exist_ok=True)
    
    # Lista de bancos de dados
    databases = ['sistema.db', 'avecontrol.db', 'database.db']
    
    for db_name in databases:
        db_path = os.path.join('instance', db_name)
        if os.path.exists(db_path):
            # Criar backup
            backup_path = os.path.join(backup_dir, db_name)
            with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
            print(f"Backup criado: {backup_path}")
            
            try:
                # Conectar ao banco
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Listar todas as tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                # Deletar dados de cada tabela
                for table in tables:
                    table_name = table[0]
                    if table_name != 'sqlite_sequence':  # Preservar tabela de sequência
                        cursor.execute(f"DELETE FROM {table_name};")
                        print(f"Dados da tabela {table_name} foram removidos")
                
                # Commit e fechar conexão
                conn.commit()
                conn.close()
                print(f"Banco {db_name} foi zerado com sucesso")
                
            except Exception as e:
                print(f"Erro ao zerar {db_name}: {str(e)}")
    
    print("\nProcesso concluído!")
    print("Backups foram salvos em:", backup_dir)
    print("Todos os bancos de dados foram zerados mantendo a estrutura das tabelas")

# Executar direto
reset_database()
