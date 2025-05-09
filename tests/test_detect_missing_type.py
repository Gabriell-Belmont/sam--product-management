"""
Teste simples para a função detect_missing_type do módulo hierarchy_builder.
"""
import unittest
from unittest.mock import patch

# Importamos apenas a função que queremos testar
from hierarchy_builder import detect_missing_type


class TestDetectMissingType(unittest.TestCase):
    """Testes para a função detect_missing_type."""
    
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


if __name__ == '__main__':
    unittest.main()
