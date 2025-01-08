import os
import shutil
import datetime
import time
import schedule
import logging
import pytz
from pathlib import Path
from config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup/backup.log'),
        logging.StreamHandler()
    ]
)

# Configurar timezone
TIMEZONE = pytz.timezone('America/Sao_Paulo')

def create_backup():
    try:
        # Criar nome do backup com data e hora
        now = datetime.datetime.now(TIMEZONE)
        backup_time = now.strftime("%Y%m%d_%H%M")
        
        # Criar diretório do backup
        backup_dir = Path('backup')
        backup_dir.mkdir(exist_ok=True)
        
        # Nome do arquivo de backup
        backup_name = f"backup_{backup_time}"
        backup_path = backup_dir / backup_name
        
        # Criar diretório para este backup
        backup_path.mkdir(exist_ok=True)
        
        # Backup do banco de dados
        db_source = Path(Config.DB_PATH)
        if db_source.exists():
            shutil.copy2(db_source, backup_path / 'sistema.db')
            logging.info(f"Backup do banco de dados criado em {backup_path}")
        else:
            logging.warning("Arquivo do banco de dados não encontrado")
        
        # Backup dos arquivos do sistema (exceto diretório de backup e arquivos temporários)
        source_dir = Path('.')
        ignore_patterns = shutil.ignore_patterns(
            'backup*', '__pycache__*', '*.pyc', '*.pyo', 
            '*.pyd', '.git*', 'instance*', 'env*', 'venv*'
        )
        
        shutil.copytree(
            source_dir, 
            backup_path / 'sistema',
            ignore=ignore_patterns,
            dirs_exist_ok=True
        )
        logging.info(f"Backup dos arquivos do sistema criado em {backup_path}")
        
        # Remover backups antigos (mais de 15 dias)
        cleanup_old_backups()
        
    except Exception as e:
        logging.error(f"Erro ao criar backup: {str(e)}")

def cleanup_old_backups():
    try:
        # Calcular data limite (15 dias atrás)
        limit_date = datetime.datetime.now(TIMEZONE) - datetime.timedelta(days=15)
        backup_dir = Path('backup')
        
        # Listar todos os diretórios de backup
        for backup_folder in backup_dir.glob('backup_*'):
            if backup_folder.is_dir():
                try:
                    # Extrair data do nome do backup (formato: backup_YYYYMMDD_HHMM)
                    date_str = backup_folder.name.split('_')[1]
                    backup_date = datetime.datetime.strptime(date_str, '%Y%m%d')
                    backup_date = TIMEZONE.localize(backup_date)
                    
                    # Remover se for mais antigo que 15 dias
                    if backup_date.date() < limit_date.date():
                        shutil.rmtree(backup_folder)
                        logging.info(f"Backup antigo removido: {backup_folder}")
                        
                except (ValueError, IndexError):
                    logging.warning(f"Formato de nome de backup inválido: {backup_folder}")
                    
    except Exception as e:
        logging.error(f"Erro ao limpar backups antigos: {str(e)}")

def run_scheduler():
    # Agendar backups
    schedule.every().day.at("07:00").do(create_backup)
    schedule.every().day.at("18:00").do(create_backup)
    
    logging.info("Agendador de backup iniciado")
    logging.info("Backups agendados para 07:00 e 18:00 (Horário de Brasília)")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar a cada minuto

if __name__ == "__main__":
    run_scheduler()
