from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.solicitacao import Solicitacao
from models.carga import Carga, SubCarga
from models.documento import DocumentoCarga
from models.usuario import Usuario
from extensions import db
from datetime import datetime, timedelta
import traceback
from utils.email_notificador import notificar_solicitacao, notificar_analise_solicitacao, notificar_setor_responsavel, notificar_tarefa_concluida

solicitacoes_bp = Blueprint('solicitacoes', __name__)

def solicitacao_to_dict(solicitacao):
    return {
        'id': solicitacao.id,
        'carga_numero': solicitacao.carga.numero_carga,
        'tipo': solicitacao.tipo,
        'setor': solicitacao.setor,
        'motivo': solicitacao.motivo,
        'status': solicitacao.status,
        'criado_em': solicitacao.criado_em.strftime('%d/%m/%Y %H:%M'),
        'solicitado_por': solicitacao.solicitado_por.nome,
        'analisado_por': solicitacao.analisado_por.nome if solicitacao.analisado_por else None,
        'analisado_em': solicitacao.analisado_em.strftime('%d/%m/%Y %H:%M') if solicitacao.analisado_em else None,
        'observacao_analise': solicitacao.observacao_analise,
    }

@solicitacoes_bp.route('/')
@login_required
def index():
    """Página principal de solicitações"""
    solicitacoes = None
    if current_user.tipo not in ['gerente', 'admin']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
        
    solicitacoes = Solicitacao.query.order_by(Solicitacao.criado_em.desc()).all()
    solicitacoes_dict = [solicitacao_to_dict(s) for s in solicitacoes]
    
    # Buscar solicitações de exclusão de documentos
    solicitacoes_documentos = []
    solicitacoes_documentos = DocumentoCarga.query.filter_by(
        status_exclusao='pendente'
    ).join(
        Carga, DocumentoCarga.carga_id == Carga.id
    ).all()

    return render_template('solicitacoes/index.html', 
                         solicitacoes=solicitacoes,
                         solicitacoes_json=solicitacoes_dict,
                         solicitacoes_documentos=solicitacoes_documentos)

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
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados não fornecidos.'
            }), 400
            
        setor = data.get('setor')  # 'balanca', 'fechamento', 'producao'
        motivo = data.get('motivo')
        
        if not all([setor, motivo]):
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
            tipo='revisao',
            setor=setor,
            motivo=motivo,
            solicitado_por_id=current_user.id
        )
        
        db.session.add(solicitacao)
        db.session.commit()
        
        # Enviar email para os gerentes
        notificar_solicitacao(solicitacao)
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de revisão enviada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@solicitacoes_bp.route('/solicitar_exclusao/<int:carga_id>', methods=['POST'])
@login_required
def solicitar_exclusao(carga_id):
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados não fornecidos.'
            }), 400
            
        setor = data.get('setor')  # 'balanca', 'fechamento', 'producao'
        motivo = data.get('motivo')
        
        if not all([setor, motivo]):
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
            tipo='exclusao',
            setor=setor,
            motivo=motivo,
            solicitado_por_id=current_user.id
        )
        
        db.session.add(solicitacao)
        db.session.commit()
        
        # Enviar email para os gerentes
        notificar_solicitacao(solicitacao)
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de exclusão enviada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@solicitacoes_bp.route('/analisar_solicitacao/<int:id>', methods=['GET'])
@login_required
def visualizar_solicitacao(id):
    if current_user.tipo not in ['gerente', 'admin']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
        
    solicitacao = Solicitacao.query.get_or_404(id)
    return render_template('solicitacoes/analisar.html', solicitacao=solicitacao)

@solicitacoes_bp.route('/analisar_solicitacao/<int:id>', methods=['POST'])
@login_required
def analisar_solicitacao(id):
    if current_user.tipo not in ['gerente', 'admin']:
        return jsonify({
            'success': False,
            'message': 'Acesso negado.'
        }), 403
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados não fornecidos.'
            }), 400

        status = data.get('status')
        observacao = data.get('observacao', '')
        
        if not status or status not in ['aprovada', 'reprovada', 'rejeitada']:
            return jsonify({
                'success': False,
                'message': 'Status inválido.'
            }), 400
            
        # Padronizar o status se for "rejeitada"
        if status == 'rejeitada':
            status = 'reprovada'
            
        solicitacao = Solicitacao.query.get_or_404(id)
        
        # Se a solicitação já foi analisada
        if solicitacao.status != 'pendente':
            return jsonify({
                'success': False,
                'message': 'Esta solicitação já foi analisada.'
            }), 400

        # Se for uma solicitação de exclusão e foi aprovada
        if solicitacao.tipo == 'exclusao' and status == 'aprovada':
            carga = Carga.query.get(solicitacao.carga_id)
            if not carga:
                return jsonify({
                    'success': False,
                    'message': 'Carga não encontrada.'
                }), 404

            # Verificar se existem documentos pendentes
            documentos_pendentes = DocumentoCarga.query.filter_by(
                carga_id=carga.id,
                status_exclusao='pendente'
            ).count()

            if documentos_pendentes > 0:
                return jsonify({
                    'success': False,
                    'message': 'Existem solicitações de exclusão de documentos pendentes para esta carga.'
                }), 400

            try:
                # Primeiro excluímos todas as solicitações relacionadas à carga
                Solicitacao.query.filter(
                    Solicitacao.carga_id == carga.id,
                    Solicitacao.id != solicitacao.id
                ).delete()
                
                # Excluir documentos
                DocumentoCarga.query.filter_by(carga_id=carga.id).delete()
                
                # Excluir subcargas
                SubCarga.query.filter_by(carga_id=carga.id).delete()
                
                # Depois excluímos a carga
                db.session.delete(carga)
                
                # Salvar os dados da solicitação antes de excluí-la para enviar a notificação
                solicitante_id = solicitacao.solicitado_por_id
                solicitante = Usuario.query.get(solicitante_id)
                carga_numero = carga.numero_carga
                
                # Por fim, excluímos a solicitação atual
                db.session.delete(solicitacao)
                
                db.session.commit()
                
                # Enviar notificação de tarefa concluída ao solicitante
                # Como a solicitação foi excluída, criamos uma cópia temporária com os dados necessários
                solicitacao_temp = type('obj', (object,), {
                    'solicitado_por': solicitante,
                    'tipo': 'exclusao',
                    'carga_id': id,
                    'numero_carga': carga_numero
                })
                
                notificar_tarefa_concluida(solicitacao_temp, tipo_conclusao="excluída")
                
                return jsonify({
                    'success': True,
                    'message': 'Carga excluída com sucesso!'
                })
                
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao excluir carga: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Erro ao excluir carga: {str(e)}'
                }), 400

        # Atualizar a solicitação
        solicitacao.status = status
        solicitacao.observacao_analise = observacao
        solicitacao.analisado_por_id = current_user.id
        solicitacao.analisado_em = datetime.now()
        
        try:
            db.session.commit()
            
            # Enviar email para o solicitante informando sobre a análise
            notificar_analise_solicitacao(solicitacao)
            
            # Se a solicitação foi aprovada, enviar email para o setor responsável
            if status == 'aprovada':
                notificar_setor_responsavel(solicitacao)
            
            return jsonify({
                'success': True,
                'message': f'Solicitação {status} com sucesso!'
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar solicitação: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Erro ao atualizar solicitação: {str(e)}'
            }), 400
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao analisar solicitação: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao analisar solicitação: {str(e)}'
        }), 400

@solicitacoes_bp.route('/limpar_antigas', methods=['POST'])
@login_required
def limpar_antigas():
    """Limpa solicitações antigas que estão pendentes"""
    if current_user.tipo not in ['gerente', 'admin']:
        return jsonify({
            'success': False,
            'message': 'Acesso negado.'
        }), 403
        
    try:
        # Pegar todas as solicitações pendentes
        solicitacoes = Solicitacao.query.filter_by(status='pendente').all()
        
        count = 0
        for solicitacao in solicitacoes:
            solicitacao.status = 'reprovada'
            solicitacao.observacao_analise = 'Solicitação antiga reprovada automaticamente'
            solicitacao.analisado_por_id = current_user.id
            solicitacao.analisado_em = datetime.now()
            count += 1
            
            # Enviar email para o solicitante informando sobre a reprovação automática
            notificar_analise_solicitacao(solicitacao)
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{count} solicitações antigas foram reprovadas.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@solicitacoes_bp.route('/visualizar_carga/<int:solicitacao_id>')
@login_required
def visualizar_carga_solicitacao(solicitacao_id):
    solicitacao = Solicitacao.query.get_or_404(solicitacao_id)
    return redirect(url_for('cargas.visualizar_carga', id=solicitacao.carga_id))

@solicitacoes_bp.route('/relatorios')
@login_required
def relatorios():
    if current_user.tipo not in ['gerente', 'admin']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    # Obter todas as solicitações
    solicitacoes = Solicitacao.query.all()
    
    # Estatísticas por setor
    stats_setor = db.session.query(
        Solicitacao.setor,
        db.func.count(Solicitacao.id).label('total')
    ).group_by(Solicitacao.setor).all()
    stats_setor_dict = [{'setor': s[0], 'total': s[1]} for s in stats_setor]
    
    # Estatísticas por tipo
    stats_tipo = db.session.query(
        Solicitacao.tipo,
        db.func.count(Solicitacao.id).label('total')
    ).group_by(Solicitacao.tipo).all()
    stats_tipo_dict = [{'tipo': t[0], 'total': t[1]} for t in stats_tipo]
    
    # Estatísticas por solicitante
    stats_solicitante = db.session.query(
        Usuario.nome,
        db.func.count(Solicitacao.id).label('total')
    ).join(Usuario, Solicitacao.solicitado_por_id == Usuario.id)\
     .group_by(Usuario.nome)\
     .order_by(db.func.count(Solicitacao.id).desc())\
     .limit(10).all()
    stats_solicitante_dict = [{'nome': s[0], 'total': s[1]} for s in stats_solicitante]
    
    # Estatísticas por status
    stats_status = db.session.query(
        Solicitacao.status,
        db.func.count(Solicitacao.id).label('total')
    ).group_by(Solicitacao.status).all()
    stats_status_dict = [{'status': s[0], 'total': s[1]} for s in stats_status]
    
    # Estatísticas mensais (últimos 12 meses)
    hoje = datetime.now()
    stats_mensais = []
    for i in range(12):
        data_inicio = hoje.replace(day=1) - timedelta(days=30*i)
        data_fim = (data_inicio.replace(day=28) + timedelta(days=4)).replace(day=1)
        total = Solicitacao.query.filter(
            Solicitacao.criado_em >= data_inicio,
            Solicitacao.criado_em < data_fim
        ).count()
        stats_mensais.append({
            'mes': data_inicio.strftime('%Y-%m'),
            'total': total
        })
    
    return render_template(
        'solicitacoes/relatorios.html',
        stats_setor=stats_setor_dict,
        stats_tipo=stats_tipo_dict,
        stats_solicitante=stats_solicitante_dict,
        stats_status=stats_status_dict,
        stats_mensais=stats_mensais
    )

@solicitacoes_bp.route('/api/stats/filtradas', methods=['POST'])
@login_required
def get_stats_filtradas():
    data = request.json
    data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d') if data.get('data_inicio') else None
    data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d') if data.get('data_fim') else None
    setor = data.get('setor')
    tipo = data.get('tipo')
    
    query = Solicitacao.query
    
    if data_inicio:
        query = query.filter(Solicitacao.criado_em >= data_inicio)
    if data_fim:
        query = query.filter(Solicitacao.criado_em <= data_fim)
    if setor:
        query = query.filter(Solicitacao.setor == setor)
    if tipo:
        query = query.filter(Solicitacao.tipo == tipo)
        
    # Estatísticas filtradas
    stats_setor = db.session.query(
        Solicitacao.setor,
        db.func.count(Solicitacao.id).label('total')
    ).filter(Solicitacao.id.in_(query.with_entities(Solicitacao.id)))\
     .group_by(Solicitacao.setor).all()
    
    stats_tipo = db.session.query(
        Solicitacao.tipo,
        db.func.count(Solicitacao.id).label('total')
    ).filter(Solicitacao.id.in_(query.with_entities(Solicitacao.id)))\
     .group_by(Solicitacao.tipo).all()
    
    stats_solicitante = db.session.query(
        Usuario.nome,
        db.func.count(Solicitacao.id).label('total')
    ).join(Usuario, Solicitacao.solicitado_por_id == Usuario.id)\
     .filter(Solicitacao.id.in_(query.with_entities(Solicitacao.id)))\
     .group_by(Usuario.nome)\
     .order_by(db.func.count(Solicitacao.id).desc())\
     .limit(10).all()
    
    return jsonify({
        'stats_setor': [{'setor': s[0], 'total': s[1]} for s in stats_setor],
        'stats_tipo': [{'tipo': t[0], 'total': t[1]} for t in stats_tipo],
        'stats_solicitante': [{'nome': n[0], 'total': n[1]} for n in stats_solicitante]
    })
