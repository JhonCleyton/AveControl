from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Carga, Notificacao, Usuario, Producao
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from extensions import db
from dateutil.relativedelta import relativedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    try:
        # Obter data atual e início do mês
        hoje = datetime.now().date()
        inicio_mes = hoje.replace(day=1)
        
        # Consultas para estatísticas básicas
        total_cargas = Carga.query.count()
        cargas_pendentes = Carga.query.filter_by(_status=Carga.STATUS_PENDENTE).count()
        cargas_hoje = Carga.query.filter(
            func.date(Carga.criado_em) == hoje
        ).count()
        cargas_mes = Carga.query.filter(
            func.date(Carga.criado_em) >= inicio_mes
        ).count()
        
        # Obter contagem de cargas por status
        status_counts = db.session.query(Carga._status, func.count(Carga.id)).group_by(Carga._status).all()
        
        # Criar dicionário de status
        status_dict = {
            'pendente': 0,
            'em andamento': 0,
            'concluida': 0,
            'cancelada': 0,
            'incompleta': 0
        }
        
        # Preencher contagens
        for status, count in status_counts:
            if status:
                status_dict[status.lower()] = count
        
        # Buscar top produtores por quantidade de cargas
        top_produtores = (
            db.session.query(
                Carga.produtor,
                func.count(Carga.id).label('total_cargas'),
                func.sum(Carga.peso_frigorifico).label('total_peso')
            )
            .filter(Carga.produtor.isnot(None))
            .filter(Carga.produtor != '')  # Ignorar produtores vazios
            .group_by(Carga.produtor)
            .order_by(func.count(Carga.id).desc())
            .limit(5)
            .all()
        )
        
        # Formatar dados dos produtores
        produtores_data = [{
            'nome': produtor,
            'total_cargas': total_cargas,  # Corrigido: usar o total_cargas da query
            'total_peso': float(total_peso) if total_peso else 0
        } for produtor, total_cargas, total_peso in top_produtores]
        
        # Log para debug dos produtores
        print("Dados dos produtores:")
        for produtor in produtores_data:
            print(f"Nome: {produtor['nome']}, Cargas: {produtor['total_cargas']}, Peso: {produtor['total_peso']}")
        
        # Log para debug
        print("Total de cargas:", total_cargas)
        print("Status das cargas:", status_dict)
        # Verificar cargas com status diferentes dos esperados
        outros_status = Carga.query.filter(~Carga._status.in_([
            Carga.STATUS_PENDENTE,
            Carga.STATUS_EM_ANDAMENTO,
            Carga.STATUS_CONCLUIDA,
            Carga.STATUS_CANCELADA,
            Carga.STATUS_INCOMPLETA
        ])).all()
        if outros_status:
            print("Cargas com status diferentes dos esperados:")
            for carga in outros_status:
                print(f"Carga {carga.numero_carga}: status='{carga._status}'")
        
        # Top transportadoras
        top_transportadoras = db.session.query(
            Carga.transportadora.label('nome'),
            func.count(Carga.id).label('total')
        ).group_by(Carga.transportadora).order_by(func.count(Carga.id).desc()).limit(5).all()
        
        top_transportadoras = [{'nome': t.nome, 'total': t.total} for t in top_transportadoras]
        
        # Últimas 5 cargas
        ultimas_cargas = Carga.query.order_by(desc(Carga.criado_em)).limit(5).all()
        
        # Estatísticas de produção
        producao_stats = db.session.query(
            func.sum(Producao.aves_recebidas).label('total_aves'),
            (func.sum(Producao.mortalidade_excesso) / func.sum(Carga.peso_frigorifico) * 100).label('media_mortalidade'),
            (func.sum(Producao.total_avarias) / func.sum(Carga.peso_frigorifico) * 100).label('media_avarias')
        ).join(
            Carga, Producao.carga_id == Carga.id
        ).filter(
            Carga.peso_frigorifico > 0  # Apenas cargas com peso do frigorífico registrado
        ).first()
        
        # Tendência mensal (últimos 6 meses)
        data_inicio = hoje - relativedelta(months=5)
        tendencia = db.session.query(
            func.strftime('%Y-%m', Carga.criado_em).label('mes'),
            func.count(Carga.id).label('total')
        ).filter(
            Carga.criado_em >= data_inicio
        ).group_by(
            func.strftime('%Y-%m', Carga.criado_em)
        ).order_by('mes').all()
        
        tendencia_mensal = [{'mes': t.mes, 'total': t.total} for t in tendencia]
        
        # Últimas 5 notificações do usuário
        notificacoes = Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=False
        ).order_by(desc(Notificacao.data_criacao)).limit(5).all()
        
        # Usuários online (ativos nas últimas 24h)
        limite_online = datetime.now() - timedelta(hours=24)
        usuarios_online = Usuario.query.filter(
            Usuario.ultimo_acesso >= limite_online
        ).count()
        
        stats = {
            'total_cargas': total_cargas,
            'cargas_pendentes': cargas_pendentes,
            'cargas_hoje': cargas_hoje,
            'cargas_mes': cargas_mes,
            'status': status_dict,
            'ultimas_cargas': [
                {
                    'numero': c.numero_carga,
                    'tipo_ave': c.tipo_ave,
                    'quantidade_cargas': c.quantidade_cargas,
                    'transportadora': c.transportadora,
                    '_status': c._status,
                    'criado_em': c.criado_em
                } for c in ultimas_cargas
            ],
            'top_transportadoras': top_transportadoras,
            'notificacoes': notificacoes,
            'usuarios_online': usuarios_online,
            'tendencia_mensal': tendencia_mensal,
            'top_produtores': produtores_data,
            'producao': {
                'total_aves': producao_stats.total_aves or 0,
                'media_mortalidade': float(producao_stats.media_mortalidade or 0),
                'media_avarias': float(producao_stats.media_avarias or 0)
            } if producao_stats else {
                'total_aves': 0,
                'media_mortalidade': 0,
                'media_avarias': 0
            }
        }
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        print(f"Erro ao carregar dashboard: {str(e)}")
        # Em caso de erro, ainda renderiza a dashboard, mas com estatísticas zeradas
        stats = {
            'total_cargas': 0,
            'cargas_pendentes': 0,
            'cargas_hoje': 0,
            'cargas_mes': 0,
            'status': {
                'pendente': 0,
                'em andamento': 0,
                'concluida': 0,
                'cancelada': 0,
                'incompleta': 0
            },
            'ultimas_cargas': [],
            'top_transportadoras': [],
            'notificacoes': [],
            'usuarios_online': 0,
            'tendencia_mensal': [],
            'top_produtores': [],
            'producao': {
                'total_aves': 0,
                'media_mortalidade': 0,
                'media_avarias': 0
            }
        }
        return render_template('dashboard.html', stats=stats, error=str(e))
