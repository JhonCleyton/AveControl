from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Carga, Notificacao, Usuario
from datetime import datetime, timedelta
from sqlalchemy import func, desc

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
        ultimas_cargas = Carga.query.order_by(desc(Carga.criado_em)).limit(5).all()
        
        # Últimas 5 notificações do usuário
        notificacoes = Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=False
        ).order_by(desc(Notificacao.criado_em)).limit(5).all()
        
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
            'stats_status': stats_status,
            'ultimas_cargas': ultimas_cargas,
            'notificacoes': notificacoes,
            'usuarios_online': usuarios_online
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
            'stats_status': {
                'pendente': 0,
                'em_andamento': 0,
                'concluida': 0,
                'cancelada': 0
            },
            'ultimas_cargas': [],
            'notificacoes': [],
            'usuarios_online': 0
        }
        return render_template('dashboard.html', stats=stats)
