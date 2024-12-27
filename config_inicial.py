TIPOS_AVE = [
    'Frango',
    'Galinha Leve',
    'Galinha Matriz',
    'Galinha Vermelha',
    'Galo'
]

MOTORISTAS = [
    'Claudio Ferreira Salomão',
    'Edimilton Silca Santos',
    'Fabricio Santos de Sá',
    'Gilson dos Santos Gonçalves',
    'Lucielio dos Santos Bonfim',
    'Sadraque Ramos Sales',
    'Willian Cacio Cabral Neres',
    'outro'
]

TRANSPORTADORAS = [
    'Ellen Transportes',
    'Terceirizado'
]

PLACAS_ELLEN = [
    'AZT7223',
    'QVC1E87',
    'HMV9126',
    'MYY8770',
    'PIW6G46',
    'PAM9J75',
    'OGB9164',
    'RLS3A83',
    'RLV0F19',
    'RCY3A00'
]

VALORES_KM = [
    'R$5,70',
    'R$5,90',
    'outro'
]

STATUS_FRETE = [
    'A pagar',
    'Incluso'
]

ESTADOS_BRASIL = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

# Configuração do número inicial da carga
NUMERO_INICIAL_CARGA = 4000

# Permissões iniciais do sistema
PERMISSOES_INICIAIS = {
    'gerente': [
        'ver_todas_cargas',
        'gerenciar_usuarios',
        'ver_relatorios'
    ],
    'balanca': [
        'criar_carga',
        'editar_carga',
        'ver_cargas_incompletas',
        'ver_suas_cargas'
    ],
    'financeiro': [
        'ver_todas_cargas',
        'ver_relatorios_financeiros',
        'editar_valores_frete'
    ],
    'diretoria': [
        'ver_todas_cargas',
        'ver_todos_relatorios',
        'ver_dashboard'
    ],
    'desenvolvedor': [
        'editar_formularios',
        'gerenciar_permissoes',
        'ver_todas_cargas',
        'editar_todas_cargas',
        'ver_logs_sistema'
    ],
    'transportadora': [
        'ver_suas_cargas',
        'ver_relatorio_fretes'
    ],
    'producao': [
        'ver_cargas_dia',
        'ver_relatorio_producao'
    ],
    'fechamento': [
        'ver_todas_cargas',
        'ver_relatorio_fechamento'
    ]
}

# Configuração inicial dos campos do formulário
CAMPOS_FORMULARIO = [
    {
        'nome_campo': 'numero_carga',
        'tipo_campo': 'numero',
        'obrigatorio': True,
        'visivel': True,
        'secao': 'informacoes_basicas',
        'ordem': 1
    },
    # ... outros campos serão adicionados aqui
]
