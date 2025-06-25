from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Carga, Producao
from sqlalchemy import func
from datetime import datetime

bp_gerenciamento_produto = Blueprint('gerenciamento_produto', __name__)

@bp_gerenciamento_produto.route('/gerenciamento-produto', methods=['GET'])
@login_required
def gerenciamento_produto():
    # Filtros
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    produtor = request.args.get('produtor')
    query = db.session.query(Carga, Producao).join(Producao, Producao.carga_id == Carga.id)
    if data_inicio:
        query = query.filter(Carga.data_abate >= data_inicio)
    if data_fim:
        query = query.filter(Carga.data_abate <= data_fim)
    if produtor:
        query = query.filter(Carga.produtor == produtor)
    rows = query.all()
    # Processamento dos dados
    dados = []
    for carga, prod in rows:
        perdas = carga.peso_granja - carga.peso_frigorifico
        perdas_percent = (perdas / carga.peso_granja * 100) if carga.peso_granja else 0
        mortalidade_percent = (prod.aves_mortas / prod.aves_granja * 100) if prod.aves_granja else 0
        dados.append({
            'numero_carga': carga.numero_carga,
            'data_abate': carga.data_abate.strftime('%d/%m/%Y'),
            'produtor': carga.produtor,
            'peso_granja': carga.peso_granja,
            'peso_frigorifico': carga.peso_frigorifico,
            'perdas': perdas,
            'perdas_percent': perdas_percent,
            'mortalidade': prod.aves_mortas,
            'mortalidade_percent': mortalidade_percent,
            'aves_granja': prod.aves_granja,
            'aves_recebidas': prod.aves_recebidas,
            'aves_contador': prod.aves_contador
        })
    # KPIs
    total_granja = sum(d['peso_granja'] for d in dados)
    total_frigorifico = sum(d['peso_frigorifico'] for d in dados)
    total_perdas = total_granja - total_frigorifico
    total_mortalidade = sum(d['mortalidade'] for d in dados)
    total_aves_granja = sum(d['aves_granja'] for d in dados)
    return render_template('gerenciamento_produto.html', dados=dados,
                           total_granja=total_granja, total_frigorifico=total_frigorifico,
                           total_perdas=total_perdas, total_mortalidade=total_mortalidade,
                           total_aves_granja=total_aves_granja)
