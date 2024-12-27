from flask import Flask, render_template, redirect, url_for
from flask_login import login_required
from config import Config
from extensions import db, login_manager, csrf
from flask_migrate import Migrate
from models import Usuario
from datetime import datetime, timezone
from routes.auth import auth_bp
from routes.cargas import cargas_bp
from routes.usuarios import usuarios_bp
from routes.dev import dev_bp
from routes.solicitacoes import solicitacoes_bp
from routes.notificacoes import notificacoes_bp
from routes.chat import chat_bp
from routes.main import main_bp
from routes.resumos import resumos_bp
from routes.relatorios import relatorios_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Inicializar extensões
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configurar login
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints
    app.register_blueprint(main_bp)  # Registrar primeiro para ter prioridade na rota '/'
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(cargas_bp, url_prefix='/cargas')
    app.register_blueprint(solicitacoes_bp, url_prefix='/solicitacoes')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    app.register_blueprint(dev_bp, url_prefix='/dev')
    app.register_blueprint(notificacoes_bp, url_prefix='/notificacoes')
    app.register_blueprint(resumos_bp, url_prefix='/resumos')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

    return app

def create_default_users():
    # Lista de usuários padrão
    default_users = [
        {
            'nome': 'gerente',
            'email': 'gerente@exemplo.com',
            'senha': 'gerente123',
            'tipo': 'gerente',
            'ativo': True,
            'data_criacao': datetime.now(timezone.utc)
        },
        {
            'nome': 'balanca',
            'email': 'balanca@exemplo.com',
            'senha': 'balanca123',
            'tipo': 'balanca',
            'ativo': True,
            'data_criacao': datetime.now(timezone.utc)
        },
        {
            'nome': 'fechamento',
            'email': 'fechamento@exemplo.com',
            'senha': 'fechamento123',
            'tipo': 'fechamento',
            'ativo': True,
            'data_criacao': datetime.now(timezone.utc)
        },
        {
            'nome': 'producao',
            'email': 'producao@exemplo.com',
            'senha': 'producao123',
            'tipo': 'producao',
            'ativo': True,
            'data_criacao': datetime.now(timezone.utc)
        },
        {
            'nome': 'financeiro',
            'email': 'financeiro@exemplo.com',
            'senha': 'financeiro123',
            'tipo': 'financeiro',
            'ativo': True,
            'data_criacao': datetime.now(timezone.utc)
        },
        {
            'nome': 'diretoria',
            'email': 'diretoria@exemplo.com',
            'senha': 'diretoria123',
            'tipo': 'diretoria',
            'ativo': True,
            'data_criacao': datetime.now(timezone.utc)
        }
    ]

    # Criar usuários se não existirem
    for user_data in default_users:
        if not Usuario.query.filter_by(nome=user_data['nome']).first():
            user = Usuario(
                nome=user_data['nome'],
                email=user_data['email'],
                tipo=user_data['tipo'],
                ativo=user_data['ativo'],
                data_criacao=user_data['data_criacao']
            )
            user.set_senha(user_data['senha'])
            db.session.add(user)
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Criar o banco de dados e usuários padrão
        db.create_all()
        create_default_users()
        
    app.run(debug=True)
