from extensions import db
from datetime import datetime
from pytz import UTC

class Carga(db.Model):
    __tablename__ = 'cargas'
    
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
    status_frete = db.Column(db.String(50))
    status = db.Column(db.String(50), default='pendente')  # pendente, em_andamento, concluida, cancelada
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
    nota_aprovada = db.Column(db.Boolean, default=False)
    aprovado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    aprovado_em = db.Column(db.DateTime)
    nota_autorizada = db.Column(db.Boolean, default=False)
    autorizado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    autorizado_em = db.Column(db.DateTime)
    assinatura_autorizacao = db.Column(db.String(500))
    
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

class SubCarga(db.Model):
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
    
    # Contagem de Aves
    aves_granja = db.Column(db.Integer, nullable=False)
    aves_mortas = db.Column(db.Integer, nullable=False)
    aves_recebidas = db.Column(db.Integer, nullable=False)
    aves_contador = db.Column(db.Integer, nullable=False)
    aves_por_caixa = db.Column(db.Integer, nullable=False)
    
    # Avarias
    mortalidade_excesso = db.Column(db.Float, nullable=False, default=0)
    aves_molhadas_granja = db.Column(db.Float, nullable=False, default=0)
    aves_molhadas_chuva = db.Column(db.Float, nullable=False, default=0)
    quebra_maus_tratos = db.Column(db.Float, nullable=False, default=0)
    aves_papo_cheio = db.Column(db.Float, nullable=False, default=0)
    outras_quebras = db.Column(db.Float, nullable=False, default=0)
    descricao_quebras = db.Column(db.Text)
    total_avarias = db.Column(db.Float, nullable=False, default=0)

class Fechamento(db.Model):
    __tablename__ = 'fechamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    carga_id = db.Column(db.Integer, db.ForeignKey('cargas.id'), unique=True)
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
        """Atualiza os campos do fechamento com os dados fornecidos"""
        # Campos da primeira tratativa (obrigatórios)
        self.tratativas = data['tratativas']
        self.tipo_fechamento_1 = data['tipo_fechamento_1']
        self.quantidade_1 = float(data['quantidade_1'])
        self.valor_unitario_1 = float(data['valor_unitario_1'])
        self.descontos_1 = float(data.get('descontos_1', 0))
        self.valor_total_1 = float(data['valor_total_1'])
        self.observacoes_1 = data.get('observacoes_1')

        # Campos da segunda tratativa (opcionais)
        if data['tratativas'] == '2':
            self.tipo_fechamento_2 = data.get('tipo_fechamento_2')
            self.quantidade_2 = float(data.get('quantidade_2', 0))
            self.valor_unitario_2 = float(data.get('valor_unitario_2', 0))
            self.descontos_2 = float(data.get('descontos_2', 0))
            self.valor_total_2 = float(data.get('valor_total_2', 0))
            self.observacoes_2 = data.get('observacoes_2')

class ConfiguracaoFormulario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_campo = db.Column(db.String(100), nullable=False)
    tipo_campo = db.Column(db.String(50), nullable=False)
    obrigatorio = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer)
    opcoes = db.Column(db.Text)

def criar_subcarga(carga, subcarga_data, i):
    subcarga = SubCarga(
        carga_id=carga.id,
        numero_subcarga=f"{str(carga.numero_carga)}.{str(i+1)}",
        tipo_ave=subcarga_data.get('tipo_ave', ''),
        produtor=subcarga_data.get('produtor', ''),
        uf_produtor=subcarga_data.get('uf_produtor', ''),
        numero_nfe=subcarga_data.get('numero_nfe', ''),
        data_nfe=datetime.strptime(subcarga_data.get('data_nfe', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if subcarga_data.get('data_nfe') else None,
        numero_gta=subcarga_data.get('numero_gta', ''),
        data_gta=datetime.strptime(subcarga_data.get('data_gta', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if subcarga_data.get('data_gta') else None
    )
    return subcarga
