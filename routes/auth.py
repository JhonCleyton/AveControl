from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, validators
from wtforms.validators import DataRequired, Email, EqualTo, Length
from models import Usuario, TipoUsuario
from extensions import db, mail
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Message
from functools import wraps

def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    msg = Message(
        'Redefinição de Senha - AveControl',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    
    msg.body = f'''Para redefinir sua senha, clique no link abaixo:

{reset_url}

Se você não solicitou esta redefinição de senha, ignore este e-mail e sua senha permanecerá inalterada.

Atenciosamente,
Equipe AveControl
'''
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Erro ao enviar e-mail de redefinição: {str(e)}')
        return False

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = kwargs.get('token')
        if not token:
            flash('Token de redefinição inválido ou expirado.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        user = Usuario.verify_reset_token(token)
        if user is None:
            flash('Token de redefinição inválido ou expirado.', 'danger')
            return redirect(url_for('auth.forgot_password'))
            
        return f(user, *args, **kwargs)
    return decorated_function

class LoginForm(FlaskForm):
    nome = StringField('Nome de Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    lembrar_me = BooleanField('Lembrar-me')

class ForgotPasswordForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    senha = PasswordField('Nova Senha', validators=[
        DataRequired(),
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres.'),
        validators.EqualTo('confirmar_senha', message='As senhas não conferem.')
    ])
    confirmar_senha = PasswordField('Confirmar Nova Senha')

auth = Blueprint('auth', __name__)

@auth.route('/')
@login_required
def index():
    return render_template('index.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(nome=form.nome.data).first()
        if usuario and usuario.check_senha(form.senha.data):
            if usuario.ativo:
                # Fazer login e definir sessão como permanente
                login_user(usuario, remember=True, duration=timedelta(days=30))
                session.permanent = True
                
                # Verificar e limpar URL de redirecionamento
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '' or not next_page.startswith('/'):
                    next_page = url_for('main.index')
                    
                # Registrar login bem-sucedido
                flash('Login realizado com sucesso!', 'success')
                return redirect(next_page)
            else:
                flash('Sua conta está inativa. Por favor, contate o administrador.', 'danger')
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth.route('/esqueci-minha-senha', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user:
            if send_reset_email(user):
                flash('Um e-mail com as instruções para redefinição de senha foi enviado para o endereço cadastrado.', 'info')
            else:
                flash('Ocorreu um erro ao enviar o e-mail de redefinição. Por favor, tente novamente mais tarde.', 'danger')
        else:
            flash('Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha.', 'info')
        
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html', form=form)

@auth.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
@token_required
def reset_password(user, token):
    if current_user.is_authenticated and current_user != user:
        logout_user()
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_senha(form.senha.data)
        user.reset_password_token = None
        user.reset_password_expires = None
        db.session.commit()
        
        flash('Sua senha foi redefinida com sucesso! Faça login com sua nova senha.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form, token=token)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/usuarios')
@login_required
def usuarios():
    if current_user.tipo != TipoUsuario.admin.value:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('auth.index'))
    
    usuarios = Usuario.query.all()
    return render_template('auth/usuarios.html', usuarios=usuarios)

@auth.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    if current_user.tipo != TipoUsuario.admin.value:
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
        
        usuario = Usuario(nome=nome, email=email, tipo=TipoUsuario(tipo).value.lower())
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('auth.usuarios'))
    
    return render_template('auth/novo_usuario.html')

@auth.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if current_user.tipo != TipoUsuario.admin.value:
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
        usuario.tipo = TipoUsuario(tipo).value
        usuario.ativo = ativo
        
        if senha:
            usuario.set_senha(senha)
        
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('auth.usuarios'))
    
    return render_template('auth/editar_usuario.html', usuario=usuario)
