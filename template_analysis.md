# Análise dos Templates para Criação de Itens no Jira

Este documento apresenta a análise dos templates que serão utilizados pelo aplicativo Python para criar histórias, épicos, tasks e subtasks no Jira através de prompts.

## Estrutura Geral dos Templates

O arquivo analisado contém três templates principais:
1. Template para Épicos
2. Template para Histórias de Usuário
3. Template para Bugs

Cada template possui uma estrutura específica com campos que precisam ser preenchidos pelo aplicativo.

## 1. Template para Épicos

### Campos Obrigatórios:
- **Descrição**: Visão geral do épico
- **Objetivo**: Objetivo principal do épico
- **Benefícios**: Lista de benefícios que a conclusão do épico trará
- **Critérios de Aceitação**: Lista de critérios que definem quando o épico está concluído
- **Riscos**: Lista de riscos potenciais que podem impactar o desenvolvimento

### Formato:
```
Epico:
Descrição
Visão geral
[Descrição do épico]

Objetivo: 
[Objetivo principal]

Benefícios: 
• [Benefício 1]
• [Benefício 2]
...

Critérios de Aceitação:
• [Critério 1]
• [Critério 2]
...

Riscos:
• [Risco 1]
• [Risco 2]
...
```

## 2. Template para Histórias de Usuário

### Campos Obrigatórios:
- **Descrição**: Descrição da história no formato "Como... Gostaria... Para..."
  - **Como**: Papel do usuário
  - **Gostaria**: O que o usuário deseja fazer
  - **Para**: Objetivo do usuário
- **Pré Condições**: Lista de condições necessárias para a história
- **Regras**: Lista de regras aplicáveis à história
- **Exceção à Regra**: Lista de exceções às regras
- **Critérios de Aceite**: Lista de critérios que definem quando a história está concluída
- **Cenários de Teste**: Cenários no formato "Dado que... Quando... Então..."
  - **Dado que**: Pré-requisito
  - **Quando**: Ação do usuário
  - **Então**: Resultado esperado

### Formato:
```
História:
Descrição
Como: [Papel do usuário]
Gostaria: [O que o usuário deseja fazer]
Para: [Objetivo do usuário]

Pré Condições
• [Pré-condição 1]
• [Pré-condição 2]
...

Regras
• [Regra 1]
• [Regra 2]
...

Exceção à Regra
• [Exceção 1]
• [Exceção 2]
...

Critérios de Aceite
• [Critério 1]
• [Critério 2]
...

Cenários de Teste
Cenário: [Nome do Cenário]
Dado que [pré-requisito]
Quando [ação do usuário]
Então [resultado esperado]
```

## 3. Template para Bugs

### Campos Obrigatórios:
- **Cenário de Erro**: Descrição do que acontece (o erro)
- **Cenário Esperado**: Descrição do que deveria acontecer
- **Impacto**: Descrição do impacto do bug (usuários afetados, lentidão, etc.)
- **Origem**: Como o bug foi descoberto
- **Solução**: Como solucionar o bug ou indicação de que necessita discovery

### Formato:
```
Bug:
Descrição
Cenário de Erro
[Descrição do cenário de erro]

Cenário Esperado
[Descrição do cenário esperado]

Impacto
[Descrição do impacto]

Origem
[Descrição da origem]

Solução
[Descrição da solução ou "Necessita discovery"]
```

## Observações para o Desenvolvimento do Aplicativo

1. O aplicativo deverá ser capaz de identificar o tipo de item a ser criado (épico, história ou bug) com base no prompt do usuário.

2. Para cada tipo de item, o aplicativo deverá solicitar as informações específicas necessárias para preencher todos os campos obrigatórios do template correspondente.

3. O aplicativo deverá formatar corretamente as listas com marcadores (•) para os campos que exigem múltiplos itens.

4. Para histórias de usuário, o aplicativo deverá garantir que a descrição siga o formato "Como... Gostaria... Para...".

5. Para cenários de teste, o aplicativo deverá garantir que cada cenário siga o formato "Dado que... Quando... Então...".

6. O aplicativo deverá armazenar o contexto das interações anteriores no S3 para manter a continuidade das conversas e facilitar a criação de itens relacionados.

7. Não foi identificado um template específico para subtasks no documento analisado. O aplicativo pode precisar derivar o formato para subtasks a partir do template de histórias, simplificando-o conforme necessário.
