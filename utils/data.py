"""
Funções auxiliares para manipulação e formatação de dados.
"""
from datetime import datetime
import pytz
from flask import current_app

def formatar_data(data, formato='%d/%m/%Y'):
    """
    Formata um objeto datetime para string no formato especificado.
    
    Args:
        data: objeto datetime para formatar
        formato: string de formato (padrão: '%d/%m/%Y')
        
    Returns:
        str: Data formatada
    """
    if data is None:
        return ""
        
    if hasattr(data, 'strftime'):
        return data.strftime(formato)
    return str(data)

def converter_data(data_str, formato='%d/%m/%Y'):
    """
    Converte uma string de data para objeto datetime.
    
    Args:
        data_str: String contendo a data
        formato: Formato da data na string
        
    Returns:
        datetime: Objeto datetime correspondente à data
    """
    try:
        return datetime.strptime(data_str, formato)
    except (ValueError, TypeError):
        return None
