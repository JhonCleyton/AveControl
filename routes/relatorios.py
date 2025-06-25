from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from models import Carga
from utils import permissao_diretoria
from datetime import datetime
from sqlalchemy import desc, func
from extensions import db

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/')
@login_required
@permissao_diretoria
def index():
    try:
        # Obter parâmetros de filtro
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        transportadora = request.args.get('transportadora')

        # Consulta base
        query = db.session.query(Carga)

        # Aplicar filtros se fornecidos
        if transportadora:
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

        # Buscar todas as transportadoras
        transportadoras = db.session.query(Carga.transportadora).distinct().all()
        transportadoras = [t[0] for t in transportadoras if t[0]]

        # Preparar dados para o template
        resumo = {
            'cargas': cargas,
            'total_cargas': len(cargas),
            'total_frete': sum(carga.valor_frete or 0 for carga in cargas),
            'total_pedagios': sum(carga.pedagios or 0 for carga in cargas),
            'total_despesas': sum(carga.outras_despesas or 0 for carga in cargas),
            'total_abastecimento': sum((carga.abastecimento_empresa or 0) + (carga.abastecimento_posto or 0) for carga in cargas),
            'total_pagar': sum(carga.valor_pagar or 0 for carga in cargas),
            'grafico_linha': {
                'datas': [],
                'valores': {
                    'frete': [],
                    'pedagios': [],
                    'despesas': [],
                    'abastecimento': [],
                    'pagar': []
                }
            },
            'grafico_pizza': {
                'labels': [],
                'valores': []
            }
        }

        # Dados do gráfico de linha
        if cargas:
            datas = sorted(set(carga.data_abate for carga in cargas))
            valores_por_data = {}
            for data in datas:
                cargas_do_dia = [c for c in cargas if c.data_abate == data]
                valores_por_data[data] = {
                    'total_frete': sum(c.valor_frete or 0 for c in cargas_do_dia),
                    'total_pedagios': sum(c.pedagios or 0 for c in cargas_do_dia),
                    'total_despesas': sum(c.outras_despesas or 0 for c in cargas_do_dia),
                    'total_abastecimento': sum((c.abastecimento_empresa or 0) + (c.abastecimento_posto or 0) for c in cargas_do_dia),
                    'total_pagar': sum(c.valor_pagar or 0 for c in cargas_do_dia)
                }

            resumo['grafico_linha'] = {
                'datas': [data.strftime('%d/%m/%Y') for data in datas],
                'valores': {
                    'frete': [valores_por_data[data]['total_frete'] for data in datas],
                    'pedagios': [valores_por_data[data]['total_pedagios'] for data in datas],
                    'despesas': [valores_por_data[data]['total_despesas'] for data in datas],
                    'abastecimento': [valores_por_data[data]['total_abastecimento'] for data in datas],
                    'pagar': [valores_por_data[data]['total_pagar'] for data in datas]
                }
            }

            # Dados do gráfico de pizza
            valores_por_transportadora = {}
            for t in transportadoras:
                cargas_transportadora = [c for c in cargas if c.transportadora == t]
                valores_por_transportadora[t] = sum(c.valor_pagar or 0 for c in cargas_transportadora)

            resumo['grafico_pizza'] = {
                'labels': list(valores_por_transportadora.keys()),
                'valores': list(valores_por_transportadora.values())
            }

        return render_template(
            'relatorios/index.html',
            resumo=resumo,
            transportadoras=transportadoras,
            transportadora_selecionada=transportadora,
            data_inicial=data_inicial,
            data_final=data_final,
            now=datetime.now()
        )
    except Exception as e:
        print(f"Erro ao gerar relatório: {str(e)}")
        flash('Erro ao gerar relatório', 'error')
        return render_template(
            'relatorios/index.html',
            resumo={
                'cargas': [],
                'total_cargas': 0,
                'total_frete': 0,
                'total_pedagios': 0,
                'total_despesas': 0,
                'total_abastecimento': 0,
                'total_pagar': 0,
                'grafico_linha': {
                    'datas': [],
                    'valores': {
                        'frete': [],
                        'pedagios': [],
                        'despesas': [],
                        'abastecimento': [],
                        'pagar': []
                    }
                },
                'grafico_pizza': {
                    'labels': [],
                    'valores': []
                }
            },
            transportadoras=[],
            transportadora_selecionada=None,
            data_inicial=None,
            data_final=None,
            now=datetime.now()
        )

@relatorios_bp.route('/imprimir')
@login_required
@permissao_diretoria
def imprimir():
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
        query = db.session.query(Carga)
        
        # Aplicar filtros
        if transportadora:
            query = query.filter(Carga.transportadora == transportadora)
            
        if data_inicial:
            query = query.filter(Carga.data_abate >= data_inicial)
        if data_final:
            query = query.filter(Carga.data_abate <= data_final)
            
        # Buscar cargas
        cargas = query.order_by(Carga.data_abate).all()
        
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
            'transportadora_selecionada': transportadora,
            'data_inicial': data_inicial.strftime('%Y-%m-%d') if data_inicial else '',
            'data_final': data_final.strftime('%Y-%m-%d') if data_final else '',
            'grafico_linha': {
                'datas': datas,
                'fretes': fretes
            },
            'grafico_pizza': dados_pizza
        }
        
        return render_template('relatorios/imprimir.html', 
                             resumo=resumo, 
                             now=datetime.now())
    except Exception as e:
        print(f"Erro ao gerar impressão: {str(e)}")
        flash('Erro ao gerar impressão', 'error')
        return redirect(url_for('relatorios.index'))
