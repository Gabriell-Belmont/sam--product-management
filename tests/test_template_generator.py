"""
Script para testar o módulo template_generator.
"""
import sys
import os
import json

# Add the parent directory to sys.path to allow importing the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from template_generator import generate_item, TemplateGeneratorError

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
