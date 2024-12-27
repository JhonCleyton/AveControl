from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, ConfiguracaoFormulario, Carga
from datetime import datetime
from utils import permissao_desenvolvedor

dev_bp = Blueprint('dev', __name__)

@dev_bp.route('/configuracoes')
@login_required
@permissao_desenvolvedor
def configuracoes():
    configuracoes = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
    return render_template('dev/configuracoes.html', configuracoes=configuracoes)

@dev_bp.route('/configuracoes/salvar', methods=['POST'])
@login_required
@permissao_desenvolvedor
def salvar_configuracoes():
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
@permissao_desenvolvedor
def adicionar_campo():
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
@permissao_desenvolvedor
def remover_campo(id):
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

@dev_bp.route('/atualizar_status', methods=['POST'])
@login_required
@permissao_desenvolvedor
def atualizar_status():
    try:
        if Carga.atualizar_status_cargas():
            flash('Status das cargas atualizado com sucesso!', 'success')
        else:
            flash('Erro ao atualizar status das cargas.', 'danger')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'danger')
    
    return redirect(url_for('dev.configuracoes'))

@dev_bp.route('/formularios')
@login_required
@permissao_desenvolvedor
def formularios():
    campos = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
    return render_template('dev/formularios.html', campos=campos)
