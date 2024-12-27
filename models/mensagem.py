from extensions import db
from datetime import datetime

class TipoMensagem:
    INDIVIDUAL = 'individual'
    GRUPO = 'grupo'

class Mensagem(db.Model):
    __tablename__ = 'mensagens'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # individual ou grupo
    conteudo = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)
    
    # Remetente
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    remetente = db.relationship('Usuario', foreign_keys=[remetente_id], backref='mensagens_enviadas')
    
    # Destinatário (apenas para mensagens individuais)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id], backref='mensagens_recebidas')

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
        mensagem = Mensagem(
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
        mensagem = Mensagem(
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
        return Mensagem.query.filter(
            Mensagem.tipo == TipoMensagem.INDIVIDUAL,
            db.or_(
                db.and_(
                    Mensagem.remetente_id == usuario1_id,
                    Mensagem.destinatario_id == usuario2_id
                ),
                db.and_(
                    Mensagem.remetente_id == usuario2_id,
                    Mensagem.destinatario_id == usuario1_id
                )
            )
        ).order_by(Mensagem.data_envio.desc()).limit(limit).all()

    @staticmethod
    def get_mensagens_grupo(limit=50):
        """Retorna as mensagens do grupo"""
        return Mensagem.query.filter_by(
            tipo=TipoMensagem.GRUPO
        ).order_by(Mensagem.data_envio.desc()).limit(limit).all()

    @staticmethod
    def marcar_como_lida(mensagem_id, usuario_id):
        """Marca uma mensagem como lida"""
        mensagem = Mensagem.query.get(mensagem_id)
        if mensagem and mensagem.destinatario_id == usuario_id:
            mensagem.lida = True
            db.session.commit()
