from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Usuario
from werkzeug.security import check_password_hash

perfil = Blueprint('perfil', __name__)

@perfil.route('/perfil', methods=['GET'])
@login_required
def ver_perfil():
    return render_template('perfil/perfil.html', usuario=current_user)

@perfil.route('/perfil/atualizar', methods=['POST'])
@login_required
def atualizar_perfil():
    try:
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')

        # Validações básicas
        if not nome or not email:
            flash('Nome e email são obrigatórios', 'error')
            return redirect(url_for('perfil.ver_perfil'))

        # Se o usuário está tentando mudar a senha
        if senha_atual and nova_senha:
            if not check_password_hash(current_user.senha_hash, senha_atual):
                flash('Senha atual incorreta', 'error')
                return redirect(url_for('perfil.ver_perfil'))
            
            if nova_senha != confirmar_senha:
                flash('As senhas não coincidem', 'error')
                return redirect(url_for('perfil.ver_perfil'))
            
            current_user.set_senha(nova_senha)
            flash('Senha atualizada com sucesso', 'success')

        # Atualiza os dados básicos
        current_user.nome = nome
        current_user.email = email
        
        db.session.commit()
        flash('Perfil atualizado com sucesso', 'success')
        return redirect(url_for('perfil.ver_perfil'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {str(e)}', 'error')
        return redirect(url_for('perfil.ver_perfil'))
