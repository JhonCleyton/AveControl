from flask import Flask, render_template, redirect, url_for
from flask_login import login_required
from config import Config
from extensions import db, login_manager, csrf
from flask_migrate import Migrate
from models import Usuario
from datetime import datetime
from routes.auth import auth_bp
from routes.cargas import cargas
from routes.usuarios import usuarios_bp
from routes.dev import dev_bp
from routes.solicitacoes import solicitacoes_bp
from routes.notificacoes import notificacoes_bp
from routes.chat import chat_bp
from routes.main import main_bp
from routes.resumos import resumos_bp
from routes.relatorios import relatorios_bp
from routes.perfil import perfil
from utils import filters
from sqlalchemy import text

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Inicializar extensões
    db.init_app(app)
    migrate = Migrate(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Configurar timezone
    @app.template_filter('format_datetime')
    def format_datetime(value, format='%d/%m/%Y %H:%M'):
        if value is None:
            return ""
        if value.tzinfo is None:
            value = app.config['TIMEZONE'].localize(value)
        return value.strftime(format)

    # Configurar login
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(cargas, url_prefix='/cargas')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    app.register_blueprint(dev_bp, url_prefix='/dev')
    app.register_blueprint(solicitacoes_bp, url_prefix='/solicitacoes')
    app.register_blueprint(notificacoes_bp, url_prefix='/notificacoes')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(main_bp)  # Registrar primeiro para ter prioridade na rota '/'
    app.register_blueprint(resumos_bp, url_prefix='/resumos')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(perfil)
    
    # Registrar filtros personalizados
    filters.init_app(app)

    return app

def create_default_users():
    """Cria usuários padrão se não existirem"""
    default_users = [
        {
            'nome': 'admin',
            'email': 'admin@exemplo.com',
            'senha': 'admin',
            'tipo': 'admin'
        },
        {
            'nome': 'gerente',
            'email': 'gerente@exemplo.com',
            'senha': 'gerente',
            'tipo': 'gerente'
        }
    ]

    from models import Usuario
    from extensions import db

    for user_data in default_users:
        # Verifica se já existe usuário com mesmo nome ou email
        if not Usuario.query.filter(
            (Usuario.nome == user_data['nome']) | 
            (Usuario.email == user_data['email'])
        ).first():
            user = Usuario(
                nome=user_data['nome'],
                email=user_data['email'],
                tipo=user_data['tipo'],
                ativo=True
            )
            user.set_senha(user_data['senha'])
            db.session.add(user)
            
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar usuários padrão: {str(e)}")

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Criar o banco de dados e usuários padrão
        db.create_all()
        create_default_users()
        
    app.run(host='0.0.0.0', port=5000, debug=True)
