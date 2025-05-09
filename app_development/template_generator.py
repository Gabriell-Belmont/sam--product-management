"""
Módulo para geração de itens baseada nos templates analisados.

Este módulo contém funções para formatar os itens de acordo com os templates analisados,
garantir que todos os campos obrigatórios sejam preenchidos e tratar casos especiais
para cada tipo de item (épico, história, task, subtask, bug, sub-bug).
"""
import re
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict

try:
    # Try importing from app_development package first (for production)
    from app_development.items import BaseItem, Epic, Story, Task, SubTask, Bug
except ImportError:
    # Fall back to local import (for testing)
    from items import BaseItem, Epic, Story, Task, SubTask, Bug

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('template_generator')


class TemplateGeneratorError(Exception):
    """Exceção personalizada para erros do gerador de templates."""
    pass


class MissingRequiredFieldError(TemplateGeneratorError):
    """Exceção para campos obrigatórios ausentes."""
    pass


class UnknownTemplateError(TemplateGeneratorError):
    """Exceção para templates desconhecidos."""
    pass


class InvalidFormatError(TemplateGeneratorError):
    """Exceção para formatos inválidos."""
    pass


# Definição dos campos obrigatórios por tipo de item
REQUIRED_FIELDS = {
    "épico": ["summary", "description"],
    "história": ["summary", "description"],
    "task": ["summary", "description"],
    "subtask": ["summary", "description", "parent_key"],
    "bug": ["summary", "description"],
    "sub-bug": ["summary", "description", "parent_key"]
}


def generate_item(item: Union[Dict[str, Any], BaseItem], template_name: str) -> Dict[str, Any]:
    """
    Gera um item formatado de acordo com o template especificado.
    
    Args:
        item: Dicionário ou objeto de item com os dados a serem formatados.
        template_name: Nome do template a ser utilizado (épico, história, task, etc.).
        
    Returns:
        Dict[str, Any]: Item formatado de acordo com o template.
        
    Raises:
        UnknownTemplateError: Se o template especificado não for reconhecido.
        MissingRequiredFieldError: Se campos obrigatórios estiverem ausentes.
        InvalidFormatError: Se os dados não estiverem no formato esperado.
    """
    logger.info(f"Gerando item com template: {template_name}")
    
    # Converte o item para dicionário se for um objeto
    if isinstance(item, BaseItem):
        item_dict = asdict(item)
    else:
        item_dict = item
    
    # Valida campos obrigatórios
    _validate_required_fields(item_dict, template_name)
    
    # Formata o item de acordo com o template
    if template_name == "épico":
        return _format_epic(item_dict)
    elif template_name in ["história", "historia"]:
        return _format_story(item_dict)
    elif template_name == "task":
        return _format_task(item_dict)
    elif template_name == "subtask":
        return _format_subtask(item_dict)
    elif template_name == "bug":
        return _format_bug(item_dict)
    elif template_name == "sub-bug":
        return _format_sub_bug(item_dict)
    else:
        raise UnknownTemplateError(f"Template desconhecido: {template_name}")


def _validate_required_fields(item: Dict[str, Any], template_name: str) -> None:
    """
    Valida se todos os campos obrigatórios estão presentes no item.
    
    Args:
        item: Dicionário com os dados do item.
        template_name: Nome do template a ser validado.
        
    Raises:
        MissingRequiredFieldError: Se campos obrigatórios estiverem ausentes.
    """
    if template_name not in REQUIRED_FIELDS:
        raise UnknownTemplateError(f"Template desconhecido: {template_name}")
    
    missing_fields = []
    for field in REQUIRED_FIELDS[template_name]:
        if field not in item or not item[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise MissingRequiredFieldError(
            f"Campos obrigatórios ausentes para {template_name}: {', '.join(missing_fields)}"
        )


def _format_list_items(items: Union[str, List[str]]) -> str:
    """
    Formata uma lista de itens com marcadores.
    
    Args:
        items: String com itens separados por quebra de linha ou lista de strings.
        
    Returns:
        str: Lista formatada com marcadores.
    """
    if not items:
        return ""
    
    # Se for uma string, divide por quebras de linha
    if isinstance(items, str):
        items_list = [item.strip() for item in items.split("\n") if item.strip()]
    else:
        items_list = [item.strip() for item in items if item.strip()]
    
    # Formata cada item com marcador
    formatted_items = ""
    for item in items_list:
        # Remove marcadores existentes para evitar duplicação
        item = re.sub(r'^[•\-\*]\s*', '', item)
        formatted_items += f"• {item}\n"
    
    return formatted_items


def _format_description(description: str) -> str:
    """
    Formata a descrição geral de um item.
    
    Args:
        description: Texto da descrição.
        
    Returns:
        str: Descrição formatada.
    """
    if not description:
        return "Não fornecido"
    
    # Remove formatação existente para evitar duplicação
    description = description.strip()
    
    return description


def _format_epic(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formata um épico de acordo com o template.
    
    Args:
        item: Dicionário com os dados do épico.
        
    Returns:
        Dict[str, Any]: Épico formatado.
    """
    formatted_item = item.copy()
    
    # Formata a descrição
    description = "Descrição\nVisão geral\n"
    description += _format_description(item.get("description", "")) + "\n\n"
    
    # Adiciona objetivo
    if "objective" in item and item["objective"]:
        description += f"Objetivo: \n{item['objective']}\n\n"
    
    # Adiciona benefícios
    if "benefits" in item and item["benefits"]:
        description += "Benefícios: \n"
        description += _format_list_items(item["benefits"])
        description += "\n"
    
    # Adiciona critérios de aceitação
    if "acceptance_criteria" in item and item["acceptance_criteria"]:
        description += "Critérios de Aceitação:\n"
        description += _format_list_items(item["acceptance_criteria"])
        description += "\n"
    
    # Adiciona riscos
    if "risks" in item and item["risks"]:
        description += "Riscos:\n"
        description += _format_list_items(item["risks"])
        description += "\n"
    
    formatted_item["description"] = description.strip()
    
    # Garante que o epic_name está preenchido
    if "epic_name" not in formatted_item or not formatted_item["epic_name"]:
        formatted_item["epic_name"] = formatted_item["summary"]
    
    return formatted_item


def _format_story(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formata uma história de acordo com o template.
    
    Args:
        item: Dicionário com os dados da história.
        
    Returns:
        Dict[str, Any]: História formatada.
    """
    formatted_item = item.copy()
    
    # Formata a descrição
    description = "Descrição\n"
    
    # Formata a história no formato "Como... Gostaria... Para..."
    as_a = item.get("as_a", "")
    i_want = item.get("i_want", "")
    so_that = item.get("so_that", "")
    
    if as_a and i_want:
        description += f"Como: {as_a}\n"
        description += f"Gostaria: {i_want}\n"
        if so_that:
            description += f"Para: {so_that}\n"
    else:
        # Se não tiver o formato específico, usa a descrição geral
        description += _format_description(item.get("description", ""))
    
    description += "\n\n"
    
    # Adiciona pré-condições
    if "preconditions" in item and item["preconditions"]:
        description += "Pré Condições\n"
        description += _format_list_items(item["preconditions"])
        description += "\n"
    
    # Adiciona regras
    if "rules" in item and item["rules"]:
        description += "Regras\n"
        description += _format_list_items(item["rules"])
        description += "\n"
    
    # Adiciona exceções às regras
    if "exceptions" in item and item["exceptions"]:
        description += "Exceção à Regra\n"
        description += _format_list_items(item["exceptions"])
        description += "\n"
    
    # Adiciona critérios de aceite
    if "acceptance_criteria" in item and item["acceptance_criteria"]:
        description += "Critérios de Aceite\n"
        description += _format_list_items(item["acceptance_criteria"])
        description += "\n"
    
    # Adiciona cenários de teste
    if "test_scenarios" in item and item["test_scenarios"]:
        description += "Cenários de Teste\n"
        
        # Verifica se os cenários já estão no formato correto
        test_scenarios = item["test_scenarios"]
        if isinstance(test_scenarios, str):
            # Tenta formatar os cenários no formato "Dado que... Quando... Então..."
            if not re.search(r'Cenário:', test_scenarios, re.IGNORECASE):
                # Divide os cenários por quebras de linha
                scenarios = [s.strip() for s in test_scenarios.split("\n") if s.strip()]
                formatted_scenarios = ""
                
                # Agrupa os cenários
                current_scenario = ""
                scenario_name = "Cenário 1"
                
                for line in scenarios:
                    if re.match(r'^Cenário\s*\d*\s*:', line, re.IGNORECASE):
                        # Se já temos um cenário acumulado, adicionamos ele
                        if current_scenario:
                            formatted_scenarios += current_scenario + "\n\n"
                        
                        # Começamos um novo cenário
                        scenario_name = line
                        current_scenario = scenario_name + "\n"
                    elif re.match(r'^Dado que', line, re.IGNORECASE):
                        # Se já temos um cenário acumulado, adicionamos ele
                        if current_scenario and not current_scenario.startswith("Cenário"):
                            formatted_scenarios += current_scenario + "\n\n"
                        
                        # Começamos um novo cenário
                        current_scenario = f"Cenário: {scenario_name}\n{line}\n"
                    elif re.match(r'^Quando', line, re.IGNORECASE) or re.match(r'^Então', line, re.IGNORECASE):
                        # Continuamos o cenário atual
                        current_scenario += line + "\n"
                    else:
                        # Se não temos um cenário atual, começamos um novo
                        if not current_scenario:
                            current_scenario = f"Cenário: {scenario_name}\n"
                        
                        # Adicionamos a linha ao cenário atual
                        current_scenario += line + "\n"
                
                # Adicionamos o último cenário
                if current_scenario:
                    formatted_scenarios += current_scenario
                
                description += formatted_scenarios
            else:
                # Os cenários já estão formatados
                description += test_scenarios
        else:
            # Se for uma lista, formata cada cenário
            formatted_scenarios = ""
            for i, scenario in enumerate(test_scenarios, 1):
                formatted_scenarios += f"Cenário: {i}\n{scenario}\n\n"
            
            description += formatted_scenarios
    
    formatted_item["description"] = description.strip()
    
    return formatted_item


def _format_bug(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formata um bug de acordo com o template.
    
    Args:
        item: Dicionário com os dados do bug.
        
    Returns:
        Dict[str, Any]: Bug formatado.
    """
    formatted_item = item.copy()
    
    # Formata a descrição
    description = "Descrição\n"
    
    # Adiciona cenário de erro
    if "error_scenario" in item and item["error_scenario"]:
        description += "Cenário de Erro\n"
        description += _format_description(item["error_scenario"]) + "\n\n"
    
    # Adiciona cenário esperado
    if "expected_scenario" in item and item["expected_scenario"]:
        description += "Cenário Esperado\n"
        description += _format_description(item["expected_scenario"]) + "\n\n"
    
    # Adiciona impacto
    if "impact" in item and item["impact"]:
        description += "Impacto\n"
        description += _format_description(item["impact"]) + "\n\n"
    
    # Adiciona origem
    if "origin" in item and item["origin"]:
        description += "Origem\n"
        description += _format_description(item["origin"]) + "\n\n"
    
    # Adiciona solução
    if "solution" in item and item["solution"]:
        description += "Solução\n"
        description += _format_description(item["solution"])
    elif "steps_to_reproduce" in item and item["steps_to_reproduce"]:
        # Se não tiver solução mas tiver passos para reproduzir, adiciona
        description += "Passos para Reproduzir\n"
        description += _format_list_items(item["steps_to_reproduce"])
    
    # Se não houver campos específicos, usa a descrição geral
    if len(description.split("\n")) <= 2:
        description += _format_description(item.get("description", ""))
    
    formatted_item["description"] = description.strip()
    
    # Garante que a severidade está preenchida
    if "severity" not in formatted_item or not formatted_item["severity"]:
        formatted_item["severity"] = "Medium"
    
    return formatted_item


def _format_task(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formata uma task de acordo com o template.
    
    Args:
        item: Dicionário com os dados da task.
        
    Returns:
        Dict[str, Any]: Task formatada.
    """
    formatted_item = item.copy()
    
    # Tasks têm um formato mais simples
    description = _format_description(item.get("description", ""))
    
    # Adiciona critérios de aceite se existirem
    if "acceptance_criteria" in item and item["acceptance_criteria"]:
        description += "\n\nCritérios de Aceite:\n"
        description += _format_list_items(item["acceptance_criteria"])
    
    formatted_item["description"] = description.strip()
    
    return formatted_item


def _format_subtask(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formata uma subtask de acordo com o template.
    
    Args:
        item: Dicionário com os dados da subtask.
        
    Returns:
        Dict[str, Any]: Subtask formatada.
    """
    formatted_item = item.copy()
    
    # Subtasks têm um formato mais simples, similar a tasks
    description = _format_description(item.get("description", ""))
    
    # Adiciona critérios de aceite se existirem
    if "acceptance_criteria" in item and item["acceptance_criteria"]:
        description += "\n\nCritérios de Aceite:\n"
        description += _format_list_items(item["acceptance_criteria"])
    
    formatted_item["description"] = description.strip()
    
    # Valida que a chave do item pai está presente
    if "parent_key" not in formatted_item or not formatted_item["parent_key"]:
        raise MissingRequiredFieldError("O campo 'parent_key' é obrigatório para subtasks")
    
    return formatted_item


def _format_sub_bug(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formata um sub-bug de acordo com o template.
    
    Args:
        item: Dicionário com os dados do sub-bug.
        
    Returns:
        Dict[str, Any]: Sub-bug formatado.
    """
    # Sub-bugs são subtasks com características de bugs
    formatted_item = _format_subtask(item)
    
    # Adiciona informações específicas de bugs
    description = formatted_item["description"]
    
    # Adiciona cenário de erro se não estiver presente
    if "error_scenario" in item and item["error_scenario"] and "Cenário de Erro" not in description:
        description += "\n\nCenário de Erro\n"
        description += _format_description(item["error_scenario"])
    
    # Adiciona cenário esperado se não estiver presente
    if "expected_scenario" in item and item["expected_scenario"] and "Cenário Esperado" not in description:
        description += "\n\nCenário Esperado\n"
        description += _format_description(item["expected_scenario"])
    
    formatted_item["description"] = description.strip()
    
    # Garante que a label "bug" está presente
    if "labels" not in formatted_item:
        formatted_item["labels"] = []
    
    if "bug" not in [label.lower() for label in formatted_item["labels"]]:
        formatted_item["labels"].append("bug")
    
    return formatted_item


def format_test_scenarios(scenarios: str) -> str:
    """
    Formata cenários de teste no padrão "Dado que... Quando... Então...".
    
    Args:
        scenarios: String com os cenários de teste.
        
    Returns:
        str: Cenários formatados.
    """
    if not scenarios:
        return ""
    
    # Divide os cenários por quebras de linha
    lines = [line.strip() for line in scenarios.split("\n") if line.strip()]
    
    formatted_scenarios = ""
    current_scenario = ""
    scenario_count = 1
    
    for line in lines:
        # Verifica se é o início de um novo cenário
        if re.match(r'^Cenário\s*\d*\s*:', line, re.IGNORECASE):
            # Se já temos um cenário acumulado, adicionamos ele
            if current_scenario:
                formatted_scenarios += current_scenario + "\n\n"
            
            # Começamos um novo cenário
            current_scenario = line + "\n"
        elif re.match(r'^Dado que', line, re.IGNORECASE):
            # Se já temos um cenário acumulado, adicionamos ele
            if current_scenario:
                formatted_scenarios += current_scenario + "\n\n"
            
            # Começamos um novo cenário se não tiver um título explícito
            if not current_scenario or not re.match(r'^Cenário', current_scenario, re.IGNORECASE):
                current_scenario = f"Cenário: {scenario_count}\n"
                scenario_count += 1
            
            current_scenario += line + "\n"
        elif re.match(r'^Quando', line, re.IGNORECASE) or re.match(r'^Então', line, re.IGNORECASE):
            # Continuamos o cenário atual
            current_scenario += line + "\n"
        else:
            # Se não temos um cenário atual, começamos um novo
            if not current_scenario:
                current_scenario = f"Cenário: {scenario_count}\n"
                scenario_count += 1
            
            # Adicionamos a linha ao cenário atual
            current_scenario += line + "\n"
    
    # Adicionamos o último cenário
    if current_scenario:
        formatted_scenarios += current_scenario
    
    return formatted_scenarios.strip()


def format_user_story(as_a: str, i_want: str, so_that: str = None) -> str:
    """
    Formata uma história de usuário no padrão "Como... Gostaria... Para...".
    
    Args:
        as_a: Papel do usuário.
        i_want: O que o usuário deseja fazer.
        so_that: Objetivo do usuário (opcional).
        
    Returns:
        str: História de usuário formatada.
    """
    if not as_a or not i_want:
        return ""
    
    story = f"Como: {as_a}\nGostaria: {i_want}"
    if so_that:
        story += f"\nPara: {so_that}"
    
    return story


def extract_user_story_components(description: str) -> Dict[str, str]:
    """
    Extrai os componentes de uma história de usuário de uma descrição.
    
    Args:
        description: Texto da descrição.
        
    Returns:
        Dict[str, str]: Componentes da história (as_a, i_want, so_that).
    """
    components = {
        "as_a": "",
        "i_want": "",
        "so_that": ""
    }
    
    # Extrai "Como..."
    as_a_match = re.search(r'Como:?\s+(.+?)(?:\n|$)', description, re.IGNORECASE)
    if as_a_match:
        components["as_a"] = as_a_match.group(1).strip()
    
    # Extrai "Gostaria..."
    i_want_match = re.search(r'Gostaria:?\s+(.+?)(?:\n|$)', description, re.IGNORECASE)
    if i_want_match:
        components["i_want"] = i_want_match.group(1).strip()
    
    # Extrai "Para..."
    so_that_match = re.search(r'Para:?\s+(.+?)(?:\n|$)', description, re.IGNORECASE)
    if so_that_match:
        components["so_that"] = so_that_match.group(1).strip()
    
    return components
