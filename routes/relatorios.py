from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import Carga
from utils import permissao_resumos
from datetime import datetime
from sqlalchemy import desc, func
import json

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/')
@login_required
@permissao_resumos
def index():
    try:
        # Pegar parâmetros do filtro
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        transportadora = request.args.get('transportadora')
        
        # Converter datas se fornecidas
        if data_inicial:
            data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
        if data_final:
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
        
        # Query base
        query = Carga.query
        
        # Aplicar filtros
        if current_user.tipo == 'transportadora':
            query = query.filter(Carga.transportadora == current_user.nome)
        elif transportadora:
            query = query.filter(Carga.transportadora == transportadora)
            
        if data_inicial:
            query = query.filter(Carga.data_abate >= data_inicial)
        if data_final:
            query = query.filter(Carga.data_abate <= data_final)
            
        # Buscar cargas
        cargas = query.order_by(Carga.data_abate).all()
        
        # Buscar lista de transportadoras para o filtro
        transportadoras = Carga.query.with_entities(Carga.transportadora).distinct().order_by(Carga.transportadora).all()
        transportadoras = [t[0] for t in transportadoras if t[0]]
        
        # Calcular métricas
        total_cargas = len(cargas)
        
        # Evitar divisão por zero
        if total_cargas > 0:
            abastecimento_medio = sum((c.abastecimento_empresa or 0) + (c.abastecimento_posto or 0) for c in cargas) / total_cargas
            frete_medio = sum(c.valor_frete or 0 for c in cargas) / total_cargas
        else:
            abastecimento_medio = 0
            frete_medio = 0
            
        abastecimento_total = sum((c.abastecimento_empresa or 0) + (c.abastecimento_posto or 0) for c in cargas)
        frete_total = sum(c.valor_frete or 0 for c in cargas)
        valor_pagar_total = sum(c.valor_pagar or 0 for c in cargas)
        
        # Dados para o gráfico de linha (evolução do frete)
        datas = [c.data_abate.strftime('%d/%m/%Y') for c in cargas]
        fretes = [float(c.valor_frete or 0) for c in cargas]
        
        # Dados para o gráfico de pizza
        total_abastecimento_posto = sum(c.abastecimento_posto or 0 for c in cargas)
        total_abastecimento_empresa = sum(c.abastecimento_empresa or 0 for c in cargas)
        total_pedagios = sum(c.pedagios or 0 for c in cargas)
        total_outras_despesas = sum(c.outras_despesas or 0 for c in cargas)
        
        dados_pizza = {
            'labels': ['Abastecimento Posto', 'Abastecimento Empresa', 'Pedágios', 'Frete', 'Outras Despesas'],
            'valores': [
                total_abastecimento_posto,
                total_abastecimento_empresa,
                total_pedagios,
                frete_total,
                total_outras_despesas
            ]
        }
        
        resumo = {
            'total_cargas': total_cargas,
            'abastecimento_medio': abastecimento_medio,
            'abastecimento_total': abastecimento_total,
            'frete_medio': frete_medio,
            'frete_total': frete_total,
            'valor_pagar_total': valor_pagar_total,
            'transportadoras': transportadoras,
            'transportadora_selecionada': transportadora,
            'data_inicial': data_inicial.strftime('%Y-%m-%d') if data_inicial else '',
            'data_final': data_final.strftime('%Y-%m-%d') if data_final else '',
            'grafico_linha': {
                'datas': datas,
                'fretes': fretes
            },
            'grafico_pizza': dados_pizza
        }
        
        return render_template('relatorios/index.html', resumo=resumo)
    except Exception as e:
        print(f"Erro ao carregar relatórios: {str(e)}")
        return render_template('relatorios/index.html', resumo={
            'total_cargas': 0,
            'abastecimento_medio': 0,
            'abastecimento_total': 0,
            'frete_medio': 0,
            'frete_total': 0,
            'valor_pagar_total': 0,
            'transportadoras': [],
            'transportadora_selecionada': None,
            'data_inicial': '',
            'data_final': '',
            'grafico_linha': {'datas': [], 'fretes': []},
            'grafico_pizza': {'labels': [], 'valores': []}
        })
