from flask import Blueprint, jsonify, request, current_app, send_file, render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from pytz import UTC
from models.documento import DocumentoCarga
from models import db, HistoricoCarga, Carga
from models.usuario import Usuario
from utils.decorators import gerente_required
import traceback
from extensions import csrf
import mimetypes

bp = Blueprint('documentos', __name__)

# Desabilitar CSRF para uploads de arquivo
csrf.exempt(bp)

UPLOAD_FOLDER = 'uploads/documentos'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.errorhandler(Exception)
def handle_error(error):
    """Manipulador de erros global para o blueprint"""
    print("Erro na rota de documentos:", str(error))
    traceback.print_exc()
    return jsonify({'error': str(error)}), 400

@bp.route('/api/carga/<int:carga_id>/documentos', methods=['GET'])
@login_required
def listar_documentos(carga_id):
    """Lista todos os documentos de uma carga"""
    documentos = DocumentoCarga.query.filter_by(carga_id=carga_id).all()
    return jsonify([{
        'id': doc.id,
        'tipo_documento': doc.tipo_documento,
        'outro_tipo_descricao': doc.outro_tipo_descricao,
        'nome_arquivo': doc.nome_arquivo,
        'data_upload': doc.data_upload.isoformat(),
        'usuario': doc.usuario.nome,
        'ausente': doc.ausente,
        'motivo_ausencia': doc.motivo_ausencia,
        'status_exclusao': doc.status_exclusao
    } for doc in documentos])

@bp.route('/api/carga/<int:carga_id>/documentos', methods=['POST'])
@login_required
def adicionar_documento(carga_id):
    """Adiciona um novo documento à carga"""
    try:
        print(f"Recebendo upload para carga {carga_id}")
        print("Form data:", request.form.to_dict())
        print("Files:", request.files.to_dict())
        
        if not request.form.get('tipo_documento'):
            raise ValueError('Tipo de documento é obrigatório')

        if request.form.get('tipo_documento') == 'Outro' and not request.form.get('outro_tipo_descricao'):
            raise ValueError('Descrição do outro tipo é obrigatória')

        ausente = request.form.get('ausente') == 'true'
        if ausente and not request.form.get('motivo_ausencia'):
            raise ValueError('Motivo da ausência é obrigatório')

        if not ausente:
            if 'arquivo' not in request.files:
                raise ValueError('Nenhum arquivo enviado')

            arquivos = request.files.getlist('arquivo')
            if not arquivos or all([arq.filename == '' for arq in arquivos]):
                raise ValueError('Nenhum arquivo selecionado')

            upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, str(carga_id))
            os.makedirs(upload_path, exist_ok=True)

            documentos_criados = []
            from uuid import uuid4
            for arquivo in arquivos:
                if arquivo.filename == '':
                    continue
                if not allowed_file(arquivo.filename):
                    continue  # Ignora arquivos inválidos
                # Gera nome único
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}_{secure_filename(arquivo.filename)}"
                arquivo_path = os.path.join(upload_path, filename)
                arquivo.save(arquivo_path)
                # Cria registro do documento
                doc = DocumentoCarga(
                    carga_id=carga_id,
                    tipo_documento=request.form['tipo_documento'],
                    outro_tipo_descricao=request.form.get('outro_tipo_descricao'),
                    nome_arquivo=filename,
                    caminho_arquivo=os.path.join(str(carga_id), filename),
                    usuario_id=current_user.id
                )
                db.session.add(doc)
                documentos_criados.append(doc)
            if not documentos_criados:
                raise ValueError('Nenhum arquivo válido foi enviado')
            doc = documentos_criados[-1]  # Para manter compatibilidade com retorno e histórico
        else:
            # Registrar documento ausente
            doc = DocumentoCarga(
                carga_id=carga_id,
                tipo_documento=request.form['tipo_documento'],
                outro_tipo_descricao=request.form.get('outro_tipo_descricao'),
                ausente=True,
                motivo_ausencia=request.form['motivo_ausencia'],
                usuario_id=current_user.id,
                nome_arquivo='N/A',
                caminho_arquivo='N/A'
            )

        db.session.add(doc)

        # Registrar no histórico
        historico = HistoricoCarga(
            carga_id=carga_id,
            usuario_id=current_user.id,
            acao=f"{'Registrou ausência de documento' if ausente else 'Adicionou documento'}: {doc.tipo_documento}",
            data_hora=datetime.now(UTC)
        )
        db.session.add(historico)

        # Commit das alterações
        print("Fazendo commit das alterações")
        db.session.commit()
        
        return jsonify({
            'message': 'Documento adicionado com sucesso',
            'id': doc.id
        })
        
    except Exception as e:
        print("Erro ao processar documento:", str(e))
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/api/documentos/<int:doc_id>/download', methods=['GET'])
@login_required
def download_documento(doc_id):
    """Download do documento"""
    doc = DocumentoCarga.query.get_or_404(doc_id)
    if doc.ausente:
        return jsonify({'error': 'Documento está marcado como ausente'}), 400
        
    arquivo_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, doc.caminho_arquivo)
    if not os.path.exists(arquivo_path):
        return jsonify({'error': 'Arquivo não encontrado'}), 404

    # Determinar o tipo MIME do arquivo
    mime_type, _ = mimetypes.guess_type(arquivo_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    try:
        return send_file(
            arquivo_path,
            as_attachment=True,
            mimetype=mime_type,
            download_name=doc.nome_arquivo
        )
    except Exception as e:
        print(f"Erro ao fazer download do arquivo: {str(e)}")
        return jsonify({'error': 'Erro ao fazer download do arquivo'}), 500

@bp.route('/api/documentos/<int:doc_id>/visualizar', methods=['GET'])
@login_required
def visualizar_documento(doc_id):
    """Visualiza o documento no navegador"""
    doc = DocumentoCarga.query.get_or_404(doc_id)
    if doc.ausente:
        return jsonify({'error': 'Documento está marcado como ausente'}), 400
        
    arquivo_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, doc.caminho_arquivo)
    if not os.path.exists(arquivo_path):
        return jsonify({'error': 'Arquivo não encontrado'}), 404

    # Determinar o tipo MIME do arquivo
    mime_type, _ = mimetypes.guess_type(arquivo_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    try:
        return send_file(
            arquivo_path,
            as_attachment=False,
            mimetype=mime_type
        )
    except Exception as e:
        print(f"Erro ao visualizar arquivo: {str(e)}")
        return jsonify({'error': 'Erro ao visualizar arquivo'}), 500

@bp.route('/api/documentos/<int:doc_id>/solicitar-exclusao', methods=['POST'])
@login_required
def solicitar_exclusao(doc_id):
    """Solicita a exclusão de um documento"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Requisição deve ser JSON'}), 400

        motivo = request.json.get('motivo')
        if not motivo:
            return jsonify({'error': 'Motivo é obrigatório'}), 400

        doc = DocumentoCarga.query.get_or_404(doc_id)
        
        if doc.status_exclusao == 'pendente':
            return jsonify({'error': 'Já existe uma solicitação de exclusão pendente'}), 400

        doc.status_exclusao = 'pendente'
        doc.solicitado_exclusao_por_id = current_user.id
        doc.data_solicitacao_exclusao = datetime.now(UTC)
        doc.motivo_exclusao = motivo

        # Registrar no histórico
        historico = HistoricoCarga(
            carga_id=doc.carga_id,
            usuario_id=current_user.id,
            acao=f"Solicitou exclusão do documento: {doc.tipo_documento}",
            data_hora=datetime.now(UTC)
        )
        db.session.add(historico)
        db.session.commit()

        return jsonify({
            'message': 'Solicitação de exclusão registrada',
            'status': 'pendente'
        })
    except Exception as e:
        print("Erro ao solicitar exclusão:", str(e))
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/api/documentos/<int:doc_id>/aprovar-exclusao', methods=['POST'])
@gerente_required
def aprovar_exclusao(doc_id):
    """Aprova ou reprova a exclusão de um documento"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Requisição deve ser JSON'}), 400

        doc = DocumentoCarga.query.get_or_404(doc_id)
        
        if doc.status_exclusao != 'pendente':
            return jsonify({'error': 'Não há solicitação de exclusão pendente'}), 400

        aprovado = request.json.get('aprovado', False)
        observacao = request.json.get('observacao', '')
        
        if aprovado:
            # Se aprovado, excluir o arquivo físico se existir
            if not doc.ausente:
                arquivo_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, doc.caminho_arquivo)
                if os.path.exists(arquivo_path):
                    os.remove(arquivo_path)
            
            # Registrar no histórico antes de excluir o documento
            acao = f"Aprovou e excluiu o documento: {doc.tipo_documento}"
            if observacao:
                acao += f" - Observação: {observacao}"
                
            historico = HistoricoCarga(
                carga_id=doc.carga_id,
                usuario_id=current_user.id,
                acao=acao,
                data_hora=datetime.now(UTC)
            )
            db.session.add(historico)
            
            # Excluir o documento do banco de dados
            db.session.delete(doc)
        else:
            # Se rejeitado, apenas atualizar o status
            doc.status_exclusao = 'reprovado'
            doc.aprovado_exclusao_por_id = current_user.id
            doc.data_aprovacao_exclusao = datetime.now(UTC)
            doc.motivo_exclusao = observacao

            # Registrar no histórico
            acao = f"Rejeitou exclusão do documento: {doc.tipo_documento}"
            if observacao:
                acao += f" - Observação: {observacao}"
                
            historico = HistoricoCarga(
                carga_id=doc.carga_id,
                usuario_id=current_user.id,
                acao=acao,
                data_hora=datetime.now(UTC)
            )
            db.session.add(historico)

        db.session.commit()

        return jsonify({
            'message': 'Documento excluído com sucesso' if aprovado else 'Solicitação de exclusão rejeitada',
            'status': 'excluido' if aprovado else 'reprovado'
        })
    except Exception as e:
        print("Erro ao processar aprovação/rejeição:", str(e))
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/api/documentos/solicitacoes-exclusao', methods=['GET'])
@gerente_required
def listar_solicitacoes_exclusao():
    """Lista todas as solicitações de exclusão pendentes"""
    try:
        # Buscar documentos com solicitação pendente
        solicitacoes = db.session.query(
            DocumentoCarga,
            Carga.numero_carga.label('numero_carga'),
            Usuario.nome.label('solicitado_por_nome')
        ).join(
            Carga, DocumentoCarga.carga_id == Carga.id
        ).join(
            Usuario, DocumentoCarga.solicitado_exclusao_por_id == Usuario.id
        ).filter(
            DocumentoCarga.status_exclusao == 'pendente'
        ).all()

        # Formatar resposta
        resultado = []
        for doc, numero_carga, solicitado_por_nome in solicitacoes:
            resultado.append({
                'id': doc.id,
                'carga_id': doc.carga_id,
                'numero_carga': numero_carga,
                'tipo_documento': doc.tipo_documento,
                'solicitado_por': solicitado_por_nome,
                'data_solicitacao': doc.data_solicitacao_exclusao.strftime('%d/%m/%Y %H:%M'),
                'motivo': doc.motivo_exclusao
            })

        return render_template('solicitacoes/index.html', solicitacoes_documentos=resultado)
    except Exception as e:
        print("Erro ao listar solicitações:", str(e))
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@bp.route('/api/documentos/<int:carga_id>', methods=['GET'])
@login_required
def listar_documentos_carga(carga_id):
    """Lista todos os documentos de uma carga"""
    try:
        documentos = DocumentoCarga.query.filter_by(carga_id=carga_id).all()
        return jsonify({
            'documentos': [{
                'id': doc.id,
                'tipo_documento': doc.tipo_documento,
                'outro_tipo_descricao': doc.outro_tipo_descricao,
                'nome_arquivo': doc.nome_arquivo,
                'data_adicao': doc.data_upload.isoformat() if doc.data_upload else None,
                'usuario': doc.usuario.nome if doc.usuario else None,
                'ausente': doc.ausente,
                'motivo_ausencia': doc.motivo_ausencia,
                'status_exclusao': doc.status_exclusao,
                'solicitado_exclusao_por_id': doc.solicitado_exclusao_por_id,
                'data_solicitacao_exclusao': doc.data_solicitacao_exclusao.isoformat() if doc.data_solicitacao_exclusao else None,
                'motivo_exclusao': doc.motivo_exclusao
            } for doc in documentos]
        })
    except Exception as e:
        print("Erro ao listar documentos:", str(e))
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400
