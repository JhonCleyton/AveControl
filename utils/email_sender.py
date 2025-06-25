from flask import current_app
from flask_mail import Message, Mail
from models.usuario import Usuario
from extensions import db

mail = Mail()

def init_app(app):
    """Inicializa a extensão de email com a aplicação Flask"""
    mail.init_app(app)

def enviar_email(destinatarios, assunto, corpo_html, remetente=None):
    """
    Envia um email para os destinatários especificados.
    
    Args:
        destinatarios (list): Lista de endereços de email dos destinatários
        assunto (str): Assunto do email
        corpo_html (str): Corpo do email em formato HTML
        remetente (str, optional): Email do remetente. Se não fornecido, usa o configurado na aplicação.
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    try:
        if not destinatarios:
            current_app.logger.warning("Tentativa de enviar email sem destinatários")
            return False
            
        # Remover emails vazios ou inválidos
        destinatarios = [email for email in destinatarios if email and '@' in email]
        if not destinatarios:
            current_app.logger.warning("Nenhum destinatário válido para envio de email")
            return False
            
        sender = remetente or current_app.config['MAIL_DEFAULT_SENDER']
        msg = Message(assunto, 
                      sender=sender,
                      recipients=destinatarios)
        msg.html = corpo_html
        
        # Log das configurações de email para debug
        current_app.logger.info(f"Tentando enviar email com as seguintes configurações:")
        current_app.logger.info(f"MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}")
        current_app.logger.info(f"MAIL_PORT: {current_app.config.get('MAIL_PORT')}")
        current_app.logger.info(f"MAIL_USE_TLS: {current_app.config.get('MAIL_USE_TLS')}")
        current_app.logger.info(f"MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}")
        current_app.logger.info(f"Destinatários: {destinatarios}")
        
        mail.send(msg)
        current_app.logger.info(f"Email enviado com sucesso para {', '.join(destinatarios)}")
        return True
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar email: {str(e)}")
        # Detalhar o erro para melhor diagnóstico
        import traceback
        current_app.logger.error(f"Detalhes do erro: {traceback.format_exc()}")
        return False

def notificar_solicitacao(solicitacao):
    """
    Envia email de notificação sobre uma nova solicitação para os gerentes.
    
    Args:
        solicitacao: Objeto da classe Solicitacao
    """
    # Buscar todos os gerentes com notificações por email ativadas
    gerentes = Usuario.query.filter_by(
        tipo='gerente', 
        ativo=True,
        notif_email=True
    ).all()
    
    if not gerentes:
        return False
        
    destinatarios = [g.email for g in gerentes if g.email]
    
    # Tipos de solicitação em português
    tipos = {
        'revisao': 'revisão',
        'edicao': 'edição',
        'exclusao': 'exclusão'
    }
    
    tipo_pt = tipos.get(solicitacao.tipo, solicitacao.tipo)
    
    assunto = f'Nova solicitação de {tipo_pt} - Carga {solicitacao.carga.numero_carga}'
    
    corpo_html = f"""
    <h2>Nova solicitação de {tipo_pt}</h2>
    <p>Foi registrada uma nova solicitação no sistema AveControl:</p>
    <ul>
        <li><strong>Carga:</strong> {solicitacao.carga.numero_carga}</li>
        <li><strong>Tipo:</strong> {tipo_pt}</li>
        <li><strong>Setor:</strong> {solicitacao.setor}</li>
        <li><strong>Solicitante:</strong> {solicitacao.solicitado_por.nome}</li>
        <li><strong>Motivo:</strong> {solicitacao.motivo}</li>
        <li><strong>Data:</strong> {solicitacao.criado_em.strftime('%d/%m/%Y %H:%M')}</li>
    </ul>
    <p>Acesse o <a href="{current_app.config.get('APP_URL', '')}/solicitacoes">painel de solicitações</a> para analisar esta solicitação.</p>
    """
    
    return enviar_email(destinatarios, assunto, corpo_html)

def notificar_analise_solicitacao(solicitacao):
    """
    Envia email de notificação ao solicitante sobre a análise de sua solicitação.
    
    Args:
        solicitacao: Objeto da classe Solicitacao
    """
    # Verificar se o solicitante tem notificações por email ativadas
    solicitante = solicitacao.solicitado_por
    if not solicitante or not solicitante.notif_email or not solicitante.email:
        return False
    
    destinatarios = [solicitante.email]
    
    # Tipos de solicitação em português
    tipos = {
        'revisao': 'revisão',
        'edicao': 'edição',
        'exclusao': 'exclusão'
    }
    
    tipo_pt = tipos.get(solicitacao.tipo, solicitacao.tipo)
    
    # Status em português
    status = {
        'aprovada': 'aprovada',
        'rejeitada': 'rejeitada'
    }
    
    status_pt = status.get(solicitacao.status, solicitacao.status)
    
    assunto = f'Solicitação de {tipo_pt} {status_pt} - Carga {solicitacao.carga.numero_carga}'
    
    corpo_html = f"""
    <h2>Solicitação de {tipo_pt} {status_pt}</h2>
    <p>Sua solicitação para a carga {solicitacao.carga.numero_carga} foi {status_pt}:</p>
    <ul>
        <li><strong>Tipo:</strong> {tipo_pt}</li>
        <li><strong>Setor:</strong> {solicitacao.setor}</li>
        <li><strong>Status:</strong> {status_pt.upper()}</li>
        <li><strong>Analisado por:</strong> {solicitacao.analisado_por.nome if solicitacao.analisado_por else 'Não informado'}</li>
        <li><strong>Data da análise:</strong> {solicitacao.analisado_em.strftime('%d/%m/%Y %H:%M') if solicitacao.analisado_em else 'Não informado'}</li>
    </ul>
    """
    
    if solicitacao.observacao_analise:
        corpo_html += f"<p><strong>Observações do analista:</strong> {solicitacao.observacao_analise}</p>"
    
    if solicitacao.status == 'aprovada':
        corpo_html += "<p>Aguarde o usuário do setor responsável executar a tarefa.</p>"
    else:
        corpo_html += f"<p>Você pode consultar mais detalhes no <a href='{current_app.config.get('APP_URL', '')}/solicitacoes/minhas_solicitacoes'>painel de minhas solicitações</a>.</p>"
    
    return enviar_email(destinatarios, assunto, corpo_html)

def notificar_setor_responsavel(solicitacao):
    """
    Envia email de notificação aos usuários do setor responsável após uma solicitação ser aprovada.
    
    Args:
        solicitacao: Objeto da classe Solicitacao
    """
    if solicitacao.status != 'aprovada':
        return False
    
    # Buscar usuários do setor adequado
    # Setores: balanca, producao, fechamento
    # Mapear setores aos tipos de usuário
    mapeamento_setor_tipo = {
        'balanca': 'balanca',
        'producao': 'producao',
        'fechamento': 'fechamento'
    }
    
    tipo_usuario = mapeamento_setor_tipo.get(solicitacao.setor)
    if not tipo_usuario:
        usuarios_setor = Usuario.query.filter_by(ativo=True).all()
    else:
        usuarios_setor = Usuario.query.filter(
            (Usuario.tipo == tipo_usuario) | (Usuario.tipo == 'admin') | (Usuario.tipo == 'gerente'),
            Usuario.ativo == True,
            Usuario.notif_email == True
        ).all()
    
    if not usuarios_setor:
        return False
        
    destinatarios = [u.email for u in usuarios_setor if u.email]
    
    # Tipos de solicitação em português
    tipos = {
        'revisao': 'revisão',
        'edicao': 'edição',
        'exclusao': 'exclusão'
    }
    
    tipo_pt = tipos.get(solicitacao.tipo, solicitacao.tipo)
    
    assunto = f'Solicitação de {tipo_pt} aprovada - Carga {solicitacao.carga.numero_carga}'
    
    corpo_html = f"""
    <h2>Solicitação de {tipo_pt} aprovada</h2>
    <p>Uma solicitação de {tipo_pt} para a carga {solicitacao.carga.numero_carga} foi aprovada e precisa ser executada:</p>
    <ul>
        <li><strong>Carga:</strong> {solicitacao.carga.numero_carga}</li>
        <li><strong>Tipo:</strong> {tipo_pt}</li>
        <li><strong>Setor:</strong> {solicitacao.setor}</li>
        <li><strong>Solicitante:</strong> {solicitacao.solicitado_por.nome}</li>
        <li><strong>Motivo:</strong> {solicitacao.motivo}</li>
    </ul>
    <p>Por favor, execute a {tipo_pt} o mais rápido possível.</p>
    <p>Acesse o sistema para verificar mais detalhes.</p>
    """
    
    return enviar_email(destinatarios, assunto, corpo_html)

def notificar_tarefa_concluida(solicitacao, tipo_conclusao="concluída"):
    """
    Envia email de notificação ao solicitante informando que a tarefa foi concluída.
    
    Args:
        solicitacao: Objeto da classe Solicitacao
        tipo_conclusao: String descrevendo o tipo de conclusão
    """
    solicitante = solicitacao.solicitado_por
    if not solicitante or not solicitante.notif_email or not solicitante.email:
        return False
    
    destinatarios = [solicitante.email]
    
    # Tipos de solicitação em português
    tipos = {
        'revisao': 'revisão',
        'edicao': 'edição',
        'exclusao': 'exclusão'
    }
    
    tipo_pt = tipos.get(solicitacao.tipo, solicitacao.tipo)
    
    assunto = f'{tipo_pt.capitalize()} da carga {solicitacao.carga.numero_carga} {tipo_conclusao}'
    
    corpo_html = f"""
    <h2>{tipo_pt.capitalize()} {tipo_conclusao}</h2>
    <p>A {tipo_pt} da carga {solicitacao.carga.numero_carga} solicitada por você foi {tipo_conclusao}:</p>
    <ul>
        <li><strong>Carga:</strong> {solicitacao.carga.numero_carga}</li>
        <li><strong>Tipo:</strong> {tipo_pt}</li>
        <li><strong>Setor:</strong> {solicitacao.setor}</li>
    </ul>
    <p>Você pode acessar o sistema para verificar mais detalhes.</p>
    """
    
    return enviar_email(destinatarios, assunto, corpo_html)
