"""
Serviço para interação com a API do Jira.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List, Union

from config import (
    JIRA_BASE_URL, 
    JIRA_PROJECT_KEY, 
    JIRA_EMAIL, 
    JIRA_API_TOKEN, 
    ITEM_TYPES,
    JIRA_EPIC_LINK_FIELD
)

logger = logging.getLogger(__name__)

class JiraError(Exception):
    """Exceção personalizada para erros relacionados ao Jira."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class JiraService:
    """Classe para interagir com a API do Jira."""
    
    def __init__(self, base_url: str = None, email: str = None, token: str = None, project_key: str = None):
        """
        Inicializa o serviço Jira.
        
        Args:
            base_url: URL base do Jira. Se não fornecido, usa a configuração.
            email: Email de usuário do Jira. Se não fornecido, usa a configuração.
            token: Token de API do Jira. Se não fornecido, usa a configuração.
            project_key: Chave do projeto Jira. Se não fornecido, usa a configuração.
        """
        self.base_url = base_url or JIRA_BASE_URL
        self.email = email or JIRA_EMAIL
        self.token = token or JIRA_API_TOKEN or os.environ.get("JIRA_API_TOKEN")
        self.project_key = project_key or JIRA_PROJECT_KEY
        
        if not self.token:
            raise ValueError("Token de API do Jira não encontrado. Configure a variável de ambiente JIRA_API_TOKEN.")
        
        if not self.email:
            raise ValueError("Email do usuário Jira não encontrado. Configure JIRA_EMAIL.")
        
        if not self.project_key:
            raise ValueError("Chave do projeto Jira não encontrada. Configure JIRA_PROJECT_KEY.")
        
        self.auth = (self.email, self.token)  # Jira Cloud usa email como usuário
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _handle_error(self, response: requests.Response, operation: str) -> None:
        """
        Trata erros de resposta da API do Jira.
        
        Args:
            response: Objeto de resposta do requests.
            operation: Descrição da operação que falhou.
            
        Raises:
            JiraError: Se a resposta contiver um erro.
        """
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}
        
        error_message = f"Erro ao {operation}: {response.status_code}"
        if "errorMessages" in response_data:
            error_message += f" - {', '.join(response_data['errorMessages'])}"
        elif "errors" in response_data:
            error_message += f" - {json.dumps(response_data['errors'])}"
        
        logger.error(f"{error_message}. Resposta completa: {response_data}")
        raise JiraError(error_message, response.status_code, response_data)
    
    def _validate_response(self, response: requests.Response, operation: str) -> Dict[str, Any]:
        """
        Valida a resposta da API do Jira.
        
        Args:
            response: Objeto de resposta do requests.
            operation: Descrição da operação.
            
        Returns:
            Dict[str, Any]: Dados da resposta em formato JSON.
            
        Raises:
            JiraError: Se a resposta contiver um erro.
        """
        if not response.ok:
            self._handle_error(response, operation)
        
        try:
            return response.json()
        except ValueError:
            error_message = f"Resposta inválida ao {operation}: não é um JSON válido"
            logger.error(f"{error_message}. Resposta: {response.text}")
            raise JiraError(error_message)
    
    def create_issue(self, payload: Dict[str, Any], project_key: str = None) -> Dict[str, Any]:
        """
        Cria um novo item no Jira.
        
        Args:
            payload: Payload com os dados do item.
            project_key: Chave do projeto Jira. Se não fornecido, usa o valor padrão.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira.
        """
        project_key = project_key or self.project_key
        
        # Adiciona o projeto ao payload
        if "fields" in payload:
            payload["fields"]["project"] = {"key": project_key}
        else:
            payload["fields"] = {"project": {"key": project_key}}
        
        url = f"{self.base_url}/rest/api/2/issue"
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload)
            )
            return self._validate_response(response, "criar item")
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao criar item: {str(e)}")
            raise JiraError(f"Erro de conexão ao criar item: {str(e)}")
    
    def create_epic(self, summary: str, description: str, epic_name: str, labels: List[str] = None, 
                   custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Cria um novo épico no Jira.
        
        Args:
            summary: Título do épico.
            description: Descrição do épico.
            epic_name: Nome do épico (campo específico para épicos).
            labels: Lista de etiquetas para o épico.
            custom_fields: Campos personalizados adicionais.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira com os detalhes do épico criado.
        """
        fields = {
            "summary": summary,
            "description": description,
            "issuetype": {"name": ITEM_TYPES.get("épico", "Epic")},
        }
        
        # Adiciona o nome do épico (campo personalizado no Jira)
        fields[JIRA_EPIC_LINK_FIELD] = epic_name
        
        if labels:
            fields["labels"] = labels
        
        # Adiciona campos personalizados
        if custom_fields:
            fields.update(custom_fields)
        
        payload = {"fields": fields}
        return self.create_issue(payload)
    
    def create_story(self, summary: str, description: str, epic_key: str = None, 
                    labels: List[str] = None, custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Cria uma nova história no Jira.
        
        Args:
            summary: Título da história.
            description: Descrição da história.
            epic_key: Chave do épico ao qual a história será vinculada.
            labels: Lista de etiquetas para a história.
            custom_fields: Campos personalizados adicionais.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira com os detalhes da história criada.
        """
        fields = {
            "summary": summary,
            "description": description,
            "issuetype": {"name": ITEM_TYPES.get("história", "Story")},
        }
        
        if labels:
            fields["labels"] = labels
        
        # Adiciona campos personalizados
        if custom_fields:
            fields.update(custom_fields)
        
        payload = {"fields": fields}
        response = self.create_issue(payload)
        
        # Se um épico foi especificado, vincula a história ao épico
        if epic_key and response.get("key"):
            self.link_to_epic(response["key"], epic_key)
        
        return response
    
    def create_task(self, summary: str, description: str, parent_key: str = None,
                   labels: List[str] = None, custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Cria uma nova tarefa no Jira.
        
        Args:
            summary: Título da tarefa.
            description: Descrição da tarefa.
            parent_key: Chave do item pai (história ou épico).
            labels: Lista de etiquetas para a tarefa.
            custom_fields: Campos personalizados adicionais.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira com os detalhes da tarefa criada.
        """
        fields = {
            "summary": summary,
            "description": description,
            "issuetype": {"name": ITEM_TYPES.get("task", "Task")},
        }
        
        if labels:
            fields["labels"] = labels
        
        # Adiciona campos personalizados
        if custom_fields:
            fields.update(custom_fields)
        
        payload = {"fields": fields}
        response = self.create_issue(payload)
        
        # Se um pai foi especificado, vincula a tarefa ao pai
        if parent_key and response.get("key"):
            self.link_parent_child(parent_key, response["key"])
        
        return response
    
    def create_subtask(self, summary: str, description: str, parent_key: str,
                      labels: List[str] = None, custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Cria uma nova subtarefa no Jira.
        
        Args:
            summary: Título da subtarefa.
            description: Descrição da subtarefa.
            parent_key: Chave do item pai (obrigatório para subtarefas).
            labels: Lista de etiquetas para a subtarefa.
            custom_fields: Campos personalizados adicionais.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira com os detalhes da subtarefa criada.
        """
        if not parent_key:
            raise ValueError("A chave do item pai é obrigatória para criar uma subtarefa.")
        
        fields = {
            "summary": summary,
            "description": description,
            "issuetype": {"name": ITEM_TYPES.get("subtask", "Sub-task")},
            "parent": {"key": parent_key}
        }
        
        if labels:
            fields["labels"] = labels
        
        # Adiciona campos personalizados
        if custom_fields:
            fields.update(custom_fields)
        
        payload = {"fields": fields}
        return self.create_issue(payload)
    
    def create_bug(self, summary: str, description: str, parent_key: str = None,
                  labels: List[str] = None, custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Cria um novo bug no Jira.
        
        Args:
            summary: Título do bug.
            description: Descrição do bug.
            parent_key: Chave do item pai (opcional).
            labels: Lista de etiquetas para o bug.
            custom_fields: Campos personalizados adicionais.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira com os detalhes do bug criado.
        """
        fields = {
            "summary": summary,
            "description": description,
            "issuetype": {"name": ITEM_TYPES.get("bug", "Bug")},
        }
        
        # Garante que o bug tenha a etiqueta "bug"
        if labels:
            if "bug" not in labels:
                labels.append("bug")
        else:
            labels = ["bug"]
        
        fields["labels"] = labels
        
        # Adiciona campos personalizados
        if custom_fields:
            fields.update(custom_fields)
        
        payload = {"fields": fields}
        response = self.create_issue(payload)
        
        # Se um pai foi especificado, vincula o bug ao pai
        if parent_key and response.get("key"):
            self.link_parent_child(parent_key, response["key"])
        
        return response
    
    def create_sub_bug(self, summary: str, description: str, parent_key: str,
                      labels: List[str] = None, custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Cria um novo sub-bug no Jira (implementado como uma subtarefa com etiqueta de bug).
        
        Args:
            summary: Título do sub-bug.
            description: Descrição do sub-bug.
            parent_key: Chave do item pai (obrigatório para sub-bugs).
            labels: Lista de etiquetas para o sub-bug.
            custom_fields: Campos personalizados adicionais.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira com os detalhes do sub-bug criado.
        """
        # Garante que o sub-bug tenha a etiqueta "bug"
        if labels:
            if "bug" not in labels:
                labels.append("bug")
        else:
            labels = ["bug"]
        
        # Cria como uma subtarefa com etiqueta de bug
        return self.create_subtask(summary, description, parent_key, labels, custom_fields)
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um item do Jira.
        
        Args:
            issue_key: Chave do item.
            
        Returns:
            Dict[str, Any]: Detalhes do item.
        """
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers
            )
            return self._validate_response(response, f"obter item {issue_key}")
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao obter item {issue_key}: {str(e)}")
            raise JiraError(f"Erro de conexão ao obter item {issue_key}: {str(e)}")
    
    def update_issue(self, issue_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza um item existente no Jira.
        
        Args:
            issue_key: Chave do item a ser atualizado.
            payload: Payload com os dados a serem atualizados.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira.
        """
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        try:
            response = requests.put(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # PUT para atualização pode retornar 204 No Content
            if response.status_code == 204:
                return {"success": True, "key": issue_key}
            
            return self._validate_response(response, f"atualizar item {issue_key}")
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao atualizar item {issue_key}: {str(e)}")
            raise JiraError(f"Erro de conexão ao atualizar item {issue_key}: {str(e)}")
    
    def link_issues(self, outward_issue_key: str, inward_issue_key: str, link_type: str = "Relates") -> Dict[str, Any]:
        """
        Cria um link entre dois itens no Jira.
        
        Args:
            outward_issue_key: Chave do item de origem.
            inward_issue_key: Chave do item de destino.
            link_type: Tipo de link (ex: "Relates", "Blocks", "is blocked by").
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira.
        """
        url = f"{self.base_url}/rest/api/2/issueLink"
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_issue_key},
            "outwardIssue": {"key": outward_issue_key}
        }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # POST para criar link pode retornar 201 Created sem corpo
            if response.status_code == 201:
                return {
                    "success": True, 
                    "outward_key": outward_issue_key, 
                    "inward_key": inward_issue_key,
                    "link_type": link_type
                }
            
            return self._validate_response(response, f"vincular itens {outward_issue_key} e {inward_issue_key}")
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao vincular itens: {str(e)}")
            raise JiraError(f"Erro de conexão ao vincular itens: {str(e)}")
    
    def link_to_epic(self, issue_key: str, epic_key: str) -> Dict[str, Any]:
        """
        Vincula um item a um épico no Jira.
        
        Args:
            issue_key: Chave do item a ser vinculado.
            epic_key: Chave do épico.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira.
        """
        # Verifica se o épico existe
        try:
            epic = self.get_issue(epic_key)
            if epic.get("fields", {}).get("issuetype", {}).get("name") != ITEM_TYPES.get("épico", "Epic"):
                raise JiraError(f"O item {epic_key} não é um épico.")
        except JiraError:
            raise
        
        # Atualiza o item para incluir o link para o épico
        payload = {
            "fields": {
                JIRA_EPIC_LINK_FIELD: epic_key
            }
        }
        
        return self.update_issue(issue_key, payload)
    
    def link_parent_child(self, parent_key: str, child_key: str) -> Dict[str, Any]:
        """
        Estabelece uma relação pai-filho entre dois itens no Jira.
        
        Args:
            parent_key: Chave do item pai.
            child_key: Chave do item filho.
            
        Returns:
            Dict[str, Any]: Resposta da API do Jira.
        """
        # Verifica o tipo do item filho
        child = self.get_issue(child_key)
        child_type = child.get("fields", {}).get("issuetype", {}).get("name")
        
        # Se for uma subtarefa, usa a API específica para subtarefas
        if child_type == ITEM_TYPES.get("subtask", "Sub-task"):
            payload = {
                "fields": {
                    "parent": {"key": parent_key}
                }
            }
            return self.update_issue(child_key, payload)
        
        # Caso contrário, cria um link "relates to"
        return self.link_issues(parent_key, child_key, "Relates")
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Obtém a lista de projetos disponíveis.
        
        Returns:
            List[Dict[str, Any]]: Lista de projetos.
        """
        url = f"{self.base_url}/rest/api/2/project"
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers
            )
            return self._validate_response(response, "obter projetos")
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao obter projetos: {str(e)}")
            raise JiraError(f"Erro de conexão ao obter projetos: {str(e)}")
    
    def get_issue_types(self, project_key: str = None) -> List[Dict[str, Any]]:
        """
        Obtém os tipos de itens disponíveis para um projeto.
        
        Args:
            project_key: Chave do projeto. Se não fornecido, usa o valor padrão.
            
        Returns:
            List[Dict[str, Any]]: Lista de tipos de itens.
        """
        project_key = project_key or self.project_key
        url = f"{self.base_url}/rest/api/2/project/{project_key}/statuses"
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers
            )
            return self._validate_response(response, f"obter tipos de itens para o projeto {project_key}")
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao obter tipos de itens: {str(e)}")
            raise JiraError(f"Erro de conexão ao obter tipos de itens: {str(e)}")
    
    def search_issues(self, jql: str, max_results: int = 50, fields: List[str] = None) -> Dict[str, Any]:
        """
        Pesquisa itens no Jira usando JQL (Jira Query Language).
        
        Args:
            jql: Consulta JQL.
            max_results: Número máximo de resultados a retornar.
            fields: Lista de campos a incluir nos resultados.
            
        Returns:
            Dict[str, Any]: Resultados da pesquisa.
        """
        url = f"{self.base_url}/rest/api/2/search"
        payload = {
            "jql": jql,
            "maxResults": max_results
        }
        
        if fields:
            payload["fields"] = fields
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload)
            )
            return self._validate_response(response, f"pesquisar itens com JQL: {jql}")
        except requests.RequestException as e:
            logger.error(f"Erro de conexão ao pesquisar itens: {str(e)}")
            raise JiraError(f"Erro de conexão ao pesquisar itens: {str(e)}")
