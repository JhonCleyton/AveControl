from datetime import datetime
from flask import current_app
import pytz

def get_current_time():
    """Retorna a data e hora atual no timezone de São Paulo"""
    # Pega o horário atual em UTC
    now = datetime.utcnow()
    # Adiciona o timezone UTC
    now = pytz.UTC.localize(now)
    # Converte para São Paulo
    return now.astimezone(current_app.config['TIMEZONE'])

def localize_datetime(dt):
    """Converte um datetime para o timezone de São Paulo"""
    if dt is None:
        return None
        
    # Se não tem timezone, assume UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # Converte para São Paulo
    return dt.astimezone(current_app.config['TIMEZONE'])
