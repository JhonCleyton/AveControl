from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired
from models import Usuario
from extensions import db
from urllib.parse import urlparse

class LoginForm(FlaskForm):
    nome = StringField('Nome de Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    lembrar_me = BooleanField('Lembrar-me')

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(nome=form.nome.data).first()
        if usuario and usuario.check_senha(form.senha.data):
            if usuario.ativo:
                login_user(usuario, remember=form.lembrar_me.data)
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('main.index')
                return redirect(next_page)
            else:
                flash('Sua conta está inativa. Por favor, contate o administrador.', 'danger')
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/usuarios')
@login_required
def usuarios():
    if current_user.tipo != 'admin':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('auth.index'))
    
    usuarios = Usuario.query.all()
    return render_template('auth/usuarios.html', usuarios=usuarios)

@auth_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    if current_user.tipo != 'admin':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        tipo = request.form.get('tipo')
        
        if Usuario.query.filter_by(nome=nome).first():
            flash('Nome de usuário já existe.', 'danger')
            return redirect(url_for('auth.novo_usuario'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Email já está em uso.', 'danger')
            return redirect(url_for('auth.novo_usuario'))
        
        usuario = Usuario(nome=nome, email=email, tipo=tipo)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('auth.usuarios'))
    
    return render_template('auth/novo_usuario.html')

@auth_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if current_user.tipo != 'admin':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('auth.index'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        tipo = request.form.get('tipo')
        ativo = request.form.get('ativo') == 'on'
        senha = request.form.get('senha')
        
        usuario_existente = Usuario.query.filter_by(nome=nome).first()
        if usuario_existente and usuario_existente.id != id:
            flash('Nome de usuário já existe.', 'danger')
            return redirect(url_for('auth.editar_usuario', id=id))
        
        email_existente = Usuario.query.filter_by(email=email).first()
        if email_existente and email_existente.id != id:
            flash('Email já está em uso.', 'danger')
            return redirect(url_for('auth.editar_usuario', id=id))
        
        usuario.nome = nome
        usuario.email = email
        usuario.tipo = tipo
        usuario.ativo = ativo
        
        if senha:
            usuario.set_senha(senha)
        
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('auth.usuarios'))
    
    return render_template('auth/editar_usuario.html', usuario=usuario)
