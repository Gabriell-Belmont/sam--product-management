"""
Ponto de entrada principal do aplicativo CLI para Product Managers.
"""
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings

from app.modules.cli import prompt_item_type, prompt_for_details, confirm_creation, print_header
from config import ITEM_TYPES, S3_ITEM_TYPE_PREFIXES, GPT_ENABLED, GPT_API_KEY
from app.models.models import Epic, Story, Task, SubTask, Bug
from app.infra.s3_service import S3Service, S3ServiceError
from app.infra.jira_service import JiraService
from app.modules.prompt_processor import PromptProcessor, PromptProcessorError
from app.modules.template_generator import generate_item, TemplateGeneratorError
from app.modules.hierarchy_builder import (
    build_hierarchy, link_items, review_and_confirm, HierarchyBuilderError
)
load_dotenv()
# Importação condicional do serviço GPT
try:
    from app.infra.gpt_service import GPTService, GPTServiceError
    gpt_available = True
except ImportError:
    gpt_available = False


def create_item_instance(item_type: str, details: Dict[str, Any]):
    """
    Cria uma instância do tipo de item apropriado com base nos detalhes fornecidos.
    
    Args:
        item_type: O tipo de item a ser criado.
        details: Os detalhes do item.
        
    Returns:
        Uma instância da classe apropriada.
    """
    try:
        # Primeiro, formata os detalhes de acordo com o template
        formatted_details = generate_item(details, item_type)
        
        # Agora cria a instância com os detalhes formatados
        if item_type == "épico":
            return Epic(
                summary=formatted_details["summary"],
                description=formatted_details["description"],
                labels=formatted_details["labels"],
                assignee=formatted_details["assignee"],
                priority=formatted_details["priority"],
                epic_name=formatted_details.get("epic_name", "")
            )
        
        elif item_type in ["história", "historia"]:
            return Story(
                summary=formatted_details["summary"],
                description=formatted_details["description"],
                labels=formatted_details["labels"],
                assignee=formatted_details["assignee"],
                priority=formatted_details["priority"],
                epic_link=formatted_details.get("epic_link"),
                acceptance_criteria=formatted_details.get("acceptance_criteria", "")
            )
        
        elif item_type == "task":
            return Task(
                summary=formatted_details["summary"],
                description=formatted_details["description"],
                labels=formatted_details["labels"],
                assignee=formatted_details["assignee"],
                priority=formatted_details["priority"],
                story_link=formatted_details.get("story_link")
            )
        
        elif item_type == "subtask":
            return SubTask(
                summary=formatted_details["summary"],
                description=formatted_details["description"],
                labels=formatted_details["labels"],
                assignee=formatted_details["assignee"],
                priority=formatted_details["priority"],
                parent_key=formatted_details["parent_key"]
            )
        
        elif item_type == "bug":
            return Bug(
                summary=formatted_details["summary"],
                description=formatted_details["description"],
                labels=formatted_details["labels"],
                assignee=formatted_details["assignee"],
                priority=formatted_details["priority"],
                severity=formatted_details.get("severity", "Medium"),
                steps_to_reproduce=formatted_details.get("steps_to_reproduce", "")
            )
        
        elif item_type == "sub-bug":
            # Sub-bug é uma subtask com label de bug
            subtask = SubTask(
                summary=formatted_details["summary"],
                description=formatted_details["description"],
                labels=formatted_details["labels"] + ["bug"] if "bug" not in [label.lower() for label in formatted_details["labels"]] else formatted_details["labels"],
                assignee=formatted_details["assignee"],
                priority=formatted_details["priority"],
                parent_key=formatted_details["parent_key"]
            )
            return subtask
        
        raise ValueError(f"Tipo de item desconhecido: {item_type}")
    
    except TemplateGeneratorError as e:
        print(f"Aviso: Erro ao formatar item com template: {str(e)}")
        # Em caso de erro no template, usa os detalhes originais
        
        if item_type == "épico":
            return Epic(
                summary=details["summary"],
                description=details["description"],
                labels=details["labels"],
                assignee=details["assignee"],
                priority=details["priority"],
                epic_name=details.get("epic_name", "")
            )
        
        elif item_type in ["história", "historia"]:
            return Story(
                summary=details["summary"],
                description=details["description"],
                labels=details["labels"],
                assignee=details["assignee"],
                priority=details["priority"],
                epic_link=details.get("epic_link"),
                acceptance_criteria=details.get("acceptance_criteria", "")
            )
        
        elif item_type == "task":
            return Task(
                summary=details["summary"],
                description=details["description"],
                labels=details["labels"],
                assignee=details["assignee"],
                priority=details["priority"],
                story_link=details.get("story_link")
            )
        
        elif item_type == "subtask":
            return SubTask(
                summary=details["summary"],
                description=details["description"],
                labels=details["labels"],
                assignee=details["assignee"],
                priority=details["priority"],
                parent_key=details["parent_key"]
            )
        
        elif item_type == "bug":
            return Bug(
                summary=details["summary"],
                description=details["description"],
                labels=details["labels"],
                assignee=details["assignee"],
                priority=details["priority"],
                severity=details.get("severity", "Medium"),
                steps_to_reproduce=details.get("steps_to_reproduce", "")
            )
        
        elif item_type == "sub-bug":
            # Sub-bug é uma subtask com label de bug
            subtask = SubTask(
                summary=details["summary"],
                description=details["description"],
                labels=details["labels"] + ["bug"],
                assignee=details["assignee"],
                priority=details["priority"],
                parent_key=details["parent_key"]
            )
            return subtask
        
        raise ValueError(f"Tipo de item desconhecido: {item_type}")


def get_recent_items(project_key: str, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
    """
    Obtém itens recentes do S3 para usar como contexto.
    
    Args:
        project_key: Chave do projeto Jira.
        days: Número de dias para olhar para trás.
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dicionário com listas de itens por tipo.
    """
    try:
        s3_service = S3Service()        
        # Obtém o histórico de itens por tipo
        history = s3_service.get_item_history(project_key, days=days)
        
        return history
    except S3ServiceError as e:
        print(f"Aviso: Não foi possível carregar o histórico de itens: {str(e)}")
        return {}


def save_item_to_s3(project_key: str, item_type: str, item: object, metadata: Dict[str, Any] = None) -> str:
    """
    Salva um item no S3.
    
    Args:
        project_key: Chave do projeto Jira.
        item_type: Tipo do item (epic, story, task, etc).
        item: Item a ser salvo.
        metadata: Metadados adicionais.
        
    Returns:
        str: Chave S3 onde o item foi salvo.
    """
    try:
        s3_service = S3Service()
        
        # Mapeia o tipo de item para o prefixo S3
        s3_item_type = S3_ITEM_TYPE_PREFIXES.get(ITEM_TYPES[item_type], item_type)
        
        # Adiciona metadados padrão
        if metadata is None:
            metadata = {}
        metadata.update({
            "created_at": datetime.utcnow().isoformat(),
            "item_type": item_type,
            "project": project_key
        })
        
        # Salva o item no S3
        key = s3_service.save_item(
            project_key=project_key,
            item_type=s3_item_type,
            item=item,
            metadata=metadata
        )
        
        return key
    except S3ServiceError as e:
        print(f"Aviso: Não foi possível salvar o item no S3: {str(e)}")
        return ""


def process_prompt_flow(prompt_text: str, project_key: str = "SAM", force_hierarchy: bool = False) -> Dict[str, Any]:
    """
    Processa um prompt de texto para criar um item no Jira.
    
    Args:
        prompt_text: Texto do prompt do usuário.
        project_key: Chave do projeto Jira.
        force_hierarchy: Se True, força a criação de uma hierarquia completa.
        
    Returns:
        Dict[str, Any]: Resultado do processamento.
    """
    try:
        # Inicializa os serviços
        s3_service = S3Service()
        jira_service = JiraService(project_key=project_key)
        
        # Inicializa o processador de prompts
        processor = PromptProcessor(
            s3_service=s3_service,
            jira_service=jira_service,
            user_id=os.environ.get("USER", "default_user"),
            project_key=project_key
        )
        
        # Se forçar hierarquia, adiciona indicação no prompt
        if force_hierarchy:
            prompt_text = f"[criar hierarquia completa] {prompt_text}"
        
        # Processa o prompt
        result = processor.process_prompt(prompt_text)
        
        if result["success"]:
            if result["item_type"] == "hierarchy":
                print("\n=== Hierarquia criada com sucesso ===")
                for item in result.get("items", []):
                    if "jira_key" in item:
                        print(f"[{item['type']}] {item['summary']} - {item['jira_key']}")
                
                if result.get("s3_keys"):
                    print(f"\n{len(result['s3_keys'])} itens armazenados no S3")
            else:
                print(f"\nItem criado com sucesso no Jira: {result['jira_response'].get('key')}")
                if result.get("s3_key"):
                    print(f"Item armazenado no S3: {result['s3_key']}")
        else:
            print(f"\nErro ao processar o prompt: {result.get('error', 'Erro desconhecido')}")
        
        return result
    
    except Exception as e:
        print(f"\nErro ao processar o prompt: {str(e)}")
        return {"success": False, "error": str(e)}


def process_hierarchy_flow(prompt_text: str, project_key: str = "SAM") -> Dict[str, Any]:
    """
    Processa um prompt de texto para criar uma hierarquia completa de itens no Jira.
    
    Args:
        prompt_text: Texto do prompt do usuário.
        project_key: Chave do projeto Jira.
        
    Returns:
        Dict[str, Any]: Resultado do processamento.
    """
    return process_prompt_flow(prompt_text, project_key, force_hierarchy=True)


def enrich_with_gpt(details: Dict[str, Any], item_type: str) -> Dict[str, Any]:
    """
    Enriquece os detalhes do item usando o GPT, se disponível.
    
    Args:
        details: Detalhes do item.
        item_type: Tipo de item.
        
    Returns:
        Dict[str, Any]: Detalhes enriquecidos.
    """
    if not gpt_available or not GPT_ENABLED:
        return details
    
    try:
        # Inicializa o serviço GPT
        gpt_service = GPTService()
        
        # Enriquece o conteúdo
        enriched_details = gpt_service.create_jira_content(item_type, details)
        
        print(f"Conteúdo enriquecido com GPT para {item_type}")
        return enriched_details
    
    except Exception as e:
        print(f"Aviso: Não foi possível enriquecer o conteúdo com GPT: {str(e)}")
        return details


def main():
    """Função principal do aplicativo."""
    try:
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        print_header()
        required_vars = [
            "JIRA_BASE_URL",
            "JIRA_EMAIL",
            "JIRA_API_TOKEN",
            "JIRA_PROJECT_KEY",
            "AWS_S3_BUCKET",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]

        missing = [v for v in required_vars if not os.getenv(v)]
        if missing:
            print(f"❌ Variáveis de ambiente faltando: {', '.join(missing)}")
            sys.exit(1)

        print("Bem-vindo ao PM JIRA CLI - Criação de Demandas via Prompt")
        
        # Informa sobre o status do GPT
        if gpt_available and GPT_ENABLED:
            print("\n[✓] Integração com GPT ativada para processamento avançado de prompts")
        else:
            if not gpt_available:
                print("\n[!] Integração com GPT não disponível (módulo não encontrado)")
            elif not GPT_ENABLED:
                print("\n[!] Integração com GPT desativada (GPT_ENABLED=false)")
        
        print("\nVocê pode criar itens no Jira de três maneiras:")
        print("1. Usando o assistente interativo (modo padrão)")
        print("2. Usando um prompt de texto (modo avançado)")
        print("3. Criando uma hierarquia completa (épico, história, tasks, subtasks)")
        
        mode = input("\nEscolha o modo (1, 2 ou 3): ").strip()
        
        # Projeto padrão para testes
        project_key = "SAM"  # Em uma versão completa, o usuário escolheria o projeto
        
        if mode == "3":
            # Modo de hierarquia automática
            print("\n=== Modo de Hierarquia Automática ===")
            print("Digite seu prompt descrevendo a funcionalidade que deseja implementar.")
            print("O sistema criará automaticamente uma hierarquia completa de itens:")
            print("- Um épico para agrupar a funcionalidade")
            print("- Uma história de usuário detalhando a necessidade")
            print("- Tasks para implementação (backend, frontend, testes)")
            print("- Subtasks para cada task")
            print("Digite 'sair' para encerrar.")
            print("\nExemplo: 'Implementar sistema de login com redes sociais'")
            
            if gpt_available and GPT_ENABLED:
                print("\n[✓] O GPT será usado para gerar uma hierarquia mais detalhada e contextualizada")
            
            while True:
                prompt_text = input("\nPrompt: ").strip()
                
                if prompt_text.lower() in ["sair", "exit", "quit"]:
                    break
                
                if not prompt_text:
                    print("Prompt vazio. Tente novamente.")
                    continue
                
                # Processa o prompt com hierarquia forçada
                result = process_hierarchy_flow(prompt_text, project_key)
                
                # Pergunta se o usuário deseja criar outra hierarquia
                if input("\nDeseja criar outra hierarquia? (s/n): ").strip().lower() != "s":
                    break
        
        elif mode == "2":
            # Modo de prompt de texto
            print("\n=== Modo de Prompt de Texto ===")
            print("Digite seu prompt descrevendo o item que deseja criar.")
            print("Inclua o tipo de item (épico, história, task, etc.) e os detalhes relevantes.")
            print("Digite 'sair' para encerrar.")
            print("\nExemplo: 'Crie uma história para o usuário poder fazer login com redes sociais'")
            print("Dica: Você pode solicitar uma hierarquia incluindo 'criar hierarquia' no prompt.")
            
            if gpt_available and GPT_ENABLED:
                print("\n[✓] O GPT será usado para extrair informações e enriquecer o conteúdo do seu prompt")
                print("     Você pode usar linguagem natural e o sistema extrairá os detalhes necessários")
            
            while True:
                prompt_text = input("\nPrompt: ").strip()
                
                if prompt_text.lower() in ["sair", "exit", "quit"]:
                    break
                
                if not prompt_text:
                    print("Prompt vazio. Tente novamente.")
                    continue
                
                # Processa o prompt
                result = process_prompt_flow(prompt_text, project_key)
                
                # Pergunta se o usuário deseja criar outro item
                if input("\nDeseja criar outro item? (s/n): ").strip().lower() != "s":
                    break
        
        else:
            # Modo assistente interativo (original)
            print("\n=== Modo Assistente Interativo ===")
            print("Neste modo, você será guiado passo a passo para criar um item.")
            
            if gpt_available and GPT_ENABLED:
                print("\n[✓] O GPT será usado para enriquecer o conteúdo dos itens criados")
            
            # Pergunta ao usuário qual tipo de item ele deseja criar
            item_type = prompt_item_type()
            
            print(f"\nVocê escolheu criar um(a): {item_type}")
            
            # Carrega contexto recente do S3 (será usado para sugestões inteligentes)
            recent_items = get_recent_items(project_key)
            
            if recent_items:
                print(f"\nEncontrados {sum(len(items) for items in recent_items.values())} itens recentes para referência.")
            
            # Solicita detalhes do item
            details = prompt_for_details(item_type)
            
            # Enriquece os detalhes com GPT se disponível
            if gpt_available and GPT_ENABLED:
                details = enrich_with_gpt(details, item_type)
            
            if confirm_creation(item_type, details):
                # Cria a instância do item
                item = create_item_instance(item_type, details)
                
                # Salva o item no S3
                s3_key = save_item_to_s3(
                    project_key=project_key,
                    item_type=item_type,
                    item=item,
                    metadata={"source": "cli", "user": os.environ.get("USER", "unknown")}
                )
                
                if s3_key:
                    print(f"\nItem armazenado no S3 com sucesso: {s3_key}")
                
                # Inicializa o serviço Jira e cria o item
                try:
                    jira_service = JiraService(project_key=project_key)
                    
                    # Cria o item no Jira com base no tipo
                    if item_type == "épico":
                        response = jira_service.create_epic(
                            summary=details["summary"],
                            description=details["description"],
                            epic_name=details.get("epic_name", details["summary"]),
                            labels=details.get("labels", [])
                        )
                    elif item_type in ["história", "historia"]:
                        response = jira_service.create_story(
                            summary=details["summary"],
                            description=details["description"],
                            epic_key=details.get("epic_link"),
                            labels=details.get("labels", [])
                        )
                    elif item_type == "task":
                        response = jira_service.create_task(
                            summary=details["summary"],
                            description=details["description"],
                            parent_key=details.get("story_link"),
                            labels=details.get("labels", [])
                        )
                    elif item_type == "subtask":
                        response = jira_service.create_subtask(
                            summary=details["summary"],
                            description=details["description"],
                            parent_key=details["parent_key"],
                            labels=details.get("labels", [])
                        )
                    elif item_type == "bug":
                        response = jira_service.create_bug(
                            summary=details["summary"],
                            description=details["description"],
                            parent_key=details.get("parent_key"),
                            labels=details.get("labels", [])
                        )
                    elif item_type == "sub-bug":
                        response = jira_service.create_sub_bug(
                            summary=details["summary"],
                            description=details["description"],
                            parent_key=details["parent_key"],
                            labels=details.get("labels", [])
                        )
                    
                    print(f"\nItem criado com sucesso no Jira: {response.get('key')}")
                
                except Exception as e:
                    print(f"\nErro ao criar item no Jira: {str(e)}")
            else:
                print("\nOperação cancelada pelo usuário.")
        
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except S3ServiceError as e:
        print(f"\nErro no serviço S3: {str(e)}")
        sys.exit(1)
    except PromptProcessorError as e:
        print(f"\nErro no processador de prompts: {str(e)}")
        sys.exit(1)
    except HierarchyBuilderError as e:
        print(f"\nErro na construção da hierarquia: {str(e)}")
        sys.exit(1)
    except GPTServiceError as e:
        print(f"\nErro no serviço GPT: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro: {str(e)}")
        sys.exit(1)

def salvar_em_arquivo(strings, caminho_arquivo):
    """
    Recebe uma lista de strings e salva cada item em uma linha de um arquivo texto.
    :param strings: lista de strings a serem gravadas
    :param caminho_arquivo: caminho (com nome) do arquivo de saída, ex. "vars.txt"
    """
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        for s in strings:
            f.write(f"{s}\n")

if __name__ == "__main__":
    main()
