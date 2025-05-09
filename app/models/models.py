"""
Classes que representam os diferentes tipos de itens do Jira.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class BaseItem:
    """Classe base para todos os itens do Jira."""
    summary: str
    description: str = ""
    labels: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    priority: str = "Medium"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_jira_payload(self) -> dict:
        """Converte o item para o formato de payload do Jira API."""
        raise NotImplementedError("Subclasses devem implementar este método")
    
    def to_dict(self) -> dict:
        """
        Converte o item para um dicionário para armazenamento.
        
        Returns:
            dict: Representação do item como dicionário.
        """
        data = {}
        for key, value in self.__dict__.items():
            # Converte datetime para string ISO
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            else:
                data[key] = value
        return data


@dataclass
class Epic(BaseItem):
    """Representa um épico no Jira."""
    epic_name: str = ""  # Campo específico para épicos
    
    def to_jira_payload(self) -> dict:
        payload = {
            "fields": {
                "summary": self.summary,
                "description": self.description,
                "issuetype": {"name": "Epic"},
                "labels": self.labels,
                "customfield_10011": self.epic_name or self.summary  # Epic Name field
            }
        }
        if self.assignee:
            payload["fields"]["assignee"] = {"name": self.assignee}
        if self.priority:
            payload["fields"]["priority"] = {"name": self.priority}
        return payload


@dataclass
class Story(BaseItem):
    """Representa uma história no Jira."""
    epic_link: Optional[str] = None
    acceptance_criteria: str = ""
    
    def to_jira_payload(self) -> dict:
        payload = {
            "fields": {
                "summary": self.summary,
                "description": self.description,
                "issuetype": {"name": "Story"},
                "labels": self.labels
            }
        }
        if self.epic_link:
            payload["fields"]["customfield_10014"] = self.epic_link  # Epic Link field
        if self.assignee:
            payload["fields"]["assignee"] = {"name": self.assignee}
        if self.priority:
            payload["fields"]["priority"] = {"name": self.priority}
        return payload


@dataclass
class Task(BaseItem):
    """Representa uma task no Jira."""
    story_link: Optional[str] = None
    
    def to_jira_payload(self) -> dict:
        payload = {
            "fields": {
                "summary": self.summary,
                "description": self.description,
                "issuetype": {"name": "Task"},
                "labels": self.labels
            }
        }
        if self.assignee:
            payload["fields"]["assignee"] = {"name": self.assignee}
        if self.priority:
            payload["fields"]["priority"] = {"name": self.priority}
        return payload


@dataclass
class SubTask(BaseItem):
    """Representa uma subtask no Jira."""
    parent_key: str = ""
    
    def to_jira_payload(self) -> dict:
        payload = {
            "fields": {
                "summary": self.summary,
                "description": self.description,
                "issuetype": {"name": "Sub-task"},
                "parent": {"key": self.parent_key},
                "labels": self.labels
            }
        }
        if self.assignee:
            payload["fields"]["assignee"] = {"name": self.assignee}
        if self.priority:
            payload["fields"]["priority"] = {"name": self.priority}
        return payload


@dataclass
class Bug(BaseItem):
    """Representa um bug no Jira."""
    severity: str = "Medium"
    steps_to_reproduce: str = ""
    
    def to_jira_payload(self) -> dict:
        payload = {
            "fields": {
                "summary": self.summary,
                "description": self.description,
                "issuetype": {"name": "Bug"},
                "labels": self.labels + ["bug"]
            }
        }
        if self.assignee:
            payload["fields"]["assignee"] = {"name": self.assignee}
        if self.priority:
            payload["fields"]["priority"] = {"name": self.priority}
        return payload
