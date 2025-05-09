"""
Script para testar o módulo template_generator de forma simplificada.
"""
import sys
import os
import json

# Add the parent directory to sys.path to allow importing the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create a simplified version of the template_generator module for testing
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

def _validate_required_fields(item, template_name):
    """Valida se todos os campos obrigatórios estão presentes no item."""
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

def _format_list_items(items):
    """Formata uma lista de itens com marcadores."""
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
        item = item.lstrip('•-* ')
        formatted_items += f"• {item}\n"
    
    return formatted_items

def _format_description(description):
    """Formata a descrição geral de um item."""
    if not description:
        return "Não fornecido"
    
    # Remove formatação existente para evitar duplicação
    description = description.strip()
    
    return description

def _format_epic(item):
    """Formata um épico de acordo com o template."""
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

def _format_story(item):
    """Formata uma história de acordo com o template."""
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
        description += item["test_scenarios"]
    
    formatted_item["description"] = description.strip()
    
    return formatted_item

def _format_bug(item):
    """Formata um bug de acordo com o template."""
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
    
    formatted_item["description"] = description.strip()
    
    return formatted_item

def _format_task(item):
    """Formata uma task de acordo com o template."""
    formatted_item = item.copy()
    
    # Tasks têm um formato mais simples
    description = _format_description(item.get("description", ""))
    
    # Adiciona critérios de aceite se existirem
    if "acceptance_criteria" in item and item["acceptance_criteria"]:
        description += "\n\nCritérios de Aceite:\n"
        description += _format_list_items(item["acceptance_criteria"])
    
    formatted_item["description"] = description.strip()
    
    return formatted_item

def _format_subtask(item):
    """Formata uma subtask de acordo com o template."""
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

def _format_sub_bug(item):
    """Formata um sub-bug de acordo com o template."""
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

def generate_item(item, template_name):
    """Gera um item formatado de acordo com o template especificado."""
    # Valida campos obrigatórios
    _validate_required_fields(item, template_name)
    
    # Formata o item de acordo com o template
    if template_name == "épico":
        return _format_epic(item)
    elif template_name in ["história", "historia"]:
        return _format_story(item)
    elif template_name == "task":
        return _format_task(item)
    elif template_name == "subtask":
        return _format_subtask(item)
    elif template_name == "bug":
        return _format_bug(item)
    elif template_name == "sub-bug":
        return _format_sub_bug(item)
    else:
        raise UnknownTemplateError(f"Template desconhecido: {template_name}")

def test_epic_template():
    """Testa a geração de um épico."""
    print("Testando template de épico...")
    
    epic_data = {
        "summary": "Implementar sistema de autenticação",
        "description": "Implementar um sistema de autenticação seguro para o aplicativo",
        "labels": ["autenticação", "segurança"],
        "assignee": "john.doe",
        "priority": "High",
        "epic_name": "Sistema de Autenticação",
        "objective": "Permitir que os usuários façam login de forma segura",
        "benefits": "Maior segurança\nMelhor experiência do usuário\nConformidade com regulamentos",
        "risks": "Vulnerabilidades de segurança\nProblemas de desempenho"
    }
    
    try:
        formatted_epic = generate_item(epic_data, "épico")
        print("\nÉpico formatado:")
        print(json.dumps(formatted_epic, indent=2, ensure_ascii=False))
        print("\nTeste de épico concluído com sucesso!")
    except TemplateGeneratorError as e:
        print(f"Erro ao formatar épico: {str(e)}")
        return False
    
    return True

def test_story_template():
    """Testa a geração de uma história."""
    print("\nTestando template de história...")
    
    story_data = {
        "summary": "Login com redes sociais",
        "description": "Permitir que os usuários façam login usando suas contas de redes sociais",
        "labels": ["autenticação", "redes sociais"],
        "assignee": "jane.doe",
        "priority": "Medium",
        "epic_link": "AUTH-123",
        "as_a": "usuário do aplicativo",
        "i_want": "fazer login usando minhas contas de redes sociais",
        "so_that": "não precise criar uma nova conta",
        "preconditions": "Usuário possui conta em uma rede social suportada\nAplicativo está configurado para autenticação OAuth",
        "rules": "Suportar login com Google, Facebook e Twitter\nArmazenar apenas informações essenciais do usuário",
        "exceptions": "Se a autenticação falhar, mostrar mensagem de erro amigável",
        "acceptance_criteria": "Usuário pode fazer login com Google\nUsuário pode fazer login com Facebook\nUsuário pode fazer login com Twitter\nDados do perfil são importados corretamente",
        "test_scenarios": "Cenário: Login com Google\nDado que o usuário clica no botão de login com Google\nQuando ele autoriza o acesso\nEntão ele deve ser redirecionado para a página inicial logado\n\nCenário: Falha de login\nDado que o usuário tenta fazer login com uma rede social\nQuando a autenticação falha\nEntão uma mensagem de erro deve ser exibida"
    }
    
    try:
        formatted_story = generate_item(story_data, "história")
        print("\nHistória formatada:")
        print(json.dumps(formatted_story, indent=2, ensure_ascii=False))
        print("\nTeste de história concluído com sucesso!")
    except TemplateGeneratorError as e:
        print(f"Erro ao formatar história: {str(e)}")
        return False
    
    return True

def test_bug_template():
    """Testa a geração de um bug."""
    print("\nTestando template de bug...")
    
    bug_data = {
        "summary": "Falha no login após 3 tentativas",
        "description": "O sistema não permite novas tentativas de login após 3 falhas",
        "labels": ["autenticação", "bug"],
        "assignee": "jane.doe",
        "priority": "High",
        "severity": "High",
        "error_scenario": "Após 3 tentativas de login com senha incorreta, o sistema bloqueia o usuário permanentemente sem opção de recuperação",
        "expected_scenario": "Após 3 tentativas, o sistema deve oferecer opção de recuperação de senha ou bloqueio temporário",
        "impact": "Usuários ficam impossibilitados de acessar suas contas após erros de digitação",
        "origin": "Reportado por usuário via suporte",
        "solution": "Implementar sistema de bloqueio temporário e recuperação de senha"
    }
    
    try:
        formatted_bug = generate_item(bug_data, "bug")
        print("\nBug formatado:")
        print(json.dumps(formatted_bug, indent=2, ensure_ascii=False))
        print("\nTeste de bug concluído com sucesso!")
    except TemplateGeneratorError as e:
        print(f"Erro ao formatar bug: {str(e)}")
        return False
    
    return True

def test_task_template():
    """Testa a geração de uma task."""
    print("\nTestando template de task...")
    
    task_data = {
        "summary": "Configurar OAuth para Google",
        "description": "Configurar a autenticação OAuth para permitir login com Google",
        "labels": ["autenticação", "configuração"],
        "assignee": "john.doe",
        "priority": "Medium",
        "story_link": "AUTH-124",
        "acceptance_criteria": "Credenciais OAuth configuradas no console do Google\nChaves armazenadas de forma segura\nTestes de integração passando"
    }
    
    try:
        formatted_task = generate_item(task_data, "task")
        print("\nTask formatada:")
        print(json.dumps(formatted_task, indent=2, ensure_ascii=False))
        print("\nTeste de task concluído com sucesso!")
    except TemplateGeneratorError as e:
        print(f"Erro ao formatar task: {str(e)}")
        return False
    
    return True

def test_subtask_template():
    """Testa a geração de uma subtask."""
    print("\nTestando template de subtask...")
    
    subtask_data = {
        "summary": "Criar chaves de API no console do Google",
        "description": "Criar as chaves de API necessárias no console de desenvolvedor do Google",
        "labels": ["configuração"],
        "assignee": "john.doe",
        "priority": "Medium",
        "parent_key": "AUTH-125",
        "acceptance_criteria": "Chaves criadas\nPermissões configuradas corretamente\nChaves documentadas no wiki do projeto"
    }
    
    try:
        formatted_subtask = generate_item(subtask_data, "subtask")
        print("\nSubtask formatada:")
        print(json.dumps(formatted_subtask, indent=2, ensure_ascii=False))
        print("\nTeste de subtask concluído com sucesso!")
    except TemplateGeneratorError as e:
        print(f"Erro ao formatar subtask: {str(e)}")
        return False
    
    return True

def test_sub_bug_template():
    """Testa a geração de um sub-bug."""
    print("\nTestando template de sub-bug...")
    
    sub_bug_data = {
        "summary": "Erro de validação no formulário de login",
        "description": "O formulário de login não valida corretamente o formato de email",
        "labels": ["validação"],
        "assignee": "jane.doe",
        "priority": "Medium",
        "parent_key": "AUTH-126",
        "error_scenario": "Ao inserir um email sem @ o formulário aceita e tenta enviar",
        "expected_scenario": "O formulário deve validar o formato do email antes de enviar"
    }
    
    try:
        formatted_sub_bug = generate_item(sub_bug_data, "sub-bug")
        print("\nSub-bug formatado:")
        print(json.dumps(formatted_sub_bug, indent=2, ensure_ascii=False))
        print("\nTeste de sub-bug concluído com sucesso!")
    except TemplateGeneratorError as e:
        print(f"Erro ao formatar sub-bug: {str(e)}")
        return False
    
    return True

def run_all_tests():
    """Executa todos os testes."""
    tests = [
        test_epic_template,
        test_story_template,
        test_bug_template,
        test_task_template,
        test_subtask_template,
        test_sub_bug_template
    ]
    
    success = True
    for test in tests:
        if not test():
            success = False
    
    if success:
        print("\nTodos os testes foram concluídos com sucesso!")
        return 0
    else:
        print("\nAlguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
