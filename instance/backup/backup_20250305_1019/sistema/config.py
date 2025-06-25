import os
from datetime import timedelta
import pytz
import secrets

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    DB_PATH = os.path.join(INSTANCE_DIR, 'sistema.db')
    
    # Gerar chave secreta aleatória se não existir no ambiente
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    VERSION = '0.1.0.2'
    
    # Diretórios
    UPLOAD_FOLDER = os.path.join(INSTANCE_DIR, 'uploads')
    LOG_DIR = os.path.join(INSTANCE_DIR, 'logs')
    CHAT_ICONS_FOLDER = os.path.join(INSTANCE_DIR, 'chat_icons')
    PROFILE_PICS_FOLDER = os.path.join(INSTANCE_DIR, 'profile_pics')
    BACKUP_DIR = os.path.join(INSTANCE_DIR, 'backup')
    TEMP_DIR = os.path.join(INSTANCE_DIR, 'temp')
    
    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de segurança
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or secrets.token_hex(32)
    WTF_CSRF_TIME_LIMIT = None
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Aumentar o tempo de vida da sessão
    SESSION_COOKIE_SECURE = False  # Permitir cookies em HTTP
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_TYPE = 'filesystem'
    REMEMBER_COOKIE_DURATION = timedelta(days=30)  # Cookie de "lembrar-me" dura 30 dias
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_PERMANENT = True
    
    # Configurações regionais
    TIMEZONE = pytz.timezone('America/Sao_Paulo')
    
    # Configurações de upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Configurações de logging
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')
    os.makedirs(LOG_DIR, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False  # Para desenvolvimento local sem HTTPS

class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
    TESTING = False
    
    # Configurações de segurança adicionais para produção
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

# Informações do desenvolvedor
DEVELOPER_INFO = {
    'name': 'Jhon Cleyton',
    'company': 'JC Bytes - Soluções em Tecnologia',
    'email': 'jhon.freire@ftc.edu.br',
    'whatsapp': '73 98172-3483',
    'github': 'https://github.com/jhoncleyton',
    'linkedin': 'https://linkedin.com/in/jhon-freire',
}

COPYRIGHT = 'Copyright  2025 JC Bytes - Soluções em Tecnologia. Todos os direitos reservados.'