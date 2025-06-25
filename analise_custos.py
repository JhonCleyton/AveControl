from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models.carga import Carga, Fechamento
from models.custo_ave import CustoAve
from extensions import db
from sqlalchemy import func, text
from datetime import datetime, timedelta

bp = Blueprint('analise_custos', __name__)

@bp.route('/')
@login_required
def index():
    if current_user.tipo not in ['gerente', 'diretoria']:
        return render_template('error.html', message='Acesso não autorizado'), 403
    return render_template('analise_custos.html')

def get_filter_dates():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    try:
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    except ValueError:
        return None, None
        
    return data_inicio, data_fim

@bp.route('/api/metricas-gerais')
@login_required
def get_metricas_gerais():
    if current_user.tipo not in ['gerente', 'diretoria']:
        return jsonify({'error': 'Acesso não autorizado'}), 403

    try:
        data_inicio, data_fim = get_filter_dates()
        
        if data_inicio and data_fim:
            periodo_atual = [data_inicio, data_fim]
            dias_periodo = (data_fim - data_inicio).days
            data_inicio_anterior = data_inicio - timedelta(days=dias_periodo)
            data_fim_anterior = data_inicio - timedelta(days=1)
            periodo_anterior = [data_inicio_anterior, data_fim_anterior]
        else:
            hoje = datetime.now().date()
            inicio_mes = hoje.replace(day=1)
            inicio_mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
            periodo_atual = [inicio_mes, hoje]
            periodo_anterior = [inicio_mes_anterior, inicio_mes - timedelta(days=1)]

        # Métricas do período atual
        metricas_atual = db.session.query(
            func.count(Carga.id).label('total_cargas'),
            func.sum(Carga.valor_frete).label('total_frete'),
            func.sum(Carga.km_rodados).label('total_km'),
            func.sum(CustoAve.custo_carregamento).label('total_carregamento'),
            func.sum(CustoAve.comissao).label('total_comissao'),
            func.sum(
                func.coalesce(Fechamento.valor_total_1, 0) + 
                func.coalesce(Fechamento.valor_total_2, 0)
            ).label('total_fechamento')
        ).select_from(Carga).outerjoin(
            CustoAve
        ).outerjoin(
            Fechamento
        ).filter(
            Carga.data_abate >= periodo_atual[0],
            Carga.data_abate <= periodo_atual[1]
        ).first()

        # Métricas do período anterior para comparação
        metricas_anterior = db.session.query(
            func.count(Carga.id).label('total_cargas'),
            func.sum(Carga.valor_frete).label('total_frete'),
            func.sum(Carga.km_rodados).label('total_km'),
            func.sum(CustoAve.custo_carregamento).label('total_carregamento'),
            func.sum(CustoAve.comissao).label('total_comissao'),
            func.sum(
                func.coalesce(Fechamento.valor_total_1, 0) + 
                func.coalesce(Fechamento.valor_total_2, 0)
            ).label('total_fechamento')
        ).select_from(Carga).outerjoin(
            CustoAve
        ).outerjoin(
            Fechamento
        ).filter(
            Carga.data_abate >= periodo_anterior[0],
            Carga.data_abate <= periodo_anterior[1]
        ).first()

        return jsonify({
            'dados': {
                'mes_atual': {
                    'total_cargas': metricas_atual.total_cargas or 0,
                    'total_frete': float(metricas_atual.total_frete or 0),
                    'total_km': float(metricas_atual.total_km or 0),
                    'total_carregamento': float(metricas_atual.total_carregamento or 0),
                    'total_comissao': float(metricas_atual.total_comissao or 0),
                    'total_fechamento': float(metricas_atual.total_fechamento or 0),
                    'custo_medio_km': float(metricas_atual.total_frete or 0) / float(metricas_atual.total_km or 1)
                },
                'mes_anterior': {
                    'total_cargas': metricas_anterior.total_cargas or 0,
                    'total_frete': float(metricas_anterior.total_frete or 0),
                    'total_km': float(metricas_anterior.total_km or 0),
                    'total_carregamento': float(metricas_anterior.total_carregamento or 0),
                    'total_comissao': float(metricas_anterior.total_comissao or 0),
                    'total_fechamento': float(metricas_anterior.total_fechamento or 0),
                    'custo_medio_km': float(metricas_anterior.total_frete or 0) / float(metricas_anterior.total_km or 1)
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/tendencias-mensais')
@login_required
def get_tendencias_mensais():
    if current_user.tipo not in ['gerente', 'diretoria']:
        return jsonify({'error': 'Acesso não autorizado'}), 403

    try:
        data_inicio, data_fim = get_filter_dates()
        
        if not data_inicio:
            hoje = datetime.now().date()
            data_inicio = hoje - timedelta(days=180)
            data_fim = hoje

        # Agregação mensal de métricas usando strftime para SQLite
        resultados = db.session.query(
            func.strftime('%Y', Carga.data_abate).label('ano'),
            func.strftime('%m', Carga.data_abate).label('mes'),
            func.count(Carga.id).label('total_cargas'),
            func.sum(Carga.valor_frete).label('total_frete'),
            func.sum(Carga.km_rodados).label('total_km'),
            func.sum(CustoAve.custo_carregamento).label('total_carregamento'),
            func.sum(CustoAve.comissao).label('total_comissao'),
            func.sum(
                func.coalesce(Fechamento.valor_total_1, 0) + 
                func.coalesce(Fechamento.valor_total_2, 0)
            ).label('total_fechamento')
        ).select_from(Carga).outerjoin(
            CustoAve
        ).outerjoin(
            Fechamento
        ).filter(
            Carga.data_abate >= data_inicio,
            Carga.data_abate <= data_fim
        ).group_by(
            func.strftime('%Y', Carga.data_abate),
            func.strftime('%m', Carga.data_abate)
        ).order_by(
            func.strftime('%Y', Carga.data_abate),
            func.strftime('%m', Carga.data_abate)
        ).all()

        dados_mensais = []
        for r in resultados:
            mes_str = f"{r.ano}-{r.mes}"
            dados_mensais.append({
                'mes': mes_str,
                'total_cargas': r.total_cargas or 0,
                'total_frete': float(r.total_frete or 0),
                'total_km': float(r.total_km or 0),
                'total_carregamento': float(r.total_carregamento or 0),
                'total_comissao': float(r.total_comissao or 0),
                'total_fechamento': float(r.total_fechamento or 0),
                'custo_medio_km': float(r.total_frete or 0) / float(r.total_km or 1)
            })

        return jsonify({'dados': dados_mensais})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/distribuicao-custos')
@login_required
def get_distribuicao_custos():
    if current_user.tipo not in ['gerente', 'diretoria']:
        return jsonify({'error': 'Acesso não autorizado'}), 403

    try:
        data_inicio, data_fim = get_filter_dates()
        
        if not data_inicio:
            hoje = datetime.now().date()
            data_inicio = hoje.replace(day=1)
            data_fim = hoje

        # Distribuição dos custos por carga no período selecionado
        cargas = db.session.query(
            Carga.id,
            Carga.numero_carga,
            Carga.valor_frete,
            Carga.km_rodados,
            CustoAve.custo_carregamento,
            CustoAve.comissao,
            (func.coalesce(Fechamento.valor_total_1, 0) + 
             func.coalesce(Fechamento.valor_total_2, 0)).label('valor_fechamento')
        ).select_from(Carga).outerjoin(
            CustoAve
        ).outerjoin(
            Fechamento
        ).filter(
            Carga.data_abate >= data_inicio,
            Carga.data_abate <= data_fim
        ).all()

        distribuicao = []
        for c in cargas:
            total = (float(c.valor_frete or 0) + 
                    float(c.custo_carregamento or 0) + 
                    float(c.comissao or 0))
            
            if total > 0:
                distribuicao.append({
                    'numero_carga': c.numero_carga,
                    'percentual_frete': (float(c.valor_frete or 0) / total) * 100,
                    'percentual_carregamento': (float(c.custo_carregamento or 0) / total) * 100,
                    'percentual_comissao': (float(c.comissao or 0) / total) * 100,
                    'custo_por_km': float(c.valor_frete or 0) / float(c.km_rodados or 1),
                    'valor_fechamento': float(c.valor_fechamento or 0)
                })

        return jsonify({'dados': distribuicao})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
