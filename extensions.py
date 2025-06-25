from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
mail = Mail()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'
login_manager.needs_refresh_message = 'Por favor, faça login novamente para continuar.'
login_manager.needs_refresh_message_category = 'info'
login_manager.session_protection = 'basic'  # Menos restritivo que 'strong'
login_manager.refresh_view = 'auth.login'
