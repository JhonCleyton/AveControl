from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Carga
from datetime import datetime, timedelta
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    try:
        # Obter data atual e início do mês
        hoje = datetime.now().date()
        inicio_mes = hoje.replace(day=1)
        
        # Consultas para estatísticas
        total_cargas = Carga.query.count()
        cargas_pendentes = Carga.query.filter_by(status='incompleta').count()
        cargas_hoje = Carga.query.filter(
            func.date(Carga.criado_em) == hoje
        ).count()
        cargas_mes = Carga.query.filter(
            func.date(Carga.criado_em) >= inicio_mes
        ).count()
        
        stats = {
            'total_cargas': total_cargas,
            'cargas_pendentes': cargas_pendentes,
            'cargas_hoje': cargas_hoje,
            'cargas_mes': cargas_mes
        }
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        print(f"Erro ao carregar dashboard: {str(e)}")
        # Em caso de erro, ainda renderiza a dashboard, mas com estatísticas zeradas
        stats = {
            'total_cargas': 0,
            'cargas_pendentes': 0,
            'cargas_hoje': 0,
            'cargas_mes': 0
        }
        return render_template('dashboard.html', stats=stats)
