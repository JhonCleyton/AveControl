from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import relationship

class TipoUsuario:
    GERENTE = 'gerente'
    DIRETORIA = 'diretoria'
    FINANCEIRO = 'financeiro'
    DEV = 'dev'
    BALANCA = 'balanca'
    PRODUCAO = 'producao'
    FECHAMENTO = 'fechamento'
    TRANSPORTADORA = 'transportadora'

    @staticmethod
    def get_tipos():
        return [
            TipoUsuario.GERENTE,
            TipoUsuario.DIRETORIA,
            TipoUsuario.FINANCEIRO,
            TipoUsuario.DEV,
            TipoUsuario.BALANCA,
            TipoUsuario.PRODUCAO,
            TipoUsuario.FECHAMENTO,
            TipoUsuario.TRANSPORTADORA
        ]

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime)

    # Relacionamentos
    historicos_carga = relationship('HistoricoCarga', 
                                  back_populates='usuario',
                                  primaryjoin="Usuario.id == HistoricoCarga.usuario_id",
                                  cascade='all, delete-orphan')

    @property
    def is_gerente(self):
        return self.tipo == TipoUsuario.GERENTE

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'tipo': self.tipo,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None
        }

    @staticmethod
    def criar_usuario(nome, email, senha, tipo):
        if tipo not in TipoUsuario.get_tipos():
            raise ValueError(f"Tipo de usuário inválido. Tipos permitidos: {', '.join(TipoUsuario.get_tipos())}")
        
        usuario = Usuario(
            nome=nome,
            email=email,
            tipo=tipo
        )
        usuario.set_senha(senha)
        return usuario

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<Usuario {self.nome}>'
