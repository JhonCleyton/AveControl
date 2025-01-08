# AveControl - Sistema de Controle de Aves

Sistema web para gerenciamento e controle de cargas de aves, desenvolvido com Flask.

## Funcionalidades

- Gestão de usuários com diferentes níveis de acesso
- Controle de cargas de aves
- Sistema de notificações em tempo real
- Geração de relatórios
- Dashboard com indicadores
- Chat integrado

## Requisitos

- Python 3.8+
- Flask
- SQLAlchemy
- Bootstrap 5
- FontAwesome
- SweetAlert2

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/AveControl.git
cd AveControl
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute o servidor:
```bash
python app.py
```

O sistema estará disponível em `http://localhost:5000`

## Usuários Padrão

- Admin: admin@exemplo.com / admin
- Gerente: gerente@exemplo.com / gerente

## Estrutura do Projeto

```
AveControl/
├── app.py              # Arquivo principal
├── extensions.py       # Extensões Flask
├── constants.py        # Constantes do sistema
├── models/            # Modelos do banco de dados
├── routes/            # Rotas e views
├── static/            # Arquivos estáticos (CSS, JS)
├── templates/         # Templates HTML
└── utils/            # Utilitários
```

## Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

<div align="center">
  <h2>JC Bytes - Solução em Tecnologia</h2>
  <p><em>Excelência em Desenvolvimento de Software</em></p>
  
  [![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/jhon97cleyton)
  [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/Jhon-freite)
  [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/JhonCleyton)
  [![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/5573981723483)
</div>

## 📋 Sumário

- [Sobre o Sistema](#-sobre-o-sistema)
- [Funcionalidades](#-funcionalidades)
- [Requisitos do Sistema](#-requisitos-do-sistema)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Módulos do Sistema](#-módulos-do-sistema)
- [Backup e Segurança](#-backup-e-segurança)
- [Suporte](#-suporte)

## 🔍 Sobre o Sistema

O AveControl é um sistema profissional desenvolvido pela JC Bytes, focado na gestão e controle de cargas de aves. O sistema oferece uma solução completa para o gerenciamento de todo o processo logístico, desde o cadastro inicial até o fechamento das cargas, com recursos avançados de rastreamento, notificações em tempo real e geração de relatórios detalhados.

## ⭐ Funcionalidades

### Gestão de Cargas
- **Cadastro de Cargas**
  - Registro detalhado de informações
  - Numeração automática sequencial
  - Controle de status (Pendente, Em Andamento, Concluída, Cancelada)
  - Registro de datas e horários
  - Associação com motoristas e veículos

- **Controle de Produção**
  - Registro de quantidade de aves
  - Controle de peso médio
  - Cálculo automático de sobras
  - Monitoramento de mortalidade

- **Fechamento de Cargas**
  - Registro de informações finais
  - Cálculo de diferenças
  - Validação de dados
  - Geração de relatório de fechamento

### Sistema de Notificações
- Alertas em tempo real
- Notificações de novas cargas
- Avisos de cargas pendentes
- Alertas de cargas incompletas
- Notificações de atualizações importantes

### Gestão de Usuários
- Múltiplos níveis de acesso
  - Administrador
  - Gerente
  - Operador
  - Visualizador
- Controle de permissões por função
- Registro de ações dos usuários
- Perfis personalizáveis

### Relatórios e Análises
- **Relatórios Operacionais**
  - Cargas por período
  - Produtividade por motorista
  - Análise de eficiência
  - Estatísticas de produção

- **Relatórios Gerenciais**
  - Dashboard interativo
  - Gráficos de desempenho
  - Indicadores-chave (KPIs)
  - Análises comparativas

### Sistema de Backup
- Backup automático duas vezes ao dia
- Retenção de 15 dias de histórico
- Logs detalhados de operações
- Recuperação simplificada de dados

### Recursos Adicionais
- **Pesquisa Avançada**
  - Filtros múltiplos
  - Busca por número de carga
  - Filtro por status
  - Pesquisa por motorista

- **Integração e Exportação**
  - Exportação de dados para Excel
  - Geração de PDFs
  - APIs para integração
  - Backup em nuvem (opcional)

## 💻 Requisitos do Sistema

### Requisitos de Hardware
- Processador: Intel Core i3 ou superior
- Memória RAM: 4GB ou superior
- Espaço em Disco: 10GB disponíveis
- Conexão com Internet

### Requisitos de Software
- Sistema Operacional: Windows 10 ou superior
- Python 3.8 ou superior
- Navegador web atualizado (Chrome, Firefox, Edge)
- SQLite 3

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/JhonCleyton/AveControl.git
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o ambiente:
```bash
python config_inicial.py
```

4. Inicie o servidor:
```bash
python run.py
```

## ⚙️ Configuração

### Configuração do Banco de Dados
- O sistema utiliza SQLite por padrão
- Localização do banco: `instance/avecontrol.db`
- Backup automático configurado em `backup_system.py`

### Configuração de Notificações
- Intervalo de verificação: 30 segundos
- Tipos de notificações configuráveis
- Alertas personalizáveis por usuário

### Configuração de Backup
- Horários: 7h e 18h
- Retenção: 15 dias
- Local: pasta `backups/`

## 📦 Módulos do Sistema

### Módulo de Cargas
- `routes/cargas.py`: Gerenciamento de cargas
- `models/carga.py`: Modelo de dados de cargas
- `templates/cargas/`: Templates da interface

### Módulo de Usuários
- `routes/usuarios.py`: Gerenciamento de usuários
- `models/usuario.py`: Modelo de dados de usuários
- `templates/usuarios/`: Templates da interface

### Módulo de Notificações
- `routes/notificacoes.py`: Sistema de notificações
- `models/notificacao.py`: Modelo de notificações
- `templates/components/notificacoes.html`: Interface de notificações

### Módulo de Relatórios
- `routes/relatorios.py`: Geração de relatórios
- `templates/relatorios/`: Templates de relatórios
- Exportação em múltiplos formatos

## 🔒 Backup e Segurança

### Sistema de Backup
- Backup automático duas vezes ao dia
- Retenção de 15 dias
- Logs detalhados em `backup/backup.log`
- Procedimentos de recuperação documentados

### Segurança
- Autenticação obrigatória
- Senhas criptografadas
- Controle de sessão
- Logs de atividades

## 📞 Suporte

### Contato
- **Desenvolvedor**: Jhon Cleyton
- **Empresa**: JC Bytes - Solução em Tecnologia
- **WhatsApp**: (73) 98172-3483
- **Instagram**: [@jhon97cleyton](https://www.instagram.com/jhon97cleyton)
- **LinkedIn**: [/Jhon-freite](https://www.linkedin.com/in/Jhon-freite)
- **GitHub**: [/JhonCleyton](https://github.com/JhonCleyton)

### Documentação Adicional
- Manual do usuário disponível em PDF
- Vídeos de treinamento
- FAQ com dúvidas comuns
- Guia de resolução de problemas

---

<div align="center">
  <p> 2025 JC Bytes - Solução em Tecnologia. Todos os direitos reservados.</p>
  <p>Desenvolvido por <a href="https://github.com/JhonCleyton">Jhon Cleyton</a> com e dedicação</p>
</div>
