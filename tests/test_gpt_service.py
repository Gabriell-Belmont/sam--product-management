"""
Script para testar a integração com o serviço GPT.

Este script testa as principais funcionalidades do módulo gpt_service.py,
verificando se a conexão com a API do GPT está funcionando corretamente e
se as funções de extração de campos e enriquecimento de conteúdo estão operando como esperado.
"""
import os
import sys
import json
from typing import Dict, Any

# Adiciona o diretório pai ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa os módulos necessários
from config import GPT_ENABLED
from app.infra.gpt_service import GPTService, GPTServiceError


def test_gpt_connection():
    """Testa a conexão com a API do GPT."""
    print("\n=== Testando conexão com a API do GPT ===")
    
    if not GPT_ENABLED:
        print("GPT está desabilitado nas configurações. Ativando temporariamente para o teste.")
    
    try:
        # Inicializa o serviço GPT
        gpt_service = GPTService()
        
        # Testa a geração de texto simples
        prompt = "Olá, estou testando a integração com o GPT. Por favor, responda com uma mensagem curta."
        response = gpt_service.generate(prompt)
        
        print(f"Resposta do GPT: {response}")
        print("✓ Conexão com a API do GPT funcionando corretamente!")
        return True
        
    except GPTServiceError as e:
        print(f"✗ Erro ao conectar com a API do GPT: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {str(e)}")
        return False


def test_extract_fields():
    """Testa a extração de campos de um prompt usando o GPT."""
    print("\n=== Testando extração de campos com GPT ===")
    
    try:
        # Inicializa o serviço GPT
        gpt_service = GPTService()
        
        # Prompt de exemplo para uma história
        prompt = """
        Crie uma história para permitir que o usuário faça login com redes sociais.
        
        Como usuário do aplicativo, gostaria de poder fazer login usando minhas contas do Google e Facebook para não precisar criar uma nova conta.
        
        Critérios de aceite:
        - O usuário deve poder escolher entre login com Google ou Facebook
        - O sistema deve validar o email do usuário
        - O sistema deve criar uma conta automaticamente se for o primeiro acesso
        
        Essa funcionalidade é importante para aumentar a conversão de novos usuários.
        """
        
        # Extrai campos para uma história
        fields = gpt_service.extract_fields(prompt, "história")
        
        print("Campos extraídos:")
        print(json.dumps(fields, indent=2, ensure_ascii=False))
        
        # Verifica se os campos essenciais foram extraídos
        essential_fields = ["summary", "as_a", "i_want", "acceptance_criteria"]
        missing_fields = [field for field in essential_fields if field not in fields]
        
        if missing_fields:
            print(f"✗ Campos essenciais não extraídos: {', '.join(missing_fields)}")
            return False
        else:
            print("✓ Extração de campos funcionando corretamente!")
            return True
        
    except GPTServiceError as e:
        print(f"✗ Erro ao extrair campos com GPT: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {str(e)}")
        return False


def test_create_jira_content():
    """Testa o enriquecimento de conteúdo para itens do Jira usando o GPT."""
    print("\n=== Testando enriquecimento de conteúdo com GPT ===")
    
    try:
        # Inicializa o serviço GPT
        gpt_service = GPTService()
        
        # Campos básicos para uma história
        fields = {
            "summary": "Login com redes sociais",
            "as_a": "usuário do aplicativo",
            "i_want": "poder fazer login usando minhas contas do Google e Facebook",
            "so_that": "não precise criar uma nova conta",
            "acceptance_criteria": "- O usuário deve poder escolher entre login com Google ou Facebook\n- O sistema deve validar o email do usuário"
        }
        
        # Enriquece o conteúdo
        enriched_fields = gpt_service.create_jira_content("história", fields)
        
        print("Conteúdo enriquecido:")
        print(json.dumps(enriched_fields, indent=2, ensure_ascii=False))
        
        # Verifica se o conteúdo foi enriquecido
        if len(enriched_fields.get("description", "")) > len(fields.get("description", "")):
            print("✓ Enriquecimento de conteúdo funcionando corretamente!")
            return True
        else:
            print("✗ O conteúdo não foi enriquecido como esperado.")
            return False
        
    except GPTServiceError as e:
        print(f"✗ Erro ao enriquecer conteúdo com GPT: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {str(e)}")
        return False


def test_suggest_hierarchy():
    """Testa a sugestão de hierarquia usando o GPT."""
    print("\n=== Testando sugestão de hierarquia com GPT ===")
    
    try:
        # Inicializa o serviço GPT
        gpt_service = GPTService()
        
        # Prompt para uma funcionalidade
        prompt = "Implementar sistema de notificações push para o aplicativo móvel, incluindo configurações de preferências do usuário."
        
        # Sugere uma hierarquia
        hierarchy = gpt_service.suggest_hierarchy(prompt)
        
        print(f"Hierarquia sugerida ({len(hierarchy)} itens):")
        for item in hierarchy:
            print(f"- [{item.get('type', 'unknown')}] {item.get('summary', 'Sem título')}")
        
        # Verifica se a hierarquia foi gerada
        if len(hierarchy) >= 3:  # Deve ter pelo menos um épico, uma história e uma task
            print("✓ Sugestão de hierarquia funcionando corretamente!")
            return True
        else:
            print("✗ A hierarquia não foi gerada como esperado.")
            return False
        
    except GPTServiceError as e:
        print(f"✗ Erro ao sugerir hierarquia com GPT: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {str(e)}")
        return False


def main():
    """Função principal para executar os testes."""
    print("=== Testes do Serviço GPT ===")
    
    # Verifica se o GPT está habilitado
    if not GPT_ENABLED:
        print("\nAtenção: GPT está desabilitado nas configurações.")
        print("Os testes serão executados, mas o serviço usará o modo de fallback.")
    
    # Executa os testes
    tests = [
        ("Conexão com a API", test_gpt_connection),
        ("Extração de campos", test_extract_fields),
        ("Enriquecimento de conteúdo", test_create_jira_content),
        ("Sugestão de hierarquia", test_suggest_hierarchy)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Erro ao executar o teste '{name}': {str(e)}")
            results.append((name, False))
    
    # Exibe o resumo dos resultados
    print("\n=== Resumo dos Resultados ===")
    for name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{status} - {name}")
    
    # Calcula a taxa de sucesso
    success_rate = sum(1 for _, result in results if result) / len(results) * 100
    print(f"\nTaxa de sucesso: {success_rate:.1f}%")
    
    # Retorna código de saída com base no sucesso dos testes
    return 0 if all(result for _, result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
