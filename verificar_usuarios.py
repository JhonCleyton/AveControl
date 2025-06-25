"""
Script para verificar as configurações dos usuários gerentes no sistema.
"""
import sys
from os.path import dirname, abspath
import os

# Adicionar o diretório pai ao path para permitir importações
current_dir = dirname(abspath(__file__))
sys.path.append(current_dir)

from extensions import db, create_app

# Criar a aplicação
app = create_app()

# Este script precisa rodar dentro do contexto da aplicação Flask
with app.app_context():
    print('Usuários gerentes:')
    from models.usuario import Usuario
    gerentes = Usuario.query.filter_by(tipo='gerente').all()
    for g in gerentes:
        print(f'Nome: {g.nome}, Email: {g.email}, Notificações ativas: {g.notif_email}')
    
    print('\nUsuários admin:')
    admins = Usuario.query.filter_by(tipo='admin').all()
    for a in admins:
        print(f'Nome: {a.nome}, Email: {a.email}, Notificações ativas: {a.notif_email}')
