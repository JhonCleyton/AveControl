import os
import shutil
from datetime import datetime
import zipfile

def create_backup():
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
            # Filtrar diretórios ignorados
            dirs[:] = [d for d in dirs if not should_ignore(d)]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not should_ignore(file_path):
                    # Adicionar arquivo ao zip
                    arcname = os.path.relpath(file_path, '.')
                    zipf.write(file_path, arcname)
    
    print(f"Backup criado com sucesso: {zip_path}")
    return zip_path

if __name__ == '__main__':
    create_backup()
