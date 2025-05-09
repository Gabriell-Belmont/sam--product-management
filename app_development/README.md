# PM JIRA CLI - Criação de Demandas via Prompt

Uma ferramenta de linha de comando para Product Managers criarem histórias, épicos, tasks e subtasks no Jira através de prompts, com uma memória de contextos anteriores armazenada em S3.

## Visão Geral

O PM JIRA CLI é uma aplicação Python que permite aos Product Managers criar e gerenciar itens no Jira de forma eficiente através de prompts de texto. A aplicação utiliza processamento de linguagem natural para interpretar os prompts e criar os itens correspondentes no Jira, além de armazenar o contexto em S3 para referência futura.

### Principais Recursos

- **Criação de Itens via Prompt**: Crie épicos, histórias, tasks, subtasks e bugs no Jira usando linguagem natural.
- **Assistente Interativo**: Interface de linha de comando guiada para criação de itens passo a passo.
- **Processamento Avançado de Prompts**: Extração automática de informações relevantes de prompts de texto.
- **Integração com GPT**: Enriquecimento de conteúdo e processamento avançado de prompts usando modelos GPT.
- **Armazenamento de Contexto**: Armazenamento de itens e contextos no S3 para referência futura.
- **Criação de Hierarquias**: Criação automática de hierarquias completas (épico, história, tasks, subtasks) a partir de um único prompt.
- **Integração com Jira**: Criação e vinculação de itens diretamente no Jira.

## Requisitos

- Python 3.8 ou superior
- Conta Jira com permissões de criação de itens
- Conta AWS com acesso ao S3 (opcional, para armazenamento de contexto)
- Chave de API do OpenAI (opcional, para integração com GPT)

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/sua-empresa/pm-jira-cli.git
cd pm-jira-cli
```

### 2. Execute o script de instalação

```bash
chmod +x setup.sh
./setup.sh
```

O script de instalação irá:
- Verificar se o Python está instalado
- Criar um ambiente virtual
- Instalar as dependências
- Criar um arquivo `.env` para configuração

### 3. Ative o ambiente virtual

```bash
source venv/bin/activate
```

### 4. Configure as variáveis de ambiente

Edite o arquivo `.env` com suas configurações:

```
# Configurações do Jira
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=seu-email@empresa.com
JIRA_API_TOKEN=seu-token-api-jira
JIRA_PROJECT_KEY=PROJ

# Configurações do AWS S3
AWS_S3_BUCKET=pm-cli-memory
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=sua-access-key
AWS_SECRET_ACCESS_KEY=sua-secret-key

# Configurações do GPT
GPT_ENABLED=true
GPT_API_KEY=sua-chave-api-openai
GPT_MODEL=gpt-4o
GPT_MAX_TOKENS=2000
GPT_TEMPERATURE=0.7
```

## Configuração

### Configuração do Jira

1. Obtenha um token de API do Jira:
   - Acesse [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Clique em "Create API token"
   - Dê um nome ao token e clique em "Create"
   - Copie o token gerado para o arquivo `.env`

2. Configure as variáveis de ambiente do Jira:
   - `JIRA_BASE_URL`: URL base da sua instância do Jira (ex: https://sua-empresa.atlassian.net)
   - `JIRA_EMAIL`: Seu email de login no Jira
   - `JIRA_API_TOKEN`: Token de API gerado no passo anterior
   - `JIRA_PROJECT_KEY`: Chave do projeto Jira padrão (ex: PROJ)

### Configuração do S3

1. Crie um bucket S3:
   - Acesse o console da AWS e crie um bucket S3
   - Anote o nome do bucket e a região

2. Configure as credenciais AWS:
   - `AWS_S3_BUCKET`: Nome do bucket S3 criado
   - `AWS_REGION`: Região do bucket S3
   - `AWS_ACCESS_KEY_ID`: Sua chave de acesso AWS
   - `AWS_SECRET_ACCESS_KEY`: Sua chave secreta AWS

### Configuração do GPT (Opcional)

1. Obtenha uma chave de API do OpenAI:
   - Acesse [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Crie uma nova chave de API
   - Copie a chave para o arquivo `.env`

2. Configure as variáveis de ambiente do GPT:
   - `GPT_ENABLED`: Define se a integração com GPT está ativada (true/false)
   - `GPT_API_KEY`: Sua chave de API do OpenAI
   - `GPT_MODEL`: Modelo GPT a ser usado (ex: gpt-4o)
   - `GPT_MAX_TOKENS`: Número máximo de tokens para respostas
   - `GPT_TEMPERATURE`: Temperatura para geração de texto (0.0 a 1.0)

## Uso

### Iniciar o aplicativo

```bash
python main.py
```

### Modos de Operação

O aplicativo oferece três modos de operação:

#### 1. Modo Assistente Interativo

Guia o usuário passo a passo na criação de um item no Jira.

```
Escolha o modo (1, 2 ou 3): 1
```

#### 2. Modo de Prompt de Texto

Permite criar itens no Jira usando prompts de texto em linguagem natural.

```
Escolha o modo (1, 2 ou 3): 2

Prompt: Crie uma história para o usuário poder fazer login com redes sociais
```

#### 3. Modo de Hierarquia Automática

Cria automaticamente uma hierarquia completa de itens (épico, história, tasks, subtasks) a partir de um único prompt.

```
Escolha o modo (1, 2 ou 3): 3

Prompt: Implementar sistema de login com redes sociais
```

### Exemplos de Uso

#### Criar uma História

```
Prompt: Crie uma história para permitir que o usuário faça login usando sua conta do Google
```

#### Criar um Épico

```
Prompt: Crie um épico para o sistema de autenticação com redes sociais
```

#### Criar uma Task

```
Prompt: Crie uma task para implementar a integração com a API do Google
```

#### Criar uma Hierarquia Completa

```
Prompt: Implementar sistema de notificações por email e push
```

## Estrutura do Projeto

```
pm-jira-cli/
├── __init__.py
├── cli.py                  # Interface de linha de comando
├── config.py               # Configurações e constantes
├── example_gpt_usage.py    # Exemplos de uso do GPT
├── gpt_service.py          # Serviço de integração com GPT
├── hierarchy_builder.py    # Construção de hierarquias de itens
├── items.py                # Classes para os diferentes tipos de itens
├── jira_service.py         # Serviço de integração com Jira
├── main.py                 # Ponto de entrada principal
├── prompt_processor.py     # Processamento de prompts
├── s3_service.py           # Serviço de armazenamento em S3
├── template_generator.py   # Geração de templates para itens
├── setup.sh                # Script de instalação
├── requirements.txt        # Dependências do projeto
└── tests/                  # Testes automatizados
```

### Descrição dos Módulos

- **cli.py**: Interface de linha de comando para interação com o usuário.
- **config.py**: Configurações e constantes do aplicativo.
- **gpt_service.py**: Serviço para integração com a API do GPT.
- **hierarchy_builder.py**: Construção de hierarquias de itens (épico, história, tasks, subtasks).
- **items.py**: Classes para os diferentes tipos de itens (Epic, Story, Task, etc.).
- **jira_service.py**: Serviço para integração com a API do Jira.
- **main.py**: Ponto de entrada principal do aplicativo.
- **prompt_processor.py**: Processamento de prompts de texto e extração de informações.
- **s3_service.py**: Serviço para armazenamento de contexto e itens no S3.
- **template_generator.py**: Geração de templates para itens com base em prompts.

## Solução de Problemas

### Problemas de Conexão com o Jira

- **Erro de autenticação**: Verifique se o email e o token de API do Jira estão corretos.
- **Erro de permissão**: Verifique se o usuário tem permissão para criar itens no projeto.
- **URL incorreta**: Verifique se a URL base do Jira está correta.

### Problemas com o S3

- **Erro de autenticação**: Verifique se as credenciais AWS estão corretas.
- **Bucket não encontrado**: Verifique se o bucket S3 existe e está acessível.
- **Permissões insuficientes**: Verifique se o usuário AWS tem permissões para ler e escrever no bucket.

### Problemas com o GPT

- **Erro de autenticação**: Verifique se a chave de API do OpenAI está correta.
- **Limite de requisições**: Verifique se você não atingiu o limite de requisições da API do OpenAI.
- **Modelo não disponível**: Verifique se o modelo especificado está disponível para sua conta.

### Outros Problemas

- **Dependências faltando**: Execute `pip install -r requirements.txt` para instalar todas as dependências.
- **Versão do Python**: Verifique se você está usando Python 3.8 ou superior.
- **Variáveis de ambiente**: Verifique se todas as variáveis de ambiente necessárias estão configuradas.

## Contribuição

Contribuições são bem-vindas! Por favor, siga estas etapas:

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um novo Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
