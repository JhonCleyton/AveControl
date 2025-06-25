import os
import shutil
from datetime import datetime
import zipfile

def criar_backup():
    # Diretório base do projeto
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Diretório do banco de dados
    instance_dir = os.path.join(base_dir, 'instance')
    db_file = os.path.join(instance_dir, 'sistema.db')
    
    # Diretório de uploads
    uploads_dir = os.path.join(base_dir, 'static', 'uploads')
    
    # Criar nome do arquivo de backup com data e hora
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    backup_filename = f'backup_sistema_{timestamp}.zip'
    backup_path = os.path.join(base_dir, 'backups', backup_filename)
    
    # Criar diretório de backups se não existir
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    # Criar arquivo ZIP com banco de dados e uploads
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Adicionar banco de dados
        if os.path.exists(db_file):
            zipf.write(db_file, os.path.join('instance', 'sistema.db'))
            print(f'Banco de dados adicionado ao backup: {db_file}')
        
        # Adicionar pasta de uploads
        if os.path.exists(uploads_dir):
            for foldername, _, filenames in os.walk(uploads_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, base_dir)
                    zipf.write(file_path, arcname)
            print(f'Arquivos de upload adicionados ao backup: {uploads_dir}')
    
    print(f'\nBackup criado com sucesso: {backup_path}')
    print('\nEste arquivo contém:')
    print('1. Banco de dados (sistema.db)')
    print('2. Arquivos de upload (imagens, etc)')
    print('\nPara restaurar no VPS:')
    print('1. Extraia o arquivo ZIP no diretório do projeto')
    print('2. Certifique-se que as permissões dos arquivos estejam corretas')
    print('3. Reinicie o servidor web')

if __name__ == '__main__':
    criar_backup()
