"""
Enhanced main.py with:
- Memory hierarchy (short-term + long-term)
- Session management
- Audit logging
- RBAC support (basic implementation)

This file demonstrates the key updates needed for main.py
"""

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
import logging
from typing import Optional
import uvicorn
import uuid
import time

from app.core.config import settings
from app.core.database import init_db, close_db, get_db
from app.api.graphql.schema import schema
from app.services.embedding_service import embedding_service

# Import consolidated RAG service with memory hierarchy
from app.services.rag_service import rag_service
logger_temp = logging.getLogger(__name__)
logger_temp.info("✓ Using RAG Service with memory hierarchy")
ENHANCED_RAG_AVAILABLE = True  # Always true now (consolidated)

# Import consolidated LLM service with multi-model support
from app.services.llm_service import llm_service
logger_temp.info("✓ Using LLM Service with multi-model support and Claude integration")

from app.services.document_service import document_service
from app.services.scraper_service import scraper_service
from app.services.audit_service import audit_service
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Helper function to get client IP and user agent
def get_client_info(request: Request):
    """Extract client IP and user agent from request"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


# Helper function to get or create anonymous user
async def get_anonymous_user_id(db: AsyncSession) -> Optional[uuid.UUID]:
    """Get the anonymous user ID for unauthenticated requests"""
    try:
        from app.models.database_enhanced import User
        from sqlalchemy import select

        query = select(User).where(User.username == 'anonymous')
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        return user.id if user else None
    except Exception as e:
        logger.warning(f"Could not get anonymous user: {e}")
        return None


# Lifespan context manager (same as before)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("Starting up application...")

    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    try:
        await embedding_service.initialize()
        logger.info("Embedding service initialized")
    except Exception as e:
        logger.warning(f"Embedding service initialization failed: {e}")

    try:
        await llm_service.initialize()
        logger.info("LLM service initialized")
    except Exception as e:
        logger.warning(f"LLM service initialization failed: {e}")

    try:
        await document_service.initialize()
        logger.info("Document service initialized")
    except Exception as e:
        logger.warning(f"Document service initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GraphQL router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Add Evaluation router
try:
    from app.api.routes.evaluation import router as evaluation_router
    app.include_router(evaluation_router)
    logger.info("✓ Evaluation API routes loaded")
except ImportError as e:
    logger.warning(f"⚠ Evaluation routes not available: {e}")

# Add Construction Metrics router
try:
    from app.api.routes.construction_metrics_routes import router as construction_metrics_router
    app.include_router(construction_metrics_router)
    logger.info("✓ Construction Metrics API routes loaded")
except Exception as e:
    logger.warning(f"⚠ Construction Metrics routes not available: {type(e).__name__}: {e}")

# Add Fine-Tuning router
try:
    from app.api.routes.finetuning_routes import router as finetuning_router
    app.include_router(finetuning_router)
    logger.info("✓ Fine-Tuning API routes loaded")
except Exception as e:
    logger.warning(f"⚠ Fine-Tuning routes not available: {type(e).__name__}: {e}")


# === REST API Endpoints ===

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "features": {
            "enhanced_rag": ENHANCED_RAG_AVAILABLE,
            "memory_hierarchy": ENHANCED_RAG_AVAILABLE,
            "audit_logging": True,
            "session_management": True
        }
    }


@app.post("/api/v1/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),  # NEW: Session ID
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file for processing

    NEW: Associates document with session for short-term memory
    """
    start_time = time.time()
    ip_address, user_agent = get_client_info(request)
    user_id = await get_anonymous_user_id(db)

    try:
        # Read file data
        file_data = await file.read()

        # Upload and create document
        document = await document_service.upload_file(
            file_data=file_data,
            filename=file.filename,
            file_type=file.content_type,
            source_type="upload",
            db=db
        )

        # Process document asynchronously (chunk and embed)
        await document_service.process_document(document.id, db)

        # NEW: Associate document with session for short-term memory
        if session_id and ENHANCED_RAG_AVAILABLE:
            await rag_service.associate_document_with_session(
                session_id=session_id,
                document_id=document.id,
                priority=1,  # Higher priority for recently uploaded docs
                db=db
            )
            logger.info(f"Associated document {document.id} with session {session_id}")

        latency_ms = (time.time() - start_time) * 1000

        # NEW: Audit logging
        await audit_service.log_upload(
            db=db,
            document_id=document.id,
            filename=file.filename,
            file_size=len(file_data),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            success=True
        )

        return {
            "success": True,
            "document_id": str(document.id),
            "filename": document.filename,
            "session_id": session_id,
            "message": "File uploaded and processed successfully",
            "in_session_memory": session_id is not None,
            "latency_ms": latency_ms
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}")

        # Audit log the failure
        await audit_service.log_upload(
            db=db,
            document_id=None,
            filename=file.filename,
            file_size=0,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            success=False,
            error_message=str(e)
        )

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/query")
async def query_endpoint(
    request: Request,
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),  # 🆕 Project-based filtering
    use_cache: bool = Form(True),
    model_id: Optional[str] = Form(None),
    # NEW: Optional threshold parameters from UI
    top_k: Optional[int] = Form(None),
    similarity_threshold: Optional[float] = Form(None),
    min_similarity_threshold: Optional[float] = Form(None),
    no_relevant_docs_threshold: Optional[float] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Query the RAG system with memory hierarchy

    NEW:
    - Uses short-term memory (session documents) first
    - Falls back to long-term memory (all documents)
    - Tracks conversation history
    - Logs to audit trail
    - Accepts threshold parameters from UI for dynamic tuning
    """
    start_time = time.time()
    ip_address, user_agent = get_client_info(request)
    user_id = await get_anonymous_user_id(db)

    try:
        # NEW: Use enhanced RAG service with memory hierarchy and UI threshold parameters
        result = await rag_service.query(
            query_text=query,
            session_id=session_id,
            project_id=project_id,  # 🆕 Pass project_id for filtering
            user_id=user_id,
            conversation_history=None,
            use_cache=use_cache,
            model_id=model_id,
            db=db,
            # Pass through threshold parameters from UI (or None to use defaults)
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            min_similarity_threshold=min_similarity_threshold,
            no_relevant_docs_threshold=no_relevant_docs_threshold
        )

        latency_ms = (time.time() - start_time) * 1000

        # NEW: Audit logging
        await audit_service.log_query(
            db=db,
            query_text=query,
            user_id=user_id,
            session_id=session_id,
            model_id=result.get('model', 'unknown'),
            response=result,
            latency_ms=latency_ms,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return result

    except Exception as e:
        logger.error(f"Error processing query: {e}")

        # Audit log the failure
        await audit_service.log_action(
            db=db,
            action='query',
            user_id=user_id,
            session_id=session_id,
            description=f"Query failed: {query[:50]}...",
            error_message=str(e),
            status_code=500,
            ip_address=ip_address
        )

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/scrape")
async def scrape_endpoint(
    request: Request,
    url: str = Form(...),
    scrape_prompt: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),  # NEW: Session ID
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape a URL and process the content

    NEW: Associates scraped document with session
    """
    ip_address, user_agent = get_client_info(request)
    user_id = await get_anonymous_user_id(db)

    try:
        result = await scraper_service.scrape_url(
            url=url,
            scrape_prompt=scrape_prompt,
            db=db
        )

        # NEW: Associate scraped document with session
        if session_id and result.get('document_id') and ENHANCED_RAG_AVAILABLE:
            doc_id = uuid.UUID(result['document_id'])
            await rag_service.associate_document_with_session(
                session_id=session_id,
                document_id=doc_id,
                priority=1,
                db=db
            )

        # NEW: Audit logging
        await audit_service.log_scrape(
            db=db,
            url=url,
            document_id=uuid.UUID(result['document_id']) if result.get('document_id') else None,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            success=result.get('success', False),
            error_message=result.get('error')
        )

        result['session_id'] = session_id
        result['in_session_memory'] = session_id is not None

        return result

    except Exception as e:
        logger.error(f"Error scraping URL: {e}")

        await audit_service.log_scrape(
            db=db,
            url=url,
            document_id=None,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            success=False,
            error_message=str(e)
        )

        raise HTTPException(status_code=500, detail=str(e))


# === NEW: Session Management Endpoints ===

@app.get("/api/v1/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get session information and conversation history"""
    try:
        from app.models.database_enhanced import ChatSession, ConversationMessage
        from sqlalchemy import select

        # Get session
        session_query = select(ChatSession).where(ChatSession.session_id == session_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get messages
        messages_query = select(ConversationMessage).where(
            ConversationMessage.session_id == session.id
        ).order_by(ConversationMessage.created_at)

        messages_result = await db.execute(messages_query)
        messages = messages_result.scalars().all()

        return {
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": len(messages),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "model_name": msg.model_name,
                    "created_at": msg.created_at.isoformat(),
                    "sources": msg.sources
                }
                for msg in messages
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions/{session_id}/audit")
async def get_session_audit(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs for a specific session"""
    try:
        logs = await audit_service.get_session_activity(
            db=db,
            session_id=session_id,
            limit=100
        )

        return {
            "session_id": session_id,
            "log_count": len(logs),
            "logs": logs
        }

    except Exception as e:
        logger.error(f"Error getting session audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Other endpoints from original main.py...
# (get_documents, get_models, etc.)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
