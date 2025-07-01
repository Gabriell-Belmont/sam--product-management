from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os
from datetime import datetime

from app.infra.jira_service import JiraService
from app.services.gpt_service import GPTService
from app.services.s3_service import S3Service
from app.agents.multi_agent_system import MultiAgentSystem
from config import *

app = FastAPI(title="SAM Product Management API", version="1.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

try:
    jira_service = JiraService()
except Exception as e:
    logging.warning(f"JiraService initialization failed: {e}. Using mock service.")
    jira_service = None

try:
    gpt_service = GPTService() if GPT_ENABLED else None
except Exception as e:
    logging.warning(f"GPTService initialization failed: {e}. Disabling GPT features.")
    gpt_service = None

try:
    s3_service = S3Service()
except Exception as e:
    logging.warning(f"S3Service initialization failed: {e}. Using mock service.")
    s3_service = None

try:
    multi_agent_system = MultiAgentSystem()
except Exception as e:
    logging.warning(f"MultiAgentSystem initialization failed: {e}. Using mock system.")
    multi_agent_system = None

class ItemRequest(BaseModel):
    item_type: str
    summary: str
    description: str
    epic_link: Optional[str] = None
    story_link: Optional[str] = None
    parent_key: Optional[str] = None
    labels: Optional[List[str]] = []
    assignee: Optional[str] = None
    priority: Optional[str] = None
    user_context: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    user_context: Optional[str] = None

class ConflictCheck(BaseModel):
    summary: str
    description: str
    item_type: str
    user_context: Optional[str] = None

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/chat")
async def chat_with_agents(request: ChatMessage):
    """Chat with the multi-agent system to discuss requirements"""
    try:
        if multi_agent_system:
            response = await multi_agent_system.process_chat(
                message=request.message,
                user_context=request.user_context
            )
        else:
            response = f"Olá! Recebi sua mensagem: '{request.message}'. Como este é um ambiente de desenvolvimento, estou funcionando em modo demo. Para funcionalidade completa, configure as chaves de API necessárias."
        
        return {"response": response, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logging.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-conflicts")
async def check_conflicts(request: ConflictCheck):
    """Check for conflicts with existing items"""
    try:
        if s3_service:
            conflicts = await s3_service.check_conflicts(
                summary=request.summary,
                description=request.description,
                item_type=request.item_type,
                user_context=request.user_context
            )
        else:
            conflicts = []
            if "botão" in request.summary.lower() and "laranja" in request.summary.lower():
                conflicts = [{
                    "item_key": "DEMO-123",
                    "summary": "Alterar cor do botão para azul",
                    "created_at": "2024-12-15",
                    "conflict_reason": "Conflito detectado: solicitação anterior para mudar cor do botão"
                }]
        
        return {"conflicts": conflicts, "has_conflicts": len(conflicts) > 0}
    except Exception as e:
        logging.error(f"Error checking conflicts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-item")
async def create_item(request: ItemRequest):
    """Create a new Jira item"""
    try:
        if s3_service:
            conflicts = await s3_service.check_conflicts(
                summary=request.summary,
                description=request.description,
                item_type=request.item_type,
                user_context=request.user_context
            )
        else:
            conflicts = []
        
        if conflicts:
            return {
                "success": False,
                "conflicts": conflicts,
                "message": "Conflitos detectados. Revise antes de prosseguir."
            }
        
        if jira_service:
            if request.item_type.lower() in ["épico", "epic"]:
                response = jira_service.create_epic(
                    summary=request.summary,
                    description=request.description,
                    epic_name=request.summary,
                    labels=request.labels or []
                )
            elif request.item_type.lower() in ["história", "historia", "story"]:
                if not request.epic_link:
                    raise HTTPException(status_code=400, detail="Epic link é obrigatório para histórias")
                response = jira_service.create_story(
                    summary=request.summary,
                    description=request.description,
                    epic_key=request.epic_link,
                    labels=request.labels or []
                )
            elif request.item_type.lower() == "task":
                if not request.story_link:
                    raise HTTPException(status_code=400, detail="Story link é obrigatório para tasks")
                response = jira_service.create_task(
                    summary=request.summary,
                    description=request.description,
                    parent_key=request.story_link,
                    labels=request.labels or []
                )
            elif request.item_type.lower() == "subtask":
                if not request.parent_key:
                    raise HTTPException(status_code=400, detail="Parent key é obrigatório para subtasks")
                response = jira_service.create_subtask(
                    summary=request.summary,
                    description=request.description,
                    parent_key=request.parent_key,
                    labels=request.labels or []
                )
            elif request.item_type.lower() == "bug":
                response = jira_service.create_bug(
                    summary=request.summary,
                    description=request.description,
                    parent_key=request.parent_key or "",
                    labels=request.labels or []
                )
            else:
                raise HTTPException(status_code=400, detail="Tipo de item não suportado")
        else:
            import random
            mock_key = f"DEMO-{random.randint(100, 999)}"
            response = {
                "key": mock_key,
                "id": str(random.randint(10000, 99999)),
                "self": f"https://demo.atlassian.net/rest/api/2/issue/{mock_key}"
            }
        
        if s3_service:
            await s3_service.save_item_context(
                item_key=response.get("key"),
                item_type=request.item_type,
                summary=request.summary,
                description=request.description,
                user_context=request.user_context
            )
        
        return {
            "success": True,
            "item": response,
            "message": f"Item {response.get('key')} criado com sucesso!" + (" (modo demo)" if not jira_service else "")
        }
        
    except Exception as e:
        logging.error(f"Error creating item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user-context/{user_id}")
async def get_user_context(user_id: str):
    """Get user's historical context from S3"""
    try:
        if s3_service:
            context = await s3_service.get_user_context(user_id)
        else:
            context = {"message": "S3 service not available in demo mode", "items": []}
        return {"context": context}
    except Exception as e:
        logging.error(f"Error getting user context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-epic-documentation")
async def generate_epic_documentation(request: dict):
    """Generate documentation for an epic using GPT"""
    try:
        epic_key = request.get("epic_key")
        if not epic_key:
            raise HTTPException(status_code=400, detail="Epic key is required")
        
        if not gpt_service:
            return {
                "epic_key": epic_key,
                "documentation": f"Documentação do épico {epic_key} (modo demo):\n\n## Visão Geral\nEste épico representa uma iniciativa importante do produto.\n\n## Objetivos\n- Melhorar a experiência do usuário\n- Aumentar a eficiência operacional\n\n## Critérios de Aceitação\n- Funcionalidade implementada conforme especificação\n- Testes unitários e de integração passando\n- Documentação atualizada",
                "generated_at": datetime.now().isoformat()
            }
        
        if jira_service:
            epic_details = jira_service.get_issue(epic_key)
        else:
            epic_details = {"key": epic_key, "summary": "Epic demo", "description": "Epic de demonstração"}
        
        documentation = await gpt_service.generate_epic_documentation(epic_details)
        
        return {
            "epic_key": epic_key,
            "documentation": documentation,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error generating epic documentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
