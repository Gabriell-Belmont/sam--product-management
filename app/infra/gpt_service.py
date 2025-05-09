"""
Módulo para integração com a API do GPT para melhorar o processamento de prompts
e a geração de conteúdo para itens do Jira.

Este módulo fornece uma interface para enviar prompts ao GPT e processar as respostas,
além de funções específicas para extrair informações de prompts e gerar conteúdo
de alta qualidade para os itens do Jira.
"""
import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import re
import random
import traceback

from config import (
    GPT_API_KEY, GPT_MODEL, GPT_MAX_TOKENS, GPT_TEMPERATURE,
    GPT_TIMEOUT, GPT_RETRY_ATTEMPTS, GPT_RETRY_DELAY, GPT_ENABLED
)

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gpt_service')


class GPTServiceError(Exception):
    """Exceção personalizada para erros do serviço GPT."""
    pass


class GPTService:
    """
    Classe para gerenciar a conexão com a API do GPT e processar prompts.
    
    Esta classe fornece métodos para enviar prompts ao GPT, processar as respostas
    e extrair informações estruturadas dos prompts dos usuários.
    """
    
    def __init__(self, api_key: str = None, model: str = None, **kwargs):
        """
        Inicializa o serviço GPT.
        
        Args:
            api_key: Chave de API do GPT (opcional, usa a configuração padrão se não fornecida)
            model: Modelo do GPT a ser usado (opcional, usa a configuração padrão se não fornecido)
            **kwargs: Argumentos adicionais para configuração
        """
        self.api_key = api_key or GPT_API_KEY
        self.model = model or GPT_MODEL
        self.max_tokens = kwargs.get('max_tokens', GPT_MAX_TOKENS)
        self.temperature = kwargs.get('temperature', GPT_TEMPERATURE)
        self.timeout = kwargs.get('timeout', GPT_TIMEOUT)
        self.retry_attempts = kwargs.get('retry_attempts', GPT_RETRY_ATTEMPTS)
        self.retry_delay = kwargs.get('retry_delay', GPT_RETRY_DELAY)
        
        # Verifica se o GPT está habilitado
        self.enabled = GPT_ENABLED
        
        # Inicializa o cliente OpenAI de forma lazy (apenas quando necessário)
        self._client = None
        
        logger.info(f"Serviço GPT inicializado com modelo: {self.model}")
    
    @property
    def client(self):
        """
        Obtém o cliente OpenAI, inicializando-o se necessário.
        
        Returns:
            Cliente OpenAI inicializado
        
        Raises:
            GPTServiceError: Se o OpenAI não estiver instalado ou ocorrer erro na inicialização
        """
        if self._client is None:
            try:
                # Importa o OpenAI apenas quando necessário
                from openai import OpenAI
                
                # Verifica se a chave de API está configurada
                if not self.api_key:
                    raise GPTServiceError(
                        "Chave de API do GPT não configurada. Configure a variável de ambiente GPT_API_KEY."
                    )
                
                # Inicializa o cliente
                self._client = OpenAI(api_key=self.api_key)
                
            except ImportError:
                raise GPTServiceError(
                    "Biblioteca OpenAI não instalada. Instale com: pip install openai"
                )
            except Exception as e:
                raise GPTServiceError(f"Erro ao inicializar cliente OpenAI: {str(e)}")
        
        return self._client
    
    def generate(self, prompt: str, system: str = None, **kwargs) -> str:
        """
        Gera uma resposta do GPT para o prompt fornecido.
        
        Args:
            prompt: Texto do prompt para enviar ao GPT
            system: Mensagem de sistema para contextualizar o GPT (opcional)
            **kwargs: Argumentos adicionais para a chamada da API
        
        Returns:
            str: Resposta gerada pelo GPT
        
        Raises:
            GPTServiceError: Se ocorrer um erro na chamada da API
        """
        if not self.enabled:
            logger.warning("Serviço GPT está desabilitado. Retornando prompt original.")
            return prompt
        
        # Prepara os parâmetros da chamada
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        timeout = kwargs.get('timeout', self.timeout)
        
        # Prepara as mensagens
        messages = []
        
        # Adiciona mensagem de sistema se fornecida
        if system:
            messages.append({"role": "system", "content": system})
        
        # Adiciona o prompt do usuário
        messages.append({"role": "user", "content": prompt})
        
        # Tenta fazer a chamada com retry
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Enviando prompt ao GPT (tentativa {attempt+1}/{self.retry_attempts})")
                
                # Faz a chamada à API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout
                )
                
                # Extrai e retorna o texto da resposta
                return response.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"Erro na chamada à API do GPT (tentativa {attempt+1}): {str(e)}")
                
                # Se for a última tentativa, levanta a exceção
                if attempt == self.retry_attempts - 1:
                    raise GPTServiceError(f"Erro ao gerar resposta do GPT após {self.retry_attempts} tentativas: {str(e)}")
                
                # Aguarda antes de tentar novamente
                time.sleep(self.retry_delay * (attempt + 1))  # Backoff exponencial
    
    def extract_fields(self, prompt: str, item_type: str = None) -> Dict[str, Any]:
        """
        Extrai campos estruturados de um prompt de usuário usando o GPT.
        
        Args:
            prompt: Texto do prompt do usuário
            item_type: Tipo de item (épico, história, task, etc.) se conhecido
        
        Returns:
            Dict[str, Any]: Dicionário com os campos extraídos
        
        Raises:
            GPTServiceError: Se ocorrer um erro na extração
        """
        if not self.enabled:
            logger.warning("Serviço GPT está desabilitado. Retornando dicionário vazio.")
            return {}
        
        try:
            # Constrói o prompt para o GPT com instruções específicas
            system_prompt = """
            Você é um assistente especializado em extrair informações estruturadas de prompts de usuários para criação de itens no Jira.
            Sua tarefa é analisar o texto do usuário e extrair campos relevantes para o tipo de item especificado.
            Retorne apenas um objeto JSON com os campos extraídos, sem explicações adicionais.
            """
            
            # Adiciona informações específicas sobre o tipo de item, se fornecido
            if item_type:
                system_prompt += f"\nO tipo de item é: {item_type}."
                
                # Adiciona instruções específicas por tipo
                if item_type == "épico":
                    system_prompt += """
                    Para épicos, extraia os seguintes campos quando disponíveis:
                    - summary: título do épico
                    - description: descrição detalhada
                    - epic_name: nome do épico (pode ser igual ao summary)
                    - objective: objetivo do épico
                    - benefits: benefícios esperados
                    - labels: etiquetas/tags (array de strings)
                    """
                elif item_type in ["história", "historia"]:
                    system_prompt += """
                    Para histórias, extraia os seguintes campos quando disponíveis:
                    - summary: título da história
                    - description: descrição detalhada
                    - as_a: persona/usuário (parte do formato "Como... Gostaria... Para...")
                    - i_want: desejo/necessidade (parte do formato "Como... Gostaria... Para...")
                    - so_that: benefício/resultado (parte do formato "Como... Gostaria... Para...")
                    - acceptance_criteria: critérios de aceitação (texto ou array de strings)
                    - preconditions: pré-condições
                    - rules: regras de negócio
                    - exceptions: exceções às regras
                    - test_scenarios: cenários de teste
                    - epic_link: referência ao épico pai (se mencionado)
                    - labels: etiquetas/tags (array de strings)
                    """
                elif item_type == "task":
                    system_prompt += """
                    Para tasks, extraia os seguintes campos quando disponíveis:
                    - summary: título da task
                    - description: descrição detalhada
                    - acceptance_criteria: critérios de aceitação (texto ou array de strings)
                    - story_link: referência à história pai (se mencionada)
                    - labels: etiquetas/tags (array de strings)
                    """
                elif item_type in ["subtask", "sub-bug"]:
                    system_prompt += """
                    Para subtasks, extraia os seguintes campos quando disponíveis:
                    - summary: título da subtask
                    - description: descrição detalhada
                    - parent_key: chave do item pai (obrigatório para subtasks)
                    - acceptance_criteria: critérios de aceitação (texto ou array de strings)
                    - labels: etiquetas/tags (array de strings)
                    """
                elif item_type == "bug":
                    system_prompt += """
                    Para bugs, extraia os seguintes campos quando disponíveis:
                    - summary: título do bug
                    - description: descrição detalhada
                    - error_scenario: cenário onde o erro ocorre
                    - expected_scenario: comportamento esperado
                    - impact: impacto do bug
                    - origin: origem do bug
                    - solution: solução proposta
                    - steps_to_reproduce: passos para reproduzir o bug
                    - severity: severidade (Low, Medium, High, Critical)
                    - parent_key: chave do item pai (se for um sub-bug)
                    - labels: etiquetas/tags (array de strings)
                    """
            else:
                # Se o tipo não for fornecido, instrui o GPT a identificar o tipo
                system_prompt += """
                Primeiro, identifique o tipo de item (épico, história, task, subtask, bug, sub-bug) com base no conteúdo.
                Inclua um campo "type" no JSON com o tipo identificado.
                Então extraia os campos relevantes para esse tipo, conforme descrito acima.
                """
            
            # Adiciona instruções sobre o formato da resposta
            system_prompt += """
            Retorne apenas um objeto JSON válido com os campos extraídos.
            Se um campo não puder ser extraído, não o inclua no JSON.
            Para campos que são arrays (como labels), retorne um array de strings.
            """
            
            # Faz a chamada ao GPT
            user_prompt = f"Extraia informações estruturadas do seguinte texto:\n\n{prompt}"
            response = self.generate(user_prompt, system=system_prompt, temperature=0.3)
            
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
                fields = json.loads(json_str)
                
                logger.info(f"Campos extraídos com sucesso: {', '.join(fields.keys())}")
                return fields
                
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao analisar JSON da resposta do GPT: {str(e)}")
                logger.debug(f"Resposta do GPT: {response}")
                raise GPTServiceError(f"Erro ao analisar resposta do GPT: {str(e)}")
            
        except Exception as e:
            logger.error(f"Erro ao extrair campos com GPT: {str(e)}")
            logger.debug(traceback.format_exc())
            raise GPTServiceError(f"Erro ao extrair campos com GPT: {str(e)}")
    
    def create_jira_content(self, item_type: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera conteúdo de alta qualidade para itens do Jira com base nos campos extraídos.
        
        Args:
            item_type: Tipo de item (épico, história, task, etc.)
            fields: Campos extraídos do prompt
        
        Returns:
            Dict[str, Any]: Dicionário com os campos enriquecidos
        
        Raises:
            GPTServiceError: Se ocorrer um erro na geração
        """
        if not self.enabled:
            logger.warning("Serviço GPT está desabilitado. Retornando campos originais.")
            return fields
        
        try:
            # Constrói o prompt para o GPT com instruções específicas
            system_prompt = """
            Você é um especialista em Product Management e desenvolvimento de software.
            Sua tarefa é enriquecer e estruturar o conteúdo de um item do Jira com base nos campos fornecidos.
            Gere conteúdo de alta qualidade, bem estruturado e detalhado para cada campo solicitado.
            """
            
            # Adiciona instruções específicas por tipo
            if item_type == "épico":
                system_prompt += """
                Para épicos, gere ou melhore os seguintes campos:
                - description: Uma descrição detalhada do épico, incluindo contexto, escopo e visão geral
                - objective: Objetivo claro e mensurável do épico
                - benefits: Lista de benefícios esperados, formatados como itens de lista
                
                Mantenha o tom profissional e objetivo. Foque em valor de negócio e impacto para o usuário.
                """
            elif item_type in ["história", "historia"]:
                system_prompt += """
                Para histórias, gere ou melhore os seguintes campos:
                - description: Descrição no formato "Como [persona], gostaria [necessidade] para [benefício]"
                - acceptance_criteria: Lista clara de critérios de aceitação, formatados como itens de lista
                - preconditions: Pré-condições necessárias para a história
                - rules: Regras de negócio relevantes
                - test_scenarios: Cenários de teste para validar a implementação
                
                Mantenha o foco no valor para o usuário e nos resultados esperados.
                """
            elif item_type == "task":
                system_prompt += """
                Para tasks, gere ou melhore os seguintes campos:
                - description: Descrição técnica clara da tarefa a ser realizada
                - acceptance_criteria: Critérios objetivos para considerar a task concluída
                
                Seja específico sobre o que precisa ser feito, como deve ser implementado e como será validado.
                """
            elif item_type in ["subtask", "sub-bug"]:
                system_prompt += """
                Para subtasks, gere ou melhore os seguintes campos:
                - description: Descrição concisa e específica da subtarefa
                - acceptance_criteria: Critérios objetivos para considerar a subtask concluída
                
                Mantenha o escopo bem definido e limitado, focando em uma única responsabilidade.
                """
            elif item_type == "bug":
                system_prompt += """
                Para bugs, gere ou melhore os seguintes campos:
                - description: Descrição clara do problema
                - error_scenario: Descrição detalhada do cenário onde o erro ocorre
                - expected_scenario: Comportamento esperado do sistema
                - impact: Impacto do bug para usuários e negócio
                - steps_to_reproduce: Passos detalhados para reproduzir o bug
                
                Seja preciso e objetivo, fornecendo todas as informações necessárias para que o bug possa ser reproduzido e corrigido.
                """
            
            # Adiciona instruções sobre o formato da resposta
            system_prompt += """
            Retorne apenas um objeto JSON válido com os campos enriquecidos.
            Mantenha os campos originais que não precisam de enriquecimento.
            Não adicione campos que não estavam presentes nos dados originais.
            """
            
            # Prepara o prompt do usuário com os campos atuais
            user_prompt = f"Enriqueça o conteúdo do seguinte item do Jira do tipo '{item_type}':\n\n"
            user_prompt += json.dumps(fields, indent=2, ensure_ascii=False)
            
            # Faz a chamada ao GPT
            response = self.generate(user_prompt, system=system_prompt, temperature=0.7)
            
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
                enriched_fields = json.loads(json_str)
                
                # Mescla os campos originais com os enriquecidos
                # (mantém os campos originais que não foram enriquecidos)
                result = {**fields}
                for key, value in enriched_fields.items():
                    if key in fields:
                        result[key] = value
                
                logger.info(f"Conteúdo enriquecido com sucesso para {item_type}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao analisar JSON da resposta do GPT: {str(e)}")
                logger.debug(f"Resposta do GPT: {response}")
                raise GPTServiceError(f"Erro ao analisar resposta do GPT: {str(e)}")
            
        except Exception as e:
            logger.error(f"Erro ao enriquecer conteúdo com GPT: {str(e)}")
            logger.debug(traceback.format_exc())
            raise GPTServiceError(f"Erro ao enriquecer conteúdo com GPT: {str(e)}")
    
    def suggest_hierarchy(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Sugere uma hierarquia completa de itens com base no prompt do usuário.
        
        Args:
            prompt: Texto do prompt do usuário
        
        Returns:
            List[Dict[str, Any]]: Lista de itens na hierarquia sugerida
        
        Raises:
            GPTServiceError: Se ocorrer um erro na geração
        """
        if not self.enabled:
            logger.warning("Serviço GPT está desabilitado. Retornando lista vazia.")
            return []
        
        try:
            # Constrói o prompt para o GPT com instruções específicas
            system_prompt = """
            Você é um especialista em Product Management e desenvolvimento de software.
            Sua tarefa é analisar o prompt do usuário e sugerir uma hierarquia completa de itens do Jira.
            
            A hierarquia deve incluir:
            1. Um épico para agrupar a funcionalidade
            2. Uma ou mais histórias de usuário detalhando as necessidades
            3. Tasks técnicas para implementação (backend, frontend, testes, etc.)
            4. Subtasks para cada task quando apropriado
            
            Para cada item, forneça:
            - type: Tipo do item (épico, história, task, subtask)
            - summary: Título conciso
            - description: Descrição detalhada
            - parent: Referência ao item pai (exceto para o épico)
            - campos específicos relevantes para cada tipo de item
            
            Retorne um array JSON com todos os itens da hierarquia.
            Cada item deve ter um campo "id" único para referência.
            Use o campo "parent_id" para indicar a relação hierárquica.
            """
            
            # Faz a chamada ao GPT
            user_prompt = f"Sugira uma hierarquia completa de itens do Jira para a seguinte funcionalidade:\n\n{prompt}"
            response = self.generate(user_prompt, system=system_prompt, temperature=0.7, max_tokens=4000)
            
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
                hierarchy = json.loads(json_str)
                
                logger.info(f"Hierarquia sugerida com sucesso: {len(hierarchy)} itens")
                return hierarchy
                
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao analisar JSON da resposta do GPT: {str(e)}")
                logger.debug(f"Resposta do GPT: {response}")
                raise GPTServiceError(f"Erro ao analisar resposta do GPT: {str(e)}")
            
        except Exception as e:
            logger.error(f"Erro ao sugerir hierarquia com GPT: {str(e)}")
            logger.debug(traceback.format_exc())
            raise GPTServiceError(f"Erro ao sugerir hierarquia com GPT: {str(e)}")
    
    def analyze_context(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa o contexto histórico para enriquecer o processamento do prompt atual.
        
        Args:
            prompt: Texto do prompt do usuário
            context: Contexto histórico (itens recentes, contextos anteriores)
        
        Returns:
            Dict[str, Any]: Sugestões e insights baseados no contexto
        
        Raises:
            GPTServiceError: Se ocorrer um erro na análise
        """
        if not self.enabled:
            logger.warning("Serviço GPT está desabilitado. Retornando dicionário vazio.")
            return {}
        
        try:
            # Limita o tamanho do contexto para evitar exceder o limite de tokens
            simplified_context = self._simplify_context(context)
            
            # Constrói o prompt para o GPT com instruções específicas
            system_prompt = """
            Você é um assistente especializado em Product Management.
            Sua tarefa é analisar o prompt atual do usuário junto com o contexto histórico
            e fornecer insights e sugestões para enriquecer o item atual.
            
            Considere:
            1. Itens relacionados no histórico
            2. Padrões de nomenclatura e estruturação
            3. Dependências potenciais
            4. Consistência com itens anteriores
            
            Retorne um objeto JSON com:
            - related_items: Itens relacionados do contexto
            - suggestions: Sugestões para melhorar o item atual
            - dependencies: Possíveis dependências a considerar
            - naming_patterns: Padrões de nomenclatura identificados
            """
            
            # Prepara o prompt do usuário
            user_prompt = f"Analise o seguinte prompt:\n\n{prompt}\n\nConsiderando o contexto histórico:\n\n"
            user_prompt += json.dumps(simplified_context, indent=2, ensure_ascii=False)
            
            # Faz a chamada ao GPT
            response = self.generate(user_prompt, system=system_prompt, temperature=0.5)
            
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
                analysis = json.loads(json_str)
                
                logger.info("Contexto analisado com sucesso")
                return analysis
                
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao analisar JSON da resposta do GPT: {str(e)}")
                logger.debug(f"Resposta do GPT: {response}")
                raise GPTServiceError(f"Erro ao analisar resposta do GPT: {str(e)}")
            
        except Exception as e:
            logger.error(f"Erro ao analisar contexto com GPT: {str(e)}")
            logger.debug(traceback.format_exc())
            raise GPTServiceError(f"Erro ao analisar contexto com GPT: {str(e)}")
    
    def _simplify_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplifica o contexto para reduzir o tamanho e focar nas informações mais relevantes.
        
        Args:
            context: Contexto completo
        
        Returns:
            Dict[str, Any]: Contexto simplificado
        """
        simplified = {}
        
        # Processa o histórico de itens
        if "item_history" in context:
            simplified["item_history"] = {}
            
            # Para cada tipo de item, mantém apenas os campos essenciais dos 5 itens mais recentes
            for item_type, items in context["item_history"].items():
                simplified["item_history"][item_type] = []
                
                # Ordena por data de criação (mais recentes primeiro) e limita a 5
                sorted_items = sorted(
                    items, 
                    key=lambda x: x.get("metadata", {}).get("created_at", ""), 
                    reverse=True
                )[:5]
                
                for item in sorted_items:
                    # Mantém apenas os campos essenciais
                    simplified_item = {
                        "summary": item.get("summary", ""),
                        "key": item.get("metadata", {}).get("jira_key", ""),
                        "created_at": item.get("metadata", {}).get("created_at", "")
                    }
                    
                    # Adiciona campos específicos por tipo
                    if item_type == "epics":
                        simplified_item["epic_name"] = item.get("epic_name", "")
                    elif item_type == "stories":
                        simplified_item["epic_link"] = item.get("epic_link", "")
                    elif item_type in ["tasks", "subtasks"]:
                        simplified_item["parent_key"] = item.get("parent_key", "")
                    
                    simplified["item_history"][item_type].append(simplified_item)
        
        # Processa os contextos anteriores
        if "contexts" in context:
            simplified["contexts"] = []
            
            # Mantém apenas os 3 contextos mais recentes
            for ctx in context["contexts"][:3]:
                # Simplifica cada contexto
                simplified_ctx = {
                    "timestamp": ctx.get("timestamp", ""),
                    "prompt": ctx.get("prompt", {}).get("raw_text", ""),
                    "type": ctx.get("prompt", {}).get("type", ""),
                    "result": {
                        "success": ctx.get("result", {}).get("success", False),
                        "item_type": ctx.get("result", {}).get("item_type", ""),
                        "jira_key": ctx.get("result", {}).get("jira_response", {}).get("key", "")
                    }
                }
                
                simplified["contexts"].append(simplified_ctx)
        
        return simplified
