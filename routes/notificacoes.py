from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import Usuario, Notificacao, TipoUsuario, Carga
from extensions import db

notificacoes_bp = Blueprint('notificacoes', __name__, url_prefix='/notificacoes')

@notificacoes_bp.route('/listar')
@login_required
def listar():
    """Retorna notificações não lidas do usuário"""
    notificacoes = Notificacao.query.filter_by(
        usuario_id=current_user.id,
        lida=False
    ).order_by(Notificacao.data_criacao.desc()).all()
    
    return jsonify({
        'notificacoes': [{
            'id': n.id,
            'tipo': n.tipo,
            'titulo': n.titulo,
            'mensagem': n.mensagem,
            'data': n.data_criacao.strftime('%d/%m/%Y %H:%M'),
            'carga_id': n.carga_id
        } for n in notificacoes]
    })

@notificacoes_bp.route('/limpar_todas', methods=['POST'])
@login_required
def limpar_todas():
    """Marca todas as notificações do usuário como lidas"""
    Notificacao.query.filter_by(
        usuario_id=current_user.id,
        lida=False
    ).update({'lida': True})
    
    db.session.commit()
    
    return jsonify({'success': True})

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

@notificacoes_bp.route('/<int:id>/marcar_popup', methods=['POST'])
@login_required
def marcar_popup(id):
    notificacao = Notificacao.query.get_or_404(id)
    notificacao.popup_mostrado = True
    db.session.commit()
    return jsonify({'success': True})

def notificar_nova_carga(carga):
    # Notificar todos os usuários ativos
    usuarios = Usuario.query.filter_by(ativo=True).all()
    
    for usuario in usuarios:
        Notificacao.criar_notificacao(
            usuario_id=usuario.id,
            tipo='carga',
            titulo='Nova Carga Registrada',
            mensagem=f'Nova carga {carga.numero_carga} foi registrada.',
            carga_id=carga.id
        )

def notificar_producao(carga):
    gerentes = Usuario.query.filter_by(tipo='gerente', ativo=True).all()
    
    for gerente in gerentes:
        Notificacao.criar_notificacao(
            usuario_id=gerente.id,
            tipo='producao',
            titulo='Produção Registrada',
            mensagem=f'Produção da carga {carga.numero_carga} foi registrada.',
            carga_id=carga.id
        )

def notificar_fechamento(carga):
    gerentes = Usuario.query.filter_by(tipo='gerente', ativo=True).all()
    
    for gerente in gerentes:
        Notificacao.criar_notificacao(
            usuario_id=gerente.id,
            tipo='fechamento',
            titulo='Fechamento Registrado',
            mensagem=f'Fechamento da carga {carga.numero_carga} foi registrado.',
            carga_id=carga.id
        )

def notificar_cargas_incompletas():
    from datetime import timedelta
    
    # Buscar cargas incompletas com mais de 24h
    cargas_incompletas = Carga.query.filter(
        Carga.status == Carga.STATUS_INCOMPLETA,
        Carga.criado_em <= (datetime.now() - timedelta(hours=24))
    ).all()
    
    if not cargas_incompletas:
        return
    
    gerentes = Usuario.query.filter_by(tipo='gerente', ativo=True).all()
    
    for gerente in gerentes:
        for carga in cargas_incompletas:
            Notificacao.criar_notificacao(
                usuario_id=gerente.id,
                tipo='carga_incompleta',
                titulo='Carga Incompleta',
                mensagem=f'A carga {carga.numero_carga} está incompleta há mais de 24h.',
                carga_id=carga.id
            )
