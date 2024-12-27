import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-super-secreta-temporaria'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///sistema.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # Sessão expira em 30 minutos
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = 'chave-csrf-super-secreta'  # Chave para tokens CSRF
    WTF_CSRF_TIME_LIMIT = 3600  # Tempo de validade do token em segundos
