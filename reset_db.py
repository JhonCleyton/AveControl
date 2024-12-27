import os
from app import create_app, db
from models.usuario import Usuario
from models.carga import Carga

def reset_database():
    # Criar a aplicação
    app = create_app()
    
    with app.app_context():
        # Remover o banco de dados existente
        if os.path.exists('instance/sistema.db'):
            os.remove('instance/sistema.db')
            print("Banco de dados antigo removido")
        
        # Criar todas as tabelas
        db.create_all()
        print("Tabelas criadas com sucesso")
        
        # Criar usuário admin padrão
        if not Usuario.query.filter_by(email='admin@example.com').first():
            admin = Usuario(
                nome='Administrador',
                email='admin@example.com',
                tipo='admin',
                ativo=True
            )
            admin.set_senha('admin')
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado")

if __name__ == '__main__':
    reset_database()
