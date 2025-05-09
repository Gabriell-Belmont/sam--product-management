"""
Central configuration/constants for o aplicativo CLI de Product Managers.
"""
import os, codecs
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()


_raw = os.getenv("JIRA_BASE_URL", "")
# Converte sequências como '\x3a' de volta para ':'
JIRA_BASE_URL = codecs.decode(_raw, "unicode_escape")
# Configurações do Jira
# JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "https://your-company.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")  # Email do usuário Jira
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")  # Token de API do Jira
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "")  # Chave do projeto Jira padrão

# Campo personalizado para link de épico (varia conforme a instância do Jira)
# Normalmente é "customfield_10014" para Jira Cloud, mas pode variar
JIRA_EPIC_LINK_FIELD = os.environ.get("JIRA_EPIC_LINK_FIELD", "customfield_10014")

# Configurações do AWS S3 para armazenamento de contexto e itens
AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "pm-cli-memory")
AWS_S3_PREFIX = os.environ.get("AWS_S3_PREFIX", "contexts/")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Opcionalmente, as credenciais AWS podem ser configuradas aqui
# Se não fornecidas, o boto3 usará as credenciais do ambiente ou do perfil AWS
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# Configurações de armazenamento S3
S3_ITEM_RETENTION_DAYS = 90  # Número de dias para manter os itens no S3
S3_MAX_ITEMS_PER_REQUEST = 100  # Número máximo de itens a retornar por solicitação

# Tipos de itens suportados
ITEM_TYPES = {
    "épico": "Epic",
    "historia": "Story",
    "história": "Story",
    "task": "Task",
    "subtask": "Sub-task",
    "bug": "Bug",
    "sub-bug": "Sub-task"  # Sub-bug é tratado como subtask com label de bug
}

# Mapeamento de tipos de itens para prefixos no S3
S3_ITEM_TYPE_PREFIXES = {
    "Epic": "epics",
    "Story": "stories",
    "Task": "tasks",
    "Sub-task": "subtasks",
    "Bug": "bugs"
}

# Tipos de links do Jira
JIRA_LINK_TYPES = {
    "relacionado": "Relates",
    "bloqueia": "Blocks",
    "bloqueado_por": "is blocked by",
    "duplica": "Duplicates",
    "duplicado_por": "is duplicated by",
    "depende_de": "Depends",
    "dependente_de": "is depended on by"
}

# Configurações de logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configurações da API do GPT
GPT_ENABLED = os.environ.get("GPT_ENABLED", "true").lower() == "true"
GPT_API_KEY = os.environ.get("GPT_API_KEY", "")
GPT_MODEL = os.environ.get("GPT_MODEL", "gpt-4o")
GPT_MAX_TOKENS = int(os.environ.get("GPT_MAX_TOKENS", "2000"))
GPT_TEMPERATURE = float(os.environ.get("GPT_TEMPERATURE", "0.7"))
GPT_TIMEOUT = int(os.environ.get("GPT_TIMEOUT", "30"))  # Timeout em segundos
GPT_RETRY_ATTEMPTS = int(os.environ.get("GPT_RETRY_ATTEMPTS", "3"))
GPT_RETRY_DELAY = int(os.environ.get("GPT_RETRY_DELAY", "2"))  # Delay em segundos