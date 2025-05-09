"""
Módulo para lidar com a interação com o usuário via CLI.
"""
import sys
from typing import Dict, Any, Optional

from config import ITEM_TYPES


def clear_screen() -> None:
    """Limpa a tela do terminal."""
    print("\033c", end="")


def print_header() -> None:
    """Imprime o cabeçalho do aplicativo."""
    clear_screen()
    print("=" * 50)
    print("  PM JIRA CLI - Criação de Demandas via Prompt")
    print("=" * 50)
    print()


def prompt_item_type() -> str:
    """
    Pergunta ao usuário qual tipo de item ele deseja criar.
    
    Returns:
        str: O tipo de item normalizado.
    """
    print_header()
    
    prompt = (
        "Qual demanda você gostaria de criar hoje?\n"
        "Você pode especificar se quer um épico, história, task, subtask, bug ou sub-bug: "
    )
    
    while True:
        user_input = input(prompt).strip().lower()
        
        # Normaliza a entrada do usuário
        for key in ITEM_TYPES:
            if key in user_input:
                return key
        
        print("\nTipo de demanda não reconhecido. Por favor, escolha entre:")
        print(", ".join(ITEM_TYPES.keys()))
        print()


def prompt_for_details(item_type: str) -> Dict[str, Any]:
    """
    Solicita ao usuário os detalhes do item a ser criado.
    
    Args:
        item_type: O tipo de item a ser criado.
        
    Returns:
        Dict[str, Any]: Um dicionário com os detalhes do item.
    """
    details = {}
    
    print(f"\nVamos criar um(a) {item_type}. Por favor, forneça os detalhes:")
    
    # Campos comuns para todos os tipos
    details["summary"] = input("Título: ").strip()
    details["description"] = input("Descrição (pressione Enter para terminar):\n").strip()
    
    # Campos específicos por tipo
    if item_type == "épico":
        details["epic_name"] = input("Nome do épico (opcional): ").strip()
    
    elif item_type == "história" or item_type == "historia":
        details["epic_link"] = input("Chave do épico relacionado (opcional): ").strip()
        details["acceptance_criteria"] = input("Critérios de aceitação: ").strip()
    
    elif item_type == "task":
        details["story_link"] = input("Chave da história relacionada (opcional): ").strip()
    
    elif item_type == "subtask" or item_type == "sub-bug":
        details["parent_key"] = input("Chave da tarefa pai (obrigatório): ").strip()
    
    elif item_type == "bug":
        details["severity"] = input("Severidade (Low/Medium/High): ").strip() or "Medium"
        details["steps_to_reproduce"] = input("Passos para reproduzir: ").strip()
    
    # Campos opcionais comuns
    details["labels"] = input("Labels (separadas por vírgula): ").strip()
    if details["labels"]:
        details["labels"] = [label.strip() for label in details["labels"].split(",")]
    else:
        details["labels"] = []
    
    details["assignee"] = input("Assignee (opcional): ").strip() or None
    details["priority"] = input("Prioridade (Low/Medium/High): ").strip() or "Medium"
    
    return details


def confirm_creation(item_type: str, details: Dict[str, Any]) -> bool:
    """
    Pede confirmação ao usuário antes de criar o item.
    
    Args:
        item_type: O tipo de item a ser criado.
        details: Os detalhes do item.
        
    Returns:
        bool: True se o usuário confirmar, False caso contrário.
    """
    print("\nResumo da demanda a ser criada:")
    print(f"Tipo: {item_type}")
    print(f"Título: {details['summary']}")
    print(f"Descrição: {details['description'][:50]}..." if len(details['description']) > 50 else f"Descrição: {details['description']}")
    
    return input("\nConfirma a criação? (s/n): ").strip().lower() == "s"
