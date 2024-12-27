from extensions import db
from datetime import datetime

class Solicitacao(db.Model):
    __tablename__ = 'solicitacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'revisao' ou 'exclusao'
    setor = db.Column(db.String(20), nullable=False)  # 'balanca', 'fechamento', 'producao'
    motivo = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # 'pendente', 'aprovada', 'reprovada'
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    solicitado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    analisado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    analisado_em = db.Column(db.DateTime)
    observacao_analise = db.Column(db.Text)
    
    # Relacionamentos
    carga = db.relationship('Carga', backref='solicitacoes')
    solicitado_por = db.relationship('Usuario', foreign_keys=[solicitado_por_id], backref='solicitacoes_feitas')
    analisado_por = db.relationship('Usuario', foreign_keys=[analisado_por_id], backref='solicitacoes_analisadas')
    
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
            'observacao_analise': self.observacao_analise
        }
