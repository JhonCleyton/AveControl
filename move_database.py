import os
import shutil
from datetime import datetime

def move_database():
    # Caminhos dos arquivos
    root_db = 'sistema.db'
    instance_dir = 'instance'
    instance_db = os.path.join(instance_dir, 'sistema.db')
    backup_dir = 'backups'
    
    # Criar diretório instance se não existir
    os.makedirs(instance_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # Se já existe um banco no instance, fazer backup
        if os.path.exists(instance_db):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"sistema_instance_{timestamp}.db.bak"
            backup_path = os.path.join(backup_dir, backup_name)
            shutil.copy2(instance_db, backup_path)
            print(f"Backup do banco instance criado: {backup_path}")
            os.remove(instance_db)
        
        # Mover o banco da raiz para instance
        if os.path.exists(root_db):
            shutil.copy2(root_db, instance_db)
            print(f"Banco de dados movido para: {instance_db}")
            
            # Fazer backup do banco da raiz antes de remover
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"sistema_root_{timestamp}.db.bak"
            backup_path = os.path.join(backup_dir, backup_name)
            shutil.copy2(root_db, backup_path)
            print(f"Backup do banco raiz criado: {backup_path}")
            
            # Remover o banco da raiz
            os.remove(root_db)
            print("Banco de dados da raiz removido")
            
        print("\nOperação concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a operação: {str(e)}")

if __name__ == '__main__':
    move_database()
