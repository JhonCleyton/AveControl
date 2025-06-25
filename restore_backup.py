import os
import sys
import shutil
from pathlib import Path
import logging
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup/restore.log'),
        logging.StreamHandler()
    ]
)

def restore_backup(backup_name, restore_type='all'):
    """Restaura um backup específico
    
    Args:
        backup_name (str): Nome do backup a ser restaurado
        restore_type (str): Tipo de restauração ('all', 'data', 'system')
    """
    try:
        # Aguardar alguns segundos para garantir que o servidor foi encerrado
        time.sleep(5)
        
        backup_dir = Path('backup') / backup_name
        if not backup_dir.exists():
            logging.error("Backup não encontrado")
            return False

        # Restaurar banco de dados (dados)
        if restore_type in ['all', 'data']:
            db_backup = backup_dir / 'sistema.db'
            if db_backup.exists():
                try:
                    shutil.copy2(db_backup, 'instance/sistema.db')
                    logging.info("Banco de dados restaurado com sucesso")
                except Exception as e:
                    logging.error(f"Erro ao restaurar banco de dados: {str(e)}")
                    return False

        # Restaurar arquivos do sistema
        if restore_type in ['all', 'system']:
            sistema_backup = backup_dir / 'sistema'
            if sistema_backup.exists():
                try:
                    # Lista de diretórios e arquivos a ignorar
                    ignore_paths = {'backup', '__pycache__', '.git', 'instance', 'env', 'venv', 'migrations'}
                    
                    # Copiar arquivos, excluindo diretórios específicos
                    for item in sistema_backup.iterdir():
                        if item.name not in ignore_paths:
                            dest = Path('.') / item.name
                            if item.is_dir():
                                if dest.exists():
                                    shutil.rmtree(dest)
                                shutil.copytree(item, dest)
                            else:
                                if dest.exists():
                                    os.remove(dest)
                                shutil.copy2(item, dest)
                    
                    logging.info("Arquivos do sistema restaurados com sucesso")
                except Exception as e:
                    logging.error(f"Erro ao restaurar arquivos do sistema: {str(e)}")
                    return False
        
        return True
    except Exception as e:
        logging.error(f"Erro durante a restauração: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Uso: python restore_backup.py <nome_do_backup> [tipo_restauracao]")
        print("Tipos de restauração disponíveis: all (padrão), data, system")
        sys.exit(1)
    
    backup_name = sys.argv[1]
    restore_type = sys.argv[2] if len(sys.argv) == 3 else 'all'
    
    if restore_type not in ['all', 'data', 'system']:
        print("Tipo de restauração inválido. Use: all, data ou system")
        sys.exit(1)
    
    success = restore_backup(backup_name, restore_type)
    
    if success:
        print("Backup restaurado com sucesso!")
    else:
        print("Erro ao restaurar backup. Verifique o arquivo restore.log para mais detalhes.")
        sys.exit(1)
