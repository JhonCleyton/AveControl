from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def gerente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.tipo != 'gerente':
            flash('Acesso negado. Apenas gerentes podem acessar esta função.', 'danger')
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function
