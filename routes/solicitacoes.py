from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.solicitacao import Solicitacao
from models.carga import Carga
from extensions import db
from datetime import datetime

solicitacoes_bp = Blueprint('solicitacoes', __name__)

def solicitacao_to_dict(solicitacao):
    return {
        'id': solicitacao.id,
        'tipo': solicitacao.tipo,
        'setor': solicitacao.setor,
        'motivo': solicitacao.motivo,
        'status': solicitacao.status,
        'criado_em': solicitacao.criado_em.strftime('%d/%m/%Y %H:%M'),
        'solicitado_por': solicitacao.solicitado_por.nome,
        'analisado_por': solicitacao.analisado_por.nome if solicitacao.analisado_por else None,
        'analisado_em': solicitacao.analisado_em.strftime('%d/%m/%Y %H:%M') if solicitacao.analisado_em else None,
        'observacao_analise': solicitacao.observacao_analise,
        'carga': {
            'id': solicitacao.carga.id,
            'numero_carga': solicitacao.carga.numero_carga
        }
    }

@solicitacoes_bp.route('/')
@login_required
def index():
    if current_user.tipo not in ['gerente', 'admin']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
        
    solicitacoes = Solicitacao.query.order_by(Solicitacao.criado_em.desc()).all()
    solicitacoes_dict = [solicitacao_to_dict(s) for s in solicitacoes]
    return render_template('solicitacoes/listar_solicitacoes.html', solicitacoes=solicitacoes, solicitacoes_json=solicitacoes_dict)

@solicitacoes_bp.route('/solicitacoes')
@login_required
def listar_solicitacoes():
    if current_user.tipo not in ['gerente', 'admin']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
        
    solicitacoes = Solicitacao.query.order_by(Solicitacao.criado_em.desc()).all()
    solicitacoes_dict = [solicitacao_to_dict(s) for s in solicitacoes]
    return render_template('solicitacoes/listar_solicitacoes.html', solicitacoes=solicitacoes, solicitacoes_json=solicitacoes_dict)

@solicitacoes_bp.route('/minhas_solicitacoes')
@login_required
def minhas_solicitacoes():
    solicitacoes = Solicitacao.query.filter_by(solicitado_por_id=current_user.id)\
        .order_by(Solicitacao.criado_em.desc()).all()
    solicitacoes_dict = [solicitacao_to_dict(s) for s in solicitacoes]
    return render_template('solicitacoes/minhas_solicitacoes.html', solicitacoes=solicitacoes, solicitacoes_json=solicitacoes_dict)

@solicitacoes_bp.route('/solicitar_revisao/<int:carga_id>', methods=['POST'])
@login_required
def solicitar_revisao(carga_id):
    try:
        data = request.json
        tipo = data.get('tipo')  # 'revisao' ou 'exclusao'
        setor = data.get('setor')  # 'balanca', 'fechamento', 'producao'
        motivo = data.get('motivo')
        
        if not all([tipo, setor, motivo]):
            return jsonify({
                'success': False,
                'message': 'Todos os campos são obrigatórios.'
            }), 400
            
        # Verificar se já existe uma solicitação pendente para esta carga
        solicitacao_existente = Solicitacao.query.filter_by(
            carga_id=carga_id,
            status='pendente'
        ).first()
        
        if solicitacao_existente:
            return jsonify({
                'success': False,
                'message': 'Já existe uma solicitação pendente para esta carga.'
            }), 400
            
        solicitacao = Solicitacao(
            carga_id=carga_id,
            tipo=tipo,
            setor=setor,
            motivo=motivo,
            solicitado_por_id=current_user.id
        )
        
        db.session.add(solicitacao)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Solicitação enviada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@solicitacoes_bp.route('/analisar_solicitacao/<int:id>', methods=['POST'])
@login_required
def analisar_solicitacao(id):
    if current_user.tipo not in ['gerente', 'admin']:
        return jsonify({
            'success': False,
            'message': 'Acesso negado.'
        }), 403
        
    try:
        data = request.json
        status = data.get('status')  # 'aprovada' ou 'reprovada'
        observacao = data.get('observacao')
        
        if not status:
            return jsonify({
                'success': False,
                'message': 'Status é obrigatório.'
            }), 400
            
        solicitacao = Solicitacao.query.get_or_404(id)
        
        # Se a solicitação já foi analisada
        if solicitacao.status != 'pendente':
            return jsonify({
                'success': False,
                'message': 'Esta solicitação já foi analisada.'
            }), 400
            
        solicitacao.status = status
        solicitacao.analisado_por_id = current_user.id
        solicitacao.analisado_em = datetime.utcnow()
        solicitacao.observacao_analise = observacao
        
        # Se for uma solicitação de exclusão e foi aprovada
        if solicitacao.tipo == 'exclusao' and status == 'aprovada':
            carga = Carga.query.get(solicitacao.carga_id)
            if carga:
                db.session.delete(carga)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Solicitação analisada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
