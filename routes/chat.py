from flask import Blueprint, jsonify, request, current_app, render_template, url_for, redirect, flash, send_from_directory
from flask_login import login_required, current_user
from extensions import db
from models import Usuario, Mensagens, PerfilChat, LeituraMensagem
from sqlalchemy import func, and_, or_
from datetime import datetime
import pytz
from werkzeug.utils import secure_filename
import uuid
import os
from sqlalchemy import func

chat = Blueprint('chat', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'ico'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chat.route('/')
@login_required
def index():
    usuarios = Usuario.query.filter(Usuario.id != current_user.id).all()
    return render_template('chat/index.html', usuarios=usuarios)

@chat.route('/mensagens_grupo')
@login_required
def mensagens_grupo():
    try:
        # Buscar mensagens do grupo
        mensagens = (Mensagens.query
                    .filter_by(tipo='grupo')
                    .order_by(Mensagens.data_envio.desc())
                    .limit(100)
                    .all())
        
        # Marcar mensagens como lidas
        for mensagem in mensagens:
            if mensagem.remetente_id != current_user.id:
                # Verificar se já existe uma leitura para esta mensagem
                leitura = LeituraMensagem.query.filter_by(
                    mensagem_id=mensagem.id,
                    usuario_id=current_user.id
                ).first()
                
                if not leitura:
                    # Criar nova leitura
                    leitura = LeituraMensagem(
                        mensagem_id=mensagem.id,
                        usuario_id=current_user.id
                    )
                    db.session.add(leitura)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar leituras: {str(e)}")
        
        return jsonify([{
            'id': m.id,
            'tipo': m.tipo,
            'conteudo': m.conteudo,
            'data_envio': m.data_envio.astimezone(current_app.config['TIMEZONE']).strftime('%d/%m/%Y %H:%M'),
            'remetente': {
                'id': m.remetente.id,
                'nome': m.remetente.nome
            },
            'leituras': [{
                'usuario_id': l.usuario_id,
                'data_leitura': l.data_leitura.astimezone(current_app.config['TIMEZONE']).strftime('%d/%m/%Y %H:%M')
            } for l in m.leituras]
        } for m in mensagens])
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar mensagens do grupo: {str(e)}')
        return jsonify({'error': 'Erro ao buscar mensagens'}), 500

@chat.route('/mensagens_individuais/<int:usuario_id>')
@login_required
def mensagens_individuais(usuario_id):
    try:
        # Buscar mensagens individuais
        mensagens = (Mensagens.query
                    .filter_by(tipo='individual')
                    .filter(
                        ((Mensagens.remetente_id == current_user.id) & (Mensagens.destinatario_id == usuario_id)) |
                        ((Mensagens.remetente_id == usuario_id) & (Mensagens.destinatario_id == current_user.id))
                    )
                    .order_by(Mensagens.data_envio.desc())
                    .limit(100)
                    .all())
        
        # Marcar mensagens recebidas como lidas
        for mensagem in mensagens:
            if mensagem.remetente_id != current_user.id:
                leitura = LeituraMensagem.query.filter_by(
                    mensagem_id=mensagem.id,
                    usuario_id=current_user.id
                ).first()
                
                if not leitura:
                    leitura = LeituraMensagem(
                        mensagem_id=mensagem.id,
                        usuario_id=current_user.id
                    )
                    db.session.add(leitura)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar leituras: {str(e)}")
        
        return jsonify([{
            'id': m.id,
            'tipo': m.tipo,
            'conteudo': m.conteudo,
            'data_envio': m.data_envio.astimezone(current_app.config['TIMEZONE']).strftime('%d/%m/%Y %H:%M'),
            'remetente': {
                'id': m.remetente.id,
                'nome': m.remetente.nome
            },
            'leituras': [{
                'usuario_id': l.usuario_id,
                'data_leitura': l.data_leitura.astimezone(current_app.config['TIMEZONE']).strftime('%d/%m/%Y %H:%M')
            } for l in m.leituras]
        } for m in mensagens])
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar mensagens individuais: {str(e)}')
        return jsonify({'error': 'Erro ao buscar mensagens'}), 500

@chat.route('/mensagens_nao_lidas')
@login_required
def mensagens_nao_lidas():
    try:
        # Criar subquery explicitamente usando select()
        lidas_subquery = (
            db.select(LeituraMensagem.mensagem_id)
            .where(LeituraMensagem.usuario_id == current_user.id)
            .scalar_subquery()
        )
        
        # Buscar mensagens não lidas do grupo
        mensagens_grupo = (
            db.session.query(Mensagens)
            .filter(Mensagens.tipo == 'grupo')
            .filter(Mensagens.remetente_id != current_user.id)
            .filter(~Mensagens.id.in_(lidas_subquery))
            .count()
        )
        
        # Buscar mensagens não lidas individuais por remetente
        mensagens_individuais = (
            db.session.query(
                Mensagens.remetente_id,
                db.func.count(Mensagens.id).label('count')
            )
            .filter(
                Mensagens.tipo == 'individual',
                Mensagens.destinatario_id == current_user.id,
                ~Mensagens.id.in_(lidas_subquery)
            )
            .group_by(Mensagens.remetente_id)
            .all()
        )
        
        return jsonify({
            'grupo': mensagens_grupo,
            'individuais': {
                str(remetente_id): count
                for remetente_id, count in mensagens_individuais
            }
        })
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar mensagens não lidas: {str(e)}')
        return jsonify({'error': 'Erro ao buscar mensagens não lidas'}), 500

@chat.route('/enviar_mensagem', methods=['POST'])
@login_required
def enviar_mensagem():
    try:
        data = request.get_json()
        
        if not data or 'conteudo' not in data or 'tipo' not in data:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        # Criar mensagem com timezone correto
        now = datetime.now(current_app.config['TIMEZONE'])
        
        mensagem = Mensagens(
            conteudo=data['conteudo'],
            tipo=data['tipo'],
            remetente_id=current_user.id,
            destinatario_id=data.get('destinatario_id') if data['tipo'] == 'individual' else None,
            data_envio=now
        )
        
        db.session.add(mensagem)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mensagem enviada com sucesso',
            'mensagem': {
                'id': mensagem.id,
                'tipo': mensagem.tipo,
                'conteudo': mensagem.conteudo,
                'data_envio': mensagem.data_envio.astimezone(current_app.config['TIMEZONE']).strftime('%d/%m/%Y %H:%M'),
                'remetente': {
                    'id': mensagem.remetente.id,
                    'nome': mensagem.remetente.nome
                },
                'destinatario': {
                    'id': mensagem.destinatario.id,
                    'nome': mensagem.destinatario.nome
                } if mensagem.destinatario else None,
                'leituras': []
            }
        })
    except Exception as e:
        current_app.logger.error(f'Erro ao enviar mensagem: {str(e)}')
        return jsonify({'error': 'Erro ao enviar mensagem'}), 500

@chat.route('/marcar_como_lida/<int:mensagem_id>', methods=['POST'])
@login_required
def marcar_como_lida(mensagem_id):
    try:
        # Verificar se a mensagem existe
        mensagem = Mensagens.query.get(mensagem_id)
        if not mensagem:
            return jsonify({'error': 'Mensagem não encontrada'}), 404
            
        # Verificar se a mensagem já foi lida
        leitura = LeituraMensagem.query.filter_by(
            mensagem_id=mensagem_id,
            usuario_id=current_user.id
        ).first()
        
        # Se ainda não foi lida, criar nova leitura
        if not leitura:
            leitura = LeituraMensagem(
                mensagem_id=mensagem_id,
                usuario_id=current_user.id
            )
            db.session.add(leitura)
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Erro ao salvar leitura: {str(e)}')
                return jsonify({'error': 'Erro ao salvar leitura'}), 500
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Erro ao marcar mensagem como lida: {str(e)}')
        return jsonify({'error': str(e)}), 500

@chat.route('/perfil', methods=['GET'])
@login_required
def get_perfil():
    if not current_user.perfil_chat:
        perfil = PerfilChat(usuario_id=current_user.id)
        db.session.add(perfil)
        db.session.commit()
    
    return jsonify(current_user.perfil_chat.to_dict())

@chat.route('/perfil', methods=['POST'])
@login_required
def atualizar_perfil():
    try:
        current_app.logger.info('Iniciando atualização de perfil')
        
        if not current_user.perfil_chat:
            current_app.logger.info('Criando novo perfil')
            perfil = PerfilChat(usuario_id=current_user.id)
            db.session.add(perfil)
            db.session.commit()
        else:
            current_app.logger.info('Atualizando perfil existente')
            perfil = current_user.perfil_chat

        # Processa os dados do formulário
        data = request.form
        current_app.logger.info(f'Dados recebidos: {data}')
        
        # Atualiza os campos de texto
        if 'nome_exibicao' in data:
            perfil.nome_exibicao = data['nome_exibicao']
        if 'descricao' in data:
            perfil.descricao = data['descricao']
        if 'icone_perfil' in data:
            current_app.logger.info(f'Atualizando ícone: {data["icone_perfil"]}')
            perfil.icone_perfil = data['icone_perfil']
            perfil.foto_perfil = None  # Remove a foto se um ícone for selecionado
        
        # Processa o upload de foto
        if 'foto_perfil' in request.files:
            file = request.files['foto_perfil']
            current_app.logger.info(f'Arquivo recebido: {file.filename if file else None}')
            
            if file and file.filename and allowed_file(file.filename):
                current_app.logger.info('Processando upload de foto')
                
                # Remove foto antiga se existir
                if perfil.foto_perfil:
                    try:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pics', perfil.foto_perfil)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception as e:
                        current_app.logger.error(f'Erro ao remover foto antiga: {e}')
                
                # Salva nova foto
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pics')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                
                perfil.foto_perfil = filename
                perfil.icone_perfil = None  # Remove o ícone se uma foto for enviada
        
        # Atualiza a data
        perfil.ultima_atualizacao = datetime.now(current_app.config['TIMEZONE'])
        
        # Salva as alterações
        current_app.logger.info('Salvando alterações no banco de dados')
        db.session.commit()
        
        return jsonify(perfil.to_dict())
        
    except Exception as e:
        current_app.logger.error(f'Erro ao atualizar perfil: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chat.route('/perfil/icones')
@login_required
def listar_icones():
    try:
        icons_dir = os.path.join(current_app.static_folder, 'icons')
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
            
        # Lista todos os arquivos na pasta de ícones
        icones = []
        for filename in os.listdir(icons_dir):
            if allowed_file(filename):
                icones.append(filename)
                
        return jsonify(icones)
    except Exception as e:
        current_app.logger.error(f'Erro ao listar ícones: {str(e)}')
        return jsonify({'error': 'Erro ao listar ícones'}), 500

@chat.route('/usuarios')
@login_required
def listar_usuarios():
    """Lista todos os usuários disponíveis para chat"""
    try:
        usuarios = Usuario.query.filter(Usuario.id != current_user.id).all()
        return jsonify([{
            'id': u.id,
            'nome': u.nome,
            'perfil': u.perfil_chat.to_dict() if u.perfil_chat else None
        } for u in usuarios])
    except Exception as e:
        current_app.logger.error(f'Erro ao listar usuários: {str(e)}')
        return jsonify({'error': str(e)}), 500

@chat.route('/notificacoes')
@login_required
def get_notificacoes():
    """Retorna o número de mensagens não lidas para o usuário atual"""
    try:
        # Criar subquery para mensagens já lidas
        lidas_subquery = (
            db.select(LeituraMensagem.mensagem_id)
            .where(LeituraMensagem.usuario_id == current_user.id)
            .scalar_subquery()
        )
        
        # Contar mensagens não lidas
        total_nao_lidas = db.session.query(Mensagens).filter(
            or_(
                and_(
                    Mensagens.tipo == 'grupo',
                    Mensagens.remetente_id != current_user.id
                ),
                and_(
                    Mensagens.tipo == 'individual',
                    Mensagens.destinatario_id == current_user.id
                )
            ),
            ~Mensagens.id.in_(lidas_subquery)
        ).count()
        
        return jsonify({'nao_lidas': total_nao_lidas})
    except Exception as e:
        print(f"Erro ao buscar notificações: {str(e)}")
        return jsonify({'error': str(e)}), 500
