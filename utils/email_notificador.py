"""
Sistema de notificações por email simplificado para o AveControl.
Utiliza smtplib diretamente em vez de Flask-Mail para maior confiabilidade.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
from flask import current_app
from models.usuario import Usuario
from datetime import datetime
from .email_templates import EMAIL_BASE_TEMPLATE, get_status_class

# Configurações de email - podem ser sobrescritas pela configuração do app
DEFAULT_SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'use_tls': True,
    'username': 'tecnologiajcbyte@gmail.com',
    'password': 'jojb ikaw qggx gjpm',
    'sender': 'AveControl <tecnologiajcbyte@gmail.com>'
}

def enviar_email(destinatarios, assunto, corpo_html, config=None):
    """
    Envia um email diretamente usando smtplib.
    
    Args:
        destinatarios (list): Lista de endereços de email
        assunto (str): Assunto do email
        corpo_html (str): Corpo do email em formato HTML
        config (dict, optional): Configurações personalizadas
        
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    if not destinatarios:
        if current_app:
            current_app.logger.warning("Tentativa de enviar email sem destinatários")
        return False
    
    # Filtrar emails vazios ou inválidos
    destinatarios = [email for email in destinatarios if email and '@' in email]
    if not destinatarios:
        if current_app:
            current_app.logger.warning("Nenhum destinatário válido para envio de email")
        return False
    
    # Usar configurações do app se disponíveis, ou as padrões
    if config is None:
        config = {}
        if current_app:
            config = {
                'server': current_app.config.get('MAIL_SERVER', DEFAULT_SMTP_CONFIG['server']),
                'port': current_app.config.get('MAIL_PORT', DEFAULT_SMTP_CONFIG['port']),
                'use_tls': current_app.config.get('MAIL_USE_TLS', DEFAULT_SMTP_CONFIG['use_tls']),
                'username': current_app.config.get('MAIL_USERNAME', DEFAULT_SMTP_CONFIG['username']),
                'password': current_app.config.get('MAIL_PASSWORD', DEFAULT_SMTP_CONFIG['password']),
                'sender': current_app.config.get('MAIL_DEFAULT_SENDER', DEFAULT_SMTP_CONFIG['sender'])
            }
        else:
            config = DEFAULT_SMTP_CONFIG
    
    # Criar a mensagem
    msg = MIMEMultipart()
    msg['From'] = config.get('sender', DEFAULT_SMTP_CONFIG['sender'])
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo_html, 'html'))
    
    # Enviar o email
    try:
        if current_app:
            current_app.logger.info(f"Conectando ao servidor SMTP: {config.get('server')}:{config.get('port')}")
        
        server = smtplib.SMTP(config.get('server'), config.get('port'))
        server.ehlo()
        
        if config.get('use_tls'):
            server.starttls()
            server.ehlo()
        
        server.login(config.get('username'), config.get('password'))
        server.send_message(msg)
        server.quit()
        
        if current_app:
            current_app.logger.info(f"Email enviado com sucesso para {', '.join(destinatarios)}")
        return True
    except Exception as e:
        error_msg = f"Erro ao enviar email: {str(e)}"
        if current_app:
            current_app.logger.error(error_msg)
            current_app.logger.error(traceback.format_exc())
        else:
            print(error_msg)
            print(traceback.format_exc())
        return False

def notificar_solicitacao(solicitacao):
    """
    Envia email de notificação aos gerentes sobre uma nova solicitação.
    
    Args:
        solicitacao: Objeto da classe Solicitacao
    """
    # Buscar todos os gerentes, ignorando temporariamente a configuração notif_email
    gerentes = Usuario.query.filter(
        (Usuario.tipo == 'gerente') | (Usuario.tipo == 'admin'),
        Usuario.ativo == True
    ).all()
    
    if not gerentes:
        print("[DEBUG] Nenhum gerente ou admin ativo encontrado")
        return False
    
    # Enviar para todos os gerentes, independentemente da configuração de email
    destinatarios = [g.email for g in gerentes if g.email]
    
    if not destinatarios:
        print("[DEBUG] Nenhum gerente ou admin com email válido")
        return False
    
    # Log dos destinatários
    print(f"[DEBUG] Destinatários: {', '.join(destinatarios)}")
    
    # Tipos de solicitação em português
    tipos = {
        'revisao': 'revisão',
        'edicao': 'edição',
        'exclusao': 'exclusão'
    }
    
    tipo_pt = tipos.get(solicitacao.tipo, solicitacao.tipo)
    
    assunto = f'Nova solicitação de {tipo_pt} - Carga {solicitacao.carga.numero_carga}'
    
    # Conteúdo HTML estilizado
    conteudo = f"""
    <h2>Nova Solicitação de {tipo_pt.capitalize()}</h2>
    
    <p>Uma nova solicitação de {tipo_pt} foi registrada e requer sua análise:</p>
    
    <div class="info-box">
        <p><strong>Detalhes da Solicitação:</strong></p>
        <ul>
            <li><strong>Número da Carga:</strong> {solicitacao.carga.numero_carga}</li>
            <li><strong>Tipo:</strong> {tipo_pt.capitalize()}</li>
            <li><strong>Setor Responsável:</strong> {solicitacao.setor}</li>
            <li><strong>Solicitante:</strong> {solicitacao.solicitado_por.nome}</li>
            <li><strong>Data da Solicitação:</strong> {solicitacao.criado_em.strftime('%d/%m/%Y às %H:%M')}</li>
        </ul>
    </div>
    
    <p><strong>Motivo da Solicitação:</strong><br>
    {solicitacao.motivo}</p>
    
    <p>Por favor, avalie esta solicitação o mais rápido possível para garantir o andamento adequado do processo.</p>
    
    <a href="http://91.108.126.1:4000/solicitacoes/solicitacoes" class="btn">Analisar Solicitação</a>
    """
    
    # Aplicar o template base
    corpo_html = EMAIL_BASE_TEMPLATE.format(
        titulo=assunto,
        conteudo=conteudo,
        ano=datetime.now().year
    )
    
    return enviar_email(destinatarios, assunto, corpo_html)

def notificar_analise_solicitacao(solicitacao):
    """
    Envia email de notificação ao solicitante sobre a análise de sua solicitação.
    
    Args:
        solicitacao: Objeto da classe Solicitacao
    """
    # Verificar se o solicitante tem notificações por email ativadas
    solicitante = solicitacao.solicitado_por
    if not solicitante or not solicitante.email:
        return False
    
    # Se o usuário for o mesmo que analisou, não enviar email
    if solicitacao.analisado_por and solicitacao.analisado_por_id == solicitante.id:
        print(f"[DEBUG] Não enviando email para o usuário {solicitante.nome} pois foi ele mesmo que analisou a solicitação")
        return False
        
    # Não enviar email se o usuário for gerente ou admin
    if solicitante.tipo in ['gerente', 'admin']:
        print(f"[DEBUG] Não enviando email para {solicitante.nome} pois é {solicitante.tipo}")
        return False
    
    # Somente enviar se o usuário tiver notificações ativadas
    if not solicitante.notif_email:
        print(f"[DEBUG] Usuário {solicitante.nome} não tem notificações por email ativadas")
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
    status_class = get_status_class(solicitacao.status)
    
    assunto = f'Solicitação de {tipo_pt} {status_pt} - Carga {solicitacao.carga.numero_carga}'
    
    conteudo = f"""
    <h2>Atualização de Solicitação</h2>
    
    <p>Prezado(a) {solicitante.nome},</p>
    
    <p>Sua solicitação de {tipo_pt} para a carga <strong>{solicitacao.carga.numero_carga}</strong> foi analisada e o status atual é: 
    <span class="{status_class}">{status_pt.upper()}</span></p>
    
    <div class="info-box">
        <p><strong>Detalhes da Solicitação:</strong></p>
        <ul>
            <li><strong>Tipo:</strong> {tipo_pt.capitalize()}</li>
            <li><strong>Setor Responsável:</strong> {solicitacao.setor}</li>
            <li><strong>Data da Solicitação:</strong> {solicitacao.criado_em.strftime('%d/%m/%Y às %H:%M')}</li>
            <li><strong>Analisado por:</strong> {solicitacao.analisado_por.nome if solicitacao.analisado_por else 'Não informado'}</li>
            <li><strong>Data da Análise:</strong> {solicitacao.analisado_em.strftime('%d/%m/%Y às %H:%M') if solicitacao.analisado_em else 'Não informado'}</li>
        </ul>
    </div>
    """
    
    if solicitacao.observacao_analise:
        conteudo += f"""
        <p><strong>Observações do Analista:</strong></p>
        <div style="padding: 10px; background-color: #f9f9f9; border-left: 3px solid #ddd; margin: 15px 0;">
            {solicitacao.observacao_analise}
        </div>
        """
    
    if solicitacao.status == 'aprovada':
        conteudo += """
        <p>Sua solicitação foi <strong>aprovada</strong> e será processada pelo setor responsável. Você receberá uma notificação quando a tarefa for concluída.</p>
        """
    else:
        conteudo += f"""
        <p>Infelizmente sua solicitação foi <strong>rejeitada</strong>. Caso necessário, você pode criar uma nova solicitação com as informações adequadas.</p>
        """
    
    conteudo += f"""
    <p>Para mais detalhes, acesse o painel de solicitações no sistema AveControl.</p>
    
    <a href="http://91.108.126.1:4000/solicitacoes/minhas_solicitacoes" class="btn">Acessar Minhas Solicitações</a>
    """
    
    # Aplicar o template base
    corpo_html = EMAIL_BASE_TEMPLATE.format(
        titulo=assunto,
        conteudo=conteudo,
        ano=datetime.now().year
    )
    
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
        usuarios_setor = Usuario.query.filter_by(ativo=True, notif_email=True).all()
    else:
        usuarios_setor = Usuario.query.filter(
            (Usuario.tipo == tipo_usuario) | (Usuario.tipo == 'admin') | (Usuario.tipo == 'gerente'),
            Usuario.ativo == True,
            Usuario.notif_email == True
        ).all()
    
    if not usuarios_setor:
        return False
    
    # Excluir o gerente que aprovou a solicitau00e7u00e3o da lista de destinatu00e1rios
    gerente_aprovador_id = solicitacao.analisado_por_id if solicitacao.analisado_por_id else None
    
    destinatarios = [u.email for u in usuarios_setor if u.email and (u.id != gerente_aprovador_id or u.tipo != 'gerente')]
    
    # Tipos de solicitação em português
    tipos = {
        'revisao': 'revisão',
        'edicao': 'edição',
        'exclusao': 'exclusão'
    }
    
    tipo_pt = tipos.get(solicitacao.tipo, solicitacao.tipo)
    
    assunto = f'Solicitação de {tipo_pt} aprovada - Carga {solicitacao.carga.numero_carga}'
    
    conteudo = f"""
    <h2>Solicitação Aprovada - Ação Necessária</h2>
    
    <p>Uma solicitação de {tipo_pt} foi <span class="status-aprovada">APROVADA</span> e requer ação do seu setor.</p>
    
    <div class="info-box">
        <p><strong>Detalhes da Solicitação:</strong></p>
        <ul>
            <li><strong>Número da Carga:</strong> {solicitacao.carga.numero_carga}</li>
            <li><strong>Tipo de Solicitação:</strong> {tipo_pt.capitalize()}</li>
            <li><strong>Setor Responsável:</strong> {solicitacao.setor}</li>
            <li><strong>Solicitante:</strong> {solicitacao.solicitado_por.nome}</li>
            <li><strong>Aprovado por:</strong> {solicitacao.analisado_por.nome if solicitacao.analisado_por else 'Sistema'}</li>
            <li><strong>Data de Aprovação:</strong> {solicitacao.analisado_em.strftime('%d/%m/%Y às %H:%M') if solicitacao.analisado_em else 'Não informado'}</li>
        </ul>
    </div>
    
    <p><strong>Motivo da Solicitação:</strong></p>
    <div style="padding: 10px; background-color: #f9f9f9; border-left: 3px solid #ddd; margin: 15px 0;">
        {solicitacao.motivo}
    </div>
    
    <p>Esta solicitação deve ser processada com prioridade. Por favor, execute a {tipo_pt} da carga conforme solicitado.</p>
    
    <a href="http://91.108.126.1:4000/cargas/visualizar/{solicitacao.carga_id}" class="btn">Visualizar Carga</a>
    """
    
    # Aplicar o template base
    corpo_html = EMAIL_BASE_TEMPLATE.format(
        titulo=assunto,
        conteudo=conteudo,
        ano=datetime.now().year
    )
    
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
    
    conteudo = f"""
    <h2>Tarefa Concluída</h2>
    
    <p>Prezado(a) {solicitante.nome},</p>
    
    <p>Temos o prazer de informar que a {tipo_pt} da carga <strong>{solicitacao.carga.numero_carga}</strong> 
    solicitada por você foi <span class="status-concluida">{tipo_conclusao.upper()}</span> com sucesso.</p>
    
    <div class="info-box">
        <p><strong>Detalhes da Solicitação:</strong></p>
        <ul>
            <li><strong>Número da Carga:</strong> {solicitacao.carga.numero_carga}</li>
            <li><strong>Tipo de Solicitação:</strong> {tipo_pt.capitalize()}</li>
            <li><strong>Setor Responsável:</strong> {solicitacao.setor}</li>
            <li><strong>Data da Solicitação:</strong> {solicitacao.criado_em.strftime('%d/%m/%Y às %H:%M')}</li>
            <li><strong>Concluída em:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</li>
        </ul>
    </div>
    
    <p>Todas as alterações solicitadas foram implementadas. Você pode acessar o sistema para verificar os detalhes da carga atualizada.</p>
    
    <a href="http://91.108.126.1:4000/cargas/visualizar/{solicitacao.carga_id}" class="btn">Visualizar Carga</a>
    """
    
    # Aplicar o template base
    corpo_html = EMAIL_BASE_TEMPLATE.format(
        titulo=assunto,
        conteudo=conteudo,
        ano=datetime.now().year
    )
    
    return enviar_email(destinatarios, assunto, corpo_html)
