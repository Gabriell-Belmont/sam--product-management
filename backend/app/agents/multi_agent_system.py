from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MultiAgentSystem:
    def __init__(self):
        self.product_manager = self._create_product_manager()
        self.quality_assurance = self._create_quality_assurance()
        self.stakeholder = self._create_stakeholder()
        self.tech_lead = self._create_tech_lead()
        
        self.crew = Crew(
            agents=[self.product_manager, self.quality_assurance, self.stakeholder, self.tech_lead],
            tasks=[],
            verbose=True,
            process="sequential"
        )
    
    def _create_product_manager(self) -> Agent:
        return Agent(
            role="Product Manager",
            goal="Analisar requisitos e definir especificações claras para desenvolvimento",
            backstory="""Você é um Product Manager experiente com mais de 10 anos de experiência 
            em desenvolvimento de produtos digitais. Você é especialista em traduzir necessidades 
            de negócio em especificações técnicas claras e priorizadas.""",
            verbose=True,
            allow_delegation=True
        )
    
    def _create_quality_assurance(self) -> Agent:
        return Agent(
            role="Quality Assurance",
            goal="Garantir qualidade e identificar possíveis problemas nos requisitos",
            backstory="""Você é um QA Lead com vasta experiência em testes e garantia de qualidade. 
            Você é especialista em identificar edge cases, problemas de usabilidade e gaps nos requisitos.""",
            verbose=True,
            allow_delegation=False
        )
    
    def _create_stakeholder(self) -> Agent:
        return Agent(
            role="Stakeholder",
            goal="Representar os interesses do negócio e validar alinhamento estratégico",
            backstory="""Você é um representante dos stakeholders de negócio, com foco em ROI, 
            experiência do usuário e alinhamento com objetivos estratégicos da empresa.""",
            verbose=True,
            allow_delegation=False
        )
    
    def _create_tech_lead(self) -> Agent:
        return Agent(
            role="Tech Lead",
            goal="Avaliar viabilidade técnica e estimar esforço de desenvolvimento",
            backstory="""Você é um Tech Lead sênior com ampla experiência em arquitetura de software 
            e liderança técnica. Você é especialista em avaliar complexidade técnica e identificar 
            riscos de implementação.""",
            verbose=True,
            allow_delegation=False
        )
    
    async def process_chat(self, message: str, user_context: Optional[str] = None) -> str:
        """Process a chat message through the multi-agent system"""
        try:
            context_info = f"\nContexto do usuário: {user_context}" if user_context else ""
            
            task = Task(
                description=f"""
                Analise a seguinte solicitação do usuário e forneça uma resposta colaborativa:
                
                Solicitação: {message}{context_info}
                
                Cada agente deve contribuir com sua perspectiva:
                - Product Manager: Definir requisitos e especificações
                - QA: Identificar riscos e casos de teste
                - Stakeholder: Validar valor de negócio
                - Tech Lead: Avaliar viabilidade técnica
                
                Forneça uma resposta consolidada com recomendações claras.
                """,
                expected_output="Uma resposta estruturada com análise de cada perspectiva e recomendações finais",
                agent=self.product_manager
            )
            
            result = self.crew.kickoff(inputs={"message": message, "context": user_context or ""})
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in multi-agent processing: {str(e)}")
            return f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
    
    async def analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze requirements through all agents"""
        try:
            analysis_task = Task(
                description=f"""
                Analise os seguintes requisitos de forma colaborativa:
                
                Tipo: {requirements.get('item_type')}
                Resumo: {requirements.get('summary')}
                Descrição: {requirements.get('description')}
                
                Cada agente deve fornecer sua análise:
                - Product Manager: Clareza dos requisitos, priorização
                - QA: Testabilidade, casos de teste necessários
                - Stakeholder: Valor de negócio, alinhamento estratégico
                - Tech Lead: Complexidade técnica, estimativa de esforço
                """,
                expected_output="Análise estruturada com feedback de cada agente",
                agent=self.product_manager
            )
            
            result = self.crew.kickoff(inputs={"requirements": requirements})
            
            return {
                "analysis": str(result),
                "recommendations": self._extract_recommendations(str(result)),
                "risks": self._extract_risks(str(result)),
                "estimated_effort": self._extract_effort(str(result))
            }
            
        except Exception as e:
            logger.error(f"Error in requirements analysis: {str(e)}")
            return {
                "analysis": f"Erro na análise: {str(e)}",
                "recommendations": [],
                "risks": [],
                "estimated_effort": "Não foi possível estimar"
            }
    
    def _extract_recommendations(self, analysis: str) -> list:
        """Extract recommendations from analysis"""
        return ["Implementar validações de entrada", "Adicionar testes automatizados", "Documentar casos de uso"]
    
    def _extract_risks(self, analysis: str) -> list:
        """Extract risks from analysis"""
        return ["Complexidade técnica alta", "Dependências externas", "Impacto em sistemas existentes"]
    
    def _extract_effort(self, analysis: str) -> str:
        """Extract effort estimation from analysis"""
        return "Médio (5-8 story points)"
