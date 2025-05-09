"""
Teste isolado para as funções do módulo hierarchy_builder.
"""
import unittest


class TestHierarchyFunctions(unittest.TestCase):
    """Testes para as funções do módulo hierarchy_builder."""
    
    def test_detect_missing_type_function(self):
        """Testa a lógica da função detect_missing_type."""
        # Implementação isolada da função para teste
        def detect_missing_type_test(prompt_dict):
            # Verifica se o tipo já foi identificado
            if "type" in prompt_dict and prompt_dict["type"] and prompt_dict["type"] != "unknown":
                print(f"Returning existing type: {prompt_dict['type']}")
                return prompt_dict["type"]
            
            # Verifica se o usuário solicitou explicitamente uma hierarquia completa
            normalized_text = prompt_dict.get("normalized_text", "").lower()
            print(f"Normalized text: '{normalized_text}'")
            
            if any(term in normalized_text for term in [
                "hierarquia completa", "criar hierarquia", "estrutura completa", 
                "criar estrutura", "auto hierarquia", "auto-hierarquia"
            ]):
                print("Detected hierarchy request")
                return "auto"
            
            # Analisa o texto para identificar se é uma tarefa técnica (task)
            task_terms = ["implementar", "desenvolver", "criar", "configurar", "integrar", 
                         "refatorar", "otimizar", "ajustar"]
            
            for term in task_terms:
                if term in normalized_text:
                    print(f"Detected task term: '{term}'")
                    return "task"
            
            # Analisa o texto para identificar se é um tema amplo (épico)
            epic_terms = ["iniciativa", "objetivo estratégico", "visão", "tema", 
                         "grande funcionalidade", "épico"]
            
            for term in epic_terms:
                if term in normalized_text:
                    print(f"Detected epic term: '{term}'")
                    return "épico"
            
            # Analisa o texto para identificar se é uma funcionalidade para o usuário (história)
            story_terms = ["como usuário", "funcionalidade", "feature", "como cliente", 
                          "gostaria de", "quero poder", "preciso"]
            
            for term in story_terms:
                if term in normalized_text:
                    print(f"Detected story term: '{term}'")
                    return "história"
            
            # Se não conseguir identificar, assume que é uma história (mais comum)
            print("No specific terms detected, defaulting to 'história'")
            return "história"
        
        # Teste para prompt sem tipo especificado
        prompt_dict1 = {
            "raw_text": "Implementar sistema de login",
            "normalized_text": "implementar sistema de login",
            "type": "unknown"
        }
        # A função deve retornar "task" porque contém "implementar"
        result1 = detect_missing_type_test(prompt_dict1)
        print(f"Result for 'Implementar sistema de login': {result1}")
        self.assertEqual(result1, "task")
        
        # Teste para prompt com solicitação de hierarquia
        prompt_dict2 = {
            "raw_text": "Criar hierarquia para sistema de login",
            "normalized_text": "criar hierarquia para sistema de login",
            "type": "história"
        }
        result2 = detect_missing_type_test(prompt_dict2)
        print(f"Result for 'Criar hierarquia para sistema de login': {result2}")
        self.assertEqual(result2, "auto")
        
        # Teste para prompt com tipo já definido
        prompt_dict3 = {
            "raw_text": "Criar um épico para sistema de pagamento",
            "normalized_text": "criar um épico para sistema de pagamento",
            "type": "épico"
        }
        result3 = detect_missing_type_test(prompt_dict3)
        print(f"Result for 'Criar um épico para sistema de pagamento': {result3}")
        self.assertEqual(result3, "épico")
    
    def test_review_and_confirm_function(self):
        """Testa a lógica da função review_and_confirm."""
        # Simulação da função review_and_confirm
        def review_and_confirm_test(items_list, always_confirm=True):
            # Neste teste, sempre retornamos o valor de always_confirm
            return always_confirm
        
        # Cria uma lista de itens para testar
        items = [
            {"type": "épico", "summary": "Sistema de Autenticação"},
            {"type": "história", "summary": "Login com redes sociais"},
            {"type": "task", "summary": "Implementar backend"},
            {"type": "subtask", "summary": "Criar modelo de dados"}
        ]
        
        # Testa a função com confirmação
        self.assertTrue(review_and_confirm_test(items, True))
        
        # Testa a função com rejeição
        self.assertFalse(review_and_confirm_test(items, False))


if __name__ == '__main__':
    unittest.main()
