from flask import Blueprint

filters = Blueprint('filters', __name__)

@filters.app_template_filter('prefix_currency')
def prefix_currency(value):
    """Adiciona o prefixo R$ ao valor monetário"""
    if not value:
        return "R$ 0,00"
    return f"R$ {value}"

def init_app(app):
    """Inicializa os filtros personalizados"""
    app.register_blueprint(filters)
