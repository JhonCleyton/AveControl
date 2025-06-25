from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models.carga import Carga, Fechamento
from models.custo_ave import CustoAve
from extensions import db
import pandas as pd
from io import BytesIO
from datetime import datetime
from sqlalchemy import func

bp = Blueprint('custo_aves', __name__)

@bp.route('/')
@login_required
def index():
    if current_user.tipo != 'fechamento':
        return render_template('error.html', message='Acesso não autorizado'), 403
    return render_template('custo_aves.html')

@bp.route('/api/test-auth')
@login_required
def test_auth():
    print(f"Teste de autenticação:")
    print(f"Usuário: {current_user.nome}")
    print(f"Tipo: {current_user.tipo}")
    print(f"ID: {current_user.id}")
    return jsonify({
        'nome': current_user.nome,
        'tipo': current_user.tipo,
        'id': current_user.id
    })

@bp.route('/api/custos')
@login_required
def get_custos():
    if current_user.tipo != 'fechamento':
        print(f"Acesso negado: usuário {current_user.nome} tem tipo {current_user.tipo}")
        return jsonify({'error': 'Acesso não autorizado'}), 403
        
    try:
        print(f"Usuário atual: {current_user.nome} (tipo: {current_user.tipo})")
        
        # Buscar todas as cargas, independente de terem fechamento ou não
        query = db.session.query(
            Carga.id,
            Carga.numero_carga,
            Carga.data_abate,
            Carga.valor_frete,
            func.coalesce(Fechamento.valor_total_1, 0).label('valor_total_1'),
            func.coalesce(Fechamento.valor_total_2, 0).label('valor_total_2'),
            func.coalesce(CustoAve.custo_carregamento, 0).label('custo_carregamento'),
            func.coalesce(CustoAve.comissao, 0).label('comissao')
        ).select_from(Carga).outerjoin(
            Fechamento, Carga.id == Fechamento.carga_id
        ).outerjoin(
            CustoAve, Carga.id == CustoAve.carga_id
        )

        # Aplicar filtros de data se fornecidos
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if data_inicio:
            query = query.filter(Carga.data_abate >= data_inicio)
        if data_fim:
            query = query.filter(Carga.data_abate <= data_fim)
            
        query = query.order_by(Carga.data_abate.desc())
        
        print("Query SQL:", str(query))
        
        result = query.all()
        print(f"Número de resultados: {len(result)}")
        
        custos = []
        for carga in result:
            valor_fechamento = carga.valor_total_1 + carga.valor_total_2
            valor_total = valor_fechamento + \
                         (carga.valor_frete or 0) + \
                         carga.custo_carregamento + \
                         carga.comissao
            
            item = {
                'id': carga.id,
                'numero_carga': carga.numero_carga,
                'data_abate': carga.data_abate.strftime('%Y-%m-%d') if carga.data_abate else None,
                'valor_fechamento': float(valor_fechamento),
                'valor_frete': float(carga.valor_frete or 0),
                'custo_carregamento': float(carga.custo_carregamento),
                'comissao': float(carga.comissao),
                'valor_total': float(valor_total)
            }
            custos.append(item)
        
        return jsonify(custos)
    except Exception as e:
        import traceback
        print(f"Erro: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/custos/<int:carga_id>', methods=['POST'])
@login_required
def update_custo(carga_id):
    if current_user.tipo != 'fechamento':
        return jsonify({'error': 'Acesso não autorizado'}), 403
        
    data = request.get_json()
    
    custo = CustoAve.query.filter_by(carga_id=carga_id).first()
    if not custo:
        custo = CustoAve(
            carga_id=carga_id,
            criado_por=current_user
        )
        db.session.add(custo)
    
    custo.custo_carregamento = data.get('custo_carregamento', 0)
    custo.comissao = data.get('comissao', 0)
    custo.atualizado_por = current_user
    
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/api/custos/export/excel')
@login_required
def export_excel():
    if current_user.tipo != 'fechamento':
        return jsonify({'error': 'Acesso não autorizado'}), 403
        
    # Atualizar a query para incluir todas as cargas
    query = db.session.query(
        Carga.id,
        Carga.numero_carga,
        Carga.data_abate,
        Carga.valor_frete,
        func.coalesce(Fechamento.valor_total_1, 0).label('valor_total_1'),
        func.coalesce(Fechamento.valor_total_2, 0).label('valor_total_2'),
        func.coalesce(CustoAve.custo_carregamento, 0).label('custo_carregamento'),
        func.coalesce(CustoAve.comissao, 0).label('comissao')
    ).select_from(Carga).outerjoin(
        Fechamento, Carga.id == Fechamento.carga_id
    ).outerjoin(
        CustoAve, Carga.id == CustoAve.carga_id
    )

    # Aplicar filtros de data se fornecidos
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    if data_inicio:
        query = query.filter(Carga.data_abate >= data_inicio)
    if data_fim:
        query = query.filter(Carga.data_abate <= data_fim)
        
    custos = query.order_by(Carga.data_abate.desc()).all()
    
    data = []
    for carga in custos:
        valor_fechamento = carga.valor_total_1 + carga.valor_total_2
        valor_total = valor_fechamento + \
                     (carga.valor_frete or 0) + \
                     carga.custo_carregamento + \
                     carga.comissao
        
        data.append({
            'Carga': carga.numero_carga,
            'Data de Abate': carga.data_abate.strftime('%d/%m/%Y') if carga.data_abate else '',
            'Preço da Ave': float(valor_fechamento),
            'Valor do Frete': float(carga.valor_frete or 0),
            'Custo do Carregamento': float(carga.custo_carregamento),
            'Comissão': float(carga.comissao),
            'Valor Total': float(valor_total)
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Custos', index=False)
    writer.close()
    
    output.seek(0)
    return output.getvalue(), {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': f'attachment; filename=custos_aves_{datetime.now().strftime("%Y%m%d")}.xlsx'
    }
