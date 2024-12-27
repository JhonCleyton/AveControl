from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Usuario
from datetime import datetime, timezone
from utils import permissao_gerente
from werkzeug.security import generate_password_hash

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/')
@login_required
@permissao_gerente
def index():
    if current_user.tipo != 'gerente':
        flash('Acesso negado. Apenas gerentes podem acessar esta página.', 'danger')
        return redirect(url_for('index'))
        
    users = Usuario.query.all()
    return render_template('gerenciar_usuarios.html', users=users)

@usuarios_bp.route('/criar', methods=['POST'])
@login_required
@permissao_gerente
def criar_usuario():
    if current_user.tipo != 'gerente':
        return jsonify({'success': False, 'message': 'Acesso negado'})
        
    try:
        dados = request.get_json()
        
        # Verificar se o usuário já existe
        if Usuario.query.filter_by(nome=dados['username']).first():
            return jsonify({'success': False, 'message': 'Nome de usuário já existe.'})
        
        # Criar novo usuário
        usuario = Usuario(
            nome=dados['username'],
            email=dados['email'],
            tipo=dados['tipo'],
            ativo=True,
            data_criacao=datetime.now(timezone.utc)
        )
        usuario.set_senha(dados['password'])
        
        db.session.add(usuario)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuário criado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@usuarios_bp.route('/editar/<int:id>', methods=['POST'])
@login_required
@permissao_gerente
def editar_usuario(id):
    if current_user.tipo != 'gerente':
        return jsonify({'success': False, 'message': 'Acesso negado'})
        
    try:
        dados = request.get_json()
        usuario = Usuario.query.get_or_404(id)
        
        # Verificar se o nome de usuário já existe
        if dados['username'] != usuario.nome:
            existente = Usuario.query.filter_by(nome=dados['username']).first()
            if existente and existente.id != id:
                return jsonify({'success': False, 'message': 'Nome de usuário já existe.'})
        
        # Atualizar dados do usuário
        usuario.nome = dados['username']
        usuario.email = dados['email']
        usuario.tipo = dados['tipo']
        usuario.ativo = dados['ativo']
        
        if dados.get('password') and dados['password'].strip():
            usuario.senha_hash = generate_password_hash(dados['password'])
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@usuarios_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
@permissao_gerente
def excluir_usuario(id):
    if current_user.tipo != 'gerente':
        return jsonify({'success': False, 'message': 'Acesso negado'})
        
    try:
        usuario = Usuario.query.get_or_404(id)
        
        # Não permitir excluir o usuário gerente
        if usuario.nome == 'gerente':
            return jsonify({'success': False, 'message': 'Não é permitido excluir o usuário gerente.'})
        
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuário excluído com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
