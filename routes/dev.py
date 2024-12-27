from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, ConfiguracaoFormulario
from datetime import datetime

dev_bp = Blueprint('dev', __name__)

@dev_bp.route('/configuracoes')
@login_required
def configuracoes():
    if current_user.tipo != 'admin':
        flash('Acesso não autorizado', 'error')
        return redirect(url_for('index'))
    
    configuracoes = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
    return render_template('dev/configuracoes.html', configuracoes=configuracoes)

@dev_bp.route('/configuracoes/salvar', methods=['POST'])
@login_required
def salvar_configuracoes():
    if current_user.tipo != 'admin':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    try:
        data = request.json
        configuracoes = data.get('configuracoes', [])
        
        # Limpar configurações existentes
        ConfiguracaoFormulario.query.delete()
        
        # Adicionar novas configurações
        for ordem, config in enumerate(configuracoes, 1):
            nova_config = ConfiguracaoFormulario(
                nome_campo=config['nome_campo'],
                tipo_campo=config['tipo_campo'],
                obrigatorio=config['obrigatorio'],
                ordem=ordem,
                opcoes=config.get('opcoes', '')
            )
            db.session.add(nova_config)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Configurações salvas com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@dev_bp.route('/configuracoes/campo', methods=['POST'])
@login_required
def adicionar_campo():
    if current_user.tipo != 'admin':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    try:
        data = request.json
        ultima_config = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem.desc()).first()
        nova_ordem = (ultima_config.ordem + 1) if ultima_config else 1
        
        novo_campo = ConfiguracaoFormulario(
            nome_campo=data['nome_campo'],
            tipo_campo=data['tipo_campo'],
            obrigatorio=data.get('obrigatorio', False),
            ordem=nova_ordem,
            opcoes=data.get('opcoes', '')
        )
        db.session.add(novo_campo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Campo adicionado com sucesso',
            'campo': {
                'id': novo_campo.id,
                'nome_campo': novo_campo.nome_campo,
                'tipo_campo': novo_campo.tipo_campo,
                'obrigatorio': novo_campo.obrigatorio,
                'ordem': novo_campo.ordem,
                'opcoes': novo_campo.opcoes
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@dev_bp.route('/configuracoes/campo/<int:id>', methods=['DELETE'])
@login_required
def remover_campo(id):
    if current_user.tipo != 'admin':
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403
    
    try:
        campo = ConfiguracaoFormulario.query.get_or_404(id)
        db.session.delete(campo)
        db.session.commit()
        
        # Reordenar campos restantes
        campos = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
        for i, campo in enumerate(campos, 1):
            campo.ordem = i
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Campo removido com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@dev_bp.route('/formularios')
@login_required
def formularios():
    if current_user.tipo != 'admin':
        flash('Acesso não autorizado', 'error')
        return redirect(url_for('index'))
    
    campos = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
    return render_template('dev/formularios.html', campos=campos)
