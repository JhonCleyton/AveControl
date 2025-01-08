from extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, text

class HistoricoCarga(db.Model):
    __tablename__ = 'historico_carga'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, ForeignKey('cargas.id', ondelete='CASCADE', name='fk_historico_carga'), nullable=False)
    usuario_id = db.Column(db.Integer, ForeignKey('usuarios.id', ondelete='CASCADE', name='fk_historico_usuario'), nullable=False)
    acao = db.Column(db.String(255), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relacionamentos
    carga = relationship('Carga', 
                        back_populates='historicos',
                        foreign_keys=[carga_id])
    usuario = relationship('Usuario', 
                         back_populates='historicos_carga',
                         foreign_keys=[usuario_id])
