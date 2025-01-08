from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Carga, SubCarga, Usuario, ConfiguracaoFormulario, Producao, Fechamento, TipoUsuario, HistoricoCarga, Solicitacao, TipoSolicitacao, StatusSolicitacao, SetorSolicitacao
from datetime import datetime
from constants import *
from config import Config
from extensions import csrf
from routes.notificacoes import notificar_nova_carga, notificar_producao, notificar_fechamento
from utils import (permissao_balanca, permissao_producao, permissao_fechamento, 
                  permissao_financeiro, permissao_diretoria, permissao_gerente)

cargas = Blueprint('cargas', __name__)

# Marcar rotas como isentas de CSRF
csrf.exempt(cargas)

from utils.datetime_utils import get_current_time  # Adicione no topo do arquivo

def registrar_historico(carga_id, acao):
    try:
        # Pega o horário atual
        from datetime import datetime
        import pytz
        
        # Cria o timestamp em UTC
        now = datetime.utcnow()
        # Converte para São Paulo (UTC-3)
        sp_tz = pytz.timezone('America/Sao_Paulo')
        sp_time = now.replace(tzinfo=pytz.UTC).astimezone(sp_tz)
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
                         configuracoes=configuracoes)

@cargas.route('/criar_carga', methods=['POST'])
@login_required
@permissao_balanca
def criar_carga():
    try:
        data = request.json
        print("Dados recebidos:", data)  # Log dos dados recebidos

        # Validar tipo de ave
        tipo_ave = data.get('tipo_ave', '').upper()
        if tipo_ave not in [t.upper() for t in TIPOS_AVE]:
            return jsonify({
                'success': False,
                'message': f'Tipo de ave inválido: {tipo_ave}. Tipos válidos: {", ".join(TIPOS_AVE)}'
            }), 400

        # Gerar número da carga
        ultima_carga = Carga.query.order_by(Carga.numero_carga.desc()).first()
        if ultima_carga:
            try:
                ultimo_numero = int(ultima_carga.numero_carga)
                numero_carga = ultimo_numero + 1
            except (ValueError, TypeError):
                numero_carga = NUMERO_INICIAL_CARGA
        else:
            numero_carga = NUMERO_INICIAL_CARGA
        print("Número da carga gerado:", numero_carga)  # Log do número da carga

        # Criar a carga
        carga = Carga(
            numero_carga=str(numero_carga),
            tipo_ave=tipo_ave,  # Usar o tipo de ave validado
            quantidade_cargas=data.get('quantidade_cargas'),
            ordem_carga=data.get('ordem_carga'),
            data_abate=datetime.strptime(data.get('data_abate'), '%Y-%m-%d').date(),
            dia_semana=data.get('dia_semana'),
            agenciador=data.get('agenciador'),
            motorista=data.get('motorista'),
            motorista_outro=data.get('motorista_outro'),
            transportadora=data.get('transportadora'),
            placa_veiculo=data.get('placa_veiculo'),
            km_saida=float(data.get('km_saida', 0)),
            km_chegada=float(data.get('km_chegada', 0)),
            km_rodados=float(data.get('km_rodados', 0)),
            valor_km=float(data.get('valor_km', 0)),
            valor_frete=float(data.get('valor_frete', 0)),
            status_frete=data.get('status_frete'),
            caixas_vazias=int(data.get('caixas_vazias', 0)),
            quantidade_caixas=int(data.get('quantidade_caixas', 0)),
            produtor=data.get('produtor'),
            uf_produtor=data.get('uf_produtor'),
            numero_nfe=data.get('numero_nfe'),
            data_nfe=datetime.strptime(data.get('data_nfe'), '%Y-%m-%d').date() if data.get('data_nfe') else None,
            numero_gta=data.get('numero_gta'),
            data_gta=datetime.strptime(data.get('data_gta'), '%Y-%m-%d').date() if data.get('data_gta') else None,
            peso_granja=float(data.get('peso_granja', 0)),
            peso_frigorifico=float(data.get('peso_frigorifico', 0)),
            percentual_quebra=float(data.get('percentual_quebra', 0)),
            quebra_peso=float(data.get('quebra_peso', 0)),
            motivo_alta_quebra=data.get('motivo_alta_quebra'),
            pedagios=float(data.get('pedagios', 0)),
            outras_despesas=float(data.get('outras_despesas', 0)),
            abastecimento_empresa=float(data.get('abastecimento_empresa', 0)),
            abastecimento_posto=float(data.get('abastecimento_posto', 0)),
            adiantamento=float(data.get('adiantamento', 0)),
            valor_pagar=float(data.get('valor_pagar', 0)),
            criado_por_id=current_user.id,
            atualizado_por_id=current_user.id
        )
        
        db.session.add(carga)
        db.session.commit()
        
        # Processar subcargas
        if 'subcargas' in data:
            for i, subcarga_data in enumerate(data['subcargas'], start=1):
                subcarga = SubCarga(
                    carga_id=carga.id,
                    numero_subcarga=f"{str(numero_carga)}.{i}",  # Gerar número da subcarga
                    tipo_ave=subcarga_data.get('tipo_ave'),
                    produtor=subcarga_data.get('produtor'),
                    uf_produtor=subcarga_data.get('uf_produtor'),
                    numero_nfe=subcarga_data.get('numero_nfe'),
                    data_nfe=datetime.strptime(subcarga_data.get('data_nfe'), '%Y-%m-%d').date() if subcarga_data.get('data_nfe') else None,
                    numero_gta=subcarga_data.get('numero_gta'),
                    data_gta=datetime.strptime(subcarga_data.get('data_gta'), '%Y-%m-%d').date() if subcarga_data.get('data_gta') else None
                )
                db.session.add(subcarga)
            
            db.session.commit()
        
        # Registrar no histórico
        registrar_historico(carga.id, f"Criou a carga #{carga.numero_carga}")
        
        # Notificar usuários
        notificar_nova_carga(carga)
        
        return jsonify({
            'success': True,
            'message': 'Carga criada com sucesso!',
            'id': carga.id
        })
    except Exception as e:
        print(f"Erro ao criar carga: {str(e)}")
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
@permissao_fechamento
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
@permissao_fechamento
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
    registrar_historico(id, f"Visualizou a carga #{carga.numero_carga}")
    producao = Producao.query.filter_by(carga_id=id).first()
    return render_template('cargas/visualizar_carga.html', carga=carga, producao=producao)

@cargas.route('/editar/<int:id>', methods=['GET'])
@login_required
@permissao_balanca
def editar_carga(id):
    carga = Carga.query.get_or_404(id)
    configuracoes = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
    return render_template('cargas/editar_carga.html', 
                         carga=carga,
                         tipos_ave=TIPOS_AVE,
                         motoristas=MOTORISTAS,
                         transportadoras=TRANSPORTADORAS,
                         placas_ellen=PLACAS_ELLEN,
                         valores_km=VALORES_KM,
                         status_frete=STATUS_FRETE,
                         estados_brasil=ESTADOS_BRASIL,
                         configuracoes=configuracoes)

@cargas.route('/atualizar_carga/<int:id>', methods=['POST'])
@login_required
@permissao_balanca
def atualizar_carga(id):
    try:
        if not verificar_permissao_edicao(id, SetorSolicitacao.BALANCA):
            return jsonify({
                'success': False,
                'message': 'Você precisa solicitar permissão para editar esta carga'
            }), 403
            
        data = request.json
        carga = Carga.query.get_or_404(id)
        
        # Validar tipo de ave
        tipo_ave = data.get('tipo_ave', '').upper()
        if tipo_ave and tipo_ave not in [t.upper() for t in TIPOS_AVE]:
            return jsonify({
                'success': False,
                'message': f'Tipo de ave inválido: {tipo_ave}. Tipos válidos: {", ".join(TIPOS_AVE)}'
            }), 400
        
        # Atualizar campos da carga
        carga.tipo_ave = tipo_ave if tipo_ave else carga.tipo_ave
        carga.quantidade_cargas = data.get('quantidade_cargas', carga.quantidade_cargas)
        carga.ordem_carga = data.get('ordem_carga', carga.ordem_carga)
        carga.data_abate = datetime.strptime(data.get('data_abate'), '%Y-%m-%d').date() if data.get('data_abate') else carga.data_abate
        carga.dia_semana = data.get('dia_semana', carga.dia_semana)
        carga.agenciador = data.get('agenciador', carga.agenciador)
        carga.motorista = data.get('motorista', carga.motorista)
        carga.motorista_outro = data.get('motorista_outro', carga.motorista_outro)
        carga.transportadora = data.get('transportadora', carga.transportadora)
        carga.placa_veiculo = data.get('placa_veiculo', carga.placa_veiculo)
        carga.km_saida = float(data.get('km_saida', carga.km_saida))
        carga.km_chegada = float(data.get('km_chegada', carga.km_chegada))
        carga.km_rodados = float(data.get('km_rodados', carga.km_rodados))
        carga.valor_km = float(data.get('valor_km', carga.valor_km))
        carga.valor_frete = float(data.get('valor_frete', carga.valor_frete))
        carga.status_frete = data.get('status_frete', carga.status_frete)
        carga.caixas_vazias = int(data.get('caixas_vazias', carga.caixas_vazias))
        carga.quantidade_caixas = int(data.get('quantidade_caixas', carga.quantidade_caixas))
        carga.produtor = data.get('produtor', carga.produtor)
        carga.uf_produtor = data.get('uf_produtor', carga.uf_produtor)
        carga.numero_nfe = data.get('numero_nfe', carga.numero_nfe)
        carga.data_nfe = datetime.strptime(data.get('data_nfe'), '%Y-%m-%d').date() if data.get('data_nfe') else carga.data_nfe
        carga.numero_gta = data.get('numero_gta', carga.numero_gta)
        carga.data_gta = datetime.strptime(data.get('data_gta'), '%Y-%m-%d').date() if data.get('data_gta') else carga.data_gta
        carga.peso_granja = float(data.get('peso_granja', carga.peso_granja))
        carga.peso_frigorifico = float(data.get('peso_frigorifico', carga.peso_frigorifico))
        carga.percentual_quebra = float(data.get('percentual_quebra', carga.percentual_quebra))
        carga.quebra_peso = float(data.get('quebra_peso', carga.quebra_peso))
        carga.motivo_alta_quebra = data.get('motivo_alta_quebra', carga.motivo_alta_quebra)
        carga.pedagios = float(data.get('pedagios', carga.pedagios))
        carga.outras_despesas = float(data.get('outras_despesas', carga.outras_despesas))
        carga.abastecimento_empresa = float(data.get('abastecimento_empresa', carga.abastecimento_empresa))
        carga.abastecimento_posto = float(data.get('abastecimento_posto', carga.abastecimento_posto))
        carga.adiantamento = float(data.get('adiantamento', carga.adiantamento))
        carga.valor_pagar = float(data.get('valor_pagar', carga.valor_pagar))
        carga.atualizado_por_id = current_user.id
        carga.atualizado_em = datetime.utcnow()

        # Atualizar subcargas
        if 'subcargas' in data:
            # Remover subcargas antigas
            for subcarga in carga.subcargas:
                db.session.delete(subcarga)
            
            # Adicionar novas subcargas
            for i, subcarga_data in enumerate(data['subcargas'], start=1):
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
                db.session.add(subcarga)

        db.session.commit()

        # Registrar no histórico
        registrar_historico(id, f"Atualizou dados da carga #{carga.numero_carga}")

        return jsonify({
            'success': True,
            'message': 'Carga atualizada com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar carga: {str(e)}'
        }), 500

@cargas.route('/listar_cargas')
@login_required
def listar_cargas():
    search = request.args.get('search', '').strip()
    
    # Query base
    query = Carga.query
    
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

@cargas.route('/producao')
@login_required
@permissao_producao
def producao():
    return render_template('cargas/producao.html')

@cargas.route('/producao/buscar/<numero_carga>')
@login_required
@permissao_producao
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
@permissao_producao
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
        return jsonify({'success': False, 'message': str(e)})

@cargas.route('/solicitar_verificacao/<int:id>', methods=['POST'])
@login_required
@permissao_financeiro
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
@permissao_financeiro
def solicitar_exclusao(id):
    try:
        carga = Carga.query.get_or_404(id)
        motivo = request.json.get('motivo', '')
        
        # Registrar no histórico
        registrar_historico(id, f"Solicitou exclusão da carga #{carga.numero_carga}. Motivo: {motivo}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de exclusão enviada com sucesso!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar exclusão: {str(e)}'
        }), 500

@cargas.route('/aprovar_nota/<int:id>', methods=['POST'])
@login_required
@permissao_financeiro
def aprovar_nota(id):
    try:
        carga = Carga.query.get_or_404(id)
        
        if carga.nota_aprovada:
            return jsonify({
                'success': False,
                'message': 'Esta nota já foi aprovada!'
            }), 400
        
        carga.nota_aprovada = True
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
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar nota: {str(e)}'
        }), 500

@cargas.route('/autorizar_nota/<int:id>', methods=['POST'])
@login_required
@permissao_diretoria
def autorizar_nota(id):
    try:
        carga = Carga.query.get_or_404(id)
        data = request.json
        
        if not carga.nota_aprovada:
            return jsonify({
                'success': False,
                'message': 'A nota precisa ser aprovada antes de ser autorizada!'
            }), 400
            
        if carga.nota_autorizada:
            return jsonify({
                'success': False,
                'message': 'Esta nota já foi autorizada!'
            }), 400
        
        carga.nota_autorizada = True
        carga.autorizado_por_id = current_user.id
        carga.autorizado_em = datetime.now()
        carga.assinatura_autorizacao = data.get('assinatura')
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Autorizou a nota da carga #{carga.numero_carga}")
        
        return jsonify({
            'success': True,
            'message': 'Nota autorizada com sucesso!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao autorizar nota: {str(e)}'
        }), 500

@cargas.route('/solicitar_verificacao_balanca/<int:id>', methods=['POST'])
@login_required
@permissao_balanca
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
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar verificação: {str(e)}'
        }), 500

@cargas.route('/solicitar_verificacao_producao/<int:id>', methods=['POST'])
@login_required
@permissao_producao
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
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar verificação: {str(e)}'
        }), 500

@cargas.route('/solicitar_verificacao_fechamento/<int:id>', methods=['POST'])
@login_required
@permissao_fechamento
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
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar verificação: {str(e)}'
        }), 500

@cargas.route('/aprovar_verificacao_balanca/<int:id>', methods=['POST'])
@login_required
@permissao_gerente
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
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar verificação: {str(e)}'
        }), 500

@cargas.route('/aprovar_verificacao_producao/<int:id>', methods=['POST'])
@login_required
@permissao_gerente
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
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar verificação: {str(e)}'
        }), 500

@cargas.route('/aprovar_verificacao_fechamento/<int:id>', methods=['POST'])
@login_required
@permissao_gerente
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
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar verificação: {str(e)}'
        }), 500

@cargas.route('/solicitar_edicao/<int:id>', methods=['POST'])
@login_required
def solicitar_edicao(id):
    try:
        data = request.json
        carga = Carga.query.get_or_404(id)
        
        # Converter string do setor para enum
        try:
            setor = SetorSolicitacao(data['setor'])
        except ValueError:
            return jsonify({
                'success': False,
                'message': f'Setor inválido: {data["setor"]}'
            }), 400
        
        # Verificar se já existe uma solicitação pendente
        solicitacao_pendente = Solicitacao.query.filter_by(
            carga_id=id,
            tipo=TipoSolicitacao.EDICAO,
            setor=setor,
            status=StatusSolicitacao.PENDENTE
        ).first()
        
        if solicitacao_pendente:
            return jsonify({
                'success': False,
                'message': 'Já existe uma solicitação pendente para esta carga'
            }), 400
        
        # Criar nova solicitação
        solicitacao = Solicitacao(
            carga_id=id,
            tipo=TipoSolicitacao.EDICAO,  # Usar o enum diretamente
            setor=setor,
            motivo=data['motivo'],
            solicitado_por_id=current_user.id,
            criado_em=datetime.now(Config.TIMEZONE)  # Usar timezone de SP
        )
        
        db.session.add(solicitacao)
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(id, f"Solicitou edição de {setor.value}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de edição enviada com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao solicitar edição: {str(e)}'
        }), 500

@cargas.route('/aprovar_edicao/<int:solicitacao_id>', methods=['POST'])
@login_required
@permissao_gerente
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
        solicitacao.aprovado_em = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar no histórico
        registrar_historico(solicitacao.carga_id, f"Aprovou edição de {solicitacao.setor.value}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de edição aprovada com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar edição: {str(e)}'
        }), 500

@cargas.route('/rejeitar_edicao/<int:solicitacao_id>', methods=['POST'])
@login_required
@permissao_gerente
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
        solicitacao.aprovado_em = datetime.utcnow()
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
        return jsonify({
            'success': False,
            'message': f'Erro ao rejeitar edição: {str(e)}'
        }), 500

@cargas.route('/verificar_edicao/<int:solicitacao_id>', methods=['POST'])
@login_required
@permissao_gerente
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
        solicitacao.verificado_em = datetime.utcnow()
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
        return jsonify({
            'success': False,
            'message': f'Erro ao verificar edição: {str(e)}'
        }), 500

@cargas.route('/solicitacoes_edicao', methods=['GET'])
@login_required
def listar_solicitacoes():
    try:
        # Gerentes veem todas as solicitações pendentes
        if current_user.tipo == TipoUsuario.GERENTE:
            solicitacoes = Solicitacao.query.filter_by(status=StatusSolicitacao.PENDENTE).all()
        # Outros usuários veem suas próprias solicitações
        else:
            solicitacoes = Solicitacao.query.filter_by(solicitado_por_id=current_user.id).all()
        
        return jsonify({
            'success': True,
            'solicitacoes': [{
                'id': s.id,
                'carga_numero': s.carga.numero_carga,
                'tipo_solicitacao': s.tipo.value,
                'setor': s.setor.value,
                'status': s.status.value,
                'motivo': s.motivo,
                'solicitado_em': s.solicitado_em.strftime('%d/%m/%Y %H:%M'),
                'solicitado_por': s.solicitado_por.nome
            } for s in solicitacoes]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao listar solicitações: {str(e)}'
        }), 500

@cargas.route('/solicitacoes', methods=['GET'])
@login_required
def solicitacoes():
    return render_template('cargas/solicitacoes_edicao.html')

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

@cargas.route('/verificar_solicitacao/<int:id>')
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
@permissao_gerente
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
        return jsonify({'success': False, 'message': str(e)}), 500
