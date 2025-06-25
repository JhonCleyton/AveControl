from extensions import db
from datetime import datetime
from pytz import UTC
from enum import Enum

class TipoMensagem(str, Enum):
    INDIVIDUAL = 'individual'
    GRUPO = 'grupo'

class Mensagens(db.Model):
    __tablename__ = 'mensagens'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # individual ou grupo
    conteudo = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)
    
    # Remetente
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    remetente = db.relationship('Usuario', foreign_keys=[remetente_id], 
                              backref=db.backref('mensagens_enviadas', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Destinatário (apenas para mensagens individuais)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=True)
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id], 
                                 backref=db.backref('mensagens_recebidas', lazy='dynamic', cascade='all, delete-orphan'))
    
    leituras = db.relationship('LeituraMensagem', backref='mensagem', cascade='all, delete-orphan', passive_deletes=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'conteudo': self.conteudo,
            'data_envio': self.data_envio.strftime('%d/%m/%Y %H:%M'),
            'lida': self.lida,
            'remetente': {
                'id': self.remetente.id,
                'nome': self.remetente.nome
            },
            'destinatario': {
                'id': self.destinatario.id,
                'nome': self.destinatario.nome
            } if self.destinatario else None
        }

    @staticmethod
    def enviar_mensagem_individual(remetente_id, destinatario_id, conteudo):
        """Envia uma mensagem individual para um usuário"""
        mensagem = Mensagens(
            tipo=TipoMensagem.INDIVIDUAL,
            conteudo=conteudo,
            remetente_id=remetente_id,
            destinatario_id=destinatario_id
        )
        db.session.add(mensagem)
        db.session.commit()
        return mensagem

    @staticmethod
    def enviar_mensagem_grupo(remetente_id, conteudo):
        """Envia uma mensagem para todos os usuários"""
        mensagem = Mensagens(
            tipo=TipoMensagem.GRUPO,
            conteudo=conteudo,
            remetente_id=remetente_id
        )
        db.session.add(mensagem)
        db.session.commit()
        return mensagem

    @staticmethod
    def get_mensagens_individuais(usuario1_id, usuario2_id, limit=50):
        """Retorna as mensagens entre dois usuários"""
        return Mensagens.query.filter(
            Mensagens.tipo == TipoMensagem.INDIVIDUAL,
            db.or_(
                db.and_(
                    Mensagens.remetente_id == usuario1_id,
                    Mensagens.destinatario_id == usuario2_id
                ),
                db.and_(
                    Mensagens.remetente_id == usuario2_id,
                    Mensagens.destinatario_id == usuario1_id
                )
            )
        ).order_by(Mensagens.data_envio.desc()).limit(limit).all()

    @staticmethod
    def get_mensagens_grupo(limit=50):
        """Retorna as mensagens do grupo"""
        return Mensagens.query.filter_by(
            tipo=TipoMensagem.GRUPO
        ).order_by(Mensagens.data_envio.desc()).limit(limit).all()

    @staticmethod
    def marcar_como_lida(mensagem_id, usuario_id):
        """Marca uma mensagem como lida"""
        mensagem = Mensagens.query.get(mensagem_id)
        if mensagem and mensagem.destinatario_id == usuario_id:
            mensagem.lida = True
            db.session.commit()

class LeituraMensagem(db.Model):
    __tablename__ = 'leituras_mensagens'
    
    id = db.Column(db.Integer, primary_key=True)
    mensagem_id = db.Column(db.Integer, db.ForeignKey('mensagens.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    data_leitura = db.Column(db.DateTime, default=datetime.now(UTC))
    
    usuario = db.relationship('Usuario', backref=db.backref('leituras_mensagens', 
                                                          lazy='dynamic', 
                                                          cascade='all, delete-orphan',
                                                          passive_deletes=True))
