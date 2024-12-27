from flask import Blueprint, render_template, request
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
        # Pegar transportadora do filtro, se houver
        transportadora = request.args.get('transportadora')
        
        # Query base
        query = Carga.query
        
        # Se for usuário transportadora, mostrar apenas suas cargas
        if current_user.tipo == 'transportadora':
            query = query.filter(Carga.transportadora == current_user.nome)
        # Se houver filtro de transportadora
        elif transportadora:
            query = query.filter(Carga.transportadora == transportadora)
            
        # Buscar todas as cargas ordenadas por data de abate
        cargas = query.order_by(desc(Carga.data_abate)).all()
        
        # Buscar lista de transportadoras para o filtro
        transportadoras = Carga.query.with_entities(Carga.transportadora).distinct().order_by(Carga.transportadora).all()
        transportadoras = [t[0] for t in transportadoras if t[0]]  # Remover None/vazios
        
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
            'transportadora_selecionada': transportadora,
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
        print(f"Erro ao carregar resumos: {str(e)}")
        return render_template('resumos/index.html', resumo={
            'cargas': [], 
            'transportadoras': [],
            'transportadora_selecionada': None,
            'totais': {
                'fretes': 0,
                'pedagios': 0,
                'outras_despesas': 0,
                'abastecimento': 0,
                'adiantamentos': 0,
                'pagar': 0
            }
        })
