from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def tipo_necessario(tipo):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.tipo != tipo:
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('auth.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Decoradores específicos para cada tipo de usuário
def permissao_gerente(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if current_user.tipo != 'gerente':
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def permissao_balanca(f):
    return tipo_necessario('balanca')(f)

def permissao_fechamento(f):
    return tipo_necessario('fechamento')(f)

def permissao_producao(f):
    return tipo_necessario('producao')(f)

def permissao_financeiro(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if current_user.tipo != 'financeiro':
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def permissao_diretoria(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if current_user.tipo != 'diretoria':
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def permissao_desenvolvedor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash('Acesso não autorizado', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def permissao_resumos(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo not in ['gerente', 'diretoria', 'transportadora', 'financeiro']:
            flash('Acesso não autorizado', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
