from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Carga, Notificacao, Usuario, Producao
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func, text, case, and_, desc, extract
from extensions import db

api = Blueprint('api', __name__)

@api.route('/dashboard/stats')
@login_required
def get_dashboard_stats():
    try:
        # Obter data atual e início do mês
        hoje = datetime.now().date()
        inicio_mes = hoje.replace(day=1)
        
        # Consultas para estatísticas básicas
        total_cargas = Carga.query.count()
        cargas_pendentes = Carga.query.filter_by(status=Carga.STATUS_PENDENTE).count()
        cargas_hoje = Carga.query.filter(
            func.date(Carga.criado_em) == hoje
        ).count()
        cargas_mes = Carga.query.filter(
            func.date(Carga.criado_em) >= inicio_mes
        ).count()
        
        # Estatísticas por status
        stats_status = {
            'pendente': Carga.query.filter_by(status=Carga.STATUS_PENDENTE).count(),
            'em_andamento': Carga.query.filter_by(status=Carga.STATUS_EM_ANDAMENTO).count(),
            'concluida': Carga.query.filter_by(status=Carga.STATUS_CONCLUIDA).count(),
            'cancelada': Carga.query.filter_by(status=Carga.STATUS_CANCELADA).count()
        }
        
        # Últimas 5 cargas
        ultimas_cargas = [{
            'numero_carga': carga.numero_carga,
            'status': carga.status,
            'criado_em': carga.criado_em.strftime('%d/%m/%Y %H:%M')
        } for carga in Carga.query.order_by(desc(Carga.criado_em)).limit(5).all()]
        
        # Últimas 5 notificações do usuário
        notificacoes = [{
            'mensagem': notif.mensagem,
            'criado_em': notif.criado_em.strftime('%d/%m/%Y %H:%M')
        } for notif in Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=False
        ).order_by(desc(Notificacao.criado_em)).limit(5).all()]
        
        # Usuários online (ativos nas últimas 24h)
        limite_online = datetime.now() - timedelta(hours=24)
        usuarios_online = Usuario.query.filter(
            Usuario.ultimo_acesso >= limite_online
        ).count()
        
        return jsonify({
            'total_cargas': total_cargas,
            'cargas_pendentes': cargas_pendentes,
            'cargas_hoje': cargas_hoje,
            'cargas_mes': cargas_mes,
            'stats_status': stats_status,
            'ultimas_cargas': ultimas_cargas,
            'notificacoes': notificacoes,
            'usuarios_online': usuarios_online
        })
    except Exception as e:
        print(f"Erro ao obter estatísticas do dashboard: {str(e)}")
        return jsonify({
            'error': 'Erro ao obter estatísticas'
        }), 500

@api.route('/dashboard/filtrado', methods=['GET'])
@login_required
def dashboard_filtrado():
    """
    Retorna os dados da dashboard filtrados por data.
    
    Args:
        data_inicial: Data inicial para filtro (formato YYYY-MM-DD)
        data_final: Data final para filtro (formato YYYY-MM-DD)
    
    Returns:
        JSON com todos os dados da dashboard filtrados pelo período
    """
    try:
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        
        # Validar que as datas são fornecidas e no formato correto
        if not data_inicial or not data_final:
            return jsonify({
                'success': False,
                'message': 'Datas inicial e final são obrigatórias'
            }), 400
        
        try:
            data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
            
            # Ajustar data final para incluir o dia inteiro
            data_final = data_final.replace(hour=23, minute=59, second=59)
            
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        # Estatísticas básicas filtradas por data
        total_cargas = Carga.query.filter(
            Carga.data_abate >= data_inicial,
            Carga.data_abate <= data_final
        ).count()
        
        cargas_pendentes = Carga.query.filter(
            Carga._status == Carga.STATUS_PENDENTE,
            Carga.data_abate >= data_inicial,
            Carga.data_abate <= data_final
        ).count()
        
        # Para cargas hoje, mantemos a data atual
        hoje = datetime.now().date()
        cargas_hoje = Carga.query.filter(
            func.date(Carga.criado_em) == hoje
        ).count()
        
        # Para cargas do mês, mantemos o mês atual
        inicio_mes = hoje.replace(day=1)
        cargas_mes = Carga.query.filter(
            func.date(Carga.criado_em) >= inicio_mes
        ).count()
        
        # Status das cargas filtrado por data
        status_counts = db.session.query(
            Carga._status, func.count(Carga.id)
        ).filter(
            Carga.data_abate >= data_inicial,
            Carga.data_abate <= data_final
        ).group_by(Carga._status).all()
        
        status_dict = {
            'pendente': 0,
            'em andamento': 0,
            'concluida': 0,
            'cancelada': 0,
            'incompleta': 0
        }
        
        for status, count in status_counts:
            if status:
                status_dict[status.lower()] = count
        
        # Top produtores filtrados por data
        top_produtores = (
            db.session.query(
                Carga.produtor,
                func.count(Carga.id).label('total_cargas'),
                func.sum(Carga.peso_frigorifico).label('total_peso')
            )
            .filter(Carga.produtor.isnot(None))
            .filter(Carga.produtor != '')
            .filter(Carga.data_abate >= data_inicial)
            .filter(Carga.data_abate <= data_final)
            .group_by(Carga.produtor)
            .order_by(func.count(Carga.id).desc())
            .limit(5)
            .all()
        )
        
        # Formatar dados dos produtores
        produtores_data = [{
            'nome': produtor,
            'total_cargas': total_cargas,
            'total_peso': float(total_peso) if total_peso else 0
        } for produtor, total_cargas, total_peso in top_produtores]
        
        # Estatísticas de produção filtradas por data
        producao_stats = db.session.query(
            func.sum(Producao.aves_recebidas).label('total_aves'),
            (func.sum(Producao.mortalidade_excesso) / func.sum(Carga.peso_frigorifico) * 100).label('media_mortalidade'),
            (func.sum(Producao.total_avarias) / func.sum(Carga.peso_frigorifico) * 100).label('media_avarias')
        ).join(
            Carga, Producao.carga_id == Carga.id
        ).filter(
            Carga.peso_frigorifico > 0,
            Carga.data_abate >= data_inicial,
            Carga.data_abate <= data_final
        ).first()
        
        # Tendência mensal filtrada (criar um intervalo entre as datas)
        tendencia = db.session.query(
            func.strftime('%Y-%m', Carga.data_abate).label('mes'),
            func.count(Carga.id).label('total')
        ).filter(
            Carga.data_abate >= data_inicial,
            Carga.data_abate <= data_final
        ).group_by(
            func.strftime('%Y-%m', Carga.data_abate)
        ).order_by('mes').all()
        
        # Converter para lista de dicionários e garantir que não há valores None
        tendencia_mensal = []
        for t in tendencia:
            if t.mes is not None:
                tendencia_mensal.append({'mes': t.mes, 'total': t.total or 0})
        
        # Se não houver dados de tendência, criar uma série vazia
        if not tendencia_mensal:
            # Criar uma lista de meses entre data_inicial e data_final
            meses = []
            atual = data_inicial
            while atual <= data_final:
                meses.append({'mes': atual.strftime('%Y-%m'), 'total': 0})
                # Avançar para o próximo mês
                if atual.month == 12:
                    atual = atual.replace(year=atual.year + 1, month=1)
                else:
                    atual = atual.replace(month=atual.month + 1)
            tendencia_mensal = meses

        # Preparar resposta, garantindo que todos os valores são serializáveis
        stats = {
            'total_cargas': total_cargas or 0,
            'cargas_pendentes': cargas_pendentes or 0,
            'cargas_hoje': cargas_hoje or 0,
            'cargas_mes': cargas_mes or 0,
            'status': status_dict,
            'top_produtores': produtores_data,
            'tendencia_mensal': tendencia_mensal,
            'producao': {
                'total_aves': int(producao_stats.total_aves or 0) if producao_stats and producao_stats.total_aves else 0,
                'media_mortalidade': float(producao_stats.media_mortalidade or 0) if producao_stats and producao_stats.media_mortalidade else 0,
                'media_avarias': float(producao_stats.media_avarias or 0) if producao_stats and producao_stats.media_avarias else 0
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except ValueError as e:
        print(f"Erro de valor ao filtrar dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro de formato: {str(e)}'
        }), 400
    except TypeError as e:
        print(f"Erro de tipo ao filtrar dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro de tipo de dado: {str(e)}'
        }), 400
    except Exception as e:
        print(f"Erro ao filtrar dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao filtrar dashboard: {str(e)}'
        }), 500

@api.route('/produtores/top', methods=['GET'])
def top_produtores():
    """
    Retorna os top produtores filtrados por data.
    
    Args:
        data_inicial: Data inicial para filtro (formato YYYY-MM-DD)
        data_final: Data final para filtro (formato YYYY-MM-DD)
    
    Returns:
        JSON com os top produtores ordenados por quantidade de cargas
    """
    try:
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        
        # Validar que as datas são fornecidas e no formato correto
        if not data_inicial or not data_final:
            return jsonify({
                'success': False,
                'message': 'Datas inicial e final são obrigatórias'
            }), 400
        
        try:
            data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
            
            # Ajustar data final para incluir o dia inteiro
            data_final = data_final.replace(hour=23, minute=59, second=59)
            
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        # Buscar top produtores por quantidade de cargas filtrados por data
        top_produtores = (
            Carga.query
            .with_entities(
                Carga.produtor,
                func.count(Carga.id).label('total_cargas'),
                func.sum(Carga.peso_frigorifico).label('total_peso')
            )
            .filter(Carga.produtor.isnot(None))
            .filter(Carga.produtor != '')  # Ignorar produtores vazios
            .filter(Carga.data_abate >= data_inicial)
            .filter(Carga.data_abate <= data_final)
            .group_by(Carga.produtor)
            .order_by(func.count(Carga.id).desc())
            .limit(5)
            .all()
        )
        
        # Formatar dados dos produtores para JSON
        produtores_data = [{
            'nome': produtor,
            'total_cargas': total_cargas,
            'total_peso': float(total_peso) if total_peso else 0
        } for produtor, total_cargas, total_peso in top_produtores]
        
        return jsonify({
            'success': True,
            'produtores': produtores_data
        })
        
    except Exception as e:
        print(f"Erro ao obter top produtores: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao obter top produtores: {str(e)}'
        }), 500
