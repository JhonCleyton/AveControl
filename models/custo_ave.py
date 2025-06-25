from extensions import db
from datetime import datetime
from pytz import UTC

class CustoAve(db.Model):
    __tablename__ = 'custo_aves'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id'), unique=True)
    custo_carregamento = db.Column(db.Float, default=0)
    comissao = db.Column(db.Float, default=0)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.now(UTC))
    atualizado_em = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    atualizado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Relacionamentos
    carga = db.relationship('Carga', back_populates='custo_ave', uselist=False)
    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id])
    atualizado_por = db.relationship('Usuario', foreign_keys=[atualizado_por_id])

    def to_dict(self):
        return {
            'id': self.id,
            'carga_id': self.carga_id,
            'custo_carregamento': self.custo_carregamento,
            'comissao': self.comissao,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
