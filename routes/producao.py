from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Carga, Producao
from datetime import datetime

producao_bp = Blueprint('producao', __name__)

@producao_bp.route('/producao')
@login_required
def producao():
    return render_template('producao/producao.html')

@producao_bp.route('/novo', methods=['GET'])
@login_required
def novo_producao():
    return render_template('producao/nova_producao.html')

@producao_bp.route('/buscar_carga_producao/<numero_carga>')
@login_required
def buscar_carga_producao(numero_carga):
    carga = Carga.query.filter_by(numero_carga=numero_carga).first()
    
    if not carga:
        return jsonify({'success': False, 'message': 'Carga não encontrada'})
    
    # Verificar se já existe produção para esta carga
    if Producao.query.filter_by(carga_id=carga.id).first():
        return jsonify({'success': False, 'message': 'Esta carga já possui dados de produção'})
    
    return jsonify({
        'success': True,
        'carga': {
            'id': carga.id,
            'motorista': carga.motorista,
            'data_abate': carga.data_abate.strftime('%d/%m/%Y') if carga.data_abate else None
        }
    })

@producao_bp.route('/salvar', methods=['POST'])
@login_required
def salvar_producao():
    if current_user.tipo not in ['producao', 'gerente']:
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    try:
        numero_carga = request.form.get('numero_carga')
        carga = Carga.query.filter_by(numero_carga=numero_carga).first()
        
        if not carga:
            return jsonify({'success': False, 'message': 'Carga não encontrada'})
        
        # Verificar se já existe produção para esta carga
        if Producao.query.filter_by(carga_id=carga.id).first():
            return jsonify({'success': False, 'message': 'Esta carga já possui dados de produção'})
        
        producao = Producao(
            carga_id=carga.id,
            data_producao=datetime.strptime(request.form.get('data_producao'), '%Y-%m-%d').date(),
            
            # Contagem de Aves
            aves_granja=int(request.form.get('aves_granja')),
            aves_mortas=int(request.form.get('aves_mortas')),
            aves_recebidas=int(request.form.get('aves_recebidas')),
            aves_contador=int(request.form.get('aves_contador')),
            aves_por_caixa=int(request.form.get('aves_por_caixa')),
            
            # Avarias
            mortalidade_excesso=float(request.form.get('mortalidade_excesso')),
            aves_molhadas_granja=float(request.form.get('aves_molhadas_granja')),
            aves_molhadas_chuva=float(request.form.get('aves_molhadas_chuva')),
            quebra_maus_tratos=float(request.form.get('quebra_maus_tratos')),
            aves_papo_cheio=float(request.form.get('aves_papo_cheio')),
            outras_quebras=float(request.form.get('outras_quebras')),
            descricao_quebras=request.form.get('descricao_quebras'),
            total_avarias=float(request.form.get('total_avarias'))
        )
        
        db.session.add(producao)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Produção salva com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@producao_bp.route('/listar')
@login_required
def listar_producao():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    numero_carga = request.args.get('numero_carga')
    
    query = db.session.query(Producao, Carga.numero_carga)\
        .join(Carga, Producao.carga_id == Carga.id)
    
    if data_inicio:
        query = query.filter(Producao.data_producao >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Producao.data_producao <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    if numero_carga:
        query = query.filter(Carga.numero_carga.ilike(f'%{numero_carga}%'))
    
    resultados = query.all()
    
    producoes = []
    for producao, numero_carga in resultados:
        producoes.append({
            'id': producao.id,
            'data_producao': producao.data_producao.isoformat(),
            'numero_carga': numero_carga,
            
            # Contagem de Aves
            'aves_granja': producao.aves_granja,
            'aves_mortas': producao.aves_mortas,
            'aves_recebidas': producao.aves_recebidas,
            'aves_contador': producao.aves_contador,
            'aves_por_caixa': producao.aves_por_caixa,
            
            # Avarias
            'mortalidade_excesso': producao.mortalidade_excesso,
            'aves_molhadas_granja': producao.aves_molhadas_granja,
            'aves_molhadas_chuva': producao.aves_molhadas_chuva,
            'quebra_maus_tratos': producao.quebra_maus_tratos,
            'aves_papo_cheio': producao.aves_papo_cheio,
            'outras_quebras': producao.outras_quebras,
            'descricao_quebras': producao.descricao_quebras,
            'total_avarias': producao.total_avarias
        })
    
    return jsonify(producoes)
