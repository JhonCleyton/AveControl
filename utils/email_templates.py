"""
Templates HTML para emails do AveControl com estilos incorporados.
"""

# Template base com estilos CSS
EMAIL_BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <style>
        /* Estilos globais */
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            background-color: #007bff;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px;
        }}
        .footer {{
            background-color: #f4f4f4;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #777;
            border-top: 1px solid #eaeaea;
        }}
        h2 {{
            color: #007bff;
            margin-top: 0;
            font-size: 20px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .info-box {{
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 20px 0;
        }}
        .btn {{
            display: inline-block;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: 500;
            margin-top: 15px;
        }}
        .status-aprovada {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-rejeitada {{
            color: #dc3545;
            font-weight: bold;
        }}
        .status-pendente {{
            color: #ffc107;
            font-weight: bold;
        }}
        .status-concluida {{
            color: #6c757d;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AveControl</h1>
        </div>
        <div class="content">
            {conteudo}
        </div>
        <div class="footer">
            <p>Este é um email automático, por favor não responda.</p>
            <p>&copy; {ano} AveControl - JC Byte - Soluções em Tecnologia</p>
        </div>
    </div>
</body>
</html>
"""

def get_status_class(status):
    """Retorna a classe CSS para o status"""
    status_map = {
        'aprovada': 'status-aprovada',
        'rejeitada': 'status-rejeitada',
        'pendente': 'status-pendente',
        'concluida': 'status-concluida'
    }
    return status_map.get(status.lower(), '')
