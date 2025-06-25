from extensions import db
from datetime import datetime
from pytz import UTC

class DocumentoCarga(db.Model):
    __tablename__ = 'documentos_carga'

    # Tipos de documentos
    TIPO_BOLETIM_SANITARIO = 'Boletim Sanitário'
    TIPO_BOLETO = 'Boleto'
    TIPO_CHECKLIST = 'Check-List'
    TIPO_COMPROVANTE_ABASTECIMENTO = 'Comprovante de abastecimento'
    TIPO_GTA = 'GTA'
    TIPO_NDFE_CTE = 'NDFE/CTE'
    TIPO_NOTA_FISCAL = 'Nota Fiscal'
    TIPO_TICKET_PESO_GRANJA = 'Ticket de Peso Granja'
    TIPO_TICKET_PESO_FRIGORIFICO = 'Ticket de peso Frigorífico'
    TIPO_OUTRO = 'Outro'

    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id', ondelete='CASCADE'), nullable=False)
    tipo_documento = db.Column(db.String(100), nullable=False)
    outro_tipo_descricao = db.Column(db.String(255))  # Usado quando tipo_documento é 'Outro'
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.now(UTC))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    
    # Campo para registrar documentos faltantes
    ausente = db.Column(db.Boolean, default=False)
    motivo_ausencia = db.Column(db.Text)
    
    # Campos para controle de exclusão
    status_exclusao = db.Column(db.String(20))  # 'pendente', 'aprovado', 'reprovado'
    solicitado_exclusao_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'))
    data_solicitacao_exclusao = db.Column(db.DateTime)
    aprovado_exclusao_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'))
    data_aprovacao_exclusao = db.Column(db.DateTime)
    motivo_exclusao = db.Column(db.Text)
    
    # Relacionamentos
    carga = db.relationship('Carga', backref=db.backref('documentos', lazy=True, cascade='all, delete-orphan'))
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref=db.backref('documentos_carregados', lazy=True))
    solicitado_exclusao_por = db.relationship('Usuario', foreign_keys=[solicitado_exclusao_por_id], backref=db.backref('solicitacoes_exclusao_documento', lazy=True))
    aprovado_exclusao_por = db.relationship('Usuario', foreign_keys=[aprovado_exclusao_por_id], backref=db.backref('aprovacoes_exclusao_documento', lazy=True))

    @staticmethod
    def get_tipos_documento():
        """Retorna lista de tipos de documentos disponíveis"""
        return [
            DocumentoCarga.TIPO_BOLETIM_SANITARIO,
            DocumentoCarga.TIPO_BOLETO,
            DocumentoCarga.TIPO_CHECKLIST,
            DocumentoCarga.TIPO_COMPROVANTE_ABASTECIMENTO,
            DocumentoCarga.TIPO_GTA,
            DocumentoCarga.TIPO_NDFE_CTE,
            DocumentoCarga.TIPO_NOTA_FISCAL,
            DocumentoCarga.TIPO_TICKET_PESO_GRANJA,
            DocumentoCarga.TIPO_TICKET_PESO_FRIGORIFICO,
            DocumentoCarga.TIPO_OUTRO
        ]
