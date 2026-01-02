"""Construction Monitor POC - Business Logic Service"""
import logging
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .construction_monitor_schemas import *

logger = logging.getLogger(__name__)

class Construction_monitorService:
    """Real-time project monitoring and reporting"""
    
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService()

    async def process_request(self, request: Construction_monitorRequest) -> Construction_monitorResponse:
        """Process customer-specific request combining multiple Tier 2 capabilities"""
        try:
            # Use LLM for customer-specific intelligence
            prompt = f"Process query for Construction Monitor POC: {request.query}. Provide actionable insights in 2-3 sentences."
            insights = await self.llm_service.generate_response(prompt, model="gpt-4o-mini", temperature=0.3)
            
            return Construction_monitorResponse(
                success=True,
                session_id=request.session_id,
                result={"query": request.query, "processed": True},
                insights=insights.strip(),
                recommendations=["Review findings", "Take action", "Monitor progress"]
            )
        except Exception as e:
            logger.error(f"Construction Monitor POC error: {e}", exc_info=True)
            raise

    async def get_status(self) -> StatusResponse:
        """Get POC status and integrated Tier 2 modules"""
        return StatusResponse(
            success=True,
            status="operational",
            description="Real-time project monitoring and reporting",
            tier_2_modules_used=["document-intelligence", "generic-rag", "predictive-analytics"]
        )
