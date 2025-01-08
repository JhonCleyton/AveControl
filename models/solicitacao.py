from extensions import db
from datetime import datetime
from enum import Enum
from config import Config

class TipoSolicitacao(str, Enum):
    REVISAO = 'revisao'
    EXCLUSAO = 'exclusao'
    EDICAO = 'edicao'

class StatusSolicitacao(str, Enum):
    PENDENTE = 'pendente'
    APROVADA = 'aprovada'
    REJEITADA = 'rejeitada'
    FINALIZADA = 'finalizada'

class SetorSolicitacao(str, Enum):
    BALANCA = 'balanca'
    PRODUCAO = 'producao'
    FECHAMENTO = 'fechamento'

class Solicitacao(db.Model):
    __tablename__ = 'solicitacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id', ondelete='CASCADE'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # TipoSolicitacao
    setor = db.Column(db.String(20), nullable=False)  # SetorSolicitacao
    motivo = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default=StatusSolicitacao.PENDENTE)  # StatusSolicitacao
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE))
    atualizado_em = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE), onupdate=lambda: datetime.now(Config.TIMEZONE))
    solicitado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    analisado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    analisado_em = db.Column(db.DateTime)
    observacao_analise = db.Column(db.Text)
    verificado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # Para solicitações de edição
    verificado_em = db.Column(db.DateTime)  # Para solicitações de edição
    
    # Relacionamentos
    carga = db.relationship('Carga', backref=db.backref('solicitacoes', passive_deletes=True))
    solicitado_por = db.relationship('Usuario', foreign_keys=[solicitado_por_id], backref='solicitacoes_feitas')
    analisado_por = db.relationship('Usuario', foreign_keys=[analisado_por_id], backref='solicitacoes_analisadas')
    verificado_por = db.relationship('Usuario', foreign_keys=[verificado_por_id], backref='solicitacoes_verificadas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'carga_id': self.carga_id,
            'tipo': self.tipo,
            'setor': self.setor,
            'motivo': self.motivo,
            'status': self.status,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M'),
            'solicitado_por': self.solicitado_por.nome,
            'analisado_por': self.analisado_por.nome if self.analisado_por else None,
            'analisado_em': self.analisado_em.strftime('%d/%m/%Y %H:%M') if self.analisado_em else None,
            'observacao_analise': self.observacao_analise,
            'verificado_por': self.verificado_por.nome if self.verificado_por else None,
            'verificado_em': self.verificado_em.strftime('%d/%m/%Y %H:%M') if self.verificado_em else None
        }
