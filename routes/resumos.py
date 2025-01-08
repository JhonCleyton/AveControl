from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Carga
from utils import permissao_resumos
from datetime import datetime
from sqlalchemy import desc, func

resumos_bp = Blueprint('resumos', __name__)

@resumos_bp.route('/')
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
        
        # Se for usuário transportadora, sempre filtrar por Ellen Transportes
        if current_user.tipo == 'transportadora':
            query = query.filter(Carga.transportadora == 'Ellen Transportes')
        # Se houver filtro de transportadora e não for usuário transportadora
        elif transportadora:
            query = query.filter(Carga.transportadora == transportadora)
            
        # Aplicar filtros de data
        if data_inicial:
            data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d')
            query = query.filter(Carga.data_abate >= data_inicial_obj)
        if data_final:
            data_final_obj = datetime.strptime(data_final, '%Y-%m-%d')
            query = query.filter(Carga.data_abate <= data_final_obj)
            
        # Buscar todas as cargas ordenadas por data de abate
        cargas = query.order_by(desc(Carga.data_abate)).all()
        
        # Buscar lista de transportadoras para o filtro
        if current_user.tipo == 'transportadora':
            transportadoras = ['Ellen Transportes']
        else:
            transportadoras = Carga.query.with_entities(Carga.transportadora).distinct().order_by(Carga.transportadora).all()
            transportadoras = [t[0] for t in transportadoras if t[0]]
        
        # Calcular totais
        total_fretes = sum(carga.valor_frete or 0 for carga in cargas)
        total_pedagios = sum(carga.pedagios or 0 for carga in cargas)
        total_outras_despesas = sum(carga.outras_despesas or 0 for carga in cargas)
        total_abastecimento = sum((carga.abastecimento_empresa or 0) + (carga.abastecimento_posto or 0) for carga in cargas)
        total_adiantamentos = sum(carga.adiantamento or 0 for carga in cargas)
        total_pagar = sum(carga.valor_pagar or 0 for carga in cargas)
        
        resumo = {
            'cargas': cargas,
            'transportadoras': transportadoras,
            'transportadora_selecionada': transportadora or 'Ellen Transportes' if current_user.tipo == 'transportadora' else transportadora,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'totais': {
                'fretes': total_fretes,
                'pedagios': total_pedagios,
                'outras_despesas': total_outras_despesas,
                'abastecimento': total_abastecimento,
                'adiantamentos': total_adiantamentos,
                'pagar': total_pagar
            }
        }
        
        return render_template('resumos/index.html', resumo=resumo)
    except Exception as e:
        flash(f'Erro ao carregar resumo: {str(e)}', 'danger')
        return redirect(url_for('main.index'))
