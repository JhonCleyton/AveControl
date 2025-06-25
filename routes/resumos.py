from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import Carga, HistoricoCarga
from utils import permissao_resumos, permissao_financeiro
from datetime import datetime
from sqlalchemy import desc, func
from extensions import db, csrf

resumos_bp = Blueprint('resumos', __name__)

@resumos_bp.route('/', methods=['GET'])
@login_required
@permissao_resumos
def index():
    try:
        # Pegar parâmetros dos filtros
        transportadora = request.args.get('transportadora')
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        
        # Query base
        query = Carga.query
        
        # Filtro de produtor
        produtor = request.args.get('produtor')
        if produtor:
            query = query.filter(Carga.produtor == produtor)
        
        # Se for usuário transportadora, sempre filtrar por Ellen Transportes
        if current_user.tipo == 'transportadora':
            query = query.filter(Carga.transportadora == 'Ellen Transportes')
        # Se houver filtro de transportadora e não for usuário transportadora
        elif transportadora:
            query = query.filter(Carga.transportadora == transportadora)
            
        # Aplicar filtros de data
        if data_inicial and data_final:
            try:
                data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d')
                data_final_obj = datetime.strptime(data_final, '%Y-%m-%d')
                query = query.filter(func.date(Carga.data_abate).between(data_inicial_obj.date(), data_final_obj.date()))
            except ValueError:
                flash('Data inicial ou final inválida', 'danger')
                
        # Buscar todas as cargas ordenadas por data de abate
        cargas = query.order_by(desc(Carga.data_abate)).all()
        
        # Buscar lista de transportadoras para o filtro
        if current_user.tipo == 'transportadora':
            transportadoras = ['Ellen Transportes']
        else:
            transportadoras = Carga.query.with_entities(Carga.transportadora).distinct().order_by(Carga.transportadora).all()
            transportadoras = [t[0] for t in transportadoras if t[0]]
        
        # Buscar lista de produtores para o filtro
        produtores = Carga.query.with_entities(Carga.produtor).distinct().order_by(Carga.produtor).all()
        produtores = [p[0] for p in produtores if p[0]]
        
        # Calcular totais
        total_fretes = sum(carga.valor_frete or 0 for carga in cargas)
        total_adiantamentos = sum(carga.adiantamento or 0 for carga in cargas)
        total_outras_despesas = sum(carga.outras_despesas or 0 for carga in cargas)
        total_abastecimento = sum((carga.abastecimento_empresa or 0) + (carga.abastecimento_posto or 0) for carga in cargas)
        total_pagar = sum(carga.valor_pagar or 0 for carga in cargas)
        
        resumo = {
            'cargas': [{
                'id': carga.id,
                'data_abate': carga.data_abate,
                'numero_carga': carga.numero_carga,
                'transportadora': carga.transportadora,
                'valor_frete': carga.valor_frete,
                'adiantamento': carga.adiantamento,
                'outras_despesas': carga.outras_despesas,
                'abastecimento_empresa': carga.abastecimento_empresa,
                'abastecimento_posto': carga.abastecimento_posto,
                'valor_pagar': carga.valor_pagar
            } for carga in cargas],
            'transportadoras': transportadoras,
            'transportadora_selecionada': transportadora,
            'produtores': produtores,
            'produtor_selecionado': produtor,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'total_fretes': total_fretes,
            'total_adiantamentos': total_adiantamentos,
            'total_outras_despesas': total_outras_despesas,
            'total_abastecimento': total_abastecimento,
            'total_pagar': total_pagar
        }
        
        return render_template('resumos/index.html', resumo=resumo)
    except Exception as e:
        flash(f'Erro ao carregar resumo: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@resumos_bp.route('/aprovar_nota/<int:id>', methods=['POST'])
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
        db.session.rollback()
        print(f"Erro ao aprovar nota: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao aprovar nota: {str(e)}'
        }), 500

def registrar_historico(carga_id, acao):
    try:
        historico = HistoricoCarga(
            carga_id=carga_id,
            usuario_id=current_user.id,
            acao=acao,
            data_hora=datetime.now()
        )
        db.session.add(historico)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar histórico: {str(e)}")
