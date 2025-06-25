"""
Módulo com funções de validação para cargas e outros dados.
"""

def validar_carga(dados):
    """
    Valida os dados de uma carga.
    
    Args:
        dados (dict): Dicionário contendo os dados da carga a serem validados
        
    Returns:
        tuple: (bool, str) - Indica se os dados são válidos e a mensagem de erro (se houver)
    """
    # Validação básica - pode ser expandida conforme necessário
    if not dados.get('numero_carga'):
        return False, "Número da carga é obrigatório"
        
    # Se chegou até aqui, tudo está válido
    return True, ""
