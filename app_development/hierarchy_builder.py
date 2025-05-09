"""
Módulo para construção hierárquica de itens no Jira.

Este módulo contém funções para identificar quando o usuário não especificou o tipo de item,
criar automaticamente a hierarquia completa (épico, história, task, subtask) e estabelecer
as relações corretas entre os itens.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

# try:
    # Try importing from app_development package first (for production)
from app_development.items import BaseItem, Epic, Story, Task, SubTask, Bug
from app_development.jira_service import JiraService
# from app_development.prompt_processor import PromptProcessor
from app_development.template_generator import generate_item, TemplateGeneratorError
# except ImportError:
#     # Fall back to local import (for testing)
#     from items import BaseItem, Epic, Story, Task, SubTask, Bug
#     from jira_service import JiraService
#     from prompt_processor import PromptProcessor
#     from template_generator import generate_item, TemplateGeneratorError

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('hierarchy_builder')


class HierarchyBuilderError(Exception):
    """Exceção personalizada para erros do construtor de hierarquia."""
    pass


def detect_missing_type(prompt_dict: Dict[str, Any]) -> str:
    """
    Identifica quando o usuário não especificou o tipo de item e sugere um tipo padrão.
    
    Args:
        prompt_dict: Dicionário com os dados do prompt processado.
        
    Returns:
        str: Tipo de item sugerido ou "auto" para construção hierárquica completa.
    """
    # Verifica se o tipo já foi identificado
    if "type" in prompt_dict and prompt_dict["type"] and prompt_dict["type"] != "unknown":
        return prompt_dict["type"]
    
    # Verifica se o usuário solicitou explicitamente uma hierarquia completa
    normalized_text = prompt_dict.get("normalized_text", "").lower()
    if any(term in normalized_text for term in [
        "hierarquia completa", "criar hierarquia", "estrutura completa", 
        "criar estrutura", "auto hierarquia", "auto-hierarquia"
    ]):
        return "auto"
    
    # Analisa o texto para identificar se é um tema amplo (épico)
    if any(term in normalized_text for term in [
        "iniciativa", "objetivo estratégico", "visão", "tema", "grande funcionalidade"
    ]):
        return "épico"
    
    # Analisa o texto para identificar se é uma funcionalidade para o usuário (história)
    if any(term in normalized_text for term in [
        "como usuário", "funcionalidade", "feature", "como cliente", 
        "gostaria de", "quero poder", "preciso"
    ]):
        return "história"
    
    # Analisa o texto para identificar se é uma tarefa técnica (task)
    if any(term in normalized_text for term in [
        "implementar", "desenvolver", "criar", "configurar", "integrar", 
        "refatorar", "otimizar", "ajustar"
    ]):
        return "task"
    
    # Se não conseguir identificar, assume que é uma história (mais comum)
    return "história"


def build_hierarchy(prompt_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Constrói uma hierarquia completa de itens com base no prompt.
    
    Args:
        prompt_dict: Dicionário com os dados do prompt processado.
        processor: Instância do processador de prompts.
        
    Returns:
        List[Dict[str, Any]]: Lista de itens na hierarquia, ordenados de pai para filho.
    """
    from app_development import PromptProcessor as processor
    try:
        raw_text = prompt_dict.get("raw_text", "")
        normalized_text = prompt_dict.get("normalized_text", "").lower()
        
        # Extrai campos básicos do prompt
        fields = processor.extract_fields(raw_text, "história")  # Usa história como base para extração
        
        # Lista para armazenar os itens da hierarquia
        hierarchy_items = []
        
        # 1. Cria o épico
        epic_summary = _generate_epic_summary(fields.get("summary", ""))
        epic_description = _generate_epic_description(fields)
        
        epic = {
            "type": "épico",
            "summary": epic_summary,
            "description": epic_description,
            "labels": fields.get("labels", []),
            "epic_name": epic_summary,
            "objective": _extract_objective(fields, normalized_text),
            "benefits": _extract_benefits(fields, normalized_text)
        }
        
        # Adiciona o épico à hierarquia
        hierarchy_items.append(epic)
        
        # 2. Cria a história
        story_summary = fields.get("summary", "")
        story_description = fields.get("description", "")
        
        # Extrai componentes da história de usuário
        as_a = fields.get("as_a", "")
        i_want = fields.get("i_want", "")
        so_that = fields.get("so_that", "")
        
        # Se não tiver o formato específico, tenta extrair do texto
        if not (as_a and i_want):
            as_a, i_want, so_that = _extract_user_story_components(normalized_text)
        
        story = {
            "type": "história",
            "summary": story_summary,
            "description": story_description,
            "labels": fields.get("labels", []),
            "as_a": as_a,
            "i_want": i_want,
            "so_that": so_that,
            "acceptance_criteria": fields.get("acceptance_criteria", ""),
            "epic_link": None  # Será preenchido após a criação do épico
        }
        
        # Adiciona a história à hierarquia
        hierarchy_items.append(story)
        
        # 3. Cria as tasks
        tasks = _generate_tasks(fields, normalized_text)
        
        for task in tasks:
            task_item = {
                "type": "task",
                "summary": task["summary"],
                "description": task["description"],
                "labels": fields.get("labels", []),
                "story_link": None  # Será preenchido após a criação da história
            }
            
            # Adiciona a task à hierarquia
            hierarchy_items.append(task_item)
            
            # 4. Cria as subtasks para cada task
            subtasks = task.get("subtasks", [])
            
            for subtask in subtasks:
                subtask_item = {
                    "type": "subtask",
                    "summary": subtask["summary"],
                    "description": subtask["description"],
                    "labels": fields.get("labels", []),
                    "parent_key": None  # Será preenchido após a criação da task
                }
                
                # Adiciona a subtask à hierarquia
                hierarchy_items.append(subtask_item)
        
        logger.info(f"Hierarquia construída com {len(hierarchy_items)} itens")
        return hierarchy_items
    
    except Exception as e:
        logger.error(f"Erro ao construir hierarquia: {str(e)}")
        raise HierarchyBuilderError(f"Erro ao construir hierarquia: {str(e)}")


def link_items(items_list: List[Dict[str, Any]], jira_service: JiraService) -> List[Dict[str, Any]]:
    """
    Cria os itens no Jira e estabelece as relações corretas entre eles.
    
    Args:
        items_list: Lista de itens na hierarquia, ordenados de pai para filho.
        jira_service: Instância do serviço Jira.
        
    Returns:
        List[Dict[str, Any]]: Lista de itens criados com suas chaves Jira.
    """
    try:
        created_items = []
        
        # Dicionário para armazenar as chaves Jira dos itens criados
        item_keys = {}
        
        # Cria os itens no Jira e estabelece as relações
        for i, item in enumerate(items_list):
            item_type = item["type"]
            
            # Atualiza os links com base nos itens já criados
            if item_type == "história":
                # Vincula a história ao épico
                if "épico" in item_keys:
                    item["epic_link"] = item_keys["épico"]
            
            elif item_type == "task":
                # Vincula a task à história
                if "história" in item_keys:
                    item["story_link"] = item_keys["história"]
            
            elif item_type == "subtask":
                # Vincula a subtask à task
                # Encontra a task pai (a última task criada)
                for j in range(i-1, -1, -1):
                    if items_list[j]["type"] == "task" and "jira_key" in items_list[j]:
                        item["parent_key"] = items_list[j]["jira_key"]
                        break
            
            # Cria o item no Jira
            response = _create_item_in_jira(item, jira_service)
            
            # Armazena a chave Jira do item criado
            if "key" in response:
                item["jira_key"] = response["key"]
                
                # Armazena a chave do primeiro item de cada tipo
                if item_type not in item_keys:
                    item_keys[item_type] = response["key"]
            
            # Adiciona o item criado à lista
            created_items.append(item)
        
        # Estabelece links adicionais se necessário
        for item in created_items:
            if "jira_key" in item:
                if item["type"] == "história" and "epic_link" in item and item["epic_link"]:
                    jira_service.link_to_epic(item["jira_key"], item["epic_link"])
                
                elif item["type"] == "task" and "story_link" in item and item["story_link"]:
                    jira_service.link_parent_child(item["story_link"], item["jira_key"])
        
        logger.info(f"Criados {len(created_items)} itens na hierarquia")
        return created_items
    
    except Exception as e:
        logger.error(f"Erro ao criar e vincular itens: {str(e)}")
        raise HierarchyBuilderError(f"Erro ao criar e vincular itens: {str(e)}")


def review_and_confirm(items_list: List[Dict[str, Any]], cli_interface=None) -> bool:
    """
    Permite que o usuário revise e confirme a hierarquia antes de criar os itens no Jira.
    
    Args:
        items_list: Lista de itens na hierarquia.
        cli_interface: Interface CLI para interação com o usuário.
        
    Returns:
        bool: True se o usuário confirmar, False caso contrário.
    """
    print("\n=== Revisão da Hierarquia ===")
    print("Os seguintes itens serão criados no Jira:")
    
    for i, item in enumerate(items_list):
        indent = ""
        if item["type"] == "história":
            indent = "  "
        elif item["type"] == "task":
            indent = "    "
        elif item["type"] == "subtask":
            indent = "      "
        
        print(f"{indent}[{item['type']}] {item['summary']}")
    
    # Se tiver uma interface CLI específica, usa ela
    if cli_interface and hasattr(cli_interface, "confirm"):
        return cli_interface.confirm("Deseja criar estes itens no Jira?")
    
    # Caso contrário, usa input padrão
    response = input("\nDeseja criar estes itens no Jira? (s/n): ").strip().lower()
    return response == "s"


def _generate_epic_summary(story_summary: str) -> str:
    """
    Gera um título para o épico com base no título da história.
    
    Args:
        story_summary: Título da história.
        
    Returns:
        str: Título gerado para o épico.
    """
    # Remove detalhes específicos e generaliza o título
    # Exemplo: "Implementar login com Google" -> "Sistema de autenticação"
    
    # Palavras-chave para categorização
    auth_keywords = ["login", "autenticar", "senha", "credenciais", "acesso"]
    user_keywords = ["usuário", "perfil", "conta", "cadastro", "registro"]
    payment_keywords = ["pagamento", "compra", "checkout", "carrinho", "pedido"]
    report_keywords = ["relatório", "dashboard", "gráfico", "estatística", "análise"]
    
    story_lower = story_summary.lower()
    
    # Categoriza com base nas palavras-chave
    if any(keyword in story_lower for keyword in auth_keywords):
        return "Sistema de autenticação e autorização"
    elif any(keyword in story_lower for keyword in user_keywords):
        return "Gestão de usuários e perfis"
    elif any(keyword in story_lower for keyword in payment_keywords):
        return "Sistema de pagamentos e checkout"
    elif any(keyword in story_lower for keyword in report_keywords):
        return "Relatórios e dashboards"
    
    # Se não encontrar uma categoria específica, extrai o tema principal
    # Exemplo: "Implementar filtro de produtos por categoria" -> "Sistema de filtros e busca"
    words = story_lower.split()
    nouns = []
    
    # Lista de verbos comuns para remover
    common_verbs = ["implementar", "criar", "desenvolver", "adicionar", "permitir", "fazer"]
    
    for word in words:
        if word not in common_verbs and len(word) > 3:
            nouns.append(word)
    
    if nouns:
        # Usa o primeiro substantivo como base para o título do épico
        return f"Sistema de {nouns[0]}"
    
    # Fallback: usa o título da história com um prefixo genérico
    return f"Funcionalidade: {story_summary}"


def _generate_epic_description(fields: Dict[str, Any]) -> str:
    """
    Gera uma descrição para o épico com base nos campos extraídos.
    
    Args:
        fields: Campos extraídos do prompt.
        
    Returns:
        str: Descrição gerada para o épico.
    """
    description = "Descrição\nVisão geral\n"
    description += fields.get("description", "Este épico agrupa funcionalidades relacionadas.") + "\n\n"
    
    # Adiciona objetivo
    objective = fields.get("objective", "Melhorar a experiência do usuário e adicionar novas funcionalidades.")
    description += f"Objetivo: \n{objective}\n\n"
    
    # Adiciona benefícios
    benefits = fields.get("benefits", "- Melhor experiência do usuário\n- Aumento na retenção\n- Redução de custos operacionais")
    description += "Benefícios: \n"
    
    # Formata os benefícios como lista
    benefits_list = benefits.split("\n")
    for benefit in benefits_list:
        benefit = benefit.strip()
        if benefit:
            # Remove marcadores existentes para evitar duplicação
            benefit = re.sub(r'^[•\-\*]\s*', '', benefit)
            description += f"• {benefit}\n"
    
    return description.strip()


def _extract_objective(fields: Dict[str, Any], normalized_text: str) -> str:
    """
    Extrai ou gera um objetivo para o épico.
    
    Args:
        fields: Campos extraídos do prompt.
        normalized_text: Texto normalizado do prompt.
        
    Returns:
        str: Objetivo extraído ou gerado.
    """
    # Se já tiver um objetivo nos campos, usa ele
    if "objective" in fields and fields["objective"]:
        return fields["objective"]
    
    # Tenta extrair do texto normalizado
    objective_match = re.search(r'objetivo[:\s]+(.+?)(?:\n|$)', normalized_text)
    if objective_match:
        return objective_match.group(1).strip()
    
    # Gera um objetivo com base no contexto
    if "as_a" in fields and "i_want" in fields:
        return f"Permitir que {fields['as_a']} possa {fields['i_want']}"
    
    # Objetivo genérico
    return "Melhorar a experiência do usuário e adicionar novas funcionalidades relacionadas."


def _extract_benefits(fields: Dict[str, Any], normalized_text: str) -> str:
    """
    Extrai ou gera benefícios para o épico.
    
    Args:
        fields: Campos extraídos do prompt.
        normalized_text: Texto normalizado do prompt.
        
    Returns:
        str: Benefícios extraídos ou gerados.
    """
    # Se já tiver benefícios nos campos, usa eles
    if "benefits" in fields and fields["benefits"]:
        return fields["benefits"]
    
    # Tenta extrair do texto normalizado
    benefits_match = re.search(r'benefícios[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', normalized_text)
    if benefits_match:
        return benefits_match.group(1).strip()
    
    # Gera benefícios com base no contexto
    if "so_that" in fields and fields["so_that"]:
        return f"• {fields['so_that']}\n• Melhoria na experiência do usuário\n• Aumento na satisfação do cliente"
    
    # Benefícios genéricos
    return "• Melhoria na experiência do usuário\n• Aumento na retenção de usuários\n• Redução de custos operacionais"


def _extract_user_story_components(text: str) -> Tuple[str, str, str]:
    """
    Extrai os componentes de uma história de usuário do texto.
    
    Args:
        text: Texto do prompt.
        
    Returns:
        Tuple[str, str, str]: Componentes da história (as_a, i_want, so_that).
    """
    as_a = ""
    i_want = ""
    so_that = ""
    
    # Tenta extrair "Como..."
    as_a_match = re.search(r'como[:\s]+(.+?)(?:\n|$|gostaria|quero|para)', text, re.IGNORECASE)
    if as_a_match:
        as_a = as_a_match.group(1).strip()
    
    # Tenta extrair "Gostaria..."
    i_want_match = re.search(r'(?:gostaria|quero)[:\s]+(.+?)(?:\n|$|para)', text, re.IGNORECASE)
    if i_want_match:
        i_want = i_want_match.group(1).strip()
    
    # Tenta extrair "Para..."
    so_that_match = re.search(r'para[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
    if so_that_match:
        so_that = so_that_match.group(1).strip()
    
    # Se não encontrou no formato específico, tenta inferir
    if not as_a:
        # Assume que o usuário é o ator principal
        as_a = "usuário do sistema"
    
    if not i_want:
        # Tenta extrair o objetivo principal do texto
        action_verbs = ["poder", "conseguir", "realizar", "fazer", "visualizar", "acessar", "gerenciar"]
        for verb in action_verbs:
            verb_match = re.search(f'{verb}[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
            if verb_match:
                i_want = f"{verb} {verb_match.group(1).strip()}"
                break
        
        # Se ainda não encontrou, usa o texto completo
        if not i_want:
            i_want = text
    
    return as_a, i_want, so_that


def _generate_tasks(fields: Dict[str, Any], normalized_text: str) -> List[Dict[str, Any]]:
    """
    Gera tasks com base nos campos extraídos e no texto normalizado.
    
    Args:
        fields: Campos extraídos do prompt.
        normalized_text: Texto normalizado do prompt.
        
    Returns:
        List[Dict[str, Any]]: Lista de tasks geradas.
    """
    tasks = []
    
    # Verifica se há critérios de aceitação para gerar tasks
    if "acceptance_criteria" in fields and fields["acceptance_criteria"]:
        criteria = fields["acceptance_criteria"].split("\n")
        
        for i, criterion in enumerate(criteria):
            criterion = criterion.strip()
            if criterion:
                # Remove marcadores existentes
                criterion = re.sub(r'^[•\-\*]\s*', '', criterion)
                
                # Cria uma task para cada critério de aceitação
                task = {
                    "summary": f"Implementar: {criterion}",
                    "description": f"Esta task implementa o seguinte critério de aceitação:\n\n{criterion}",
                    "subtasks": _generate_subtasks(criterion)
                }
                
                tasks.append(task)
    
    # Se não houver critérios de aceitação, gera tasks padrão
    if not tasks:
        # Task para implementação do backend
        tasks.append({
            "summary": "Implementar backend",
            "description": "Desenvolver a lógica de negócio e APIs necessárias no backend.",
            "subtasks": [
                {
                    "summary": "Criar modelo de dados",
                    "description": "Definir e implementar o modelo de dados necessário."
                },
                {
                    "summary": "Implementar endpoints da API",
                    "description": "Desenvolver os endpoints da API REST."
                },
                {
                    "summary": "Escrever testes unitários",
                    "description": "Implementar testes unitários para garantir a qualidade do código."
                }
            ]
        })
        
        # Task para implementação do frontend
        tasks.append({
            "summary": "Implementar frontend",
            "description": "Desenvolver a interface de usuário e integração com o backend.",
            "subtasks": [
                {
                    "summary": "Criar componentes de UI",
                    "description": "Desenvolver os componentes visuais da interface."
                },
                {
                    "summary": "Implementar integração com API",
                    "description": "Integrar a interface com os endpoints do backend."
                },
                {
                    "summary": "Realizar testes de usabilidade",
                    "description": "Testar a interface com usuários para garantir boa experiência."
                }
            ]
        })
        
        # Task para testes e QA
        tasks.append({
            "summary": "Realizar testes e QA",
            "description": "Executar testes de qualidade e garantir que a funcionalidade atende aos requisitos.",
            "subtasks": [
                {
                    "summary": "Executar testes de integração",
                    "description": "Verificar a integração entre os diferentes componentes."
                },
                {
                    "summary": "Realizar testes de regressão",
                    "description": "Garantir que as mudanças não afetaram funcionalidades existentes."
                },
                {
                    "summary": "Validar critérios de aceitação",
                    "description": "Verificar se todos os critérios de aceitação foram atendidos."
                }
            ]
        })
    
    return tasks


def _generate_subtasks(criterion: str) -> List[Dict[str, Any]]:
    """
    Gera subtasks com base em um critério de aceitação.
    
    Args:
        criterion: Critério de aceitação.
        
    Returns:
        List[Dict[str, Any]]: Lista de subtasks geradas.
    """
    subtasks = []
    
    # Identifica se o critério envolve backend
    if any(term in criterion.lower() for term in ["api", "banco de dados", "dados", "validação", "regra de negócio"]):
        subtasks.append({
            "summary": f"Backend: {criterion}",
            "description": f"Implementar a lógica de backend para: {criterion}"
        })
    
    # Identifica se o critério envolve frontend
    if any(term in criterion.lower() for term in ["interface", "tela", "botão", "formulário", "visualizar", "exibir"]):
        subtasks.append({
            "summary": f"Frontend: {criterion}",
            "description": f"Implementar a interface de usuário para: {criterion}"
        })
    
    # Adiciona subtask de teste
    subtasks.append({
        "summary": f"Testar: {criterion}",
        "description": f"Realizar testes para validar: {criterion}"
    })
    
    return subtasks


def _create_item_in_jira(item: Dict[str, Any], jira_service: JiraService) -> Dict[str, Any]:
    """
    Cria um item no Jira com base no tipo e payload.
    
    Args:
        item: Dicionário com os dados do item.
        jira_service: Instância do serviço Jira.
        
    Returns:
        Dict[str, Any]: Resposta da API do Jira.
    """
    item_type = item["type"]
    
    try:
        # Formata o item usando o template_generator
        formatted_item = generate_item(item, item_type)
    except TemplateGeneratorError as e:
        logger.warning(f"Erro ao formatar item com template: {str(e)}")
        formatted_item = item
    
    # Cria o item no Jira com base no tipo
    if item_type == "épico":
        return jira_service.create_epic(
            summary=formatted_item["summary"],
            description=formatted_item["description"],
            epic_name=formatted_item.get("epic_name", formatted_item["summary"]),
            labels=formatted_item.get("labels", [])
        )
    
    elif item_type in ["história", "historia"]:
        return jira_service.create_story(
            summary=formatted_item["summary"],
            description=formatted_item["description"],
            epic_key=formatted_item.get("epic_link"),
            labels=formatted_item.get("labels", [])
        )
    
    elif item_type == "task":
        return jira_service.create_task(
            summary=formatted_item["summary"],
            description=formatted_item["description"],
            parent_key=formatted_item.get("story_link"),
            labels=formatted_item.get("labels", [])
        )
    
    elif item_type == "subtask":
        return jira_service.create_subtask(
            summary=formatted_item["summary"],
            description=formatted_item["description"],
            parent_key=formatted_item["parent_key"],
            labels=formatted_item.get("labels", [])
        )
    
    elif item_type == "bug":
        return jira_service.create_bug(
            summary=formatted_item["summary"],
            description=formatted_item["description"],
            parent_key=formatted_item.get("parent_key"),
            labels=formatted_item.get("labels", [])
        )
    
    elif item_type == "sub-bug":
        return jira_service.create_sub_bug(
            summary=formatted_item["summary"],
            description=formatted_item["description"],
            parent_key=formatted_item["parent_key"],
            labels=formatted_item.get("labels", [])
        )
    
    raise HierarchyBuilderError(f"Tipo de item não suportado: {item_type}")
