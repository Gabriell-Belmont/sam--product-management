"""
Testes para o módulo de processamento de prompts.
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.prompt_processor import PromptProcessor, PromptProcessorError


class TestPromptProcessor(unittest.TestCase):
    """Testes para a classe PromptProcessor."""
    
    def setUp(self):
        """Configura o ambiente de teste."""
        # Mock dos serviços
        self.s3_service_mock = MagicMock()
        self.jira_service_mock = MagicMock()
        self.jira_service_mock.project_key = "TEST"
        
        # Instância do processador de prompts
        self.processor = PromptProcessor(
            s3_service=self.s3_service_mock,
            jira_service=self.jira_service_mock,
            user_id="test_user",
            project_key="TEST"
        )
    
    def test_parse_prompt_epic(self):
        """Testa a análise de um prompt de épico."""
        prompt = "Crie um épico para implementar o sistema de login com redes sociais"
        result = self.processor.parse_prompt(prompt)
        
        self.assertEqual(result["type"], "épico")
        self.assertEqual(result["raw_text"], prompt)
    
    def test_parse_prompt_story(self):
        """Testa a análise de um prompt de história."""
        prompt = "Crie uma história para o usuário poder fazer login com o Facebook"
        result = self.processor.parse_prompt(prompt)
        
        self.assertEqual(result["type"], "história")
        self.assertEqual(result["raw_text"], prompt)
    
    def test_parse_prompt_task(self):
        """Testa a análise de um prompt de task."""
        prompt = "Crie uma task para implementar a API de autenticação com o Facebook"
        result = self.processor.parse_prompt(prompt)
        
        self.assertEqual(result["type"], "task")
        self.assertEqual(result["raw_text"], prompt)
    
    def test_parse_prompt_bug(self):
        """Testa a análise de um prompt de bug."""
        prompt = "Reporte um bug onde o login com Facebook não está funcionando"
        result = self.processor.parse_prompt(prompt)
        
        self.assertEqual(result["type"], "bug")
        self.assertEqual(result["raw_text"], prompt)
    
    def test_extract_fields_epic(self):
        """Testa a extração de campos de um épico."""
        prompt = """
        Épico: Sistema de Login com Redes Sociais
        
        Descrição: Implementar um sistema que permita aos usuários fazer login usando suas contas de redes sociais.
        
        Objetivo: Simplificar o processo de login e aumentar a taxa de conversão de novos usuários.
        
        Benefícios:
        • Redução da fricção no processo de cadastro
        • Aumento da taxa de conversão
        • Melhoria na experiência do usuário
        
        Critérios de Aceitação:
        • O usuário deve poder fazer login com Facebook
        • O usuário deve poder fazer login com Google
        • O sistema deve validar os tokens de autenticação
        • O sistema deve criar um perfil local vinculado à conta social
        
        Riscos:
        • Mudanças nas APIs das redes sociais
        • Problemas de privacidade e LGPD
        """
        
        result = self.processor.extract_fields(prompt, "épico")
        
        self.assertEqual(result["summary"], "Sistema de Login com Redes Sociais")
        self.assertIn("Implementar um sistema", result["description"])
        self.assertIn("Simplificar o processo", result["objective"])
        self.assertIn("Redução da fricção", result["benefits"])
        self.assertIn("O usuário deve poder fazer login com Facebook", result["acceptance_criteria"])
    
    def test_extract_fields_story(self):
        """Testa a extração de campos de uma história."""
        prompt = """
        História: Login com Facebook
        
        Como: usuário do sistema
        Gostaria: fazer login usando minha conta do Facebook
        Para: não precisar criar uma nova conta e senha
        
        Pré Condições
        • O usuário deve ter uma conta no Facebook
        • O aplicativo deve estar registrado no Facebook Developer
        
        Regras
        • O token de autenticação deve ser validado
        • Os dados básicos do perfil devem ser importados
        
        Critérios de Aceite
        • Deve haver um botão "Login com Facebook" na tela de login
        • Ao clicar no botão, deve abrir a janela de autenticação do Facebook
        • Após autenticação bem-sucedida, o usuário deve ser redirecionado para a página inicial
        
        Cenários de Teste
        Cenário: Login bem-sucedido
        Dado que o usuário tem uma conta no Facebook
        Quando ele clica no botão "Login com Facebook" e autoriza o aplicativo
        Então ele deve ser autenticado e redirecionado para a página inicial
        
        Cenário: Falha na autenticação
        Dado que o usuário cancela a autorização no Facebook
        Quando ele é redirecionado de volta para o aplicativo
        Então deve ver uma mensagem de erro informando que a autenticação falhou
        """
        
        result = self.processor.extract_fields(prompt, "história")
        
        self.assertEqual(result["summary"], "Login com Facebook")
        self.assertEqual(result["as_a"], "usuário do sistema")
        self.assertEqual(result["i_want"], "fazer login usando minha conta do Facebook")
        self.assertEqual(result["so_that"], "não precisar criar uma nova conta e senha")
        self.assertIn("O usuário deve ter uma conta no Facebook", result["preconditions"])
        self.assertIn("O token de autenticação deve ser validado", result["rules"])
        self.assertIn("Deve haver um botão", result["acceptance_criteria"])
        self.assertIn("Cenário: Login bem-sucedido", result["test_scenarios"])
    
    def test_extract_fields_bug(self):
        """Testa a extração de campos de um bug."""
        prompt = """
        Bug: Falha no Login com Facebook
        
        Cenário de Erro
        Ao tentar fazer login com o Facebook, o sistema exibe uma tela em branco e não completa o processo de autenticação.
        
        Cenário Esperado
        O sistema deveria autenticar o usuário com o Facebook e redirecioná-lo para a página inicial.
        
        Impacto
        Usuários não conseguem fazer login usando o Facebook, o que representa aproximadamente 30% dos novos cadastros.
        
        Origem
        Descoberto por feedback de usuários e confirmado em testes internos.
        
        Solução
        Verificar a integração com a API do Facebook e os callbacks de autenticação.
        """
        
        result = self.processor.extract_fields(prompt, "bug")
        
        self.assertEqual(result["summary"], "Falha no Login com Facebook")
        self.assertIn("Ao tentar fazer login", result["error_scenario"])
        self.assertIn("O sistema deveria autenticar", result["expected_scenario"])
        self.assertIn("Usuários não conseguem", result["impact"])
        self.assertIn("Descoberto por feedback", result["origin"])
        self.assertIn("Verificar a integração", result["solution"])
    
    def test_format_description_epic(self):
        """Testa a formatação da descrição de um épico."""
        fields = {
            "summary": "Sistema de Login com Redes Sociais",
            "description": "Implementar um sistema que permita aos usuários fazer login usando suas contas de redes sociais.",
            "objective": "Simplificar o processo de login e aumentar a taxa de conversão de novos usuários.",
            "benefits": "Redução da fricção no processo de cadastro\nAumento da taxa de conversão\nMelhoria na experiência do usuário",
            "acceptance_criteria": "O usuário deve poder fazer login com Facebook\nO usuário deve poder fazer login com Google\nO sistema deve validar os tokens de autenticação"
        }
        
        formatted = self.processor.format_description("épico", fields)
        
        self.assertIn("Descrição\nVisão geral", formatted)
        self.assertIn("Objetivo:", formatted)
        self.assertIn("Benefícios:", formatted)
        self.assertIn("• Redução da fricção", formatted)
        self.assertIn("Critérios de Aceitação:", formatted)
        self.assertIn("• O usuário deve poder fazer login com Facebook", formatted)
    
    def test_format_description_story(self):
        """Testa a formatação da descrição de uma história."""
        fields = {
            "summary": "Login com Facebook",
            "description": "Implementar login com Facebook",
            "user_story_format": "Como: usuário do sistema\nGostaria: fazer login usando minha conta do Facebook\nPara: não precisar criar uma nova conta e senha",
            "preconditions": "O usuário deve ter uma conta no Facebook\nO aplicativo deve estar registrado no Facebook Developer",
            "rules": "O token de autenticação deve ser validado\nOs dados básicos do perfil devem ser importados",
            "acceptance_criteria": "Deve haver um botão 'Login com Facebook' na tela de login\nAo clicar no botão, deve abrir a janela de autenticação do Facebook",
            "test_scenarios": "Cenário: Login bem-sucedido\nDado que o usuário tem uma conta no Facebook\nQuando ele clica no botão 'Login com Facebook' e autoriza o aplicativo\nEntão ele deve ser autenticado e redirecionado para a página inicial"
        }
        
        formatted = self.processor.format_description("história", fields)
        
        self.assertIn("Descrição", formatted)
        self.assertIn("Como: usuário do sistema", formatted)
        self.assertIn("Pré Condições", formatted)
        self.assertIn("• O usuário deve ter uma conta no Facebook", formatted)
        self.assertIn("Regras", formatted)
        self.assertIn("Critérios de Aceite", formatted)
        self.assertIn("Cenários de Teste", formatted)
        self.assertIn("Cenário: Login bem-sucedido", formatted)
    
    def test_format_description_bug(self):
        """Testa a formatação da descrição de um bug."""
        fields = {
            "summary": "Falha no Login com Facebook",
            "description": "Bug no login com Facebook",
            "error_scenario": "Ao tentar fazer login com o Facebook, o sistema exibe uma tela em branco e não completa o processo de autenticação.",
            "expected_scenario": "O sistema deveria autenticar o usuário com o Facebook e redirecioná-lo para a página inicial.",
            "impact": "Usuários não conseguem fazer login usando o Facebook, o que representa aproximadamente 30% dos novos cadastros.",
            "origin": "Descoberto por feedback de usuários e confirmado em testes internos.",
            "solution": "Verificar a integração com a API do Facebook e os callbacks de autenticação."
        }
        
        formatted = self.processor.format_description("bug", fields)
        
        self.assertIn("Descrição", formatted)
        self.assertIn("Cenário de Erro", formatted)
        self.assertIn("Cenário Esperado", formatted)
        self.assertIn("Impacto", formatted)
        self.assertIn("Origem", formatted)
        self.assertIn("Solução", formatted)
    
    @patch('app_development.prompt_processor.S3ContextService')
    def test_get_context(self, mock_context_service):
        """Testa a obtenção de contexto."""
        # Configura os mocks
        mock_context_service_instance = mock_context_service.return_value
        mock_context_service_instance.get_recent_contexts.return_value = [{"prompt": "test"}]
        self.s3_service_mock.get_item_history.return_value = {"epics": [{"key": "EPIC-1"}]}
        
        # Chama o método
        context = self.processor.get_context()
        
        # Verifica os resultados
        self.assertEqual(context["contexts"], [{"prompt": "test"}])
        self.assertEqual(context["item_history"], {"epics": [{"key": "EPIC-1"}]})
        
        # Verifica as chamadas aos mocks
        mock_context_service_instance.get_recent_contexts.assert_called_once_with("test_user")
        self.s3_service_mock.get_item_history.assert_called_once_with("TEST", days=30)
    
    @patch('app_development.prompt_processor.S3ContextService')
    def test_save_context(self, mock_context_service):
        """Testa o salvamento de contexto."""
        # Configura os mocks
        mock_context_service_instance = mock_context_service.return_value
        mock_context_service_instance.save_context.return_value = "context_key"
        
        # Dados de teste
        prompt_data = {"type": "história", "raw_text": "test"}
        result = {"success": True, "jira_response": {"key": "STORY-1"}}
        
        # Chama o método
        key = self.processor.save_context(prompt_data, result)
        
        # Verifica os resultados
        self.assertEqual(key, "context_key")
        
        # Verifica as chamadas aos mocks
        mock_context_service_instance.save_context.assert_called_once()
        args = mock_context_service_instance.save_context.call_args[0]
        self.assertEqual(args[0], "test_user")
        self.assertEqual(args[1]["prompt"], prompt_data)
        self.assertEqual(args[1]["result"], result)
    
    def test_build_item_payload_epic(self):
        """Testa a construção do payload para um épico."""
        fields = {
            "summary": "Sistema de Login com Redes Sociais",
            "description": "Implementar um sistema que permita aos usuários fazer login usando suas contas de redes sociais.",
            "epic_name": "Login Social",
            "labels": ["login", "social"]
        }
        
        payload = self.processor.build_item_payload("épico", fields)
        
        self.assertEqual(payload["summary"], "Sistema de Login com Redes Sociais")
        self.assertEqual(payload["epic_name"], "Login Social")
        self.assertEqual(payload["labels"], ["login", "social"])
    
    def test_build_item_payload_story(self):
        """Testa a construção do payload para uma história."""
        fields = {
            "summary": "Login com Facebook",
            "description": "Implementar login com Facebook",
            "epic_link": "EPIC-1",
            "acceptance_criteria": "Critérios de aceite",
            "labels": ["login", "facebook"]
        }
        
        payload = self.processor.build_item_payload("história", fields)
        
        self.assertEqual(payload["summary"], "Login com Facebook")
        self.assertEqual(payload["epic_link"], "EPIC-1")
        self.assertEqual(payload["acceptance_criteria"], "Critérios de aceite")
        self.assertEqual(payload["labels"], ["login", "facebook"])
    
    def test_create_item_in_jira_epic(self):
        """Testa a criação de um épico no Jira."""
        # Configura o mock
        self.jira_service_mock.create_epic.return_value = {"key": "EPIC-1"}
        
        # Payload de teste
        payload = {
            "summary": "Sistema de Login com Redes Sociais",
            "description": "Descrição do épico",
            "epic_name": "Login Social",
            "labels": ["login", "social"]
        }
        
        # Chama o método
        response = self.processor.create_item_in_jira("épico", payload)
        
        # Verifica os resultados
        self.assertEqual(response["key"], "EPIC-1")
        
        # Verifica as chamadas ao mock
        self.jira_service_mock.create_epic.assert_called_once_with(
            summary="Sistema de Login com Redes Sociais",
            description="Descrição do épico",
            epic_name="Login Social",
            labels=["login", "social"]
        )
    
    @patch('app_development.prompt_processor.PromptProcessor.parse_prompt')
    @patch('app_development.prompt_processor.PromptProcessor.extract_fields')
    @patch('app_development.prompt_processor.PromptProcessor.get_context')
    @patch('app_development.prompt_processor.PromptProcessor.build_item_payload')
    @patch('app_development.prompt_processor.PromptProcessor.create_item_in_jira')
    @patch('app_development.prompt_processor.PromptProcessor.save_context')
    def test_process_prompt(self, mock_save_context, mock_create_item, mock_build_payload, 
                           mock_get_context, mock_extract_fields, mock_parse_prompt):
        """Testa o fluxo completo de processamento de prompt."""
        # Configura os mocks
        mock_parse_prompt.return_value = {"type": "história", "raw_text": "test"}
        mock_extract_fields.return_value = {"summary": "Test Story"}
        mock_get_context.return_value = {"contexts": [], "item_history": {}}
        mock_build_payload.return_value = {"summary": "Test Story"}
        mock_create_item.return_value = {"key": "STORY-1"}
        mock_save_context.return_value = "context_key"
        self.s3_service_mock.save_item.return_value = "s3_key"
        
        # Chama o método
        result = self.processor.process_prompt("Crie uma história para teste")
        
        # Verifica os resultados
        self.assertTrue(result["success"])
        self.assertEqual(result["item_type"], "história")
        self.assertEqual(result["jira_response"]["key"], "STORY-1")
        self.assertEqual(result["s3_key"], "s3_key")
        
        # Verifica as chamadas aos mocks
        mock_parse_prompt.assert_called_once()
        mock_extract_fields.assert_called_once()
        mock_get_context.assert_called_once()
        mock_build_payload.assert_called_once()
        mock_create_item.assert_called_once()
        mock_save_context.assert_called_once()
        self.s3_service_mock.save_item.assert_called_once()


if __name__ == '__main__':
    unittest.main()
