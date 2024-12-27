from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Carga, SubCarga, Usuario, ConfiguracaoFormulario, Producao, Fechamento, TipoUsuario
from datetime import datetime
from constants import *
from extensions import csrf
from routes.notificacoes import notificar_nova_carga, notificar_producao, notificar_fechamento
from utils import (permissao_balanca, permissao_producao, permissao_fechamento, 
                  permissao_financeiro, permissao_diretoria, permissao_gerente)

cargas_bp = Blueprint('cargas', __name__)

# Marcar rotas como isentas de CSRF
csrf.exempt(cargas_bp)

@cargas_bp.route('/nova_carga', methods=['GET'])
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

@cargas_bp.route('/criar_carga', methods=['POST'])
@login_required
@permissao_balanca
def criar_carga():
    try:
        data = request.json
        print("Dados recebidos:", data)  # Log dos dados recebidos

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

        # Função auxiliar para converter valores
        def converter_float(valor, padrao=0.0):
            try:
                if valor is None or valor == '':
                    print(f"Valor nulo ou vazio, retornando padrão: {padrao}")  # Log de valor nulo
                    return padrao
                if isinstance(valor, str):
                    # Remove R$ e converte vírgula para ponto
                    valor = valor.replace('R$', '').replace(',', '.').strip()
                    if valor == '':
                        print(f"Valor vazio após limpeza, retornando padrão: {padrao}")  # Log de valor vazio após limpeza
                        return padrao
                resultado = float(valor)
                print(f"Conversão bem sucedida: {valor} -> {resultado}")  # Log de conversão bem sucedida
                return resultado
            except (ValueError, TypeError) as e:
                print(f"Erro ao converter valor '{valor}': {str(e)}")  # Log de erro de conversão
                return padrao

        def converter_int(valor, padrao=0):
            try:
                if valor is None or valor == '':
                    print(f"Valor nulo ou vazio, retornando padrão: {padrao}")  # Log de valor nulo
                    return padrao
                if isinstance(valor, str):
                    valor = valor.strip()
                    if valor == '':
                        print(f"Valor vazio após limpeza, retornando padrão: {padrao}")  # Log de valor vazio após limpeza
                        return padrao
                resultado = int(float(valor))
                print(f"Conversão bem sucedida: {valor} -> {resultado}")  # Log de conversão bem sucedida
                return resultado
            except (ValueError, TypeError) as e:
                print(f"Erro ao converter valor '{valor}': {str(e)}")  # Log de erro de conversão
                return padrao

        # Criar objeto Carga
        carga_data = {
            'numero_carga': str(numero_carga),  # Convertendo para string
            'tipo_ave': data.get('tipo_ave', ''),
            'quantidade_cargas': converter_int(data.get('quantidade_cargas', '0')),
            'ordem_carga': data.get('ordem_carga', ''),
            'data_abate': datetime.strptime(data.get('data_abate', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
            'dia_semana': data.get('dia_semana', ''),
            'agenciador': data.get('agenciador', ''),
            'motorista': data.get('motorista', ''),
            'motorista_outro': data.get('motorista_outro', ''),
            'transportadora': data.get('transportadora', ''),
            'placa_veiculo': data.get('placa_veiculo', ''),
            'km_saida': converter_float(data.get('km_saida')),
            'km_chegada': converter_float(data.get('km_chegada')),
            'km_rodados': converter_float(data.get('km_rodados')),
            'valor_km': converter_float(data.get('valor_km')),
            'valor_frete': converter_float(data.get('valor_frete')),
            'status_frete': data.get('status_frete', ''),
            'caixas_vazias': converter_int(data.get('caixas_vazias')),
            'quantidade_caixas': converter_int(data.get('quantidade_caixas')),
            'produtor': data.get('produtor', ''),
            'uf_produtor': data.get('uf_produtor', ''),
            'numero_nfe': data.get('numero_nfe', ''),
            'data_nfe': datetime.strptime(data.get('data_nfe', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if data.get('data_nfe') else None,
            'numero_gta': data.get('numero_gta', ''),
            'data_gta': datetime.strptime(data.get('data_gta', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if data.get('data_gta') else None,
            'peso_granja': converter_float(data.get('peso_granja')),
            'peso_frigorifico': converter_float(data.get('peso_frigorifico')),
            'percentual_quebra': converter_float(data.get('percentual_quebra')),
            'quebra_peso': converter_float(data.get('quebra_peso')),
            'motivo_alta_quebra': data.get('motivo_alta_quebra', ''),
            'pedagios': converter_float(data.get('pedagios')),
            'outras_despesas': converter_float(data.get('outras_despesas')),
            'abastecimento_empresa': converter_float(data.get('abastecimento_empresa')),
            'abastecimento_posto': converter_float(data.get('abastecimento_posto')),
            'adiantamento': converter_float(data.get('adiantamento')),
            'valor_pagar': converter_float(data.get('valor_pagar')),
        }
        print("Dados da carga processados:", carga_data)  # Log dos dados processados

        # Criar a carga principal
        carga = Carga(**carga_data)
        carga.criado_por_id = current_user.id
        carga.atualizado_por_id = current_user.id
        carga.atualizar_status(Carga.STATUS_PENDENTE)  # Define o status inicial como pendente
        
        db.session.add(carga)
        db.session.commit()
        print("Carga principal salva com sucesso")  # Log de sucesso ao salvar carga
        
        # Notificar usuários sobre a nova carga
        notificar_nova_carga(carga)
        
        # Depois processamos as subcargas
        if 'subcargas' in data:
            print("Processando subcargas:", len(data['subcargas']))  # Log do número de subcargas
            for i, subcarga_data in enumerate(data['subcargas']):
                print(f"Processando subcarga {i+1}:", subcarga_data)  # Log dos dados da subcarga
                numero_subcarga = f"{str(numero_carga)}.{i+1}"  # Convertendo para string antes da concatenação
                subcarga = SubCarga(
                    carga_id=carga.id,
                    numero_subcarga=numero_subcarga,
                    tipo_ave=subcarga_data.get('tipo_ave', ''),
                    produtor=subcarga_data.get('produtor', ''),
                    uf_produtor=subcarga_data.get('uf_produtor', ''),
                    numero_nfe=subcarga_data.get('numero_nfe', ''),
                    data_nfe=datetime.strptime(subcarga_data.get('data_nfe', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if subcarga_data.get('data_nfe') else None,
                    numero_gta=subcarga_data.get('numero_gta', ''),
                    data_gta=datetime.strptime(subcarga_data.get('data_gta', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if subcarga_data.get('data_gta') else None
                )
                db.session.add(subcarga)
                print(f"Subcarga {i+1} adicionada com sucesso")  # Log de sucesso ao adicionar subcarga

            db.session.commit()
            print("Todas as subcargas salvas com sucesso")  # Log de sucesso ao salvar subcargas

        return jsonify({'success': True, 'message': 'Carga criada com sucesso!'})

    except Exception as e:
        db.session.rollback()
        print("Erro ao criar carga:", str(e))  # Log detalhado do erro
        print("Tipo do erro:", type(e).__name__)  # Log do tipo do erro
        return jsonify({'success': False, 'message': f'Erro ao criar carga: {str(e)}'}), 400

@cargas_bp.route('/fechamento')
@login_required
def fechamento_carga():
    return render_template('cargas/fechamento_carga.html')

@cargas_bp.route('/buscar_carga_fechamento/<numero_carga>')
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

@cargas_bp.route('/salvar_fechamento', methods=['POST'])
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
        
        # Notificar gerentes sobre fechamento inserido
        notificar_fechamento(carga)
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@cargas_bp.route('/cargas_incompletas')
@login_required
def cargas_incompletas():
    cargas = Carga.query.filter_by(status='incompleto').all()
    return render_template('cargas/cargas_incompletas.html', cargas=cargas)

@cargas_bp.route('/todas_cargas')
@login_required
def todas_cargas():
    cargas = Carga.query.order_by(Carga.criado_em.desc()).all()
    return render_template('cargas/todas_cargas.html', cargas=cargas)

@cargas_bp.route('/visualizar/<int:id>')
@login_required
def visualizar_carga(id):
    carga = Carga.query.get_or_404(id)
    producao = Producao.query.filter_by(carga_id=id).first()
    return render_template('cargas/visualizar_carga.html', carga=carga, producao=producao)

@cargas_bp.route('/editar/<int:id>', methods=['GET'])
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

@cargas_bp.route('/editar/<int:id>', methods=['POST'])
@login_required
@permissao_balanca
def atualizar_carga(id):
    carga = Carga.query.get_or_404(id)
    try:
        data = request.json
        
        # Atualizar campos da carga
        for key, value in data.items():
            if hasattr(carga, key):
                setattr(carga, key, value)
        
        carga.atualizado_por_id = current_user.id
        carga.atualizar_status()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Carga atualizada com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@cargas_bp.route('/')
@login_required
def listar_cargas():
    cargas = Carga.query.order_by(Carga.criado_em.desc()).all()
    return render_template('cargas/listar_cargas.html', cargas=cargas)

@cargas_bp.route('/producao')
@login_required
@permissao_producao
def producao():
    return render_template('cargas/producao.html')

@cargas_bp.route('/producao/buscar/<numero_carga>')
@login_required
@permissao_producao
def buscar_carga_producao(numero_carga):
    carga = Carga.query.filter_by(numero_carga=numero_carga).first()
    if not carga:
        return jsonify({'success': False, 'message': 'Carga não encontrada'}), 404
    
    return jsonify({
        'success': True,
        'carga': {
            'id': carga.id,
            'numero_carga': carga.numero_carga,
            'tipo_ave': carga.tipo_ave,
            'data_abate': carga.data_abate.strftime('%Y-%m-%d'),
            'motorista': carga.motorista
        }
    })

@cargas_bp.route('/producao/salvar', methods=['POST'])
@login_required
@permissao_producao
def salvar_producao():
    try:
        data = request.json
        carga_id = data.get('carga_id')
        carga = Carga.query.get_or_404(carga_id)
        
        # Converter strings para números
        def converter_float(valor, padrao=0.0):
            try:
                return float(valor) if valor else padrao
            except (ValueError, TypeError):
                return padrao

        def converter_int(valor, padrao=0):
            try:
                return int(valor) if valor else padrao
            except (ValueError, TypeError):
                return padrao
        
        # Calcular total de avarias
        total_avarias = sum([
            converter_float(data.get('mortalidade_excesso')),
            converter_float(data.get('aves_molhadas_granja')),
            converter_float(data.get('aves_molhadas_chuva')),
            converter_float(data.get('quebra_maus_tratos')),
            converter_float(data.get('aves_papo_cheio')),
            converter_float(data.get('outras_quebras'))
        ])
        
        producao = Producao(
            carga_id=carga.id,
            data_producao=datetime.utcnow().date(),  # Data atual
            aves_granja=converter_int(data.get('aves_granja')),
            aves_mortas=converter_int(data.get('aves_mortas')),
            aves_recebidas=converter_int(data.get('aves_recebidas')),
            aves_contador=converter_int(data.get('aves_contador')),
            aves_por_caixa=converter_int(data.get('aves_por_caixa')),
            mortalidade_excesso=converter_float(data.get('mortalidade_excesso')),
            aves_molhadas_granja=converter_float(data.get('aves_molhadas_granja')),
            aves_molhadas_chuva=converter_float(data.get('aves_molhadas_chuva')),
            quebra_maus_tratos=converter_float(data.get('quebra_maus_tratos')),
            aves_papo_cheio=converter_float(data.get('aves_papo_cheio')),
            outras_quebras=converter_float(data.get('outras_quebras')),
            descricao_quebras=data.get('descricao_quebras'),
            total_avarias=total_avarias
        )
        
        db.session.add(producao)
        db.session.commit()
        
        # Notificar gerentes sobre produção inserida
        notificar_producao(carga)
        
        return jsonify({'success': True, 'message': 'Produção salva com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print("Erro ao salvar produção:", str(e))  # Log do erro
        return jsonify({'success': False, 'message': str(e)}), 400

@cargas_bp.route('/solicitar_verificacao/<int:id>', methods=['POST'])
@login_required
@permissao_financeiro
def solicitar_verificacao(id):
    try:
        data = request.json
        motivo = data.get('motivo')
        if not motivo:
            return jsonify({'success': False, 'message': 'O motivo da verificação é obrigatório'}), 400
            
        carga = Carga.query.get_or_404(id)
        # Adicionar lógica de solicitação de verificação
        carga.status_verificacao = 'pendente'
        carga.motivo_verificacao = motivo
        carga.solicitado_por_id = current_user.id
        carga.data_solicitacao = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Solicitação de verificação enviada com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@cargas_bp.route('/solicitar_exclusao/<int:id>', methods=['POST'])
@login_required
@permissao_financeiro
def solicitar_exclusao(id):
    try:
        data = request.json
        motivo = data.get('motivo')
        if not motivo:
            return jsonify({'success': False, 'message': 'O motivo da exclusão é obrigatório'}), 400
            
        carga = Carga.query.get_or_404(id)
        # Adicionar lógica de solicitação de exclusão
        carga.status_exclusao = 'pendente'
        carga.motivo_exclusao = motivo
        carga.solicitado_exclusao_por_id = current_user.id
        carga.data_solicitacao_exclusao = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Solicitação de exclusão enviada com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@cargas_bp.route('/aprovar_nota/<int:id>', methods=['POST'])
@login_required
@permissao_financeiro
def aprovar_nota(id):
    try:
        carga = Carga.query.get_or_404(id)
        carga.nota_aprovada = True
        carga.aprovado_por_id = current_user.id
        carga.aprovado_em = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Nota aprovada com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@cargas_bp.route('/autorizar_nota/<int:id>', methods=['POST'])
@login_required
@permissao_diretoria
def autorizar_nota(id):
    try:
        data = request.json
        senha = data.get('senha')
        assinatura = data.get('assinatura')
        
        # Verificar a senha do usuário
        if not current_user.check_senha(senha):
            return jsonify({'success': False, 'message': 'Senha incorreta.'}), 401
            
        # Verificar se a assinatura foi fornecida
        if not assinatura:
            return jsonify({'success': False, 'message': 'A assinatura é obrigatória.'}), 400
            
        carga = Carga.query.get_or_404(id)
        
        # Verificar se a nota foi aprovada
        if not carga.nota_aprovada:
            return jsonify({'success': False, 'message': 'A nota precisa ser aprovada antes de ser autorizada.'}), 400
            
        # Autorizar a nota
        carga.nota_autorizada = True
        carga.autorizado_por_id = current_user.id
        carga.autorizado_em = datetime.utcnow()
        carga.assinatura_autorizacao = assinatura
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Nota autorizada com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
