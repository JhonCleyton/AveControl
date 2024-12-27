from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import Usuario, Notificacao, TipoUsuario
from extensions import db

notificacoes_bp = Blueprint('notificacoes', __name__, url_prefix='/notificacoes')

@notificacoes_bp.route('/nao_lidas')
@login_required
def get_notificacoes_nao_lidas():
    """Retorna notificações não lidas do usuário"""
    notificacoes = Notificacao.query.filter_by(
        usuario_id=current_user.id,
        lida=False
    ).order_by(Notificacao.data_criacao.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'tipo': n.tipo,
        'titulo': n.titulo,
        'mensagem': n.mensagem,
        'data_criacao': n.data_criacao.strftime('%d/%m/%Y %H:%M'),
        'exibir_popup': n.exibir_popup,
        'carga_id': n.carga_id
    } for n in notificacoes])

@notificacoes_bp.route('/marcar_como_lida/<int:id>', methods=['POST'])
@login_required
def marcar_como_lida(id):
    """Marca uma notificação como lida"""
    notificacao = Notificacao.query.get_or_404(id)
    
    if notificacao.usuario_id != current_user.id:
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    notificacao.lida = True
    db.session.commit()
    
    return jsonify({'success': True})

@notificacoes_bp.route('/marcar_todas_como_lidas', methods=['POST'])
@login_required
def marcar_todas_como_lidas():
    """Marca todas as notificações do usuário como lidas"""
    Notificacao.query.filter_by(
        usuario_id=current_user.id,
        lida=False
    ).update({'lida': True})
    
    db.session.commit()
    
    return jsonify({'success': True})

def notificar_nova_carga(carga):
    """Notifica usuários sobre nova carga"""
    # Notifica todos os usuários ativos
    usuarios = Usuario.query.filter_by(ativo=True).all()
    Notificacao.criar_notificacao_nova_carga(carga, usuarios)

def notificar_producao(carga):
    """Notifica gerentes sobre produção inserida"""
    gerentes = Usuario.query.filter_by(
        tipo=TipoUsuario.GERENTE,
        ativo=True
    ).all()
    Notificacao.criar_notificacao_producao(carga, gerentes)

def notificar_fechamento(carga):
    """Notifica gerentes sobre fechamento inserido"""
    gerentes = Usuario.query.filter_by(
        tipo=TipoUsuario.GERENTE,
        ativo=True
    ).all()
    Notificacao.criar_notificacao_fechamento(carga, gerentes)

def notificar_cargas_incompletas():
    """Notifica gerentes sobre cargas incompletas após 24h"""
    from datetime import datetime, timedelta
    from models import Carga
    
    # Busca cargas criadas há mais de 24h e incompletas
    limite = datetime.utcnow() - timedelta(hours=24)
    cargas_incompletas = Carga.query.filter(
        Carga.data_criacao <= limite,
        Carga.completa == False
    ).all()
    
    if cargas_incompletas:
        gerentes = Usuario.query.filter_by(
            tipo=TipoUsuario.GERENTE,
            ativo=True
        ).all()
        
        for carga in cargas_incompletas:
            Notificacao.criar_notificacao_carga_incompleta(carga, gerentes)
