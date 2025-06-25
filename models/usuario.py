from extensions import db
from datetime import datetime, timedelta
from pytz import UTC
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from enum import Enum

class TipoUsuario(str, Enum):
    BALANCA = 'balanca'
    FECHAMENTO = 'fechamento'
    PRODUCAO = 'producao'
    FINANCEIRO = 'financeiro'
    DIRETORIA = 'diretoria'
    GERENTE = 'gerente'
    TRANSPORTADORA = 'transportadora'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default=TipoUsuario.BALANCA.value)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.now(UTC))
    ultimo_acesso = db.Column(db.DateTime)
    tema = db.Column(db.String(20), default='claro')
    notif_email = db.Column(db.Boolean, default=True)
    reset_password_token = db.Column(db.String(100), unique=True)
    reset_password_expires = db.Column(db.DateTime)
    
    # Relacionamentos
    perfil_chat = db.relationship('PerfilChat', uselist=False, back_populates='usuario', cascade='all, delete-orphan')
    historicos_carga = db.relationship('HistoricoCarga', back_populates='usuario', cascade='all, delete-orphan')

    @property
    def username(self):
        return self.nome
    
    @property
    def usuario(self):
        return self.nome

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_gerente(self):
        return self.tipo == 'gerente'

    def __repr__(self):
        return f'<Usuario {self.nome}>'

    def get_reset_token(self, expires_sec=1800):
        """Gera um token para redefinição de senha"""
        s = Serializer(current_app.config['SECRET_KEY'])
        self.reset_password_token = s.dumps({'user_id': self.id})
        self.reset_password_expires = datetime.now(UTC) + timedelta(seconds=expires_sec)
        db.session.commit()
        return self.reset_password_token

    @staticmethod
    def verify_reset_token(token):
        """Verifica se o token de redefinição é válido"""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except:
            return None
        return Usuario.query.get(user_id)

    def delete(self):
        """Método personalizado para excluir usuário e suas relações"""
        try:
            # Primeiro exclui todas as leituras de mensagem
            from models.mensagem import LeituraMensagem
            LeituraMensagem.query.filter_by(usuario_id=self.id).delete(synchronize_session=False)
            
            # Depois exclui o usuário
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
