from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, Carga, SubCarga, Usuario, ConfiguracaoFormulario, Producao, Fechamento, TipoUsuario, HistoricoCarga, Solicitacao, TipoSolicitacao, StatusSolicitacao, SetorSolicitacao
from datetime import datetime
import pytz
from utils.validators import validar_carga
from utils.email_notificador import notificar_solicitacao, notificar_analise_solicitacao, notificar_setor_responsavel, notificar_tarefa_concluida
from constants import *
from config import Config
from extensions import csrf
from routes.notificacoes import notificar_nova_carga, notificar_producao, notificar_fechamento
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, DateField, TextAreaField
from wtforms.validators import DataRequired, Optional
from utils.permissions import (permissao_balanca, permissao_producao, permissao_fechamento, 
                          permissao_financeiro, permissao_diretoria, permissao_gerente)

class CargaForm(FlaskForm):
    tipo_ave = StringField('Tipo de Ave')
    quantidade_cargas = IntegerField('Quantidade de Cargas', validators=[Optional()])
    ordem_carga = StringField('Ordem de Carga')
    data_abate = DateField('Data de Abate', format='%Y-%m-%d', validators=[Optional()])
    dia_semana = StringField('Dia da Semana')
    agenciador = StringField('Agenciador')
    motorista = StringField('Motorista')
    motorista_outro = StringField('Outro Motorista')
    transportadora = StringField('Transportadora')
    placa_veiculo = StringField('Placa do Veículo')
    km_saida = FloatField('KM Saída', validators=[Optional()])
    km_chegada = FloatField('KM Chegada', validators=[Optional()])
    km_rodados = FloatField('KM Rodados', validators=[Optional()])
    valor_km = FloatField('Valor por KM', validators=[Optional()])
    valor_frete = FloatField('Valor do Frete', validators=[Optional()])
    status_frete = StringField('Status do Frete')
    caixas_vazias = IntegerField('Caixas Vazias', validators=[Optional()])
    quantidade_caixas = IntegerField('Quantidade de Caixas', validators=[Optional()])
    produtor = StringField('Produtor')
    uf_produtor = StringField('UF do Produtor')
    numero_nfe = StringField('Número da NFe')
    data_nfe = DateField('Data da NFe', format='%Y-%m-%d', validators=[Optional()])
    numero_gta = StringField('Número do GTA')
    data_gta = DateField('Data do GTA', format='%Y-%m-%d', validators=[Optional()])
    peso_granja = FloatField('Peso na Granja', validators=[Optional()])
    peso_frigorifico = FloatField('Peso no Frigorífico', validators=[Optional()])
    percentual_quebra = FloatField('Percentual de Quebra', validators=[Optional()])
    quebra_peso = FloatField('Quebra de Peso', validators=[Optional()])
    motivo_alta_quebra = TextAreaField('Motivo de Alta Quebra')
    pedagios = FloatField('Pedágios', validators=[Optional()])
    outras_despesas = FloatField('Outras Despesas', validators=[Optional()])
    abastecimento_empresa = FloatField('Abastecimento na Empresa', validators=[Optional()])
    abastecimento_posto = FloatField('Abastecimento no Posto', validators=[Optional()])
    adiantamento = FloatField('Adiantamento', validators=[Optional()])
    valor_pagar = FloatField('Valor a Pagar', validators=[Optional()])

cargas = Blueprint('cargas', __name__)

# Marcar rotas como isentas de CSRF
@cargas.before_request
def before_request():
    if request.endpoint in ['cargas.salvar_fechamento', 'cargas.salvar_producao']:
        csrf.protect()
    elif request.endpoint == 'cargas.carregar_veiculos' and request.method == 'GET':
        return  # Não exigir CSRF para GET de veículos

def registrar_historico(carga_id, acao):
    try:
        # Pega o horário atual em São Paulo (UTC-3)
        sp_tz = pytz.timezone('America/Sao_Paulo')
        sp_time = datetime.now(sp_tz)
        # Remove a informação de timezone antes de salvar
        sp_time = sp_time.replace(tzinfo=None)
        
        historico = HistoricoCarga(
            carga_id=carga_id,
            usuario_id=current_user.id,
            acao=acao,
            data_hora=sp_time
        )
        db.session.add(historico)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar histórico: {str(e)}")
        
@cargas.route('/nova_carga', methods=['GET'])
@login_required
@permissao_balanca
def nova_carga():
    configuracoes = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
    return render_template('cargas/nova_carga.html',
                         tipos_ave=TIPOS_AVE,
                         motoristas=MOTORISTAS,
                         transportadoras=TRANSPORTADORAS,
                         placas_ellen=PLACAS_ELLEN,
                         valores_km=VALORES_KM,
                         status_frete=STATUS_FRETE,
                         estados_brasil=ESTADOS_BRASIL,
                         configuracoes=configuracoes,
                         produtores=PRODUTORES)

@cargas.route('/criar_carga', methods=['POST'])
@login_required
def criar_carga():
    try:
        data = request.json
        print("Dados recebidos:", data)  # Log dos dados recebidos

        # Gerar número da carga
        numero = str(get_proximo_numero())  # Usar a nova função auxiliar
        print("Número da carga gerado:", numero)  # Log do número da carga

        # Verificar campos obrigatórios para determinar o status
        campos_principais = ['tipo_ave', 'data_abate', 'motorista', 'transportadora', 
                           'placa_veiculo', 'km_saida', 'km_chegada', 'valor_km']
        
        campos_vazios = [campo for campo in campos_principais 
                        if not data.get(campo) or str(data.get(campo)).strip() == '']
        
        status = 'INCOMPLETA' if campos_vazios else 'PENDENTE'
        print(f"Status determinado: {status}, Campos vazios: {campos_vazios}")  # Log do status

        # Definir valores padrão para campos NOT NULL
        data_atual = datetime.now().date()
        
        # Criar a carga com valores padrão para campos que não podem ser nulos
        carga = Carga(
            numero_carga=numero,
            tipo_ave=data.get('tipo_ave') or 'Não Informado',
            quantidade_cargas=data.get('quantidade_cargas') or 0,
            ordem_carga=data.get('ordem_carga') or '',
            data_abate=datetime.strptime(data.get('data_abate'), '%Y-%m-%d').date() if data.get('data_abate') else data_atual,
            dia_semana=data.get('dia_semana') or '',
            agenciador=data.get('agenciador') or '',
            motorista=data.get('motorista') or 'Não Informado',
            motorista_outro=data.get('motorista_outro') or '',
            transportadora=data.get('transportadora') or 'Não Informado',
            placa_veiculo=data.get('placa_veiculo') or 'Não Informado',
            km_saida=float(data.get('km_saida', 0) or 0),
            km_chegada=float(data.get('km_chegada', 0) or 0),
            km_rodados=float(data.get('km_rodados', 0) or 0),
            valor_km=float(data.get('valor_km', 0) or 0),
            valor_frete=float(data.get('valor_frete', 0) or 0),
            status_frete=data.get('status_frete') or 'A_PAGAR',
            caixas_vazias=int(data.get('caixas_vazias', 0) or 0),
            quantidade_caixas=int(data.get('quantidade_caixas', 0) or 0),
            pedagios=float(data.get('pedagios', 0) or 0),
            outras_despesas=float(data.get('outras_despesas', 0) or 0),
            abastecimento_empresa=float(data.get('abastecimento_empresa', 0) or 0),
            abastecimento_posto=float(data.get('abastecimento_posto', 0) or 0),
            adiantamento=float(data.get('adiantamento', 0) or 0),
            valor_pagar=float(data.get('valor_pagar', 0) or 0),
            peso_granja=float(data.get('peso_granja', 0) or 0),
            peso_frigorifico=float(data.get('peso_frigorifico', 0) or 0),
            percentual_quebra=float(data.get('percentual_quebra', 0) or 0),
            quebra_peso=float(data.get('quebra_peso', 0) or 0),
            motivo_alta_quebra=data.get('motivo_alta_quebra') or '',
            produtor=data.get('produtor') or '',
            uf_produtor=data.get('uf_produtor') or '',
            numero_nfe=data.get('numero_nfe') or '',
            data_nfe=datetime.strptime(data.get('data_nfe'), '%Y-%m-%d').date() if data.get('data_nfe') else None,
            numero_gta=data.get('numero_gta') or '',
            data_gta=datetime.strptime(data.get('data_gta'), '%Y-%m-%d').date() if data.get('data_gta') else None,
            criado_por_id=current_user.id,
            atualizado_por_id=current_user.id,
            status=status,
            status_balanca='pendente',
            status_producao='pendente',
            status_fechamento='pendente',
            nota_aprovada=False,
            nota_autorizada=False,
            criado_em=datetime.now(),
            atualizado_em=datetime.now()
        )
        
        db.session.add(carga)
        db.session.flush()  # Obter o ID da carga sem commit
        
        # Processar subcargas
        if 'subcargas' in data and data['subcargas']:
            for i, subcarga_data in enumerate(data['subcargas'], start=1):
                subcarga = SubCarga(
                    carga_id=carga.id,
                    numero_subcarga=f"{numero}.{i}",  # Usar o número aqui também
                    tipo_ave=subcarga_data.get('tipo_ave') or 'Não Informado',
                    produtor=subcarga_data.get('produtor') or '',
                    uf_produtor=subcarga_data.get('uf_produtor') or '',
                    numero_nfe=subcarga_data.get('numero_nfe') or '',
                    data_nfe=datetime.strptime(subcarga_data.get('data_nfe'), '%Y-%m-%d').date() if subcarga_data.get('data_nfe') else None,
                    numero_gta=subcarga_data.get('numero_gta') or '',
                    data_gta=datetime.strptime(subcarga_data.get('data_gta'), '%Y-%m-%d').date() if subcarga_data.get('data_gta') else None
                )
                db.session.add(subcarga)
        
        # Registrar no histórico
        historico = HistoricoCarga(
            carga_id=carga.id,
            usuario_id=current_user.id,
            acao='CRIAÇÃO',
            data_hora=datetime.now()
        )
        db.session.add(historico)
        
        # Enviar notificação
        notificar_nova_carga(carga)
        
        db.session.commit()
        
        # Preparar mensagem de retorno
        mensagem = 'Carga salva com sucesso!'
        if status == 'INCOMPLETA':
            campos_faltantes = [campo.replace('_', ' ').title() for campo in campos_vazios]
            mensagem = f'Carga salva como incompleta. Campos não preenchidos: {", ".join(campos_faltantes)}'
        
        return jsonify({
            'success': True,
            'message': mensagem,
            'carga_id': carga.id,
            'numero_carga': numero,
            'status': status
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar carga: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao criar carga: {str(e)}'
        }), 500

@cargas.route('/fechamento')
@login_required
def fechamento_carga():
    return render_template('cargas/fechamento_carga.html')

@cargas.route('/buscar_carga_fechamento/<numero_carga>')
@login_required
def buscar_carga_fechamento(numero_carga):
    try:
        carga = Carga.query.filter_by(numero_carga=numero_carga).first()
        if not carga:
            return jsonify({'success': False, 'message': 'Carga não encontrada'})

        # Verificar se a carga já tem fechamento
        fechamento_data = None
        if carga.fechamento:
            fechamento_data = {
                'tratativas': carga.fechamento.tratativas,
                'tipo_fechamento_1': carga.fechamento.tipo_fechamento_1,
                'quantidade_1': carga.fechamento.quantidade_1,
                'valor_unitario_1': carga.fechamento.valor_unitario_1,
                'descontos_1': carga.fechamento.descontos_1,
                'valor_total_1': carga.fechamento.valor_total_1,
                'observacoes_1': carga.fechamento.observacoes_1
            }
            if carga.fechamento.tratativas == '2':
                fechamento_data.update({
                    'tipo_fechamento_2': carga.fechamento.tipo_fechamento_2,
                    'quantidade_2': carga.fechamento.quantidade_2,
                    'valor_unitario_2': carga.fechamento.valor_unitario_2,
                    'descontos_2': carga.fechamento.descontos_2,
                    'valor_total_2': carga.fechamento.valor_total_2,
                    'observacoes_2': carga.fechamento.observacoes_2
                })

        return jsonify({
            'success': True,
            'data': {
                'carga': {
                    'numero_carga': carga.numero_carga,
                    'tipo_ave': carga.tipo_ave,
                    'quantidade_cargas': carga.quantidade_cargas,
                    'motorista': carga.motorista,
                    'motorista_outro': carga.motorista_outro,
                    'transportadora': carga.transportadora,
                    'placa_veiculo': carga.placa_veiculo,
                    'km_rodados': carga.km_rodados,
                    'valor_km': carga.valor_km,
                    'valor_frete': carga.valor_frete,
                    'pedagios': carga.pedagios,
                    'outras_despesas': carga.outras_despesas,
                    'abastecimento_empresa': carga.abastecimento_empresa,
                    'abastecimento_posto': carga.abastecimento_posto,
                    'adiantamento': carga.adiantamento,
                    'valor_pagar': carga.valor_pagar
                },
                'fechamento': fechamento_data
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@cargas.route('/salvar_fechamento', methods=['POST'])
@login_required
def salvar_fechamento():
    dados = request.get_json()
    
    # Buscar a carga pelo número
    numero_carga = dados.pop('numero_carga')  # Remove e retorna o numero_carga dos dados
    carga = Carga.query.filter_by(numero_carga=numero_carga).first()
    if not carga:
        return jsonify({'success': False, 'message': 'Carga não encontrada'})

    try:
        # Se já existe um fechamento, verificar permissão de edição
        if carga.fechamento:
            # Verificar se tem permissão para editar
            if not verificar_permissao_edicao(carga.id, SetorSolicitacao.FECHAMENTO):
                return jsonify({
                    'success': False, 
                    'message': 'Não há permissão para editar este fechamento. Solicite uma autorização ao gerente.'
                }), 403

        # Converter strings para float
        for campo in ['quantidade_1', 'valor_unitario_1', 'descontos_1', 'valor_total_1']:
            if campo in dados:
                dados[campo] = float(dados[campo])
        
        if dados['tratativas'] == '2':
            for campo in ['quantidade_2', 'valor_unitario_2', 'descontos_2', 'valor_total_2']:
                if campo in dados:
                    dados[campo] = float(dados[campo])
        
        # Se já existe um fechamento, atualizar
        if carga.fechamento:
            fechamento = carga.fechamento
            for key, value in dados.items():
                setattr(fechamento, key, value)
        else:
            # Criar novo fechamento
            fechamento = Fechamento(**dados)
            fechamento.carga = carga
            db.session.add(fechamento)
        
        db.session.commit()
        
        # Registrar no histórico
        if carga.fechamento:
            registrar_historico(carga.id, f"Atualizou fechamento da carga #{carga.numero_carga}")
        else:
            registrar_historico(carga.id, f"Registrou fechamento da carga #{carga.numero_carga}")
        
        # Notificar gerentes sobre fechamento inserido
        notificar_fechamento(carga)
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar fechamento: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({'success': False, 'message': str(e)})

@cargas.route('/cargas_incompletas')
@login_required
def cargas_incompletas():
    cargas = Carga.query.filter_by(status='incompleto').all()
    return render_template('cargas/cargas_incompletas.html', cargas=cargas)

@cargas.route('/todas_cargas')
@login_required
def todas_cargas():
    cargas = Carga.query.order_by(Carga.criado_em.desc()).all()
    return render_template('cargas/todas_cargas.html', cargas=cargas)

@cargas.route('/historico/<int:id>')
@login_required
def historico_carga(id):
    carga = Carga.query.get_or_404(id)
    historicos = HistoricoCarga.query\
        .filter_by(carga_id=id)\
        .order_by(HistoricoCarga.data_hora.desc())\
        .all()
    from flask import current_app
    return render_template('cargas/historico.html', carga=carga, historicos=historicos, config=current_app.config)

@cargas.route('/visualizar/<int:id>')
@login_required
def visualizar_carga(id):
    carga = Carga.query.get_or_404(id)
    print(f"DEBUG - Visualizando carga {id}")
    print(f"DEBUG - Tipo do usuário atual: {current_user.tipo}")
    print(f"DEBUG - Status da nota: {carga.status_nota}")
    print(f"DEBUG - Condição do botão: tipo={current_user.tipo=='diretoria'} and status={carga.status_nota=='aprovado'}")
    registrar_historico(id, f"Visualizou a carga #{carga.numero_carga}")
    producao = Producao.query.filter_by(carga_id=id).first()
    return render_template('cargas/visualizar_carga.html', carga=carga, producao=producao)

@cargas.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_carga(id):
    carga = Carga.query.get_or_404(id)
    
    # Verifica se o usuário tem permissão para editar
    if not verificar_permissao_edicao(id, SetorSolicitacao.BALANCA):
        flash('Você não tem autorização para editar esta carga. Solicite uma edição primeiro.', 'error')
        return redirect(url_for('cargas.visualizar_carga', id=id))
    
    configuracoes = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
    form = CargaForm()
    
    # Preencher o formulário com os dados da carga
    if request.method == 'GET':
        form.tipo_ave.data = carga.tipo_ave
        form.quantidade_cargas.data = carga.quantidade_cargas
        form.ordem_carga.data = carga.ordem_carga
        form.data_abate.data = carga.data_abate
        form.dia_semana.data = carga.dia_semana
        form.agenciador.data = carga.agenciador
        form.motorista.data = carga.motorista
        form.motorista_outro.data = carga.motorista_outro
        form.transportadora.data = carga.transportadora
        form.placa_veiculo.data = carga.placa_veiculo
        form.km_saida.data = carga.km_saida
        form.km_chegada.data = carga.km_chegada
        form.km_rodados.data = carga.km_rodados
        form.valor_km.data = carga.valor_km
        form.valor_frete.data = carga.valor_frete
        form.status_frete.data = carga.status_frete
        form.caixas_vazias.data = carga.caixas_vazias
        form.quantidade_caixas.data = carga.quantidade_caixas
        form.produtor.data = carga.produtor
        form.uf_produtor.data = carga.uf_produtor
        form.numero_nfe.data = carga.numero_nfe
        form.data_nfe.data = carga.data_nfe
        form.numero_gta.data = carga.numero_gta
        form.data_gta.data = carga.data_gta
        form.peso_granja.data = carga.peso_granja
        form.peso_frigorifico.data = carga.peso_frigorifico
        form.percentual_quebra.data = carga.percentual_quebra
        form.quebra_peso.data = carga.quebra_peso
        form.motivo_alta_quebra.data = carga.motivo_alta_quebra
        form.pedagios.data = carga.pedagios
        form.outras_despesas.data = carga.outras_despesas
        form.abastecimento_empresa.data = carga.abastecimento_empresa
        form.abastecimento_posto.data = carga.abastecimento_posto
        form.adiantamento.data = carga.adiantamento
        form.valor_pagar.data = carga.valor_pagar
    
    if form.validate_on_submit():
        # Atualizar campos da carga
        carga.tipo_ave = form.tipo_ave.data
        carga.quantidade_cargas = form.quantidade_cargas.data
        carga.ordem_carga = form.ordem_carga.data
        carga.data_abate = form.data_abate.data
        carga.dia_semana = form.dia_semana.data
        carga.agenciador = form.agenciador.data
        carga.motorista = form.motorista.data
        carga.motorista_outro = form.motorista_outro.data
        carga.transportadora = form.transportadora.data
        carga.placa_veiculo = form.placa_veiculo.data
        carga.km_saida = form.km_saida.data
        carga.km_chegada = form.km_chegada.data
        carga.km_rodados = form.km_rodados.data
        carga.valor_km = form.valor_km.data
        carga.valor_frete = form.valor_frete.data
        carga.status_frete = form.status_frete.data
        carga.caixas_vazias = form.caixas_vazias.data
        carga.quantidade_caixas = form.quantidade_caixas.data
        carga.produtor = form.produtor.data
        carga.uf_produtor = form.uf_produtor.data
        carga.numero_nfe = form.numero_nfe.data
        carga.data_nfe = form.data_nfe.data
        carga.numero_gta = form.numero_gta.data
        carga.data_gta = form.data_gta.data
        carga.peso_granja = form.peso_granja.data
        carga.peso_frigorifico = form.peso_frigorifico.data
        carga.percentual_quebra = form.percentual_quebra.data
        carga.quebra_peso = form.quebra_peso.data
        carga.motivo_alta_quebra = form.motivo_alta_quebra.data
        carga.pedagios = form.pedagios.data
        carga.outras_despesas = form.outras_despesas.data
        carga.abastecimento_empresa = form.abastecimento_empresa.data
        carga.abastecimento_posto = form.abastecimento_posto.data
        carga.adiantamento = form.adiantamento.data
        carga.valor_pagar = form.valor_pagar.data
        carga.atualizado_por_id = current_user.id
        carga.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(carga.id, 'ATUALIZAÇÃO')
        
        flash('Carga atualizada com sucesso!')
        return redirect(url_for('cargas.visualizar_carga', id=carga.id))
    
    return render_template('cargas/editar_carga.html', 
                         form=form,
                         carga=carga,
                         tipos_ave=TIPOS_AVE,
                         motoristas=MOTORISTAS,
                         transportadoras=TRANSPORTADORAS,
                         placas_ellen=PLACAS_ELLEN,
                         valores_km=VALORES_KM,
                         status_frete=STATUS_FRETE,
                         estados_brasil=ESTADOS_BRASIL,
                         configuracoes=configuracoes,
                         produtores=PRODUTORES)

@cargas.route('/listar_cargas')
@login_required
def listar_cargas():
    search = request.args.get('search', '').strip()
    
    # Subquery para contar solicitações de edição
    edicoes_subquery = db.session.query(
        HistoricoCarga.carga_id,
        db.func.count('*').label('total_edicoes')
    ).filter(
        HistoricoCarga.acao == 'SOLICITAÇÃO DE EDIÇÃO'
    ).group_by(HistoricoCarga.carga_id).subquery()
    
    # Query principal
    query = Carga.query.outerjoin(
        edicoes_subquery,
        Carga.id == edicoes_subquery.c.carga_id
    ).add_columns(
        db.func.coalesce(edicoes_subquery.c.total_edicoes, 0).label('total_edicoes')
    )
    
    # Aplicar filtro de busca se houver termo de busca
    if search:
        search = f"%{search}%"
        query = query.filter(
            db.or_(
                Carga.numero_carga.ilike(search),
                Carga.tipo_ave.ilike(search),
                Carga.motorista.ilike(search),
                Carga.transportadora.ilike(search),
                Carga.placa_veiculo.ilike(search)
            )
        )
    
    # Ordenar por data de criação, mais recentes primeiro
    cargas = query.order_by(Carga.criado_em.desc()).all()
    
    return render_template('cargas/listar_cargas.html', cargas=cargas, search=search)

@cargas.route('/')
@login_required
def index():
    return redirect(url_for('cargas.listar_cargas'))

@cargas.route('/producao')
@login_required
def producao():
    return render_template('cargas/producao.html')

@cargas.route('/producao/buscar/<numero_carga>')
@login_required
def buscar_carga_producao(numero_carga):
    carga = Carga.query.filter_by(numero_carga=numero_carga).first()
    if not carga:
        return jsonify({'success': False, 'message': 'Carga não encontrada'}), 404
    
    # Buscar dados da produção se existirem
    producao_data = None
    if carga.producoes and len(carga.producoes) > 0:
        producao = carga.producoes[0]  # Pega a primeira produção
        producao_data = producao.to_dict()
    
    return jsonify({
        'success': True,
        'carga': {
            'id': carga.id,
            'numero_carga': carga.numero_carga,
            'tipo_ave': carga.tipo_ave,
            'data_abate': carga.data_abate.strftime('%Y-%m-%d'),
            'motorista': carga.motorista,
            'producao': producao_data
        }
    })

@cargas.route('/producao/salvar', methods=['POST'])
@login_required
def salvar_producao():
    try:
        data = request.json
        carga_id = data.get('carga_id')
        carga = Carga.query.get_or_404(carga_id)
        
        # Verificar se já existe uma produção
        tem_producao_existente = carga.producoes and len(carga.producoes) > 0
        
        if tem_producao_existente:
            # Se não for gerente/diretoria, verificar se tem permissão
            if current_user.tipo not in [TipoUsuario.GERENTE, TipoUsuario.DIRETORIA]:
                # Verificar se existe uma solicitação aprovada e não finalizada
                solicitacao = Solicitacao.query.filter_by(
                    carga_id=carga_id,
                    tipo=TipoSolicitacao.EDICAO,
                    setor=SetorSolicitacao.PRODUCAO,
                    status=StatusSolicitacao.APROVADA
                ).filter(
                    Solicitacao.verificado_em.is_(None)  # Não foi finalizada ainda
                ).first()
                
                if not solicitacao:
                    return jsonify({
                        'success': False,
                        'message': 'Não há permissão para editar esta produção. Solicite uma autorização ao gerente.'
                    }), 403
        
        # Validar tipo de ave
        tipo_ave = carga.tipo_ave.upper()
        if tipo_ave not in [t.upper() for t in TIPOS_AVE]:
            return jsonify({
                'success': False,
                'message': f'Tipo de ave inválido: {tipo_ave}. Tipos válidos: {", ".join(TIPOS_AVE)}'
            }), 400
        
        # Usar a data atual se data_producao não for fornecida
        try:
            data_producao = datetime.strptime(data.get('data_producao', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            data_producao = datetime.now().date()
        
        # Preparar dados da produção
        producao_data = {
            'data_producao': data_producao,
            'aves_granja': int(data.get('aves_granja', 0)),
            'aves_mortas': int(data.get('aves_mortas', 0)),
            'aves_recebidas': int(data.get('aves_recebidas', 0)),
            'aves_contador': int(data.get('aves_contador', 0)),
            'aves_por_caixa': int(data.get('aves_por_caixa', 0)),
            'mortalidade_excesso': float(data.get('mortalidade_excesso', 0)),
            'aves_molhadas_granja': float(data.get('aves_molhadas_granja', 0)),
            'aves_molhadas_chuva': float(data.get('aves_molhadas_chuva', 0)),
            'quebra_maus_tratos': float(data.get('quebra_maus_tratos', 0)),
            'aves_papo_cheio': float(data.get('aves_papo_cheio', 0)),
            'outras_quebras': float(data.get('outras_quebras', 0)),
            'descricao_quebras': data.get('descricao_quebras', ''),
            'total_avarias': float(data.get('total_avarias', 0))
        }
        
        # Se já existe uma produção, atualizar
        if tem_producao_existente:
            producao = carga.producoes[0]
            for key, value in producao_data.items():
                setattr(producao, key, value)
            acao = "Atualizou"
            
            # Se existe uma solicitação aprovada, finalizá-la
            if current_user.tipo not in [TipoUsuario.GERENTE, TipoUsuario.DIRETORIA]:
                solicitacao = Solicitacao.query.filter_by(
                    carga_id=carga_id,
                    tipo=TipoSolicitacao.EDICAO,
                    setor=SetorSolicitacao.PRODUCAO,
                    status=StatusSolicitacao.APROVADA
                ).first()
                
                if solicitacao:
                    solicitacao.status = StatusSolicitacao.FINALIZADA
                    solicitacao.verificado_por_id = current_user.id
                    solicitacao.verificado_em = datetime.now()
                    solicitacao.observacoes = "Edição realizada com sucesso"
        else:
            # Criar nova produção
            producao = Producao(carga_id=carga.id, **producao_data)
            db.session.add(producao)
            acao = "Registrou"
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(carga.id, f"{acao} dados de produção da carga #{carga.numero_carga}")

        # Notificar gerentes sobre produção inserida
        notificar_producao(carga)
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar produção: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({'success': False, 'message': str(e)})

@cargas.route('/solicitar_verificacao/<int:id>', methods=['POST'])
@login_required
def solicitar_verificacao(id):
    try:
        carga = Carga.query.get_or_404(id)
        motivo = request.json.get('motivo', '')
        
        # Registrar no histórico
        registrar_historico(id, f"Solicitou verificação da carga #{carga.numero_carga}. Motivo: {motivo}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de verificação enviada com sucesso!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar verificação: {str(e)}'
        }), 500

@cargas.route('/solicitar_exclusao/<int:id>', methods=['POST'])
@login_required
def solicitar_exclusao(id):
    try:
        carga = Carga.query.get_or_404(id)
        motivo = request.json.get('motivo', '')
        setor = request.json.get('setor', '')
        
        # Registrar no histórico
        registrar_historico(id, f"Solicitou exclusão da carga #{carga.numero_carga} para o setor {setor}. Motivo: {motivo}")
        
        # Criar solicitação de exclusão
        solicitacao = Solicitacao(
            carga_id=id,
            solicitado_por_id=current_user.id,
            tipo=TipoSolicitacao.EXCLUSAO.value,
            setor=setor,
            motivo=motivo,
            status=StatusSolicitacao.PENDENTE.value
        )
        db.session.add(solicitacao)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de exclusão enviada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar exclusão: {str(e)}'
        }), 500

@cargas.route('/aprovar_nota/<int:id>', methods=['POST'])
@login_required
def aprovar_nota(id):
    try:
        carga = Carga.query.get_or_404(id)
        
        if carga.status_nota == Carga.STATUS_NOTA_APROVADO:
            return jsonify({
                'success': False,
                'message': 'Esta nota já foi aprovada!'
            }), 400
        
        carga.status_nota = Carga.STATUS_NOTA_APROVADO
        carga.aprovado_por_id = current_user.id
        carga.aprovado_em = datetime.now()
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Aprovou a nota da carga #{carga.numero_carga}")
        
        return jsonify({
            'success': True,
            'message': 'Nota aprovada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao aprovar nota: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar nota: {str(e)}'
        }), 500

@cargas.route('/autorizar_nota/<int:id>', methods=['POST'])
@login_required
def autorizar_nota(id):
    current_app.logger.debug(f"Iniciando autorização de nota para carga {id}")
    current_app.logger.debug(f"Tipo do usuário atual: {current_user.tipo}")
    current_app.logger.debug(f"Dados do formulário completo: {request.form}")
    
    if current_user.tipo != TipoUsuario.DIRETORIA.value:
        current_app.logger.error(f"Usuário não autorizado: {current_user.tipo}")
        return jsonify({'error': 'Você não tem permissão para autorizar notas.'}), 403

    try:
        carga = Carga.query.get_or_404(id)
        current_app.logger.debug(f"Carga encontrada: {carga.id}")
        current_app.logger.debug(f"Status da nota atual: {carga.status_nota}")
        current_app.logger.debug(f"Nota aprovada: {carga.nota_aprovada}")

        if not carga.nota_aprovada:
            current_app.logger.error("Nota não está aprovada")
            return jsonify({'error': 'A nota precisa estar aprovada para ser autorizada.'}), 400
        
        csrf_token = request.form.get('csrf_token')
        current_app.logger.debug(f"CSRF token recebido: {csrf_token is not None}")
        
        if not csrf_token:
            current_app.logger.error("CSRF token não fornecido")
            return jsonify({'error': 'CSRF token é obrigatório.'}), 400

        senha = request.form.get('senha')
        assinatura = request.form.get('assinatura')
        
        current_app.logger.debug(f"Senha fornecida: {'Sim' if senha else 'Não'}")
        current_app.logger.debug(f"Assinatura fornecida: {'Sim' if assinatura else 'Não'}")
        
        if not senha or not assinatura:
            current_app.logger.error("Senha ou assinatura não fornecidas")
            return jsonify({'error': 'Senha e assinatura são obrigatórias.'}), 400
        
        if not current_user.check_senha(senha):
            current_app.logger.error("Senha incorreta")
            return jsonify({'error': 'Senha incorreta.'}), 400
        
        try:
            current_app.logger.debug("Iniciando atualização da carga")
            carga.nota_autorizada = True
            carga.autorizado_por_id = current_user.id
            carga.autorizado_em = datetime.now()
            carga.assinatura_autorizacao = assinatura
            
            # Registrar no histórico
            current_app.logger.debug("Criando registro no histórico")
            historico = HistoricoCarga(
                carga_id=id,
                usuario_id=current_user.id,
                acao=f"Nota autorizada por {current_user.nome} com assinatura: {assinatura}",
                data_hora=datetime.now()
            )
            db.session.add(historico)
            
            current_app.logger.debug("Realizando commit das alterações")
            db.session.commit()
            current_app.logger.info(f"Nota autorizada com sucesso para carga {id}")
            return jsonify({'message': 'Nota autorizada com sucesso!'}), 200
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar no banco de dados: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Erro ao autorizar nota: ' + str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Erro geral na autorização: {str(e)}")
        return jsonify({'error': 'Erro ao autorizar nota: ' + str(e)}), 500

@cargas.route('/solicitar_verificacao_balanca/<int:id>', methods=['POST'])
@login_required
def solicitar_verificacao_balanca(id):
    try:
        carga = Carga.query.get_or_404(id)
        motivo = request.json.get('motivo', '')
        
        carga.status_balanca = 'em_verificacao'
        carga.motivo_verificacao_balanca = motivo
        carga.data_verificacao_balanca = datetime.now()
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Solicitou verificação da balança para carga #{carga.numero_carga}. Motivo: {motivo}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de verificação enviada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao solicitar verificação: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar verificação: {str(e)}'
        }), 500

@cargas.route('/solicitar_verificacao_producao/<int:id>', methods=['POST'])
@login_required
def solicitar_verificacao_producao(id):
    try:
        carga = Carga.query.get_or_404(id)
        motivo = request.json.get('motivo', '')
        
        carga.status_producao = 'em_verificacao'
        carga.motivo_verificacao_producao = motivo
        carga.data_verificacao_producao = datetime.now()
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Solicitou verificação da produção para carga #{carga.numero_carga}. Motivo: {motivo}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de verificação enviada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao solicitar verificação: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar verificação: {str(e)}'
        }), 500

@cargas.route('/solicitar_verificacao_fechamento/<int:id>', methods=['POST'])
@login_required
def solicitar_verificacao_fechamento(id):
    try:
        carga = Carga.query.get_or_404(id)
        motivo = request.json.get('motivo', '')
        
        carga.status_fechamento = 'em_verificacao'
        carga.motivo_verificacao_fechamento = motivo
        carga.data_verificacao_fechamento = datetime.now()
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Solicitou verificação do fechamento para carga #{carga.numero_carga}. Motivo: {motivo}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de verificação enviada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao solicitar verificação: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar verificação: {str(e)}'
        }), 500

@cargas.route('/aprovar_verificacao_balanca/<int:id>', methods=['POST'])
@login_required
def aprovar_verificacao_balanca(id):
    try:
        carga = Carga.query.get_or_404(id)
        
        carga.status_balanca = 'aprovado'
        carga.verificado_por_balanca_id = current_user.id
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Aprovou verificação da balança para carga #{carga.numero_carga}")
        
        return jsonify({
            'success': True,
            'message': 'Verificação aprovada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao aprovar verificação: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar verificação: {str(e)}'
        }), 500

@cargas.route('/aprovar_verificacao_producao/<int:id>', methods=['POST'])
@login_required
def aprovar_verificacao_producao(id):
    try:
        carga = Carga.query.get_or_404(id)
        
        carga.status_producao = 'aprovado'
        carga.verificado_por_producao_id = current_user.id
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Aprovou verificação da produção para carga #{carga.numero_carga}")
        
        return jsonify({
            'success': True,
            'message': 'Verificação aprovada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao aprovar verificação: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar verificação: {str(e)}'
        }), 500

@cargas.route('/aprovar_verificacao_fechamento/<int:id>', methods=['POST'])
@login_required
def aprovar_verificacao_fechamento(id):
    try:
        carga = Carga.query.get_or_404(id)
        
        carga.status_fechamento = 'aprovado'
        carga.verificado_por_fechamento_id = current_user.id
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Aprovou verificação do fechamento para carga #{carga.numero_carga}")
        
        return jsonify({
            'success': True,
            'message': 'Verificação aprovada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao aprovar verificação: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar verificação: {str(e)}'
        }), 500

@cargas.route('/solicitar_edicao/<int:id>', methods=['GET', 'POST'])
@login_required
def solicitar_edicao(id):
    try:
        carga = Carga.query.get_or_404(id)
        
        if request.method == 'POST':
            try:
                # Obter dados do formulário
                motivo = request.form.get('motivo')
                setor = request.form.get('setor', 'balanca')  # Valor padrão é balanca
                csrf_token = request.form.get('csrf_token')
                
                print(f"[DEBUG] Dados recebidos: motivo={motivo}, setor={setor}, csrf_token={csrf_token}")
                
                # Validar CSRF token
                if not csrf_token:
                    print("[DEBUG] Erro: CSRF token não fornecido")
                    return jsonify({'erro': 'CSRF token é obrigatório.'}), 400
                
                # Validar motivo
                if not motivo:
                    print("[DEBUG] Erro: Motivo não fornecido")
                    return jsonify({'erro': 'O motivo da solicitação é obrigatório.'}), 400
                    
                # Mapear o setor para o enum correto
                setor_map = {
                    'balanca': SetorSolicitacao.BALANCA,
                    'producao': SetorSolicitacao.PRODUCAO,
                    'fechamento': SetorSolicitacao.FECHAMENTO
                }
                setor_enum = setor_map.get(setor.lower())
                
                if not setor_enum:
                    print(f"[DEBUG] Erro: Setor inválido: {setor}")
                    return jsonify({'erro': f'Setor inválido: {setor}'}), 400
                
                print(f"[DEBUG] Setor mapeado: {setor_enum}")
                
                # Criar nova solicitação
                solicitacao = Solicitacao(
                    carga_id=carga.id,
                    tipo=TipoSolicitacao.EDICAO,
                    setor=setor_enum,
                    status=StatusSolicitacao.PENDENTE,
                    motivo=motivo,
                    solicitado_por_id=current_user.id
                )
                
                print(f"[DEBUG] Solicitação criada: {solicitacao.to_dict()}")
                
                db.session.add(solicitacao)
                db.session.commit()
                registrar_historico(carga.id, 'SOLICITAÇÃO DE EDIÇÃO')
                
                # Notificar gerentes sobre a nova solicitação de edição
                notificar_solicitacao(solicitacao)
                
                print("[DEBUG] Solicitação salva com sucesso")
                
                return jsonify({'mensagem': 'Solicitação de edição enviada com sucesso!'}), 200
            except Exception as e:
                db.session.rollback()
                import traceback
                print(f"[ERROR] Erro ao solicitar edição: {str(e)}")
                print(traceback.format_exc())
                return jsonify({'erro': f'Erro ao enviar solicitação de edição: {str(e)}'}), 500
        
        return render_template('cargas/solicitar_edicao.html', carga=carga)
    except Exception as e:
        import traceback
        print(f"[ERROR] Erro geral na rota: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@cargas.route('/aprovar_edicao/<int:solicitacao_id>', methods=['POST'])
@login_required
def aprovar_edicao(solicitacao_id):
    try:
        solicitacao = Solicitacao.query.get_or_404(solicitacao_id)
        
        if solicitacao.status != StatusSolicitacao.PENDENTE:
            return jsonify({
                'success': False,
                'message': 'Esta solicitação não está pendente'
            }), 400
        
        solicitacao.status = StatusSolicitacao.APROVADA
        solicitacao.aprovado_por_id = current_user.id
        solicitacao.aprovado_em = datetime.now()
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(solicitacao.carga_id, f"Aprovou edição de {solicitacao.setor.value}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de edição aprovada com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao aprovar edição: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar edição: {str(e)}'
        }), 500

@cargas.route('/rejeitar_edicao/<int:solicitacao_id>', methods=['POST'])
@login_required
def rejeitar_edicao(solicitacao_id):
    try:
        data = request.json
        solicitacao = Solicitacao.query.get_or_404(solicitacao_id)
        
        if solicitacao.status != StatusSolicitacao.PENDENTE:
            return jsonify({
                'success': False,
                'message': 'Esta solicitação não está pendente'
            }), 400
        
        solicitacao.status = StatusSolicitacao.REJEITADA
        solicitacao.aprovado_por_id = current_user.id
        solicitacao.aprovado_em = datetime.now()
        solicitacao.observacoes = data.get('motivo_rejeicao')
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(solicitacao.carga_id, f"Rejeitou edição de {solicitacao.setor.value}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de edição rejeitada com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao rejeitar edição: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao rejeitar edição: {str(e)}'
        }), 500

@cargas.route('/verificar_edicao/<int:solicitacao_id>', methods=['POST'])
@login_required
def verificar_edicao(solicitacao_id):
    try:
        data = request.json
        solicitacao = Solicitacao.query.get_or_404(solicitacao_id)
        
        if solicitacao.status != StatusSolicitacao.APROVADA:
            return jsonify({
                'success': False,
                'message': 'Esta solicitação não está aprovada'
            }), 400
        
        solicitacao.status = StatusSolicitacao.FINALIZADA
        solicitacao.verificado_por_id = current_user.id
        solicitacao.verificado_em = datetime.now()
        solicitacao.observacoes = data.get('observacoes')
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(solicitacao.carga_id, f"Verificou edição de {solicitacao.setor.value}")
        
        return jsonify({
            'success': True,
            'message': 'Verificação de edição concluída com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao verificar edição: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({
            'success': False,
            'message': f'Erro ao verificar edição: {str(e)}'
        }), 500

@cargas.route('/solicitar_verificacao/<int:id>')
@login_required
def verificar_solicitacao(id):
    try:
        setor = request.args.get('setor')
        if not setor:
            return jsonify({
                'success': False,
                'message': 'Setor não informado'
            }), 400
            
        # Verificar se existe uma solicitação aprovada e não finalizada
        solicitacao = Solicitacao.query.filter_by(
            carga_id=id,
            tipo=TipoSolicitacao.EDICAO,
            setor=SetorSolicitacao(setor),
            status=StatusSolicitacao.APROVADA
        ).filter(
            Solicitacao.verificado_em.is_(None)  # Não foi finalizada ainda
        ).first()
        
        return jsonify({
            'success': True,
            'aprovada': solicitacao is not None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@cargas.route('/atualizar_status/<int:id>', methods=['POST'])
@login_required
def atualizar_status_carga(id):
    try:
        carga = Carga.query.get_or_404(id)
        novo_status = request.json.get('status')
        
        if novo_status not in [Carga.STATUS_PENDENTE, Carga.STATUS_EM_ANDAMENTO, Carga.STATUS_CONCLUIDA, Carga.STATUS_CANCELADA]:
            return jsonify({'success': False, 'message': 'Status inválido'}), 400
            
        carga.status = novo_status
        carga.status_atualizado_em = datetime.now(Config.TIMEZONE)
        carga.status_atualizado_por_id = current_user.id
        
        # Registra no histórico
        registrar_historico(carga.id, f"Status atualizado para {novo_status}")
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Status atualizado com sucesso',
            'novo_status': novo_status
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar status: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({'success': False, 'message': str(e)}), 500

def verificar_permissao_edicao(carga_id, setor):
    """Verifica se o usuário tem permissão para editar a carga"""
    # Gerentes sempre podem editar
    if current_user.tipo in [TipoUsuario.GERENTE, TipoUsuario.DIRETORIA]:
        return True
        
    # Verificar se existe uma solicitação aprovada e não finalizada
    solicitacao = Solicitacao.query.filter_by(
        carga_id=carga_id,
        tipo=TipoSolicitacao.EDICAO,
        setor=setor,
        status=StatusSolicitacao.APROVADA
    ).filter(
        Solicitacao.verificado_em.is_(None)  # Não foi finalizada ainda
    ).first()
    
    return solicitacao is not None

@cargas.route('/api/editar/<int:id>', methods=['POST'])
@login_required
def api_editar_carga(id):
    try:
        # Verificar permissão
        if not verificar_permissao_edicao(id, SetorSolicitacao.BALANCA):
            return jsonify({'erro': 'Sem permissão para editar'}), 403

        carga = Carga.query.get_or_404(id)
        print(f"Status atual da carga {id}: {carga.status}")
        
        # Verificar se a carga já foi editada e precisa de nova solicitação
        if carga.status == Carga.STATUS_CONCLUIDA or carga.status == 'concluida':
            print(f"Tentativa de editar carga {id} que já está concluída")
            return jsonify({'erro': 'Esta carga já foi editada. É necessário fazer uma nova solicitação de edição.'}), 403

        data = request.json

        # Atualizar campos da carga
        carga.tipo_ave = data.get('tipo_ave') or carga.tipo_ave
        carga.quantidade_cargas = data.get('quantidade_cargas') or carga.quantidade_cargas
        carga.ordem_carga = data.get('ordem_carga') or carga.ordem_carga
        carga.data_abate = datetime.strptime(data['data_abate'], '%Y-%m-%d').date() if data.get('data_abate') else carga.data_abate
        carga.dia_semana = data.get('dia_semana') or carga.dia_semana
        carga.agenciador = data.get('agenciador') or carga.agenciador
        carga.motorista = data.get('motorista') or carga.motorista
        carga.motorista_outro = data.get('motorista_outro') or carga.motorista_outro
        carga.transportadora = data.get('transportadora') or carga.transportadora
        carga.placa_veiculo = data.get('placa_veiculo') or carga.placa_veiculo
        carga.km_saida = float(data.get('km_saida', carga.km_saida))
        carga.km_chegada = float(data.get('km_chegada', carga.km_chegada))
        carga.km_rodados = float(data.get('km_rodados', carga.km_rodados))
        carga.valor_km = float(data.get('valor_km', carga.valor_km))
        carga.valor_frete = float(data.get('valor_frete', carga.valor_frete))
        carga.status_frete = data.get('status_frete') or carga.status_frete
        carga.produtor = data.get('produtor') or carga.produtor
        carga.uf_produtor = data.get('uf_produtor') or carga.uf_produtor
        carga.numero_nfe = data.get('numero_nfe') or carga.numero_nfe
        carga.data_nfe = datetime.strptime(data['data_nfe'], '%Y-%m-%d').date() if data.get('data_nfe') else carga.data_nfe
        carga.numero_gta = data.get('numero_gta') or carga.numero_gta
        carga.data_gta = datetime.strptime(data['data_gta'], '%Y-%m-%d').date() if data.get('data_gta') else carga.data_gta
        carga.peso_granja = float(data.get('peso_granja', carga.peso_granja))
        carga.peso_frigorifico = float(data.get('peso_frigorifico', carga.peso_frigorifico))
        carga.quebra_peso = float(data.get('quebra_peso', carga.quebra_peso))
        carga.percentual_quebra = float(data.get('percentual_quebra', carga.percentual_quebra))
        carga.motivo_alta_quebra = data.get('motivo_alta_quebra') or carga.motivo_alta_quebra
        carga.caixas_vazias = int(data.get('caixas_vazias', carga.caixas_vazias))
        carga.quantidade_caixas = int(data.get('quantidade_caixas', carga.quantidade_caixas))
        carga.pedagios = float(data.get('pedagios', carga.pedagios))
        carga.outras_despesas = float(data.get('outras_despesas', carga.outras_despesas))
        carga.abastecimento_empresa = float(data.get('abastecimento_empresa', carga.abastecimento_empresa))
        carga.abastecimento_posto = float(data.get('abastecimento_posto', carga.abastecimento_posto))
        carga.adiantamento = float(data.get('adiantamento', carga.adiantamento))
        carga.valor_pagar = float(data.get('valor_pagar', carga.valor_pagar))
        carga.atualizado_por_id = current_user.id
        carga.atualizado_em = datetime.utcnow()
        
        # Marcar como concluída após a edição
        carga.status = 'concluida'  # Usando string direta em vez da constante
        print(f"Novo status da carga {id}: {carga.status}")

        # Processar subcargas
        if 'subcargas' in data:
            # Remover subcargas existentes
            SubCarga.query.filter_by(carga_id=carga.id).delete()
            
            # Adicionar novas subcargas
            for i, subcarga_data in enumerate(data['subcargas'], start=1):
                subcarga = SubCarga(
                    carga_id=carga.id,
                    numero_subcarga=f"{carga.numero_carga}.{i}",
                    tipo_ave=subcarga_data.get('tipo_ave') or '',
                    produtor=subcarga_data.get('produtor') or '',
                    uf_produtor=subcarga_data.get('uf_produtor') or '',
                    numero_nfe=subcarga_data.get('numero_nfe') or '',
                    data_nfe=datetime.strptime(subcarga_data['data_nfe'], '%Y-%m-%d').date() if subcarga_data.get('data_nfe') else None,
                    numero_gta=subcarga_data.get('numero_gta') or '',
                    data_gta=datetime.strptime(subcarga_data['data_gta'], '%Y-%m-%d').date() if subcarga_data.get('data_gta') else None
                )
                db.session.add(subcarga)

        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(carga.id, 'ATUALIZAÇÃO')
        
        # Verificar se existe uma solicitação pendente para esta carga e notificar a conclusão
        solicitacoes_pendentes = Solicitacao.query.filter(
            Solicitacao.carga_id == carga.id, 
            Solicitacao.status == 'aprovada',
            (Solicitacao.tipo == TipoSolicitacao.REVISAO.value) | (Solicitacao.tipo == TipoSolicitacao.EDICAO.value)
        ).all()
        
        for solicitacao in solicitacoes_pendentes:
            # Atualizar status da solicitação para concluída
            solicitacao.status = StatusSolicitacao.CONCLUIDA.value
            solicitacao.concluido_em = datetime.utcnow()
            solicitacao.concluido_por_id = current_user.id
            db.session.commit()
            
            # Enviar notificação para o solicitante
            notificar_tarefa_concluida(solicitacao)
        
        return jsonify({'mensagem': 'Carga atualizada com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar carga: {str(e)}")  # Log do erro
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({'erro': str(e)}), 500

def get_proximo_numero():
    """Função auxiliar para obter o próximo número de carga"""
    try:
        # Buscar a última carga
        ultima_carga = Carga.query.order_by(Carga.numero_carga.desc()).first()
        
        if ultima_carga:
            # Se existe uma carga, pegar o número e adicionar 1
            try:
                ultimo_numero = int(ultima_carga.numero_carga)
                proximo = ultimo_numero + 1
            except ValueError:
                # Se não conseguir converter para inteiro, começar do 5040
                proximo = 5040
        else:
            # Se não existe nenhuma carga, começar do 5040
            proximo = 5040
            
        return proximo
    except Exception as e:
        print(f"Erro ao buscar próximo número: {str(e)}")
        return 5040  # Em caso de erro, retorna 5040 como fallback seguro

@cargas.route('/proximo_numero', methods=['GET'])
@login_required
def proximo_numero():
    """Endpoint para obter o próximo número de carga"""
    try:
        proximo = get_proximo_numero()
        return jsonify({'numero': str(proximo)})
    except Exception as e:
        print(f"Erro ao buscar próximo número: {str(e)}")
        import traceback
        print(traceback.format_exc())  # Imprime o stack trace completo
        return jsonify({'error': 'Erro ao buscar próximo número'}), 500

@cargas.route('/solicitar_revisao/<int:id>', methods=['POST'])
@login_required
def solicitar_revisao(id):
    try:
        carga = Carga.query.get_or_404(id)
        motivo = request.json.get('motivo', '')
        setor = request.json.get('setor', '')
        
        # Registrar no histórico
        registrar_historico(id, f"Solicitou revisão da carga #{carga.numero_carga} para o setor {setor}. Motivo: {motivo}")
        
        # Criar solicitação de revisão
        solicitacao = Solicitacao(
            carga_id=id,
            solicitado_por_id=current_user.id,
            tipo=TipoSolicitacao.REVISAO.value,
            setor=setor,
            motivo=motivo,
            status=StatusSolicitacao.PENDENTE.value
        )
        db.session.add(solicitacao)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de revisão enviada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar revisão: {str(e)}'
        }), 500

@cargas.route('/veiculos', methods=['GET'])
@login_required
def carregar_veiculos():
    try:
        transportadora = request.args.get('transportadora')
        if transportadora == 'Ellen Transportes':
            return jsonify(PLACAS_ELLEN)
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
