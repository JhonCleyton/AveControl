import sqlite3
import shutil
import os
from datetime import datetime

def backup_database(source_path, backup_dir='backups'):
    # Criar diretório de backup se não existir
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Criar nome do arquivo de backup com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{os.path.basename(source_path)}_{timestamp}.bak"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Fazer o backup
    shutil.copy2(source_path, backup_path)
    print(f"Backup criado: {backup_path}")
    return backup_path

def merge_databases():
    root_db = 'sistema.db'
    instance_db = 'instance/sistema.db'
    
    # Criar backups primeiro
    print("\n=== Criando backups ===")
    backup_database(root_db)
    backup_database(instance_db)
    
    # Conectar aos bancos de dados
    conn_root = sqlite3.connect(root_db)
    conn_instance = sqlite3.connect(instance_db)
    
    try:
        # Transferir solicitações do banco raiz para o instance
        print("\n=== Transferindo solicitações ===")
        solicitacoes = conn_root.execute("""
            SELECT * FROM solicitacoes
        """).fetchall()
        
        # Obter nomes das colunas
        columns = [description[0] for description in conn_root.execute("""
            SELECT * FROM solicitacoes LIMIT 1
        """).description]
        
        # Criar tabela solicitacoes no banco instance se não existir
        conn_instance.execute("""
            CREATE TABLE IF NOT EXISTS solicitacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carga_id INTEGER REFERENCES cargas(id) ON DELETE CASCADE,
                tipo VARCHAR(20) NOT NULL,
                setor VARCHAR(20) NOT NULL,
                motivo TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pendente',
                criado_em DATETIME,
                atualizado_em DATETIME,
                solicitado_por_id INTEGER REFERENCES usuarios(id),
                analisado_por_id INTEGER REFERENCES usuarios(id),
                analisado_em DATETIME,
                observacao_analise TEXT,
                verificado_por_id INTEGER REFERENCES usuarios(id),
                verificado_em DATETIME
            )
        """)
        
        # Inserir solicitações
        placeholders = ','.join(['?' for _ in columns])
        insert_query = f"INSERT OR IGNORE INTO solicitacoes ({','.join(columns)}) VALUES ({placeholders})"
        
        for solicitacao in solicitacoes:
            try:
                conn_instance.execute(insert_query, solicitacao)
                print(f"Solicitação {solicitacao[0]} transferida com sucesso")
            except sqlite3.IntegrityError as e:
                print(f"Erro ao transferir solicitação {solicitacao[0]}: {str(e)}")
        
        conn_instance.commit()
        print("\nMigração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        conn_instance.rollback()
    finally:
        conn_root.close()
        conn_instance.close()

if __name__ == '__main__':
    merge_databases()
