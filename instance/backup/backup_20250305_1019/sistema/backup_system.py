import os
import shutil
import datetime
import time
import schedule
import logging
import pytz
import stat
from pathlib import Path
from config import Config

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'backup.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Configurar timezone
TIMEZONE = pytz.timezone('America/Sao_Paulo')

def set_permissions(path):
    """Define permissões para um arquivo ou diretório"""
    try:
        if os.path.isdir(path):
            # 0777 para diretórios
            os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            # Aplicar recursivamente para subdiretórios e arquivos
            for root, dirs, files in os.walk(path):
                for d in dirs:
                    os.chmod(os.path.join(root, d), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                for f in files:
                    os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
        else:
            # 0666 para arquivos
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
    except Exception as e:
        logging.warning(f"Não foi possível definir permissões para {path}: {e}")

def create_backup():
    try:
        # Criar nome do backup com data e hora
        now = datetime.datetime.now(TIMEZONE)
        backup_time = now.strftime("%Y%m%d_%H%M")
        
        # Criar diretório do backup
        backup_dir = Config.BACKUP_DIR
        try:
            os.makedirs(backup_dir, exist_ok=True)
            set_permissions(backup_dir)
        except PermissionError as e:
            logging.error(f"Erro de permissão ao criar diretório de backup: {e}")
            raise Exception("Erro de permissão ao criar diretório de backup. Verifique as permissões da pasta.")
        
        # Nome do arquivo de backup
        backup_name = f"backup_{backup_time}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Criar diretório para este backup
        try:
            os.makedirs(backup_path, exist_ok=True)
            set_permissions(backup_path)
        except PermissionError as e:
            logging.error(f"Erro de permissão ao criar diretório do backup específico: {e}")
            raise Exception("Erro de permissão ao criar diretório do backup. Verifique as permissões da pasta.")
        
        # Backup do banco de dados
        db_source = Path(Config.DB_PATH)
        if not db_source.exists():
            logging.error("Arquivo do banco de dados não encontrado")
            raise Exception("Arquivo do banco de dados não encontrado")
            
        try:
            shutil.copy2(db_source, os.path.join(backup_path, 'sistema.db'))
            set_permissions(os.path.join(backup_path, 'sistema.db'))
            logging.info(f"Backup do banco de dados criado em {backup_path}")
        except (PermissionError, shutil.Error) as e:
            logging.error(f"Erro ao copiar banco de dados: {e}")
            raise Exception(f"Erro ao copiar banco de dados: {str(e)}")
        
        # Backup dos arquivos do sistema
        sistema_path = os.path.join(backup_path, 'sistema')
        os.makedirs(sistema_path, exist_ok=True)
        set_permissions(sistema_path)
        
        # Lista de arquivos e diretórios a ignorar
        ignore_patterns = shutil.ignore_patterns(
            'backup*', '__pycache__*', '*.pyc', '*.pyo', 
            '*.pyd', '.git*', 'instance*', 'env*', 'venv*',
            'avecontrol.sock', 'sistema.db'
        )
        
        # Copiar arquivos do sistema
        current_dir = os.path.dirname(os.path.abspath(__file__))
        for item in os.listdir(current_dir):
            source = os.path.join(current_dir, item)
            dest = os.path.join(sistema_path, item)
            
            # Ignorar diretórios e arquivos específicos
            if item not in ['backup', '__pycache__', '.git', 'instance', 'env', 'venv']:
                if os.path.isdir(source):
                    shutil.copytree(source, dest, ignore=ignore_patterns, dirs_exist_ok=True)
                    set_permissions(dest)
                else:
                    shutil.copy2(source, dest)
                    set_permissions(dest)
        
        # Backup específico dos arquivos do chat
        chat_backup_path = os.path.join(backup_path, 'chat_files')
        os.makedirs(chat_backup_path, exist_ok=True)
        set_permissions(chat_backup_path)
        
        # Backup dos ícones do chat
        icons_source = Path(Config.CHAT_ICONS_FOLDER)
        if icons_source.exists():
            icons_dest = os.path.join(chat_backup_path, 'icons')
            shutil.copytree(icons_source, icons_dest, dirs_exist_ok=True)
            set_permissions(icons_dest)
            logging.info("Backup dos ícones do chat realizado")
            
        # Backup das fotos de perfil
        profile_source = Path(Config.PROFILE_PICS_FOLDER)
        if profile_source.exists():
            profile_dest = os.path.join(chat_backup_path, 'profile_pics')
            shutil.copytree(profile_source, profile_dest, dirs_exist_ok=True)
            set_permissions(profile_dest)
            logging.info("Backup das fotos de perfil realizado")
            
        logging.info(f"Backup completo criado em {backup_path}")
        return backup_name
        
    except Exception as e:
        logging.error(f"Erro ao criar backup: {str(e)}")
        raise

def restore_backup(backup_name, tipo_restauracao='completo'):
    """
    Restaura um backup do sistema.
    
    Args:
        backup_name (str): Nome do arquivo de backup a ser restaurado
        tipo_restauracao (str): Tipo de restauração a ser realizada:
            - 'completo': Restaura sistema e dados
            - 'dados': Restaura apenas os dados
            - 'sistema': Restaura apenas os arquivos do sistema
    """
    try:
        backup_path = os.path.join(Config.BACKUP_DIR, backup_name)
        
        if not os.path.exists(backup_path):
            raise Exception(f"Backup não encontrado: {backup_name}")
            
        if tipo_restauracao not in ['completo', 'dados', 'sistema']:
            raise Exception("Tipo de restauração inválido")
            
        # Restaurar banco de dados
        if tipo_restauracao in ['completo', 'dados']:
            db_backup = os.path.join(backup_path, 'sistema.db')
            if not os.path.exists(db_backup):
                raise Exception("Arquivo de banco de dados não encontrado no backup")
                
            try:
                shutil.copy2(db_backup, Config.DB_PATH)
                set_permissions(Config.DB_PATH)
                logging.info("Banco de dados restaurado")
            except (PermissionError, shutil.Error) as e:
                raise Exception(f"Erro ao restaurar banco de dados: {str(e)}")
        
        # Restaurar arquivos do sistema
        if tipo_restauracao in ['completo', 'sistema']:
            sistema_backup = os.path.join(backup_path, 'sistema')
            if not os.path.exists(sistema_backup):
                raise Exception("Arquivos do sistema não encontrados no backup")
                
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                for item in os.listdir(sistema_backup):
                    source = os.path.join(sistema_backup, item)
                    dest = os.path.join(current_dir, item)
                    
                    if os.path.isdir(source):
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                        set_permissions(dest)
                    else:
                        shutil.copy2(source, dest)
                        set_permissions(dest)
                        
                logging.info("Arquivos do sistema restaurados")
            except (PermissionError, shutil.Error) as e:
                raise Exception(f"Erro ao restaurar arquivos do sistema: {str(e)}")
        
        # Restaurar arquivos do chat
        if tipo_restauracao in ['completo', 'dados']:
            chat_backup = os.path.join(backup_path, 'chat_files')
            if os.path.exists(chat_backup):
                try:
                    # Restaurar ícones
                    icons_backup = os.path.join(chat_backup, 'icons')
                    if os.path.exists(icons_backup):
                        shutil.rmtree(Config.CHAT_ICONS_FOLDER, ignore_errors=True)
                        shutil.copytree(icons_backup, Config.CHAT_ICONS_FOLDER, dirs_exist_ok=True)
                        set_permissions(Config.CHAT_ICONS_FOLDER)
                        logging.info("Ícones do chat restaurados")
                    
                    # Restaurar fotos de perfil
                    profile_backup = os.path.join(chat_backup, 'profile_pics')
                    if os.path.exists(profile_backup):
                        shutil.rmtree(Config.PROFILE_PICS_FOLDER, ignore_errors=True)
                        shutil.copytree(profile_backup, Config.PROFILE_PICS_FOLDER, dirs_exist_ok=True)
                        set_permissions(Config.PROFILE_PICS_FOLDER)
                        logging.info("Fotos de perfil restauradas")
                        
                except (PermissionError, shutil.Error) as e:
                    raise Exception(f"Erro ao restaurar arquivos do chat: {str(e)}")
        
        logging.info(f"Backup {backup_name} restaurado com sucesso")
        
    except Exception as e:
        logging.error(f"Erro ao restaurar backup: {str(e)}")
        raise

def list_backups():
    """Lista todos os backups disponíveis"""
    import os
    from config import Config
    
    # Garantir que o diretório existe
    os.makedirs(Config.BACKUP_DIR, exist_ok=True)
    set_permissions(Config.BACKUP_DIR)
    
    backups = []
    try:
        for item in os.listdir(Config.BACKUP_DIR):
            if item.startswith('backup_'):
                file_path = os.path.join(Config.BACKUP_DIR, item)
                if os.path.isdir(file_path):
                    try:
                        backups.append({
                            'nome': item,
                            'tamanho': sum(os.path.getsize(os.path.join(dirpath,filename)) 
                                         for dirpath, dirnames, filenames in os.walk(file_path) 
                                         for filename in filenames),
                            'data': os.path.getmtime(file_path)
                        })
                    except (PermissionError, OSError) as e:
                        logging.warning(f"Erro ao acessar backup {item}: {e}")
                        continue
    except Exception as e:
        logging.error(f"Erro ao listar backups: {str(e)}")
        raise
        
    return sorted(backups, key=lambda x: x['data'], reverse=True)

def cleanup_old_backups():
    """Remove backups antigos mantendo apenas os últimos 5"""
    try:
        backups = list_backups()
        if len(backups) > 5:
            for backup in backups[5:]:
                backup_path = os.path.join(Config.BACKUP_DIR, backup['nome'])
                try:
                    shutil.rmtree(backup_path)
                    logging.info(f"Backup antigo removido: {backup['nome']}")
                except Exception as e:
                    logging.error(f"Erro ao remover backup antigo {backup['nome']}: {e}")
    except Exception as e:
        logging.error(f"Erro ao limpar backups antigos: {e}")

def run_scheduler():
    """Configura e executa o agendador de tarefas"""
    schedule.every().day.at("03:00").do(create_backup)  # Backup diário às 3h
    schedule.every().day.at("04:00").do(cleanup_old_backups)  # Limpeza diária às 4h
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            try:
                create_backup()
                print("Backup criado com sucesso!")
            except Exception as e:
                print(f"Erro ao criar backup: {e}")
                sys.exit(1)
                
        elif command == "restore" and len(sys.argv) > 2:
            backup_name = sys.argv[2]
            tipo = sys.argv[3] if len(sys.argv) > 3 else 'completo'
            
            try:
                restore_backup(backup_name, tipo)
                print("Backup restaurado com sucesso!")
            except Exception as e:
                print(f"Erro ao restaurar backup: {e}")
                sys.exit(1)
                
        elif command == "list":
            try:
                backups = list_backups()
                if backups:
                    print("\nBackups disponíveis:")
                    for backup in backups:
                        size_mb = backup['tamanho'] / (1024 * 1024)
                        date = datetime.datetime.fromtimestamp(backup['data'])
                        print(f"{backup['nome']} ({size_mb:.2f} MB - {date})")
                else:
                    print("Nenhum backup encontrado.")
            except Exception as e:
                print(f"Erro ao listar backups: {e}")
                sys.exit(1)
                
        elif command == "clean":
            try:
                cleanup_old_backups()
                print("Limpeza de backups antigos concluída!")
            except Exception as e:
                print(f"Erro ao limpar backups antigos: {e}")
                sys.exit(1)
                
        elif command == "scheduler":
            print("Iniciando agendador de backups...")
            run_scheduler()
            
        else:
            print("Comando inválido!")
            print("Uso: python backup_system.py [create|restore <backup_name> [tipo]|list|clean|scheduler]")
            sys.exit(1)
    else:
        print("Nenhum comando especificado!")
        print("Uso: python backup_system.py [create|restore <backup_name> [tipo]|list|clean|scheduler]")
        sys.exit(1)
