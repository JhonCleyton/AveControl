from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_login import login_required
from config import Config, DevelopmentConfig, ProductionConfig
from extensions import db, login_manager, csrf
from flask_migrate import Migrate
from models import Usuario
from datetime import datetime
from routes.auth import auth
from routes.cargas import cargas
from routes.usuarios import usuarios_bp
from routes.dev import dev_bp
from routes.solicitacoes import solicitacoes_bp
from routes.notificacoes import notificacoes_bp
from routes.chat import chat
from routes.main import main_bp
from routes.resumos import resumos_bp
from routes.relatorios import relatorios_bp as relatorios
from routes.perfil import perfil_bp
from routes.backup_routes import backup_bp
from routes.documentos import bp as documentos_bp
from routes.fluxograma import bp as fluxograma_bp
from utils import filters
from sqlalchemy import text
import os
import logging
from logging.handlers import RotatingFileHandler

def create_app():
    app = Flask(__name__)
    
    # Configurar ambiente baseado na variável de ambiente
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object('config.ProductionConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Configurar timeout mais longo para operações demoradas
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
    
    # Criar diretórios necessários
    os.makedirs(app.config['INSTANCE_DIR'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOG_DIR'], exist_ok=True)
    os.makedirs(app.config['CHAT_ICONS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROFILE_PICS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BACKUP_DIR'], exist_ok=True)
    os.makedirs(app.config['TEMP_DIR'], exist_ok=True)
    
    # Garantir que os diretórios tenham permissões corretas
    import stat
    for directory in [app.config['INSTANCE_DIR'], app.config['UPLOAD_FOLDER'], 
                     app.config['LOG_DIR'], app.config['CHAT_ICONS_FOLDER'], 
                     app.config['PROFILE_PICS_FOLDER'], app.config['BACKUP_DIR'], 
                     app.config['TEMP_DIR']]:
        try:
            os.chmod(directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        except Exception as e:
            app.logger.warning(f"Não foi possível definir permissões para {directory}: {e}")
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)
    
    # Handler para arquivo
    file_handler = RotatingFileHandler(
        filename=app.config['LOG_FILE'],
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
    file_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Limpar handlers existentes e adicionar os novos
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate = Migrate(app, db)
    
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
        return db.session.get(Usuario, int(user_id))

    # Registrar blueprints
    from routes.main import main_bp
    from routes.auth import auth
    from routes.cargas import cargas
    from routes.chat import chat
    from routes.api import api
    from routes.usuarios import usuarios_bp
    from routes.dev import dev_bp
    from routes.solicitacoes import solicitacoes_bp
    from routes.notificacoes import notificacoes_bp
    from routes.resumos import resumos_bp
    from routes.relatorios import relatorios_bp as relatorios
    from routes.perfil import perfil_bp
    from routes.backup_routes import backup_bp
    from routes.documentos import bp as documentos_bp
    from routes.fluxograma import bp as fluxograma_bp
    
    app.register_blueprint(main_bp)  # Registrar primeiro para ter prioridade na rota '/'
    app.register_blueprint(auth)
    app.register_blueprint(cargas, url_prefix='/cargas')
    app.register_blueprint(chat, url_prefix='/chat')
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    app.register_blueprint(dev_bp, url_prefix='/dev')
    app.register_blueprint(solicitacoes_bp, url_prefix='/solicitacoes')
    app.register_blueprint(notificacoes_bp, url_prefix='/notificacoes')
    app.register_blueprint(resumos_bp, url_prefix='/resumos')
    app.register_blueprint(relatorios, url_prefix='/relatorios')
    app.register_blueprint(perfil_bp)
    app.register_blueprint(backup_bp, url_prefix='/sistema')
    app.register_blueprint(documentos_bp)
    app.register_blueprint(fluxograma_bp)
    
    # Handler de erro para requisições AJAX
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def handle_error(error):
        if request.headers.get('Accept') == 'application/json':
            response = jsonify({
                'status': 'error',
                'error': str(error),
                'code': error.code if hasattr(error, 'code') else 500
            })
            response.status_code = error.code if hasattr(error, 'code') else 500
            return response
        return error
    
    # Registrar filtros
    filters.init_app(app)
    
    # Rota padrão
    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')
    
    # Rota para a página Info_nutri
    @app.route('/info_nutri')
    def info_nutri():
        return render_template('Info_nutri.html')
    
    # Rota para a página Info_nutri_galinha
    @app.route('/info_nutri_galinha')
    def info_nutri_galinha():
        return render_template('Info_nutri_galinha.html')

    return app

def create_default_users():
    default_users = [
        {
            'nome': 'admin',
            'email': 'admin@exemplo.com',
            'senha': 'admin',
            'tipo': 'gerente'
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
        
    app.run(host='91.108.126.1', port=4000)
