from flask import Blueprint, jsonify, request, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Usuario, Mensagem

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def index():
    usuarios = Usuario.query.filter(Usuario.id != current_user.id).all()
    return render_template('chat/index.html', usuarios=usuarios)

@chat_bp.route('/mensagens_grupo')
@login_required
def mensagens_grupo():
    try:
        mensagens = (Mensagem.query
                    .filter_by(tipo='grupo')
                    .order_by(Mensagem.data_envio.desc())
                    .limit(100)
                    .all())
        
        return jsonify([{
            'id': m.id,
            'conteudo': m.conteudo,
            'data_envio': m.data_envio.strftime('%d/%m/%Y %H:%M'),
            'remetente': {
                'id': m.remetente.id,
                'nome': m.remetente.nome
            },
            'lida': m.lida
        } for m in mensagens])
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar mensagens do grupo: {str(e)}')
        return jsonify({'error': 'Erro ao buscar mensagens'}), 500

@chat_bp.route('/mensagens_individuais/<int:usuario_id>')
@login_required
def mensagens_individuais(usuario_id):
    try:
        mensagens = (Mensagem.query
                    .filter_by(tipo='individual')
                    .filter(
                        ((Mensagem.remetente_id == current_user.id) & (Mensagem.destinatario_id == usuario_id)) |
                        ((Mensagem.remetente_id == usuario_id) & (Mensagem.destinatario_id == current_user.id))
                    )
                    .order_by(Mensagem.data_envio.desc())
                    .limit(100)
                    .all())
        
        return jsonify([{
            'id': m.id,
            'conteudo': m.conteudo,
            'data_envio': m.data_envio.strftime('%d/%m/%Y %H:%M'),
            'remetente': {
                'id': m.remetente.id,
                'nome': m.remetente.nome
            },
            'destinatario': {
                'id': m.destinatario.id,
                'nome': m.destinatario.nome
            } if m.destinatario else None,
            'lida': m.lida
        } for m in mensagens])
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar mensagens individuais: {str(e)}')
        return jsonify({'error': 'Erro ao buscar mensagens'}), 500

@chat_bp.route('/enviar_mensagem', methods=['POST'])
@login_required
def enviar_mensagem():
    try:
        data = request.get_json()
        
        if not data or 'conteudo' not in data or 'tipo' not in data:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        mensagem = Mensagem(
            conteudo=data['conteudo'],
            tipo=data['tipo'],
            remetente_id=current_user.id,
            destinatario_id=data.get('destinatario_id'),
            data_envio=datetime.now(),
            lida=False
        )
        
        db.session.add(mensagem)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Mensagem enviada com sucesso'})
    except Exception as e:
        current_app.logger.error(f'Erro ao enviar mensagem: {str(e)}')
        return jsonify({'error': 'Erro ao enviar mensagem'}), 500

@chat_bp.route('/marcar_como_lida/<int:mensagem_id>', methods=['POST'])
@login_required
def marcar_como_lida(mensagem_id):
    try:
        mensagem = Mensagem.query.get(mensagem_id)
        if mensagem and mensagem.destinatario_id == current_user.id:
            mensagem.lida = True
            db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Erro ao marcar mensagem como lida: {str(e)}')
        return jsonify({'error': 'Erro ao marcar mensagem como lida'}), 500

@chat_bp.route('/mensagens_nao_lidas')
@login_required
def mensagens_nao_lidas():
    try:
        # Mensagens não lidas do grupo
        mensagens_grupo = (Mensagem.query
                         .filter_by(tipo='grupo', lida=False)
                         .filter(Mensagem.remetente_id != current_user.id)
                         .count())
        
        # Mensagens não lidas individuais
        mensagens_individuais = {}
        usuarios = Usuario.query.filter(Usuario.id != current_user.id).all()
        
        for usuario in usuarios:
            count = (Mensagem.query
                    .filter_by(
                        tipo='individual',
                        remetente_id=usuario.id,
                        destinatario_id=current_user.id,
                        lida=False
                    )
                    .count())
            if count > 0:
                mensagens_individuais[str(usuario.id)] = count
        
        return jsonify({
            'grupo': mensagens_grupo,
            'individuais': mensagens_individuais
        })
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar mensagens não lidas: {str(e)}')
        return jsonify({'error': 'Erro ao buscar mensagens não lidas'}), 500
