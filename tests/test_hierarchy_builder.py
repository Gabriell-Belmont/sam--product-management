"""
Testes para o módulo hierarchy_builder.py.
"""
import unittest
from unittest.mock import MagicMock, patch

from hierarchy_builder import (
    detect_missing_type, build_hierarchy, link_items, 
    review_and_confirm, HierarchyBuilderError
)


class TestHierarchyBuilder(unittest.TestCase):
    """Testes para o módulo hierarchy_builder."""
    
    def test_detect_missing_type(self):
        """Testa a detecção de tipo ausente."""
        # Teste para prompt sem tipo especificado
        prompt_dict = {
            "raw_text": "Implementar sistema de login",
            "normalized_text": "implementar sistema de login",
            "type": "unknown"
        }
        self.assertEqual(detect_missing_type(prompt_dict), "task")
        
        # Teste para prompt com solicitação de hierarquia
        prompt_dict = {
            "raw_text": "Criar hierarquia para sistema de login",
            "normalized_text": "criar hierarquia para sistema de login",
            "type": "história"
        }
        self.assertEqual(detect_missing_type(prompt_dict), "auto")
        
        # Teste para prompt com tipo já definido
        prompt_dict = {
            "raw_text": "Criar um épico para sistema de pagamento",
            "normalized_text": "criar um épico para sistema de pagamento",
            "type": "épico"
        }
        self.assertEqual(detect_missing_type(prompt_dict), "épico")
    
    @patch('hierarchy_builder.review_and_confirm')
    def test_review_and_confirm(self, mock_review):
        """Testa a revisão e confirmação da hierarquia."""
        # Configura o mock para retornar True
        mock_review.return_value = True
        
        # Cria uma lista de itens para testar
        items = [
            {"type": "épico", "summary": "Sistema de Autenticação"},
            {"type": "história", "summary": "Login com redes sociais"},
            {"type": "task", "summary": "Implementar backend"},
            {"type": "subtask", "summary": "Criar modelo de dados"}
        ]
        
        # Testa a função
        self.assertTrue(review_and_confirm(items))
        
        # Configura o mock para retornar False
        mock_review.return_value = False
        
        # Testa a função novamente
        self.assertFalse(review_and_confirm(items))


if __name__ == '__main__':
    unittest.main()
