from flask import Blueprint, render_template, jsonify, request, current_app
from functools import wraps
import os
import logging
from backup_system import create_backup, restore_backup, list_backups
from flask_login import login_required, current_user

backup_bp = Blueprint('backup', __name__, url_prefix='/sistema')

def ajax_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Requisição não-AJAX não permitida'}), 400
            
        if not current_app.login_manager._login_disabled:
            try:
                if not current_user.is_authenticated:
                    return jsonify({'error': 'Autenticação necessária'}), 401
            except Exception as e:
                return jsonify({'error': str(e)}), 401
                
        return f(*args, **kwargs)
    return decorated_function

@backup_bp.route('/backup/central')
@login_required
def backup_central():
    """Página central de gerenciamento de backups"""
    try:
        backups = list_backups()
        return render_template('backup/central.html', backups=backups)
    except Exception as e:
        logging.error(f"Erro ao carregar página de backup: {e}")
        return render_template('backup/central.html', error=str(e), backups=[])

@backup_bp.route('/backup', methods=['POST'])
@ajax_login_required
def create_system_backup():
    """Cria um backup do sistema"""
    try:
        backup_name = create_backup()
        return jsonify({
            'message': 'Backup criado com sucesso!',
            'backup_name': backup_name
        })
    except Exception as e:
        logging.error(f"Erro ao criar backup: {e}")
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/restore', methods=['POST'])
@ajax_login_required
def restore_system_backup():
    """Restaura um backup do sistema"""
    try:
        backup_file = request.form.get('backup_file')
        tipo_restauracao = request.form.get('tipo_restauracao', 'completo')
        
        if not backup_file:
            return jsonify({'error': 'Nome do backup não fornecido'}), 400
            
        if tipo_restauracao not in ['completo', 'dados', 'sistema']:
            return jsonify({'error': 'Tipo de restauração inválido'}), 400
            
        restore_backup(backup_file, tipo_restauracao)
        return jsonify({'message': 'Backup restaurado com sucesso!'})
        
    except Exception as e:
        logging.error(f"Erro ao restaurar backup: {e}")
        return jsonify({'error': str(e)}), 500
