from extensions import db
from datetime import datetime
from pytz import UTC

class PerfilChat(db.Model):
    __tablename__ = 'perfis_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), unique=True, nullable=False)
    nome_exibicao = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    foto_perfil = db.Column(db.String(255))  # Caminho para a foto
    icone_perfil = db.Column(db.String(100))  # Nome do ícone da pasta static/icons
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.now(UTC))
    
    # Relacionamento com o usuário
    usuario = db.relationship('Usuario', back_populates='perfil_chat')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome_exibicao': self.nome_exibicao or self.usuario.nome,
            'descricao': self.descricao or '',
            'foto_perfil': self.foto_perfil,
            'icone_perfil': self.icone_perfil,
            'ultima_atualizacao': self.ultima_atualizacao.isoformat() if self.ultima_atualizacao else None
        }
