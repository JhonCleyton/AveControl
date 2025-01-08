from datetime import datetime
from enum import Enum
from . import db

class StatusSolicitacao(str, Enum):
    PENDENTE = 'PENDENTE'
    APROVADA = 'APROVADA'
    REJEITADA = 'REJEITADA'
    FINALIZADA = 'FINALIZADA'

class TipoSolicitacao(str, Enum):
    BALANCA = 'BALANCA'
    PRODUCAO = 'PRODUCAO'
    FECHAMENTO = 'FECHAMENTO'

class SolicitacaoEdicao(db.Model):
    __tablename__ = 'solicitacoes_edicao'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # BALANCA, PRODUCAO, FECHAMENTO
    status = db.Column(db.String(20), default=StatusSolicitacao.PENDENTE)  # PENDENTE, APROVADA, REJEITADA, FINALIZADA
    motivo = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    solicitado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    aprovado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    verificado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    carga = db.relationship('Carga', backref=db.backref('solicitacoes_edicao', lazy=True))
    solicitado_por = db.relationship('Usuario', foreign_keys=[solicitado_por_id], backref=db.backref('solicitacoes_feitas', lazy=True))
    aprovado_por = db.relationship('Usuario', foreign_keys=[aprovado_por_id], backref=db.backref('solicitacoes_aprovadas', lazy=True))
    verificado_por = db.relationship('Usuario', foreign_keys=[verificado_por_id], backref=db.backref('solicitacoes_verificadas', lazy=True))
    
    def __repr__(self):
        return f'<SolicitacaoEdicao {self.id} - Carga {self.carga_id} - {self.tipo} - {self.status}>'
