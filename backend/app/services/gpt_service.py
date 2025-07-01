import openai
import logging
from typing import Dict, Any, Optional
from config import GPT_API_KEY, GPT_MODEL, GPT_MAX_TOKENS, GPT_TEMPERATURE

logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self):
        if not GPT_API_KEY:
            raise ValueError("GPT_API_KEY não configurado")
        openai.api_key = GPT_API_KEY
        self.client = openai.OpenAI(api_key=GPT_API_KEY)
    
    async def generate_epic_documentation(self, epic_details: Dict[str, Any]) -> str:
        """Generate documentation for an epic using GPT"""
        try:
            prompt = f"""
            Gere uma documentação completa para o seguinte épico do Jira:
            
            Título: {epic_details.get('summary', '')}
            Descrição: {epic_details.get('description', '')}
            
            A documentação deve incluir:
            1. Visão geral do épico
            2. Objetivos e metas
            3. Critérios de aceitação
            4. Riscos e dependências
            5. Cronograma estimado
            6. Stakeholders envolvidos
            
            Formate a resposta em Markdown.
            """
            
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um Product Manager experiente que cria documentação técnica detalhada."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=GPT_MAX_TOKENS,
                temperature=GPT_TEMPERATURE
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar documentação do épico: {str(e)}")
            raise
    
    async def enrich_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Enrich a user prompt with additional context and details"""
        try:
            system_prompt = """
            Você é um assistente de Product Manager que ajuda a enriquecer e detalhar prompts para criação de itens no Jira.
            Analise o prompt do usuário e adicione detalhes técnicos, critérios de aceitação e contexto relevante.
            """
            
            user_prompt = f"Prompt original: {prompt}"
            if context:
                user_prompt += f"\nContexto adicional: {context}"
            
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=GPT_MAX_TOKENS,
                temperature=GPT_TEMPERATURE
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao enriquecer prompt: {str(e)}")
            return prompt
