import os
from datetime import timedelta
import pytz

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    DB_PATH = os.path.join(INSTANCE_DIR, 'sistema.db')
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-super-secreta-temporaria'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=3)  # Sessão expira em 3 horas
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'chave-csrf-super-secreta'
    WTF_CSRF_TIME_LIMIT = None  # Desabilita o limite de tempo do token CSRF
    TIMEZONE = pytz.timezone('America/Sao_Paulo')  # Timezone de Brasília


DEVELOPER_INFO = {
    'name': 'Jhon Cleyton',
    'company': 'JC Bytes - Soluções em Tecnologia',
    'email': 'jhon.freire@ftc.edu.br',
    'whatsapp': '73 98172-3483',
    'github': 'https://github.com/jhoncleyton',
    'linkedin': 'https://linkedin.com/in/jhon-freire',
}
COPYRIGHT = 'Copyright  2025 JC Bytes - Soluções em Tecnologia. Todos os direitos reservados.'