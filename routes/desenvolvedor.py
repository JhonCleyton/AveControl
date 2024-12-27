from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, ConfiguracaoFormulario, Usuario
from datetime import datetime
import functools
from extensions import db

dev = Blueprint('dev', __name__)

def apenas_desenvolvedor(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'desenvolvedor':
            flash('Acesso restrito ao desenvolvedor.')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated_function

@dev.route('/configuracoes')
@login_required
@apenas_desenvolvedor
def configuracoes():
    return render_template('dev/configuracoes.html')

@dev.route('/formularios')
@login_required
@apenas_desenvolvedor
def formularios():
    campos = ConfiguracaoFormulario.query.order_by(ConfiguracaoFormulario.ordem).all()
    return render_template('dev/formularios.html', campos=campos)

@dev.route('/criar-campo', methods=['POST'])
@login_required
@apenas_desenvolvedor
def criar_campo():
    try:
        data = request.json
        campo = ConfiguracaoFormulario(
            nome_campo=data['nome_campo'],
            tipo_campo=data['tipo_campo'],
            obrigatorio=data.get('obrigatorio', False),
            ordem=data.get('ordem', 0),
            opcoes=data.get('opcoes')
        )
        db.session.add(campo)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Campo criado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
