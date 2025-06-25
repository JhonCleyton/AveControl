from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db
import markdown
import os

perfil_bp = Blueprint('perfil', __name__)

@perfil_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil_view():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        tema = request.form.get('tema')
        notif_email = 'notif_email' in request.form

        # Atualiza dados básicos
        current_user.nome = nome
        current_user.email = email
        current_user.tema = tema
        current_user.notif_email = notif_email

        # Verifica se há alteração de senha
        if senha_atual and nova_senha and confirmar_senha:
            if not current_user.check_senha(senha_atual):
                flash('Senha atual incorreta.', 'error')
                return redirect(url_for('perfil.perfil_view'))
            
            if nova_senha != confirmar_senha:
                flash('As senhas não coincidem.', 'error')
                return redirect(url_for('perfil.perfil_view'))
            
            current_user.set_senha(nova_senha)
            flash('Senha alterada com sucesso!', 'success')

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil.perfil_view'))

    # Carrega o manual específico do usuário
    manual_path = os.path.join(current_app.root_path, 'docs', 'manuais', f'manual_{current_user.tipo}.md')
    try:
        with open(manual_path, 'r', encoding='utf-8') as f:
            manual_content = markdown.markdown(f.read())
    except FileNotFoundError:
        manual_content = '<p>Manual não encontrado.</p>'

    # Carrega o fluxograma
    fluxograma_path = os.path.join(current_app.root_path, 'docs', 'fluxograma.md')
    try:
        with open(fluxograma_path, 'r', encoding='utf-8') as f:
            fluxograma_content = f.read()
    except FileNotFoundError:
        fluxograma_content = '<p>Fluxograma não encontrado.</p>'

    return render_template('perfil/perfil.html',
                         usuario=current_user,
                         manual_content=manual_content,
                         fluxograma_content=fluxograma_content)

@perfil_bp.route('/api/manual/<tipo>')
@login_required
def get_manual(tipo):
    """Retorna o conteúdo do manual para o tipo de usuário especificado"""
    manual_path = os.path.join(current_app.root_path, 'docs', 'manuais', f'manual_{tipo}.md')
    try:
        with open(manual_path, 'r', encoding='utf-8') as f:
            content = markdown.markdown(f.read())
            return content
    except FileNotFoundError:
        return '<p>Manual não encontrado.</p>', 404

@perfil_bp.route('/api/fluxograma')
@login_required
def get_fluxograma():
    """Retorna o conteúdo do fluxograma"""
    fluxograma_path = os.path.join(current_app.root_path, 'docs', 'fluxograma.md')
    try:
        with open(fluxograma_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return 'Fluxograma não encontrado.'
