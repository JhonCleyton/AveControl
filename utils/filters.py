from flask import Blueprint
from datetime import datetime
import locale
import pytz

# Configurar locale para português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        locale.setlocale(locale.LC_ALL, '')

filters = Blueprint('filters', __name__)

def format_date(value):
    """Formata uma data para o formato dd/mm/aaaa"""
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime('%d/%m/%Y')

def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Formata uma data e hora para o formato especificado"""
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return value
    return value.strftime(format)

def format_datetime_timestamp(timestamp):
    """Formata um timestamp em uma string de data e hora"""
    try:
        # Converter timestamp para datetime
        dt = datetime.fromtimestamp(timestamp)
        
        # Definir timezone para Brasil/São Paulo
        tz = pytz.timezone('America/Sao_Paulo')
        dt = dt.astimezone(tz)
        
        # Formatar a data
        return dt.strftime('%d/%m/%Y %H:%M')
    except Exception as e:
        return str(timestamp)

def format_currency(value):
    """Formata um valor para moeda brasileira (R$ X.XXX,XX)"""
    try:
        # Se o valor for None ou vazio, retorna R$ 0,00
        if not value:
            return "R$ 0,00"
        
        # Converter para float se for string
        if isinstance(value, str):
            value = float(value.replace('R$', '').replace('.', '').replace(',', '.').strip())
        
        # Formatar o valor usando locale
        formatted = locale.currency(float(value), grouping=True, symbol=True)
        
        # Garantir que está usando R$ como símbolo
        if not formatted.startswith('R$'):
            formatted = 'R$ ' + formatted.replace('$', '')
            
        return formatted
    except:
        return f"R$ {float(value or 0):,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

# Alias para manter compatibilidade com código antigo
@filters.app_template_filter('prefix_currency')
def prefix_currency(value):
    """Alias para format_currency para manter compatibilidade"""
    return format_currency(value)

# Registrar os filtros no blueprint
filters.add_app_template_filter(format_date)
filters.add_app_template_filter(format_datetime)
filters.add_app_template_filter(format_datetime_timestamp)
filters.add_app_template_filter(format_currency)

def init_app(app):
    """Inicializa os filtros personalizados"""
    app.register_blueprint(filters)
