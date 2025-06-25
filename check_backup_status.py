import os
import datetime
import pytz
import logging
from pathlib import Path

def check_backup_status():
    # Configurar timezone
    TIMEZONE = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(TIMEZONE)
    
    # Verificar arquivo de log
    log_file = Path('backup/backup.log')
    if not log_file.exists():
        print("❌ Arquivo de log não encontrado. O sistema de backup pode não estar configurado.")
        return False
    
    # Ler última linha do log
    with open(log_file, 'r') as f:
        lines = f.readlines()
        if lines:
            last_log = lines[-1]
            print(f"📝 Última entrada no log: {last_log.strip()}")
        else:
            print("❌ Arquivo de log está vazio")
    
    # Verificar diretório de backup
    backup_dir = Path('backup')
    if not backup_dir.exists():
        print("❌ Diretório de backup não encontrado")
        return False
    
    # Listar backups
    backups = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith('backup_')]
    if not backups:
        print("❌ Nenhum backup encontrado")
        return False
    
    # Ordenar backups por data (mais recente primeiro)
    backups.sort(reverse=True)
    latest_backup = backups[0]
    
    # Extrair data do nome do backup
    try:
        backup_date_str = latest_backup.name.split('_')[1]
        backup_date = datetime.datetime.strptime(backup_date_str, "%Y%m%d%H%M")
        backup_date = TIMEZONE.localize(backup_date)
        
        # Calcular tempo desde último backup
        time_diff = now - backup_date
        hours_diff = time_diff.total_seconds() / 3600
        
        print(f"\n📊 Status do Sistema de Backup:")
        print(f"✅ Último backup: {backup_date.strftime('%d/%m/%Y %H:%M')}")
        print(f"⏱️ Tempo desde último backup: {hours_diff:.1f} horas")
        print(f"📁 Total de backups: {len(backups)}")
        
        # Verificar se o último backup está dentro do esperado (24 horas)
        if hours_diff > 24:
            print("⚠️ AVISO: Último backup tem mais de 24 horas!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar data do backup: {e}")
        return False

if __name__ == "__main__":
    status = check_backup_status()
    print(f"\n{'✅ Sistema de backup operacional' if status else '❌ Sistema de backup pode estar com problemas'}")
