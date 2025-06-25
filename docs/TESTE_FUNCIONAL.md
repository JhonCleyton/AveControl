# Guia de Testes Funcionais - AveControl System

## 1. Login e Autenticação
- [ ] Acessar a página de login
- [ ] Tentar login com credenciais inválidas (deve mostrar erro)
- [ ] Login com credenciais válidas
- [ ] Verificar redirecionamento para dashboard
- [ ] Testar função "Lembrar-me"
- [ ] Testar logout

## 2. Dashboard
### 2.1 Informações Gerais
- [ ] Verificar exibição do total de cargas
- [ ] Verificar valor total de fretes
- [ ] Verificar valor total de abastecimentos
- [ ] Verificar valor total a pagar
- [ ] Confirmar atualização em tempo real dos valores

### 2.2 Gráficos
- [ ] Verificar gráfico de evolução de fretes
- [ ] Verificar gráfico de distribuição de gastos
- [ ] Testar interatividade dos gráficos (hover)
- [ ] Confirmar formatação correta dos valores (R$)

## 3. Gestão de Cargas
### 3.1 Cadastro de Nova Carga
- [ ] Acessar formulário de nova carga
- [ ] Testar validação de campos obrigatórios
- [ ] Cadastrar carga com todos os campos:
  - Data
  - Transportadora
  - Valor do frete
  - Valor do abastecimento
  - Observações
- [ ] Verificar salvamento correto no banco de dados

### 3.2 Listagem de Cargas
- [ ] Verificar exibição de todas as cargas
- [ ] Testar filtros:
  - Por data
  - Por transportadora
  - Por status
- [ ] Testar ordenação por colunas
- [ ] Verificar paginação

### 3.3 Edição de Cargas
- [ ] Acessar edição de uma carga existente
- [ ] Modificar diferentes campos
- [ ] Salvar alterações
- [ ] Verificar persistência das alterações

### 3.4 Exclusão de Cargas
- [ ] Tentar excluir uma carga
- [ ] Confirmar diálogo de confirmação
- [ ] Verificar exclusão do banco de dados

## 4. Gestão de Transportadoras
### 4.1 Cadastro de Transportadora
- [ ] Acessar formulário de nova transportadora
- [ ] Testar validação de campos obrigatórios
- [ ] Cadastrar com:
  - Nome
  - CNPJ
  - Contato
  - Endereço
- [ ] Verificar salvamento

### 4.2 Listagem de Transportadoras
- [ ] Verificar lista completa
- [ ] Testar busca por nome/CNPJ
- [ ] Verificar exibição de detalhes

### 4.3 Edição de Transportadoras
- [ ] Modificar dados de uma transportadora
- [ ] Salvar alterações
- [ ] Verificar persistência

## 5. Relatórios
### 5.1 Geração de Relatórios
- [ ] Acessar página de relatórios
- [ ] Testar filtros:
  - Período personalizado
  - Por transportadora
  - Todos os registros
- [ ] Verificar cálculos e totalizadores
- [ ] Confirmar exibição dos gráficos

### 5.2 Impressão de Relatórios
- [ ] Testar botão de impressão
- [ ] Verificar layout da página de impressão
- [ ] Confirmar presença da marca d'água
- [ ] Verificar formatação de valores
- [ ] Testar orientação retrato
- [ ] Confirmar qualidade dos gráficos impressos

## 6. Sistema de Notificações
- [ ] Verificar notificações de vencimentos
- [ ] Testar criação de novas notificações
- [ ] Confirmar envio de e-mails (se configurado)
- [ ] Testar marcação como lida/não lida
- [ ] Verificar exclusão de notificações

## 7. Backup do Sistema
- [ ] Testar geração de backup manual
- [ ] Verificar backup automático
- [ ] Testar restauração de backup
- [ ] Confirmar integridade dos dados após restauração

## 8. Configurações do Sistema
- [ ] Acessar página de configurações
- [ ] Testar alteração de:
  - Dados da empresa
  - Configurações de e-mail
  - Preferências do sistema
- [ ] Verificar salvamento das configurações

## 9. Testes de Responsividade
- [ ] Testar em desktop (1920x1080)
- [ ] Testar em laptop (1366x768)
- [ ] Testar em tablet (768x1024)
- [ ] Testar em mobile (375x667)

## 10. Testes de Segurança Básicos
- [ ] Verificar acesso a rotas protegidas sem login
- [ ] Testar expiração de sessão
- [ ] Verificar proteção contra SQL injection
- [ ] Testar validação de inputs

## Observações Importantes
1. Para cada item testado, marque o checkbox correspondente
2. Anote quaisquer erros ou comportamentos inesperados
3. Documente sugestões de melhorias
4. Registre o ambiente de teste (navegador, sistema operacional)

## Registro de Bugs
Use o formato abaixo para registrar bugs encontrados:

```
Bug #[número]
- Página/Funcionalidade: 
- Descrição do problema:
- Passos para reproduzir:
- Comportamento esperado:
- Comportamento atual:
- Ambiente (navegador/OS):
- Severidade (Alta/Média/Baixa):
```

## Sugestões de Melhorias
Use o formato abaixo para registrar sugestões:

```
Sugestão #[número]
- Funcionalidade:
- Descrição da melhoria:
- Benefício esperado:
- Prioridade (Alta/Média/Baixa):
```
