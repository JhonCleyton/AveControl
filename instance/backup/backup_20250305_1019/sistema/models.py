from extensions import db
from datetime import datetime
from pytz import UTC
from models.usuario import Usuario
from models.mensagem import Mensagens, LeituraMensagem

class Carga(db.Model):
    __tablename__ = 'cargas'
    
    # Constantes para status
    STATUS_PENDENTE = 'pendente'
    STATUS_EM_ANDAMENTO = 'em_andamento'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CANCELADA = 'cancelada'
    STATUS_INCOMPLETA = 'incompleta'

    id = db.Column(db.Integer, primary_key=True)
    numero_carga = db.Column(db.String(20), unique=True, nullable=False)
    tipo_ave = db.Column(db.String(50), nullable=False)
    quantidade_cargas = db.Column(db.Integer, nullable=False)
    ordem_carga = db.Column(db.String(10), nullable=False)
    data_abate = db.Column(db.Date, nullable=False)
    dia_semana = db.Column(db.String(20))
    agenciador = db.Column(db.String(100))
    motorista = db.Column(db.String(100))
    motorista_outro = db.Column(db.String(100))
    transportadora = db.Column(db.String(100))
    placa_veiculo = db.Column(db.String(20))
    km_saida = db.Column(db.Float, default=0)
    km_chegada = db.Column(db.Float, default=0)
    km_rodados = db.Column(db.Float, default=0)
    valor_km = db.Column(db.Float, default=0)
    valor_frete = db.Column(db.Float, default=0)
    status_frete = db.Column(db.String(50), default='A_PAGAR')
    caixas_vazias = db.Column(db.Integer, default=0)
    quantidade_caixas = db.Column(db.Integer, default=0)
    produtor = db.Column(db.String(100))
    uf_produtor = db.Column(db.String(2))
    numero_nfe = db.Column(db.String(50))
    data_nfe = db.Column(db.Date)
    numero_gta = db.Column(db.String(50))
    data_gta = db.Column(db.Date)
    peso_granja = db.Column(db.Float, default=0)
    peso_frigorifico = db.Column(db.Float, default=0)
    percentual_quebra = db.Column(db.Float, default=0)
    quebra_peso = db.Column(db.Float, default=0)
    motivo_alta_quebra = db.Column(db.Text)
    pedagios = db.Column(db.Float, default=0)
    outras_despesas = db.Column(db.Float, default=0)
    abastecimento_empresa = db.Column(db.Float, default=0)
    abastecimento_posto = db.Column(db.Float, default=0)
    adiantamento = db.Column(db.Float, default=0)
    valor_pagar = db.Column(db.Float, default=0)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.now(UTC))
    atualizado_em = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'))
    status = db.Column(db.String(20), default=STATUS_PENDENTE)
    
    # Campos de aprovação e autorização
    nota_aprovada = db.Column(db.Boolean, default=False)
    aprovado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'))
    aprovado_em = db.Column(db.DateTime)
    nota_autorizada = db.Column(db.Boolean, default=False)
    autorizado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'))
    autorizado_em = db.Column(db.DateTime)
    assinatura_autorizacao = db.Column(db.Text)
    
    # Campos de verificação e exclusão
    status_verificacao = db.Column(db.String(20))
    motivo_verificacao = db.Column(db.Text)
    solicitado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'))
    data_solicitacao = db.Column(db.DateTime)
    status_exclusao = db.Column(db.String(20))
    motivo_exclusao = db.Column(db.Text)
    solicitado_exclusao_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'))
    data_solicitacao_exclusao = db.Column(db.DateTime)

    def atualizar_status(self, novo_status):
        """
        Atualiza o status da carga e registra a data de atualização.
        
        Args:
            novo_status (str): Novo status da carga (deve ser um dos status definidos nas constantes)
        """
        if novo_status in [self.STATUS_PENDENTE, self.STATUS_EM_ANDAMENTO, self.STATUS_CONCLUIDA, self.STATUS_CANCELADA, self.STATUS_INCOMPLETA]:
            self.status = novo_status
            self.atualizado_em = datetime.now(UTC)
            return True
        return False
    
    # Relacionamentos
    subcargas = db.relationship('SubCarga', backref='carga_principal', lazy=True, cascade='all, delete-orphan')
    fechamento = db.relationship('Fechamento', back_populates='carga', uselist=False, cascade='all, delete-orphan')
    producoes = db.relationship('Producao', backref='carga', cascade='all, delete-orphan')
    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id], cascade='all, delete-orphan')
    aprovado_por = db.relationship('Usuario', foreign_keys=[aprovado_por_id], cascade='all, delete-orphan')
    autorizado_por = db.relationship('Usuario', foreign_keys=[autorizado_por_id], cascade='all, delete-orphan')
    solicitado_por = db.relationship('Usuario', foreign_keys=[solicitado_por_id], cascade='all, delete-orphan')
    solicitado_exclusao_por = db.relationship('Usuario', foreign_keys=[solicitado_exclusao_por_id], cascade='all, delete-orphan')

    @classmethod
    def atualizar_status_cargas(cls):
        try:
            cargas = cls.query.all()
            for carga in cargas:
                # Se a carga estiver incompleta, marcar como pendente
                if carga.status == 'incompleta':
                    carga.status = cls.STATUS_PENDENTE
                # Se a carga estiver completa, marcar como concluída
                elif carga.status == 'completa':
                    carga.status = cls.STATUS_CONCLUIDA
            
            db.session.commit()
            print("Status das cargas atualizado com sucesso!")
            return True
        except Exception as e:
            print(f"Erro ao atualizar status das cargas: {str(e)}")
            db.session.rollback()
            return False

class SubCarga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('carga.id', ondelete='CASCADE'), nullable=False)
    numero_subcarga = db.Column(db.String(20))
    tipo_ave = db.Column(db.String(50))
    produtor = db.Column(db.String(100))
    uf_produtor = db.Column(db.String(2))
    numero_nfe = db.Column(db.String(50))
    data_nfe = db.Column(db.Date)
    numero_gta = db.Column(db.String(50))
    data_gta = db.Column(db.Date)
    criado_em = db.Column(db.DateTime, default=datetime.now(UTC))

class ConfiguracaoFormulario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_campo = db.Column(db.String(100), nullable=False)
    tipo_campo = db.Column(db.String(50), nullable=False)
    obrigatorio = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer)
    opcoes = db.Column(db.Text)

class Fechamento(db.Model):
    __tablename__ = 'fechamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id', ondelete='CASCADE'), unique=True)
    tratativas = db.Column(db.String(1), nullable=False)  # '1' ou '2'
    
    # Primeira tratativa
    tipo_fechamento_1 = db.Column(db.String(10), nullable=False)  # 'unidade' ou 'kg'
    quantidade_1 = db.Column(db.Float, nullable=False)
    valor_unitario_1 = db.Column(db.Float, nullable=False)
    descontos_1 = db.Column(db.Float, nullable=False, default=0)
    valor_total_1 = db.Column(db.Float, nullable=False)
    observacoes_1 = db.Column(db.Text)
    
    # Segunda tratativa (opcional)
    tipo_fechamento_2 = db.Column(db.String(10))
    quantidade_2 = db.Column(db.Float)
    valor_unitario_2 = db.Column(db.Float)
    descontos_2 = db.Column(db.Float, default=0)
    valor_total_2 = db.Column(db.Float)
    observacoes_2 = db.Column(db.Text)
    
    # Relacionamento com a carga
    carga = db.relationship('Carga', back_populates='fechamento', uselist=False)
    
    def to_dict(self):
        data = {
            'id': self.id,
            'carga_id': self.carga_id,
            'tratativas': self.tratativas,
            'tipo_fechamento_1': self.tipo_fechamento_1,
            'quantidade_1': self.quantidade_1,
            'valor_unitario_1': self.valor_unitario_1,
            'descontos_1': self.descontos_1,
            'valor_total_1': self.valor_total_1,
            'observacoes_1': self.observacoes_1
        }
        
        if self.tratativas == '2':
            data.update({
                'tipo_fechamento_2': self.tipo_fechamento_2,
                'quantidade_2': self.quantidade_2,
                'valor_unitario_2': self.valor_unitario_2,
                'descontos_2': self.descontos_2,
                'valor_total_2': self.valor_total_2,
                'observacoes_2': self.observacoes_2
            })
            
        return data
    
    def update_from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Producao(db.Model):
    __tablename__ = 'producao'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id', ondelete='CASCADE'), nullable=False)
    
    # Contagem de Aves
    aves_granja = db.Column(db.Integer, nullable=False)
    aves_mortas = db.Column(db.Integer, nullable=False)
    aves_recebidas = db.Column(db.Integer, nullable=False)
    aves_contador = db.Column(db.Integer, nullable=False)
    aves_por_caixa = db.Column(db.Integer, nullable=False)
    
    # Avarias
    mortalidade_excesso = db.Column(db.Float, nullable=False, default=0)  # em KG
    aves_molhadas_granja = db.Column(db.Float, nullable=False, default=0)  # em KG
    aves_molhadas_chuva = db.Column(db.Float, nullable=False, default=0)  # em KG
    quebra_maus_tratos = db.Column(db.Float, nullable=False, default=0)  # em KG
    aves_papo_cheio = db.Column(db.Float, nullable=False, default=0)  # em KG
    outras_quebras = db.Column(db.Float, nullable=False, default=0)  # em KG
    descricao_quebras = db.Column(db.Text)
    total_avarias = db.Column(db.Float, nullable=False, default=0)  # em KG - calculado automaticamente
    
    data_producao = db.Column(db.Date, nullable=False, default=datetime.now(UTC).date())
    criado_em = db.Column(db.DateTime, default=datetime.now(UTC))
    
    # Relacionamento com a carga
    carga = db.relationship('Carga', backref='producoes')
    
    def calcular_total_avarias(self):
        self.total_avarias = (
            self.mortalidade_excesso +
            self.aves_molhadas_granja +
            self.aves_molhadas_chuva +
            self.quebra_maus_tratos +
            self.aves_papo_cheio +
            self.outras_quebras
        )

class PerfilChat(db.Model):
    __tablename__ = 'perfis_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), unique=True, nullable=False)
    nome_exibicao = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    foto_perfil = db.Column(db.String(255))  # Caminho para a foto
    icone_perfil = db.Column(db.String(100))  # Nome do ícone da pasta static/icons
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.now(UTC))
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome_exibicao': self.nome_exibicao or self.usuario.nome,
            'descricao': self.descricao or '',
            'foto_perfil': self.foto_perfil,
            'icone_perfil': self.icone_perfil,
            'ultima_atualizacao': self.ultima_atualizacao.isoformat() if self.ultima_atualizacao else None
        }

from utils.datetime_utils import get_current_time

class HistoricoCarga(db.Model):
    __tablename__ = 'historico_carga'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('carga.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    acao = db.Column(db.String(255), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    
    # Relacionamentos
    carga = db.relationship('Carga', backref=db.backref('historicos', lazy=True, cascade='all, delete-orphan'))
    usuario = db.relationship('Usuario', backref=db.backref('historicos_carga', lazy=True, cascade='all, delete-orphan'))

class Mensagens(db.Model):
    __tablename__ = 'mensagens'
    
    id = db.Column(db.Integer, primary_key=True)
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.now(UTC))
    tipo = db.Column(db.String(20), nullable=False, default='grupo')  # 'grupo' ou 'individual'
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'))
    
    leituras = db.relationship('LeituraMensagem', backref='mensagem', cascade='all, delete-orphan')
    remetente = db.relationship('Usuario', foreign_keys=[remetente_id], backref=db.backref('mensagens_enviadas', lazy='dynamic', cascade='all, delete-orphan'))
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id], backref=db.backref('mensagens_recebidas', lazy='dynamic', cascade='all, delete-orphan'))

class LeituraMensagem(db.Model):
    __tablename__ = 'leituras_mensagens'
    
    id = db.Column(db.Integer, primary_key=True)
    mensagem_id = db.Column(db.Integer, db.ForeignKey('mensagens.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    data_leitura = db.Column(db.DateTime, default=datetime.now(UTC))
    
    usuario = db.relationship('Usuario', backref=db.backref('leituras_mensagens', lazy='dynamic', cascade='all, delete-orphan'))

class Notificacao(db.Model):
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'carga', 'producao', 'fechamento', etc
    titulo = db.Column(db.String(255), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id', ondelete='CASCADE'))
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now(UTC))
    
    usuario = db.relationship('Usuario', backref=db.backref('notificacoes', lazy='dynamic', cascade='all, delete-orphan'))
    carga = db.relationship('Carga', backref=db.backref('notificacoes', lazy='dynamic', cascade='all, delete-orphan'))

    @staticmethod
    def criar_notificacao(usuario_id, tipo, titulo, mensagem, carga_id=None):
        notificacao = Notificacao(
            usuario_id=usuario_id,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            carga_id=carga_id
        )
        db.session.add(notificacao)
        db.session.commit()
        return notificacao

    def marcar_como_lida(self):
        self.lida = True
        db.session.commit()
