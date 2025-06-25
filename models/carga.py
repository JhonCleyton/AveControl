from extensions import db
from datetime import datetime
from pytz import UTC
from constants import TIPOS_AVE
from enum import Enum
from config import Config

class Carga(db.Model):
    __tablename__ = 'cargas'
    
    # Constantes para status
    STATUS_PENDENTE = 'pendente'
    STATUS_EM_ANDAMENTO = 'em andamento'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CANCELADA = 'cancelada'
    STATUS_INCOMPLETA = 'incompleta'
    
    # Status da nota
    STATUS_NOTA_PENDENTE = 'pendente'
    STATUS_NOTA_APROVADO = 'aprovado'
    STATUS_NOTA_AUTORIZADO = 'autorizado'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_carga = db.Column(db.String(50), unique=True, nullable=False)
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
    status_frete = db.Column(db.String(50))
    _status = db.Column(db.String(50), default=STATUS_PENDENTE)
    nota_aprovada = db.Column(db.Boolean, default=False)
    nota_autorizada = db.Column(db.Boolean, default=False)
    status_atualizado_em = db.Column(db.DateTime)
    status_atualizado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    status_atualizado_por = db.relationship('Usuario', foreign_keys=[status_atualizado_por_id])
    
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
    aprovado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    aprovado_em = db.Column(db.DateTime)
    autorizado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    autorizado_em = db.Column(db.DateTime)
    assinatura_autorizacao = db.Column(db.String(500))
    
    # Campos de verificação
    status_balanca = db.Column(db.String(20), default='pendente')  # pendente, em_verificacao, aprovado
    status_producao = db.Column(db.String(20), default='pendente')  # pendente, em_verificacao, aprovado
    status_fechamento = db.Column(db.String(20), default='pendente')  # pendente, em_verificacao, aprovado
    
    motivo_verificacao_balanca = db.Column(db.Text)
    motivo_verificacao_producao = db.Column(db.Text)
    motivo_verificacao_fechamento = db.Column(db.Text)
    
    data_verificacao_balanca = db.Column(db.DateTime)
    data_verificacao_producao = db.Column(db.DateTime)
    data_verificacao_fechamento = db.Column(db.DateTime)
    
    verificado_por_balanca_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', name='fk_verificado_por_balanca'))
    verificado_por_producao_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', name='fk_verificado_por_producao'))
    verificado_por_fechamento_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', name='fk_verificado_por_fechamento'))
    
    # Relacionamentos de verificação
    verificado_por_balanca = db.relationship('Usuario', foreign_keys=[verificado_por_balanca_id])
    verificado_por_producao = db.relationship('Usuario', foreign_keys=[verificado_por_producao_id])
    verificado_por_fechamento = db.relationship('Usuario', foreign_keys=[verificado_por_fechamento_id])
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.now(UTC))
    atualizado_em = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    atualizado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Relacionamentos
    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id])
    atualizado_por = db.relationship('Usuario', foreign_keys=[atualizado_por_id])
    aprovado_por = db.relationship('Usuario', foreign_keys=[aprovado_por_id], backref='cargas_aprovadas')
    autorizado_por = db.relationship('Usuario', foreign_keys=[autorizado_por_id], backref='cargas_autorizadas')
    subcargas = db.relationship('SubCarga', backref='carga', lazy=True)
    producoes = db.relationship('Producao', backref='carga', lazy=True)
    fechamento = db.relationship('Fechamento', back_populates='carga', uselist=False)
    custo_ave = db.relationship('CustoAve', back_populates='carga', uselist=False)
    historicos = db.relationship('HistoricoCarga', back_populates='carga', cascade='all, delete-orphan')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value:
            self._status = value.lower()
        else:
            self._status = value

    @property
    def status_nota(self):
        if self.nota_autorizada:
            return self.STATUS_NOTA_AUTORIZADO
        elif self.nota_aprovada:
            return self.STATUS_NOTA_APROVADO
        else:
            return self.STATUS_NOTA_PENDENTE

    @status_nota.setter
    def status_nota(self, value):
        if value == self.STATUS_NOTA_AUTORIZADO:
            self.nota_autorizada = True
            self.nota_aprovada = True
        elif value == self.STATUS_NOTA_APROVADO:
            self.nota_autorizada = False
            self.nota_aprovada = True
        else:  # pendente
            self.nota_autorizada = False
            self.nota_aprovada = False

    def atualizar_status(self, novo_status, usuario):
        """Atualiza o status da carga e registra no histórico."""
        if novo_status not in [
            self.STATUS_PENDENTE,
            self.STATUS_EM_ANDAMENTO,
            self.STATUS_CONCLUIDA,
            self.STATUS_CANCELADA,
            self.STATUS_INCOMPLETA
        ]:
            raise ValueError(f"Status inválido: {novo_status}")

        status_anterior = self._status
        self._status = novo_status
        self.status_atualizado_em = datetime.now()
        self.status_atualizado_por = usuario

        # Registrar no histórico
        historico = HistoricoCarga(
            carga=self,
            usuario=usuario,
            tipo='status',
            valor_anterior=status_anterior,
            valor_novo=novo_status
        )
        db.session.add(historico)

class SubCarga(db.Model):
    __tablename__ = 'subcargas'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id'), nullable=False)
    numero_subcarga = db.Column(db.String(20))
    produtor = db.Column(db.String(100))
    uf_produtor = db.Column(db.String(2))
    numero_nfe = db.Column(db.String(50))
    data_nfe = db.Column(db.Date)
    numero_gta = db.Column(db.String(50))
    data_gta = db.Column(db.Date)
    tipo_ave = db.Column(db.String(50))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Producao(db.Model):
    __tablename__ = 'producao'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id'))
    data_producao = db.Column(db.Date, nullable=False)
    aves_granja = db.Column(db.Integer, nullable=False)
    aves_mortas = db.Column(db.Integer, nullable=False)
    aves_recebidas = db.Column(db.Integer, nullable=False)
    aves_contador = db.Column(db.Integer, nullable=False)
    aves_por_caixa = db.Column(db.Integer, nullable=False)
    mortalidade_excesso = db.Column(db.Float, nullable=False, default=0)
    aves_molhadas_granja = db.Column(db.Float, nullable=False, default=0)
    aves_molhadas_chuva = db.Column(db.Float, nullable=False, default=0)
    quebra_maus_tratos = db.Column(db.Float, nullable=False, default=0)
    aves_papo_cheio = db.Column(db.Float, nullable=False, default=0)
    outras_quebras = db.Column(db.Float, nullable=False, default=0)
    descricao_quebras = db.Column(db.Text)
    total_avarias = db.Column(db.Float, nullable=False, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'carga_id': self.carga_id,
            'data_producao': self.data_producao.strftime('%Y-%m-%d'),
            'aves_granja': self.aves_granja,
            'aves_mortas': self.aves_mortas,
            'aves_recebidas': self.aves_recebidas,
            'aves_contador': self.aves_contador,
            'aves_por_caixa': self.aves_por_caixa,
            'mortalidade_excesso': self.mortalidade_excesso,
            'aves_molhadas_granja': self.aves_molhadas_granja,
            'aves_molhadas_chuva': self.aves_molhadas_chuva,
            'quebra_maus_tratos': self.quebra_maus_tratos,
            'aves_papo_cheio': self.aves_papo_cheio,
            'outras_quebras': self.outras_quebras,
            'descricao_quebras': self.descricao_quebras,
            'total_avarias': self.total_avarias
        }

class Fechamento(db.Model):
    __tablename__ = 'fechamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id'), unique=True)
    tratativas = db.Column(db.String(1), nullable=False)
    tipo_fechamento_1 = db.Column(db.String(10), nullable=False)
    quantidade_1 = db.Column(db.Float, nullable=False)
    valor_unitario_1 = db.Column(db.Float, nullable=False)
    descontos_1 = db.Column(db.Float, nullable=False, default=0)
    valor_total_1 = db.Column(db.Float, nullable=False)
    observacoes_1 = db.Column(db.Text)
    tipo_fechamento_2 = db.Column(db.String(10))
    quantidade_2 = db.Column(db.Float)
    valor_unitario_2 = db.Column(db.Float)
    descontos_2 = db.Column(db.Float, default=0)
    valor_total_2 = db.Column(db.Float)
    observacoes_2 = db.Column(db.Text)
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
        """Atualiza os campos do fechamento com os dados fornecidos"""
        self.tratativas = data.get('tratativas', self.tratativas)
        self.tipo_fechamento_1 = data.get('tipo_fechamento_1', self.tipo_fechamento_1)
        self.quantidade_1 = float(data.get('quantidade_1', self.quantidade_1))
        self.valor_unitario_1 = float(data.get('valor_unitario_1', self.valor_unitario_1))
        self.descontos_1 = float(data.get('descontos_1', self.descontos_1))
        self.valor_total_1 = float(data.get('valor_total_1', self.valor_total_1))
        self.observacoes_1 = data.get('observacoes_1', self.observacoes_1)
        
        if data.get('tratativas') == '2':
            self.tipo_fechamento_2 = data.get('tipo_fechamento_2', self.tipo_fechamento_2)
            self.quantidade_2 = float(data.get('quantidade_2', self.quantidade_2 or 0))
            self.valor_unitario_2 = float(data.get('valor_unitario_2', self.valor_unitario_2 or 0))
            self.descontos_2 = float(data.get('descontos_2', self.descontos_2 or 0))
            self.valor_total_2 = float(data.get('valor_total_2', self.valor_total_2 or 0))
            self.observacoes_2 = data.get('observacoes_2', self.observacoes_2)

class ConfiguracaoFormulario(db.Model):
    __tablename__ = 'configuracoes_formulario'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_campo = db.Column(db.String(100), nullable=False)
    tipo_campo = db.Column(db.String(50), nullable=False)
    obrigatorio = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer)
    opcoes = db.Column(db.Text)

def criar_subcarga(carga, subcarga_data, i):
    """Cria uma subcarga para a carga fornecida"""
    subcarga = SubCarga(
        carga_id=carga.id,
        numero_subcarga=f"{str(carga.numero_carga)}.{i}",  # Gerar número da subcarga
        tipo_ave=subcarga_data.get('tipo_ave'),
        produtor=subcarga_data.get('produtor'),
        uf_produtor=subcarga_data.get('uf_produtor'),
        numero_nfe=subcarga_data.get('numero_nfe'),
        data_nfe=datetime.strptime(subcarga_data.get('data_nfe'), '%Y-%m-%d').date() if subcarga_data.get('data_nfe') else None,
        numero_gta=subcarga_data.get('numero_gta'),
        data_gta=datetime.strptime(subcarga_data.get('data_gta'), '%Y-%m-%d').date() if subcarga_data.get('data_gta') else None
    )
    return subcarga
