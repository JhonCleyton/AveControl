from app import create_app
from extensions import db
from models import Usuario

def add_usuario_field():
    app = create_app()
    with app.app_context():
        # Adicionar coluna usuario
        db.engine.execute('ALTER TABLE usuarios ADD COLUMN usuario VARCHAR(50) UNIQUE')
        
        # Atualizar usuários existentes
        usuarios = Usuario.query.all()
        for usuario in usuarios:
            # Usar o nome como nome de usuário inicial
            usuario.usuario = usuario.nome.lower().replace(' ', '_')
        
        db.session.commit()
        print("Campo 'usuario' adicionado com sucesso!")

if __name__ == '__main__':
    add_usuario_field()
