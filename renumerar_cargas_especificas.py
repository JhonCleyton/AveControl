from app import create_app
from extensions import db
from models import Carga
from sqlalchemy import desc

def listar_ids_cargas():
    """
    Lista todos os IDs de cargas no banco de dados.
    
    :return: Lista de IDs de cargas
    """
    app = create_app()
    with app.app_context():
        try:
            cargas = Carga.query.all()
            ids_cargas = [carga.id for carga in cargas]
            return ids_cargas
        except Exception as e:
            print(f"Erro ao listar IDs de cargas: {str(e)}")
            return []

def buscar_carga_por_numero(numero_carga):
    """
    Busca uma carga pelo seu número.
    
    :param numero_carga: Número da carga a ser buscada
    :return: Objeto da carga ou None se não encontrada
    """
    app = create_app()
    with app.app_context():
        try:
            carga = Carga.query.filter_by(numero_carga=str(numero_carga)).first()
            return carga
        except Exception as e:
            print(f"Erro ao buscar carga: {str(e)}")
            return None

def renumerar_carga_especifica(id_carga, novo_numero):
    """
    Renumera uma carga específica pelo seu ID ou número.
    
    :param id_carga: ID ou número da carga a ser renumerada
    :param novo_numero: Novo número para a carga
    :return: Dicionário com mapeamento de números ou None se falhar
    """
    app = create_app()
    with app.app_context():
        try:
            # Buscar a carga específica
            carga = Carga.query.filter_by(id=id_carga).first()
            
            # Se não encontrar pelo ID, tentar encontrar pelo número
            if not carga:
                carga = Carga.query.filter_by(numero_carga=str(id_carga)).first()
            
            if not carga:
                print(f"Carga com ID/número {id_carga} não encontrada.")
                print("IDs disponíveis:", listar_ids_cargas())
                return None
            
            # Verificar se o novo número já existe
            carga_existente = Carga.query.filter_by(numero_carga=str(novo_numero)).first()
            
            if carga_existente:
                print(f"Número {novo_numero} já está em uso por outra carga.")
                print(f"Detalhes da carga existente:")
                print(f"  ID: {carga_existente.id}")
                print(f"  Número: {carga_existente.numero_carga}")
                print(f"  Data de Abate: {carga_existente.data_abate}")
                print(f"  Produtor: {carga_existente.produtor}")
                print(f"  Tipo de Ave: {carga_existente.tipo_ave}")
                
                return None
            
            # Armazenar número antigo para o mapeamento
            numero_antigo = carga.numero_carga
            
            # Atualizar o número da carga
            carga.numero_carga = str(novo_numero)
            
            # Salvar alterações no banco de dados
            db.session.commit()
            
            print(f"Carga {numero_antigo} (ID {carga.id}) renumerada para {novo_numero}")
            
            return {numero_antigo: str(novo_numero)}
        
        except Exception as e:
            # Reverter alterações em caso de erro
            db.session.rollback()
            print(f"Erro ao renumerar carga: {str(e)}")
            return None

def main():
    # Exemplo de uso
    # Substitua os valores de ID e novo número conforme necessário
    id_carga = input("Digite o ID ou número da carga a renumerar: ")
    novo_numero = input("Digite o novo número da carga: ")
    
    # Tentar converter para inteiro se for um número
    try:
        id_carga = int(id_carga)
    except ValueError:
        pass
    
    resultado = renumerar_carga_especifica(id_carga, novo_numero)
    
    if resultado:
        print("Renumeração concluída com sucesso!")
    else:
        print("Falha na renumeração.")

if __name__ == "__main__":
    main()