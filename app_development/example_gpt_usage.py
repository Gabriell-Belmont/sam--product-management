"""
Exemplo de uso da integração com GPT em scripts personalizados.

Este script demonstra como utilizar o módulo gpt_service.py para processar prompts
e gerar conteúdo em scripts personalizados, fora do fluxo principal do aplicativo.
"""
import os
import sys
import json
from typing import Dict, Any

# Adiciona o diretório pai ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa os módulos necessários
from app_development.config import GPT_ENABLED
from app_development.gpt_service import GPTService, GPTServiceError


def process_user_story(description: str) -> Dict[str, Any]:
    """
    Processa uma descrição de história de usuário usando o GPT.
    
    Args:
        description: Descrição da história de usuário.
        
    Returns:
        Dict[str, Any]: Campos estruturados da história.
    """
    print(f"Processando história: {description}")
    
    try:
        # Inicializa o serviço GPT
        gpt_service = GPTService()
        
        # Extrai campos da história
        fields = gpt_service.extract_fields(description, "história")
        
        # Enriquece o conteúdo
        enriched_fields = gpt_service.create_jira_content("história", fields)
        
        return enriched_fields
        
    except GPTServiceError as e:
        print(f"Erro ao processar história com GPT: {str(e)}")
        # Fallback: retorna um dicionário básico com a descrição original
        return {
            "summary": description.split("\n")[0] if "\n" in description else description[:50] + "...",
            "description": description
        }


def generate_acceptance_criteria(story_description: str) -> str:
    """
    Gera critérios de aceitação para uma história usando o GPT.
    
    Args:
        story_description: Descrição da história.
        
    Returns:
        str: Critérios de aceitação gerados.
    """
    print(f"Gerando critérios de aceitação para: {story_description}")
    
    try:
        # Inicializa o serviço GPT
        gpt_service = GPTService()
        
        # Constrói o prompt para o GPT
        prompt = f"""
        Com base na seguinte descrição de história de usuário, gere critérios de aceitação detalhados:
        
        {story_description}
        
        Os critérios de aceitação devem ser específicos, mensuráveis e testáveis.
        """
        
        # Define a mensagem de sistema
        system = """
        Você é um especialista em Product Management e desenvolvimento de software.
        Sua tarefa é criar critérios de aceitação claros e objetivos para histórias de usuário.
        Cada critério deve ser específico, mensurável e testável.
        Formate os critérios como uma lista com marcadores.
        """
        
        # Gera os critérios de aceitação
        response = gpt_service.generate(prompt, system=system)
        
        return response.strip()
        
    except GPTServiceError as e:
        print(f"Erro ao gerar critérios de aceitação com GPT: {str(e)}")
        # Fallback: retorna uma mensagem de erro
        return "Não foi possível gerar critérios de aceitação automaticamente."


def suggest_related_tasks(story_description: str, num_tasks: int = 3) -> list:
    """
    Sugere tasks relacionadas a uma história usando o GPT.
    
    Args:
        story_description: Descrição da história.
        num_tasks: Número de tasks a serem sugeridas.
        
    Returns:
        list: Lista de tasks sugeridas.
    """
    print(f"Sugerindo {num_tasks} tasks para: {story_description}")
    
    try:
        # Inicializa o serviço GPT
        gpt_service = GPTService()
        
        # Constrói o prompt para o GPT
        prompt = f"""
        Com base na seguinte descrição de história de usuário, sugira {num_tasks} tasks técnicas para implementação:
        
        {story_description}
        
        Para cada task, forneça um título e uma breve descrição.
        Retorne apenas um array JSON com as tasks, onde cada task tem os campos "title" e "description".
        """
        
        # Define a mensagem de sistema
        system = """
        Você é um especialista em desenvolvimento de software.
        Sua tarefa é sugerir tasks técnicas para implementar uma história de usuário.
        Cada task deve ser específica, focada em um aspecto técnico da implementação.
        Retorne apenas um array JSON com as tasks, onde cada task tem os campos "title" e "description".
        """
        
        # Gera as tasks
        response = gpt_service.generate(prompt, system=system)
        
        # Tenta extrair o JSON da resposta
        try:
            # Procura por um bloco JSON na resposta
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Se não encontrar o bloco, assume que toda a resposta é JSON
                json_str = response
            
            # Remove caracteres que possam interferir na análise do JSON
            json_str = json_str.strip()
            if json_str.startswith('```') and json_str.endswith('```'):
                json_str = json_str[3:-3].strip()
            
            # Analisa o JSON
            tasks = json.loads(json_str)
            
            return tasks
            
        except json.JSONDecodeError as e:
            print(f"Erro ao analisar JSON da resposta do GPT: {str(e)}")
            # Fallback: retorna uma lista vazia
            return []
        
    except GPTServiceError as e:
        print(f"Erro ao sugerir tasks com GPT: {str(e)}")
        # Fallback: retorna uma lista vazia
        return []


def main():
    """Função principal para demonstrar o uso do GPT."""
    print("=== Exemplo de Uso da Integração com GPT ===")
    
    # Verifica se o GPT está habilitado
    if not GPT_ENABLED:
        print("\nAtenção: GPT está desabilitado nas configurações.")
        print("O exemplo será executado, mas o serviço usará o modo de fallback.")
    
    # Exemplo 1: Processar uma história de usuário
    print("\n--- Exemplo 1: Processar uma história de usuário ---")
    story_description = """
    Como usuário do aplicativo de e-commerce, quero poder salvar produtos em uma lista de desejos
    para poder acompanhar itens que me interessam e comprá-los posteriormente.
    """
    
    story_fields = process_user_story(story_description)
    print("\nCampos extraídos e enriquecidos:")
    print(json.dumps(story_fields, indent=2, ensure_ascii=False))
    
    # Exemplo 2: Gerar critérios de aceitação
    print("\n--- Exemplo 2: Gerar critérios de aceitação ---")
    acceptance_criteria = generate_acceptance_criteria(story_description)
    print("\nCritérios de aceitação gerados:")
    print(acceptance_criteria)
    
    # Exemplo 3: Sugerir tasks relacionadas
    print("\n--- Exemplo 3: Sugerir tasks relacionadas ---")
    tasks = suggest_related_tasks(story_description)
    print("\nTasks sugeridas:")
    for i, task in enumerate(tasks, 1):
        print(f"\n{i}. {task.get('title', 'Sem título')}")
        print(f"   {task.get('description', 'Sem descrição')}")
    
    print("\n=== Fim do Exemplo ===")


if __name__ == "__main__":
    import re  # Importação necessária para o regex no suggest_related_tasks
    main()
