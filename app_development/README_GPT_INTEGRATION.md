# Integração com GPT para o CLI de Product Managers

Este documento descreve a integração do GPT (Generative Pre-trained Transformer) com o aplicativo CLI para Product Managers, permitindo o processamento avançado de prompts e a geração de conteúdo de alta qualidade para itens do Jira.

## Visão Geral

A integração com o GPT melhora significativamente as seguintes funcionalidades:

1. **Processamento de Prompts**: O GPT analisa prompts em linguagem natural e extrai informações estruturadas com maior precisão.
2. **Geração de Conteúdo**: O GPT gera descrições, critérios de aceitação e outros campos com conteúdo de alta qualidade.
3. **Sugestão de Hierarquia**: O GPT pode sugerir hierarquias completas de itens (épico, histórias, tasks, subtasks) a partir de uma descrição de funcionalidade.
4. **Análise de Contexto**: O GPT analisa o contexto histórico para fornecer sugestões mais relevantes e consistentes.

## Configuração

### Requisitos

- Python 3.8 ou superior
- Biblioteca `openai` instalada (`pip install openai`)
- Acesso à API do GPT (chave de API válida)

### Variáveis de Ambiente

Configure as seguintes variáveis de ambiente:

```bash
# Ativa/desativa a integração com GPT (true/false)
export GPT_ENABLED=true

# Chave de API do GPT
export GPT_API_KEY=sua_chave_api_aqui

# Modelo do GPT a ser usado (padrão: gpt-4o)
export GPT_MODEL=gpt-4o

# Configurações opcionais
export GPT_MAX_TOKENS=2000
export GPT_TEMPERATURE=0.7
export GPT_TIMEOUT=30
export GPT_RETRY_ATTEMPTS=3
export GPT_RETRY_DELAY=2
```

Alternativamente, você pode configurar essas variáveis no arquivo `config.py`.

## Uso

A integração com o GPT é usada automaticamente quando habilitada, sem necessidade de comandos adicionais. O aplicativo detecta a disponibilidade do GPT e o utiliza para melhorar o processamento de prompts e a geração de conteúdo.

### Exemplos de Prompts

Com a integração do GPT, você pode usar prompts mais naturais e menos estruturados:

#### Antes (sem GPT):
```
Crie uma história com título "Login com redes sociais"
Como usuário do aplicativo
Gostaria de poder fazer login usando minhas contas do Google e Facebook
Para não precisar criar uma nova conta
Critérios de aceite:
- O usuário deve poder escolher entre login com Google ou Facebook
- O sistema deve validar o email do usuário
```

#### Depois (com GPT):
```
Precisamos implementar login com redes sociais para que os usuários não precisem criar novas contas. Eles devem poder usar Google ou Facebook, e o sistema deve validar o email.
```

O GPT extrairá automaticamente as informações relevantes e gerará um conteúdo bem estruturado.

### Criação de Hierarquias

Para criar uma hierarquia completa, use o modo 3 no menu principal ou inclua "criar hierarquia" no seu prompt:

```
Criar hierarquia para implementar sistema de notificações push para o aplicativo móvel, incluindo configurações de preferências do usuário.
```

O GPT analisará o prompt e sugerirá uma hierarquia completa com épico, histórias, tasks e subtasks relacionadas.

## Arquitetura

A integração com o GPT é implementada através dos seguintes componentes:

1. **gpt_service.py**: Módulo principal que gerencia a conexão com a API do GPT e fornece métodos para processamento de prompts e geração de conteúdo.
2. **Integração com prompt_processor.py**: O processador de prompts utiliza o GPT para extrair informações e enriquecer o conteúdo quando disponível.
3. **Integração com main.py**: O fluxo principal do aplicativo utiliza o GPT para melhorar a experiência do usuário.

## Testando a Integração

Para testar se a integração com o GPT está funcionando corretamente, execute o script de teste:

```bash
python test_gpt_service.py
```

Este script testa a conexão com a API do GPT, a extração de campos, o enriquecimento de conteúdo e a sugestão de hierarquia.

## Fallback

Se o GPT não estiver disponível ou ocorrer um erro durante o processamento, o aplicativo utilizará automaticamente o método tradicional de processamento de prompts e geração de conteúdo, garantindo que o aplicativo continue funcionando mesmo sem acesso ao GPT.

## Limitações

- A qualidade do processamento depende do modelo do GPT utilizado.
- O processamento com GPT pode ser mais lento que o método tradicional.
- O uso da API do GPT pode gerar custos, dependendo do volume de uso.

## Solução de Problemas

### O GPT não está sendo utilizado

1. Verifique se a variável `GPT_ENABLED` está definida como `true`.
2. Verifique se a chave de API (`GPT_API_KEY`) está configurada corretamente.
3. Verifique se a biblioteca `openai` está instalada.

### Erros na API do GPT

1. Verifique se a chave de API é válida e tem saldo disponível.
2. Verifique se o modelo especificado (`GPT_MODEL`) está disponível para sua conta.
3. Aumente o valor de `GPT_TIMEOUT` se estiver ocorrendo timeouts.
4. Verifique os logs para mensagens de erro específicas.

## Contribuindo

Para contribuir com melhorias na integração com o GPT:

1. Adicione novos métodos no módulo `gpt_service.py` para funcionalidades específicas.
2. Melhore os prompts de sistema para obter respostas mais precisas do GPT.
3. Implemente tratamento de erros mais robusto para lidar com falhas na API.
4. Adicione testes para novas funcionalidades.
