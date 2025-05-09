#!/bin/bash

# Script de instalação para o aplicativo CLI de Product Managers

echo "=== Instalando o aplicativo CLI de Product Managers ==="

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não encontrado. Por favor, instale o Python 3.8 ou superior."
    exit 1
fi

# Verifica a versão do Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc) -eq 1 ]]; then
    echo "Erro: Python 3.8 ou superior é necessário. Versão atual: $PYTHON_VERSION"
    exit 1
fi

# Cria e ativa um ambiente virtual
echo "Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# Atualiza pip
echo "Atualizando pip..."
pip install --upgrade pip

# Instala as dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Verifica se a instalação do OpenAI foi bem-sucedida
if pip show openai &> /dev/null; then
    echo "Biblioteca OpenAI instalada com sucesso."
else
    echo "Aviso: Não foi possível instalar a biblioteca OpenAI. A integração com GPT não estará disponível."
fi

# Configura as variáveis de ambiente
echo "Configurando variáveis de ambiente..."
if [ ! -f .env ]; then
    cat > .env << EOF
# Configurações do Jira
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=

# Configurações do AWS S3
AWS_S3_BUCKET=pm-cli-memory
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Configurações do GPT
GPT_ENABLED=true
GPT_API_KEY=
GPT_MODEL=gpt-4o
GPT_MAX_TOKENS=2000
GPT_TEMPERATURE=0.7
EOF
    echo "Arquivo .env criado. Por favor, edite-o com suas configurações."
else
    echo "Arquivo .env já existe. Verifique se todas as configurações necessárias estão presentes."
fi

# Verifica se o arquivo .env contém a configuração do GPT
if ! grep -q "GPT_API_KEY" .env; then
    echo "Adicionando configurações do GPT ao arquivo .env..."
    cat >> .env << EOF

# Configurações do GPT
GPT_ENABLED=true
GPT_API_KEY=
GPT_MODEL=gpt-4o
GPT_MAX_TOKENS=2000
GPT_TEMPERATURE=0.7
EOF
fi

echo "Instalação concluída!"
echo "Para ativar o ambiente virtual, execute: source venv/bin/activate"
echo "Para configurar as variáveis de ambiente, edite o arquivo .env"
echo "Para testar a integração com o GPT, execute: python test_gpt_service.py"
echo "Para iniciar o aplicativo, execute: python main.py"
