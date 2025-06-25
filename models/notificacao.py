from extensions import db
from datetime import datetime
import pytz

class TipoNotificacao:
    NOVA_CARGA = 'nova_carga'
    PRODUCAO_INSERIDA = 'producao_inserida'
    FECHAMENTO_INSERIDO = 'fechamento_inserido'
    CARGA_INCOMPLETA = 'carga_incompleta'

class Notificacao(db.Model):
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('America/Sao_Paulo')))
    lida = db.Column(db.Boolean, default=False)
    exibir_popup = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    usuario = db.relationship('Usuario', backref=db.backref('notificacoes', lazy=True, cascade='all, delete-orphan'))
    
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id', ondelete='CASCADE'), nullable=True)
    carga = db.relationship('Carga', backref=db.backref('notificacoes', lazy=True, cascade='all, delete-orphan'))

    @staticmethod
    def criar_notificacao(tipo, titulo, mensagem, usuario_id, carga_id=None, exibir_popup=False):
        notificacao = Notificacao(
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            usuario_id=usuario_id,
            carga_id=carga_id,
            exibir_popup=exibir_popup
        )
        db.session.add(notificacao)
        db.session.commit()
        return notificacao

    @staticmethod
    def criar_notificacao_nova_carga(carga, usuarios):
        """Cria notificação para nova carga"""
        for usuario in usuarios:
            Notificacao.criar_notificacao(
                tipo=TipoNotificacao.NOVA_CARGA,
                titulo=f'Nova Carga #{carga.numero_carga}',
                mensagem=f'Uma nova carga foi criada: #{carga.numero_carga}',
                usuario_id=usuario.id,
                carga_id=carga.id
            )

    @staticmethod
    def criar_notificacao_producao(carga, usuarios):
        """Cria notificação quando produção é inserida"""
        for usuario in usuarios:
            Notificacao.criar_notificacao(
                tipo=TipoNotificacao.PRODUCAO_INSERIDA,
                titulo=f'Produção Inserida - Carga #{carga.numero_carga}',
                mensagem=f'A produção foi inserida para a carga #{carga.numero_carga}',
                usuario_id=usuario.id,
                carga_id=carga.id
            )

    @staticmethod
    def criar_notificacao_fechamento(carga, usuarios):
        """Cria notificação quando fechamento é inserido"""
        for usuario in usuarios:
            Notificacao.criar_notificacao(
                tipo=TipoNotificacao.FECHAMENTO_INSERIDO,
                titulo=f'Fechamento Inserido - Carga #{carga.numero_carga}',
                mensagem=f'O fechamento foi inserido para a carga #{carga.numero_carga}',
                usuario_id=usuario.id,
                carga_id=carga.id
            )

    @staticmethod
    def criar_notificacao_carga_incompleta(carga, usuarios):
        """Cria notificação para cargas incompletas após 24h"""
        for usuario in usuarios:
            Notificacao.criar_notificacao(
                tipo=TipoNotificacao.CARGA_INCOMPLETA,
                titulo=f'Carga Incompleta #{carga.numero_carga}',
                mensagem=f'A carga #{carga.numero_carga} está incompleta há mais de 24 horas.',
                usuario_id=usuario.id,
                carga_id=carga.id,
                exibir_popup=True
            )
