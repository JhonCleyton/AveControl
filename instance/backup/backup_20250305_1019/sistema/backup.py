import os
import shutil
from datetime import datetime
import zipfile
import threading
import signal
import sys
import logging

# Configurar logging
logging.basicConfig(
    filename='backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Flag global para controle de encerramento
shutdown_flag = threading.Event()

def signal_handler(signum, frame):
    """Manipulador de sinais para encerramento limpo"""
    logging.info("Sinal de encerramento recebido. Finalizando backup...")
    shutdown_flag.set()

def create_backup():
    try:
        # Registrar início do backup
        logging.info("Iniciando processo de backup")
        
        # Criar nome do backup com data e hora
        backup_name = f"backup_sistema_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Criar diretório de backup se não existir
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        # Caminho completo do arquivo zip
        zip_path = os.path.join('backups', f'{backup_name}.zip')
        
        # Lista de arquivos e pastas para ignorar no backup
        ignore = [
            '__pycache__',
            '.git',
            'backups',
            'venv',
            '.env',
            '.pyc',
            'instance'
        ]
        
        def should_ignore(path):
            return any(item in path for item in ignore)
        
        # Criar arquivo zip
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Percorrer todos os arquivos e pastas
            for root, dirs, files in os.walk('.'):
                # Verificar flag de encerramento
                if shutdown_flag.is_set():
                    logging.warning("Processo de backup interrompido pelo usuário")
                    return None
                
                # Filtrar diretórios ignorados
                dirs[:] = [d for d in dirs if not should_ignore(d)]
                
                for file in files:
                    # Verificar flag de encerramento
                    if shutdown_flag.is_set():
                        logging.warning("Processo de backup interrompido pelo usuário")
                        return None
                        
                    file_path = os.path.join(root, file)
                    if not should_ignore(file_path):
                        try:
                            # Adicionar arquivo ao zip
                            arcname = os.path.relpath(file_path, '.')
                            zipf.write(file_path, arcname)
                        except Exception as e:
                            logging.error(f"Erro ao adicionar arquivo {file_path}: {str(e)}")
        
        logging.info(f"Backup criado com sucesso: {zip_path}")
        return zip_path
        
    except Exception as e:
        logging.error(f"Erro durante o backup: {str(e)}")
        return None

if __name__ == '__main__':
    # Registrar handlers de sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar backup
    create_backup()
