"""
Módulo para processamento de prompts de usuário e extração de informações para criação de itens no Jira.

Este módulo contém a lógica para analisar o texto do prompt, identificar o tipo de item a ser criado,
extrair informações relevantes e formatar os dados de acordo com os templates analisados.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from config import ITEM_TYPES, S3_ITEM_TYPE_PREFIXES, GPT_ENABLED
from app.infra.s3_service import S3Service, S3ContextService
from app.infra.jira_service import JiraService
from app.modules.template_generator import generate_item, TemplateGeneratorError
from app.modules.hierarchy_builder import (
    detect_missing_type, build_hierarchy, link_items, 
    review_and_confirm, HierarchyBuilderError
)

# Importação condicional do serviço GPT
try:
    from app.infra.gpt_service import GPTService, GPTServiceError
    gpt_available = True
except ImportError:
    gpt_available = False

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('prompt_processor')


class PromptProcessorError(Exception):
    """Exceção personalizada para erros do processador de prompts."""
    pass


class PromptProcessor:
    """
    Classe para processar prompts de usuário e extrair informações para criação de itens no Jira.
    
    Esta classe analisa o texto do prompt, identifica o tipo de item a ser criado,
    extrai informações relevantes e formata os dados de acordo com os templates analisados.
    """
    
    def __init__(self, s3_service: S3Service, jira_service: JiraService, user_id: str = None, project_key: str = None):
        """
        Inicializa o processador de prompts.
        
        Args:
            s3_service: Instância do serviço S3 para armazenamento de contexto.
            jira_service: Instância do serviço Jira para criação de itens.
            user_id: ID do usuário para armazenamento de contexto.
            project_key: Chave do projeto Jira.
        """
        self.s3_service = s3_service
        self.jira_service = jira_service
        self.user_id = user_id or "default_user"
        self.project_key = project_key or jira_service.project_key
        self.context_service = S3ContextService()
        
        # Inicializa o serviço GPT se disponível e habilitado
        self.gpt_service = None
        if gpt_available and GPT_ENABLED:
            try:
                self.gpt_service = GPTService()
                logger.info("Serviço GPT inicializado com sucesso")
            except Exception as e:
                logger.warning(f"Não foi possível inicializar o serviço GPT: {str(e)}")
        
        # Padrões para identificação de tipos de itens
        self.item_type_patterns = {
            "épico": [r'\bépico\b', r'\bepico\b'],
            "história": [r'\bhistória\b', r'\bhistoria\b', r'\buser story\b'],
            "task": [r'\btask\b', r'\btarefa\b'],
            "subtask": [r'\bsubtask\b', r'\bsub-?task\b', r'\bsubtarefa\b', r'\bsub-?tarefa\b'],
            "bug": [r'\bbug\b', r'\berro\b', r'\bdefeito\b'],
            "sub-bug": [r'\bsub-?bug\b']
        }
        
        # Padrões para extração de campos específicos
        self.field_patterns = {
            # Padrões comuns
            "summary": [r'título[:\s]+(.+?)(?:\n|$)', r'summary[:\s]+(.+?)(?:\n|$)', r'nome[:\s]+(.+?)(?:\n|$)'],
            "description": [r'descrição[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'description[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            
            # Padrões para épicos
            "epic_name": [r'nome do épico[:\s]+(.+?)(?:\n|$)', r'epic name[:\s]+(.+?)(?:\n|$)'],
            "objective": [r'objetivo[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'objective[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            "benefits": [r'benefícios[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'benefits[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            
            # Padrões para histórias
            "as_a": [r'como[:\s]+(.+?)(?:\n|$)', r'as a[:\s]+(.+?)(?:\n|$)'],
            "i_want": [r'gostaria[:\s]+(.+?)(?:\n|$)', r'quero[:\s]+(.+?)(?:\n|$)', r'i want[:\s]+(.+?)(?:\n|$)'],
            "so_that": [r'para[:\s]+(.+?)(?:\n|$)', r'so that[:\s]+(.+?)(?:\n|$)'],
            "preconditions": [r'pré[- ]condições[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'preconditions[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            "rules": [r'regras[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'rules[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            "exceptions": [r'exceção[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'exceptions[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            
            # Padrões para bugs
            "error_scenario": [r'cenário de erro[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'error scenario[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            "expected_scenario": [r'cenário esperado[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'expected scenario[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            "impact": [r'impacto[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'impact[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            "origin": [r'origem[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'origin[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            "solution": [r'solução[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'solution[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            
            # Padrões para campos comuns
            "acceptance_criteria": [r'critérios de aceite[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'critérios de aceitação[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'acceptance criteria[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            "test_scenarios": [r'cenários de teste[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)', r'test scenarios[:\s]+([\s\S]+?)(?:\n\n|\n[A-Z]|$)'],
            
            # Padrões para links
            "epic_link": [r'épico[:\s]+([A-Z]+-\d+)', r'epico[:\s]+([A-Z]+-\d+)', r'epic[:\s]+([A-Z]+-\d+)'],
            "parent_key": [r'pai[:\s]+([A-Z]+-\d+)', r'parent[:\s]+([A-Z]+-\d+)'],
            "story_link": [r'história[:\s]+([A-Z]+-\d+)', r'historia[:\s]+([A-Z]+-\d+)', r'story[:\s]+([A-Z]+-\d+)']
        }
    
    def parse_prompt(self, prompt_text: str) -> Dict[str, Any]:
        """
        Analisa o texto do prompt e identifica o tipo de item a ser criado.
        
        Args:
            prompt_text: Texto do prompt do usuário.
            
        Returns:
            Dict[str, Any]: Dicionário com o tipo de item identificado e outras informações.
        """
        try:
            # Normaliza o texto (remove espaços extras, converte para minúsculas)
            normalized_text = ' '.join(prompt_text.lower().split())
            
            # Extrai informações básicas
            result = {
                "raw_text": prompt_text,
                "normalized_text": normalized_text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Se o GPT estiver disponível, tenta usar para identificar o tipo
            if self.gpt_service:
                try:
                    logger.info("Usando GPT para identificar o tipo de item")
                    # Usa o GPT para extrair campos, incluindo o tipo
                    gpt_fields = self.gpt_service.extract_fields(prompt_text)
                    
                    # Se o GPT identificou um tipo, usa-o
                    if "type" in gpt_fields:
                        item_type = gpt_fields["type"].lower()
                        # Normaliza o tipo para os valores esperados
                        if item_type in ["epic", "épico", "epico"]:
                            result["type"] = "épico"
                        elif item_type in ["story", "história", "historia"]:
                            result["type"] = "história"
                        elif item_type in ["task", "tarefa"]:
                            result["type"] = "task"
                        elif item_type in ["subtask", "sub-task", "subtarefa", "sub-tarefa"]:
                            result["type"] = "subtask"
                        elif item_type in ["bug", "erro", "defeito"]:
                            result["type"] = "bug"
                        elif item_type in ["sub-bug"]:
                            result["type"] = "sub-bug"
                        else:
                            # Se o tipo não for reconhecido, usa o método tradicional
                            result["type"] = self._identify_item_type(normalized_text)
                        
                        logger.info(f"Tipo identificado pelo GPT: {result['type']}")
                    else:
                        # Se o GPT não identificou um tipo, usa o método tradicional
                        result["type"] = self._identify_item_type(normalized_text)
                
                except GPTServiceError as e:
                    logger.warning(f"Erro ao usar GPT para identificar tipo: {str(e)}")
                    # Em caso de erro, usa o método tradicional
                    result["type"] = self._identify_item_type(normalized_text)
            else:
                # Se o GPT não estiver disponível, usa o método tradicional
                result["type"] = self._identify_item_type(normalized_text)
            
            # Verifica se o tipo está ausente ou se o usuário solicitou hierarquia automática
            if result["type"] == "unknown" or "hierarquia" in normalized_text or "auto" in normalized_text:
                # Usa o hierarchy_builder para detectar o tipo ou sugerir hierarquia
                suggested_type = detect_missing_type(result)
                
                if suggested_type == "auto":
                    result["hierarchy_requested"] = True
                    logger.info("Hierarquia automática solicitada")
                else:
                    result["type"] = suggested_type
                    logger.info(f"Tipo sugerido pelo hierarchy_builder: {suggested_type}")
            
            logger.info(f"Prompt analisado como tipo: {result['type']}")
            return result
        
        except Exception as e:
            logger.error(f"Erro ao analisar prompt: {str(e)}")
            raise PromptProcessorError(f"Erro ao analisar prompt: {str(e)}")
    
    def _identify_item_type(self, text: str) -> str:
        """
        Identifica o tipo de item com base no texto do prompt.
        
        Args:
            text: Texto normalizado do prompt.
            
        Returns:
            str: Tipo de item identificado.
        """
        # Verifica cada padrão de tipo de item
        for item_type, patterns in self.item_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return item_type
        
        # Se não encontrar um tipo específico, tenta inferir com base no conteúdo
        if "como" in text and "gostaria" in text and "para" in text:
            return "história"
        
        if "cenário de erro" in text or "impacto" in text:
            return "bug"
        
        if "objetivo" in text and "benefícios" in text:
            return "épico"
        
        # Padrão para quando o usuário menciona criar uma tarefa para algo
        if "criar uma tarefa para" in text or "implementar" in text:
            return "task"
        
        # Se não conseguir identificar, assume que é uma história (mais comum)
        return "história"
    
    def extract_fields(self, prompt_text: str, item_type: str) -> Dict[str, Any]:
        """
        Extrai campos relevantes do prompt com base no tipo de item.
        
        Args:
            prompt_text: Texto do prompt do usuário.
            item_type: Tipo de item identificado.
            
        Returns:
            Dict[str, Any]: Dicionário com os campos extraídos.
        """
        try:
            # Se o GPT estiver disponível, tenta usar para extrair campos
            if self.gpt_service:
                try:
                    logger.info(f"Usando GPT para extrair campos para {item_type}")
                    gpt_fields = self.gpt_service.extract_fields(prompt_text, item_type)
                    
                    # Se o GPT extraiu campos, usa-os
                    if gpt_fields:
                        logger.info(f"Campos extraídos pelo GPT: {', '.join(gpt_fields.keys())}")
                        
                        # Garante que pelo menos os campos obrigatórios estejam presentes
                        if "summary" not in gpt_fields or not gpt_fields["summary"]:
                            # Se não houver summary, tenta extrair com o método tradicional
                            summary = self._extract_field(prompt_text, "summary")
                            if summary:
                                gpt_fields["summary"] = summary
                            else:
                                # Se ainda não encontrar, usa a primeira linha como título
                                lines = prompt_text.strip().split('\n')
                                if lines:
                                    gpt_fields["summary"] = lines[0].strip()
                        
                        # Extrai labels se não estiverem presentes
                        if "labels" not in gpt_fields:
                            gpt_fields["labels"] = self._extract_labels(prompt_text)
                        
                        # Para subtasks, garante que parent_key esteja presente
                        if item_type in ["subtask", "sub-bug"] and "parent_key" not in gpt_fields:
                            parent_key = self._extract_field(prompt_text, "parent_key")
                            if parent_key:
                                gpt_fields["parent_key"] = parent_key
                        
                        return gpt_fields
                
                except GPTServiceError as e:
                    logger.warning(f"Erro ao usar GPT para extrair campos: {str(e)}")
                    # Em caso de erro, usa o método tradicional
            
            # Método tradicional de extração de campos
            fields = {}
            
            # Extrai campos comuns
            fields["summary"] = self._extract_field(prompt_text, "summary")
            fields["description"] = self._extract_field(prompt_text, "description")
            
            # Se não encontrou um título, tenta usar a primeira linha como título
            if not fields["summary"]:
                lines = prompt_text.strip().split('\n')
                if lines:
                    fields["summary"] = lines[0].strip()
            
            # Extrai campos específicos por tipo
            if item_type == "épico":
                fields.update(self._extract_epic_fields(prompt_text))
            elif item_type in ["história", "historia"]:
                fields.update(self._extract_story_fields(prompt_text))
            elif item_type == "bug":
                fields.update(self._extract_bug_fields(prompt_text))
            elif item_type == "task":
                fields.update(self._extract_task_fields(prompt_text))
            elif item_type in ["subtask", "sub-bug"]:
                fields.update(self._extract_subtask_fields(prompt_text))
            
            # Extrai campos de aceitação para todos os tipos exceto bugs
            if item_type != "bug":
                acceptance = self._extract_field(prompt_text, "acceptance_criteria")
                if acceptance:
                    fields["acceptance_criteria"] = acceptance
            
            # Extrai possíveis links para outros itens
            fields.update(self._extract_link_fields(prompt_text))
            
            # Extrai labels (tags) do texto
            fields["labels"] = self._extract_labels(prompt_text)
            
            logger.info(f"Campos extraídos para {item_type}: {', '.join(fields.keys())}")
            return fields
        
        except Exception as e:
            logger.error(f"Erro ao extrair campos: {str(e)}")
            raise PromptProcessorError(f"Erro ao extrair campos: {str(e)}")
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """
        Extrai um campo específico do texto usando padrões regex.
        
        Args:
            text: Texto do prompt.
            field_name: Nome do campo a ser extraído.
            
        Returns:
            str: Valor extraído ou string vazia se não encontrado.
        """
        if field_name not in self.field_patterns:
            return ""
        
        for pattern in self.field_patterns[field_name]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_epic_fields(self, text: str) -> Dict[str, str]:
        """
        Extrai campos específicos para épicos.
        
        Args:
            text: Texto do prompt.
            
        Returns:
            Dict[str, str]: Campos extraídos para épicos.
        """
        fields = {}
        
        # Extrai nome do épico
        epic_name = self._extract_field(text, "epic_name")
        if epic_name:
            fields["epic_name"] = epic_name
        
        # Extrai objetivo
        objective = self._extract_field(text, "objective")
        if objective:
            fields["objective"] = objective
        
        # Extrai benefícios
        benefits = self._extract_field(text, "benefits")
        if benefits:
            fields["benefits"] = benefits
        
        return fields
    
    def _extract_story_fields(self, text: str) -> Dict[str, str]:
        """
        Extrai campos específicos para histórias.
        
        Args:
            text: Texto do prompt.
            
        Returns:
            Dict[str, str]: Campos extraídos para histórias.
        """
        fields = {}
        
        # Extrai componentes da história de usuário
        as_a = self._extract_field(text, "as_a")
        i_want = self._extract_field(text, "i_want")
        so_that = self._extract_field(text, "so_that")
        
        # Formata a descrição no formato "Como... Gostaria... Para..."
        if as_a and i_want:
            story_format = f"Como: {as_a}\nGostaria: {i_want}"
            if so_that:
                story_format += f"\nPara: {so_that}"
            
            fields["user_story_format"] = story_format
            
            # Se não houver descrição, usa o formato como descrição
            if "description" not in fields or not fields["description"]:
                fields["description"] = story_format
        
        # Extrai pré-condições
        preconditions = self._extract_field(text, "preconditions")
        if preconditions:
            fields["preconditions"] = preconditions
        
        # Extrai regras
        rules = self._extract_field(text, "rules")
        if rules:
            fields["rules"] = rules
        
        # Extrai exceções
        exceptions = self._extract_field(text, "exceptions")
        if exceptions:
            fields["exceptions"] = exceptions
        
        # Extrai cenários de teste
        test_scenarios = self._extract_field(text, "test_scenarios")
        if test_scenarios:
            fields["test_scenarios"] = test_scenarios
        
        return fields
    
    def _extract_bug_fields(self, text: str) -> Dict[str, str]:
        """
        Extrai campos específicos para bugs.
        
        Args:
            text: Texto do prompt.
            
        Returns:
            Dict[str, str]: Campos extraídos para bugs.
        """
        fields = {}
        
        # Extrai cenário de erro
        error_scenario = self._extract_field(text, "error_scenario")
        if error_scenario:
            fields["error_scenario"] = error_scenario
        
        # Extrai cenário esperado
        expected_scenario = self._extract_field(text, "expected_scenario")
        if expected_scenario:
            fields["expected_scenario"] = expected_scenario
        
        # Extrai impacto
        impact = self._extract_field(text, "impact")
        if impact:
            fields["impact"] = impact
        
        # Extrai origem
        origin = self._extract_field(text, "origin")
        if origin:
            fields["origin"] = origin
        
        # Extrai solução
        solution = self._extract_field(text, "solution")
        if solution:
            fields["solution"] = solution
        
        # Formata a descrição para bugs
        bug_description = ""
        if error_scenario:
            bug_description += f"Cenário de Erro:\n{error_scenario}\n\n"
        if expected_scenario:
            bug_description += f"Cenário Esperado:\n{expected_scenario}\n\n"
        if impact:
            bug_description += f"Impacto:\n{impact}\n\n"
        if origin:
            bug_description += f"Origem:\n{origin}\n\n"
        if solution:
            bug_description += f"Solução:\n{solution}"
        
        if bug_description:
            fields["description"] = bug_description
        
        return fields
    
    def _extract_task_fields(self, text: str) -> Dict[str, str]:
        """
        Extrai campos específicos para tasks.
        
        Args:
            text: Texto do prompt.
            
        Returns:
            Dict[str, str]: Campos extraídos para tasks.
        """
        # Tasks não têm campos específicos além dos comuns
        return {}
    
    def _extract_subtask_fields(self, text: str) -> Dict[str, str]:
        """
        Extrai campos específicos para subtasks.
        
        Args:
            text: Texto do prompt.
            
        Returns:
            Dict[str, str]: Campos extraídos para subtasks.
        """
        fields = {}
        
        # Extrai chave do item pai
        parent_key = self._extract_field(text, "parent_key")
        if parent_key:
            fields["parent_key"] = parent_key
        
        return fields
    
    def _extract_link_fields(self, text: str) -> Dict[str, str]:
        """
        Extrai campos de link para outros itens.
        
        Args:
            text: Texto do prompt.
            
        Returns:
            Dict[str, str]: Campos de link extraídos.
        """
        fields = {}
        
        # Extrai link para épico
        epic_link = self._extract_field(text, "epic_link")
        if epic_link:
            fields["epic_link"] = epic_link
        
        # Extrai link para história
        story_link = self._extract_field(text, "story_link")
        if story_link:
            fields["story_link"] = story_link
        
        # Extrai chave do item pai
        parent_key = self._extract_field(text, "parent_key")
        if parent_key:
            fields["parent_key"] = parent_key
        
        return fields
    
    def _extract_labels(self, text: str) -> List[str]:
        """
        Extrai labels (tags) do texto do prompt.
        
        Args:
            text: Texto do prompt.
            
        Returns:
            List[str]: Lista de labels extraídas.
        """
        labels = []
        
        # Procura por padrões de labels
        label_patterns = [
            r'labels?[:\s]+(.+?)(?:\n|$)',
            r'tags?[:\s]+(.+?)(?:\n|$)',
            r'etiquetas?[:\s]+(.+?)(?:\n|$)'
        ]
        
        for pattern in label_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Divide as labels por vírgulas e remove espaços
                label_text = match.group(1).strip()
                labels.extend([label.strip() for label in label_text.split(',')])
                break
        
        # Procura por hashtags no texto
        hashtags = re.findall(r'#(\w+)', text)
        if hashtags:
            labels.extend(hashtags)
        
        # Remove duplicatas e converte para minúsculas
        return list(set([label.lower() for label in labels if label]))
    
    def format_description(self, item_type: str, fields: Dict[str, Any]) -> str:
        """
        Formata a descrição do item de acordo com o template apropriado.
        
        Args:
            item_type: Tipo de item.
            fields: Campos extraídos do prompt.
            
        Returns:
            str: Descrição formatada.
        """
        if item_type == "épico":
            return self._format_epic_description(fields)
        elif item_type in ["história", "historia"]:
            return self._format_story_description(fields)
        elif item_type == "bug":
            return self._format_bug_description(fields)
        elif item_type == "task":
            return self._format_task_description(fields)
        elif item_type in ["subtask", "sub-bug"]:
            return self._format_subtask_description(fields)
        else:
            return fields.get("description", "")
    
    def _format_epic_description(self, fields: Dict[str, Any]) -> str:
        """
        Formata a descrição de um épico.
        
        Args:
            fields: Campos extraídos do prompt.
            
        Returns:
            str: Descrição formatada para épico.
        """
        description = "Descrição\nVisão geral\n"
        description += fields.get("description", "Não fornecido") + "\n\n"
        
        if "objective" in fields:
            description += f"Objetivo: \n{fields['objective']}\n\n"
        
        if "benefits" in fields:
            description += "Benefícios: \n"
            benefits = fields["benefits"].split("\n")
            for benefit in benefits:
                if benefit.strip():
                    description += f"• {benefit.strip()}\n"
            description += "\n"
        
        if "acceptance_criteria" in fields:
            description += "Critérios de Aceitação:\n"
            criteria = fields["acceptance_criteria"].split("\n")
            for criterion in criteria:
                if criterion.strip():
                    description += f"• {criterion.strip()}\n"
            description += "\n"
        
        return description.strip()
    
    def _format_story_description(self, fields: Dict[str, Any]) -> str:
        """
        Formata a descrição de uma história seguindo o template_analysis.md
        
        Args:
            fields: Campos extraídos do prompt.
            
        Returns:
            str: Descrição formatada para história.
        """
        description = "História:\nDescrição\n"
        
        if fields.get("as_a") and fields.get("i_want") and fields.get("so_that"):
            description += f"Como: {fields['as_a']}\n"
            description += f"Gostaria: {fields['i_want']}\n"
            description += f"Para: {fields['so_that']}\n\n"
        elif "user_story_format" in fields:
            description += fields["user_story_format"] + "\n\n"
        else:
            description += fields.get("description", "Não fornecido") + "\n\n"
        
        if fields.get("preconditions"):
            description += "Pré Condições\n"
            preconditions = fields["preconditions"]
            if isinstance(preconditions, list):
                for condition in preconditions:
                    description += f"• {condition}\n"
            else:
                preconditions_list = preconditions.split("\n")
                for precondition in preconditions_list:
                    if precondition.strip():
                        description += f"• {precondition.strip()}\n"
            description += "\n"
        
        if fields.get("rules"):
            description += "Regras\n"
            rules = fields["rules"]
            if isinstance(rules, list):
                for rule in rules:
                    description += f"• {rule}\n"
            else:
                rules_list = rules.split("\n")
                for rule in rules_list:
                    if rule.strip():
                        description += f"• {rule.strip()}\n"
            description += "\n"
        
        if fields.get("exceptions"):
            description += "Exceção à Regra\n"
            exceptions = fields["exceptions"]
            if isinstance(exceptions, list):
                for exception in exceptions:
                    description += f"• {exception}\n"
            else:
                exceptions_list = exceptions.split("\n")
                for exception in exceptions_list:
                    if exception.strip():
                        description += f"• {exception.strip()}\n"
            description += "\n"
        
        if fields.get("acceptance_criteria"):
            description += "Critérios de Aceite\n"
            criteria = fields["acceptance_criteria"]
            if isinstance(criteria, list):
                for criterion in criteria:
                    description += f"• {criterion}\n"
            else:
                criteria_list = criteria.split("\n")
                for criterion in criteria_list:
                    if criterion.strip():
                        description += f"• {criterion.strip()}\n"
            description += "\n"
        
        if fields.get("test_scenarios"):
            description += "Cenários de Teste\n"
            scenarios = fields["test_scenarios"]
            if isinstance(scenarios, list):
                for scenario in scenarios:
                    description += f"Cenário: {scenario}\n"
            else:
                description += f"Cenário: {scenarios}\n"
        
        return description.strip()
    
    def _format_bug_description(self, fields: Dict[str, Any]) -> str:
        """
        Formata a descrição de um bug.
        
        Args:
            fields: Campos extraídos do prompt.
            
        Returns:
            str: Descrição formatada para bug.
        """
        description = "Descrição\n"
        
        if "error_scenario" in fields:
            description += "Cenário de Erro\n"
            description += fields["error_scenario"] + "\n\n"
        
        if "expected_scenario" in fields:
            description += "Cenário Esperado\n"
            description += fields["expected_scenario"] + "\n\n"
        
        if "impact" in fields:
            description += "Impacto\n"
            description += fields["impact"] + "\n\n"
        
        if "origin" in fields:
            description += "Origem\n"
            description += fields["origin"] + "\n\n"
        
        if "solution" in fields:
            description += "Solução\n"
            description += fields["solution"]
        
        # Se não houver campos específicos, usa a descrição geral
        if len(description.split("\n")) <= 2:
            description += fields.get("description", "Não fornecido")
        
        return description.strip()
    
    def _format_task_description(self, fields: Dict[str, Any]) -> str:
        """
        Formata a descrição de uma task.
        
        Args:
            fields: Campos extraídos do prompt.
            
        Returns:
            str: Descrição formatada para task.
        """
        description = fields.get("description", "")
        
        if "acceptance_criteria" in fields:
            description += "\n\nCritérios de Aceite:\n"
            criteria = fields["acceptance_criteria"].split("\n")
            for criterion in criteria:
                if criterion.strip():
                    description += f"• {criterion.strip()}\n"
        
        return description.strip()
    
    def _format_subtask_description(self, fields: Dict[str, Any]) -> str:
        """
        Formata a descrição de uma subtask.
        
        Args:
            fields: Campos extraídos do prompt.
            
        Returns:
            str: Descrição formatada para subtask.
        """
        # Subtasks geralmente têm descrições mais simples
        return fields.get("description", "")
    
    def get_context(self, days: int = 30) -> Dict[str, Any]:
        """
        Obtém o contexto armazenado para o usuário.
        
        Args:
            days: Número de dias para olhar para trás.
            
        Returns:
            Dict[str, Any]: Contexto armazenado.
        """
        try:
            # Obtém contextos recentes do usuário
            contexts = self.context_service.get_recent_contexts(self.user_id)
            
            # Obtém histórico de itens do projeto
            item_history = self.s3_service.get_item_history(self.project_key, days=days)
            
            return {
                "contexts": contexts,
                "item_history": item_history
            }
        
        except Exception as e:
            logger.warning(f"Erro ao obter contexto: {str(e)}")
            return {"contexts": [], "item_history": {}}
    
    def save_context(self, prompt_data: Dict[str, Any], result: Dict[str, Any]) -> str:
        """
        Salva o contexto da interação atual.
        
        Args:
            prompt_data: Dados do prompt processado.
            result: Resultado da criação do item.
            
        Returns:
            str: Chave do contexto salvo.
        """
        try:
            context_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "prompt": prompt_data,
                "result": result
            }
            
            key = self.context_service.save_context(self.user_id, context_data)
            logger.info(f"Contexto salvo com sucesso: {key}")
            
            return key
        
        except Exception as e:
            logger.warning(f"Erro ao salvar contexto: {str(e)}")
            return ""
    
    def build_item_payload(self, item_type: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constrói o payload para criação do item no Jira.
        
        Args:
            item_type: Tipo de item.
            fields: Campos extraídos e processados.
            
        Returns:
            Dict[str, Any]: Payload para criação do item.
        """
        try:
            # Se o GPT estiver disponível, tenta usar para enriquecer o conteúdo
            if self.gpt_service:
                try:
                    logger.info(f"Usando GPT para enriquecer conteúdo para {item_type}")
                    enriched_fields = self.gpt_service.create_jira_content(item_type, fields)
                    
                    # Se o GPT enriqueceu os campos, usa-os
                    if enriched_fields:
                        logger.info(f"Conteúdo enriquecido pelo GPT: {', '.join(enriched_fields.keys())}")
                        fields = enriched_fields
                
                except GPTServiceError as e:
                    logger.warning(f"Erro ao usar GPT para enriquecer conteúdo: {str(e)}")
                    # Em caso de erro, continua com os campos originais
            
            # Constrói o payload básico
            payload = {
                "summary": fields.get("summary", "Sem título"),
                "description": fields.get("description", ""),
                "labels": fields.get("labels", []),
                "assignee": fields.get("assignee"),
                "priority": fields.get("priority", "Medium")
            }
            
            # Adiciona campos específicos por tipo
            if item_type == "épico":
                payload["epic_name"] = fields.get("epic_name", payload["summary"])
                payload["objective"] = fields.get("objective", "")
                payload["benefits"] = fields.get("benefits", "")
                payload["risks"] = fields.get("risks", "")
            
            elif item_type in ["história", "historia"]:
                payload["epic_link"] = fields.get("epic_link")
                payload["acceptance_criteria"] = fields.get("acceptance_criteria", "")
                payload["as_a"] = fields.get("as_a", "")
                payload["i_want"] = fields.get("i_want", "")
                payload["so_that"] = fields.get("so_that", "")
                payload["preconditions"] = fields.get("preconditions", "")
                payload["rules"] = fields.get("rules", "")
                payload["exceptions"] = fields.get("exceptions", "")
                payload["test_scenarios"] = fields.get("test_scenarios", "")
            
            elif item_type == "task":
                payload["story_link"] = fields.get("story_link")
                payload["acceptance_criteria"] = fields.get("acceptance_criteria", "")
            
            elif item_type in ["subtask", "sub-bug"]:
                payload["parent_key"] = fields.get("parent_key")
                payload["acceptance_criteria"] = fields.get("acceptance_criteria", "")
            
            elif item_type == "bug":
                payload["severity"] = fields.get("severity", "Medium")
                payload["error_scenario"] = fields.get("error_scenario", "")
                payload["expected_scenario"] = fields.get("expected_scenario", "")
                payload["impact"] = fields.get("impact", "")
                payload["origin"] = fields.get("origin", "")
                payload["solution"] = fields.get("solution", "")
                payload["steps_to_reproduce"] = fields.get("steps_to_reproduce", "")
            
            # Usa o template_generator para formatar o item de acordo com o template
            formatted_payload = generate_item(payload, item_type)
            
            logger.info(f"Item formatado com sucesso usando o template: {item_type}")
            return formatted_payload
            
        except TemplateGeneratorError as e:
            logger.error(f"Erro ao formatar item com template: {str(e)}")
            # Em caso de erro no template, usa a formatação antiga como fallback
            formatted_description = self.format_description(item_type, fields)
            payload["description"] = formatted_description
            return payload
    
    def create_item_in_jira(self, item_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um item no Jira com base no tipo e payload.
        
        Args:
            item_type: Tipo de item.
            payload: Payload com os dados do item.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira com informações de sucesso/erro.
        """
        try:
            logger.info(f"Iniciando criação de {item_type} no Jira")
            logger.info(f"Payload: {payload}")
            
            logger.info(f"Configuração Jira - URL: {self.jira_service.base_url}")
            logger.info(f"Configuração Jira - Project: {self.jira_service.project_key}")
            logger.info(f"Configuração Jira - Email: {self.jira_service.email}")
            
            if not payload.get("summary"):
                raise PromptProcessorError(f"Campo 'summary' é obrigatório para criar {item_type}")
            if not payload.get("description"):
                raise PromptProcessorError(f"Campo 'description' é obrigatório para criar {item_type}")
            
            # Cria o item no Jira com base no tipo
            response = None
            
            if item_type == "épico":
                logger.info("Criando épico no Jira")
                response = self.jira_service.create_epic(
                    summary=payload["summary"],
                    description=payload["description"],
                    epic_name=payload.get("epic_name", payload["summary"]),
                    labels=payload.get("labels", [])
                )
            
            elif item_type in ["história", "historia"]:
                logger.info("Criando história no Jira")
                epic_key = payload.get("epic_link") if payload.get("epic_link") else None
                if epic_key:
                    logger.info(f"História será vinculada ao épico: {epic_key}")
                
                response = self.jira_service.create_story(
                    summary=payload["summary"],
                    description=payload["description"],
                    epic_key=epic_key,
                    labels=payload.get("labels", [])
                )
            
            elif item_type == "task":
                logger.info("Criando task no Jira")
                parent_key = payload.get("story_link") if payload.get("story_link") else None
                if parent_key:
                    logger.info(f"Task será vinculada à história: {parent_key}")
                
                response = self.jira_service.create_task(
                    summary=payload["summary"],
                    description=payload["description"],
                    parent_key=parent_key,
                    labels=payload.get("labels", [])
                )
            
            elif item_type == "subtask":
                logger.info("Criando subtask no Jira")
                if not payload.get("parent_key"):
                    error_msg = "A chave do item pai é obrigatória para criar uma subtarefa"
                    logger.error(error_msg)
                    raise PromptProcessorError(error_msg)
                
                logger.info(f"Subtask será vinculada ao item pai: {payload['parent_key']}")
                response = self.jira_service.create_subtask(
                    summary=payload["summary"],
                    description=payload["description"],
                    parent_key=payload["parent_key"],
                    labels=payload.get("labels", [])
                )
            
            elif item_type == "bug":
                logger.info("Criando bug no Jira")
                parent_key = payload.get("parent_key") if payload.get("parent_key") else None
                if parent_key:
                    logger.info(f"Bug será vinculado ao item pai: {parent_key}")
                
                response = self.jira_service.create_bug(
                    summary=payload["summary"],
                    description=payload["description"],
                    parent_key=parent_key,
                    labels=payload.get("labels", [])
                )
            
            elif item_type == "sub-bug":
                logger.info("Criando sub-bug no Jira")
                if not payload.get("parent_key"):
                    error_msg = "A chave do item pai é obrigatória para criar um sub-bug"
                    logger.error(error_msg)
                    raise PromptProcessorError(error_msg)
                
                logger.info(f"Sub-bug será vinculado ao item pai: {payload['parent_key']}")
                response = self.jira_service.create_sub_bug(
                    summary=payload["summary"],
                    description=payload["description"],
                    parent_key=payload["parent_key"],
                    labels=payload.get("labels", [])
                )
            
            else:
                error_msg = f"Tipo de item não suportado: {item_type}"
                logger.error(error_msg)
                raise PromptProcessorError(error_msg)
            
            if response and response.get("key"):
                jira_key = response.get("key")
                jira_url = f"{self.jira_service.base_url}/browse/{jira_key}"
                logger.info(f"Item {item_type} criado com sucesso no Jira!")
                logger.info(f"Jira Key: {jira_key}")
                logger.info(f"Jira URL: {jira_url}")
                logger.info(f"Resposta completa do Jira: {response}")
                
                return {
                    "success": True,
                    "jira_key": jira_key,
                    "jira_url": jira_url,
                    "item_type": item_type,
                    "response": response
                }
            else:
                error_msg = f"Resposta inválida do Jira para {item_type}: {response}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "item_type": item_type,
                    "response": response
                }
        
        except PromptProcessorError as e:
            error_msg = f"Erro de validação ao criar {item_type}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "item_type": item_type,
                "error_type": "validation_error"
            }
        
        except Exception as e:
            error_msg = f"Erro inesperado ao criar {item_type} no Jira: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Tipo do erro: {type(e).__name__}")
            logger.error(f"Payload que causou o erro: {payload}")
            
            return {
                "success": False,
                "error": error_msg,
                "item_type": item_type,
                "error_type": "jira_api_error",
                "details": str(e)
            }
    
    def process_prompt(self, prompt_text: str) -> Dict[str, Any]:
        """
        Processa um prompt completo, desde a análise até a criação do item.
        
        Args:
            prompt_text: Texto do prompt do usuário.
            
        Returns:
            Dict[str, Any]: Resultado do processamento, incluindo o item criado.
        """
        try:
            # Analisa o prompt
            prompt_data = self.parse_prompt(prompt_text)
            item_type = prompt_data["type"]
            
            # Verifica se o usuário solicitou hierarquia automática
            if prompt_data.get("hierarchy_requested", False):
                return self._process_hierarchy_prompt(prompt_data)
            
            # Extrai campos do prompt
            fields = self.extract_fields(prompt_text, item_type)
            
            # Obtém contexto para enriquecer os dados
            context = self.get_context()
            
            # Se o GPT estiver disponível, tenta analisar o contexto
            if self.gpt_service:
                try:
                    logger.info("Usando GPT para analisar contexto")
                    context_analysis = self.gpt_service.analyze_context(prompt_text, context)
                    
                    # Usa as sugestões do contexto para enriquecer os campos
                    if context_analysis and "suggestions" in context_analysis:
                        logger.info("Aplicando sugestões do contexto")
                        # Implementação simplificada: apenas loga as sugestões
                        for suggestion in context_analysis["suggestions"]:
                            logger.info(f"Sugestão do contexto: {suggestion}")
                
                except GPTServiceError as e:
                    logger.warning(f"Erro ao analisar contexto com GPT: {str(e)}")
            
            # Constrói o payload para o Jira
            payload = self.build_item_payload(item_type, fields)
            
            # Cria o item no Jira
            jira_response = self.create_item_in_jira(item_type, payload)
            
            # Salva o item no S3
            s3_key = ""
            if "key" in jira_response:
                s3_item_type = S3_ITEM_TYPE_PREFIXES.get(ITEM_TYPES[item_type], item_type)
                s3_key = self.s3_service.save_item(
                    project_key=self.project_key,
                    item_type=s3_item_type,
                    item=payload,
                    metadata={
                        "jira_key": jira_response["key"],
                        "item_type": item_type,
                        "source": "prompt"
                    }
                )
            
            # Prepara o resultado
            result = {
                "success": True,
                "item_type": item_type,
                "jira_response": jira_response,
                "s3_key": s3_key
            }
            
            # Salva o contexto da interação
            self.save_context(prompt_data, result)
            
            return result
        
        except Exception as e:
            logger.error(f"Erro ao processar prompt: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "item_type": prompt_data["type"] if "prompt_data" in locals() and "type" in prompt_data else "unknown"
            }
    
    def _process_hierarchy_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um prompt para criação hierárquica de itens.
        
        Args:
            prompt_data: Dados do prompt processado.
            
        Returns:
            Dict[str, Any]: Resultado do processamento hierárquico.
        """
        try:
            logger.info("Iniciando processamento de hierarquia")
            
            # Se o GPT estiver disponível, tenta usar para sugerir hierarquia
            if self.gpt_service:
                try:
                    logger.info("Usando GPT para sugerir hierarquia")
                    suggested_hierarchy = self.gpt_service.suggest_hierarchy(prompt_data["raw_text"])
                    
                    if suggested_hierarchy:
                        logger.info(f"Hierarquia sugerida pelo GPT: {len(suggested_hierarchy)} itens")
                        # Aqui poderia implementar a lógica para usar a hierarquia sugerida pelo GPT
                        # Por enquanto, apenas loga a sugestão e continua com o método tradicional
                
                except GPTServiceError as e:
                    logger.warning(f"Erro ao sugerir hierarquia com GPT: {str(e)}")
            
            # Constrói a hierarquia de itens (método tradicional)
            hierarchy_items = build_hierarchy(prompt_data, self)
            
            # Permite que o usuário revise e confirme a hierarquia
            if not review_and_confirm(hierarchy_items):
                return {
                    "success": False,
                    "error": "Operação cancelada pelo usuário",
                    "item_type": "hierarchy"
                }
            
            # Cria os itens no Jira e estabelece as relações
            created_items = link_items(hierarchy_items, self.jira_service)
            
            # Salva os itens no S3
            s3_keys = []
            for item in created_items:
                if "jira_key" in item:
                    item_type = item["type"]
                    s3_item_type = S3_ITEM_TYPE_PREFIXES.get(ITEM_TYPES[item_type], item_type)
                    
                    s3_key = self.s3_service.save_item(
                        project_key=self.project_key,
                        item_type=s3_item_type,
                        item=item,
                        metadata={
                            "jira_key": item["jira_key"],
                            "item_type": item_type,
                            "source": "hierarchy_prompt"
                        }
                    )
                    
                    s3_keys.append(s3_key)
            
            # Prepara o resultado
            result = {
                "success": True,
                "item_type": "hierarchy",
                "items": created_items,
                "s3_keys": s3_keys
            }
            
            # Salva o contexto da interação
            self.save_context(prompt_data, result)
            
            return result
        
        except HierarchyBuilderError as e:
            logger.error(f"Erro ao processar hierarquia: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "item_type": "hierarchy"
            }
        except Exception as e:
            logger.error(f"Erro ao processar hierarquia: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "item_type": "hierarchy"
            }
