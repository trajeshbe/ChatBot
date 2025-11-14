from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
import logging
from typing import Optional, List
import uvicorn
import uuid
import time

from app.core.config import settings
from app.core.database import init_db, close_db, get_db
from app.api.graphql.schema import schema
from app.services.embedding_service import embedding_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# Try to import enhanced LLM service, fallback to basic if it fails
try:
    from app.services.llm_service_enhanced import llm_service
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("✓ Using Enhanced LLM Service with multi-model support")
except ImportError as e:
    from app.services.llm_service import llm_service
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠ Enhanced LLM service not available: {e}")
    logger_temp.warning("⚠ Using basic LLM service - model selection will not work")
    import traceback
    logger_temp.debug(f"Import traceback: {traceback.format_exc()}")

from app.services.document_service import document_service
from app.services.scraper_service import scraper_service

# Try to import enhanced RAG service with memory hierarchy
try:
    from app.services.rag_service_enhanced import enhanced_rag_service as rag_service
    logger_temp.info("✓ Using Enhanced RAG Service with memory hierarchy")
    ENHANCED_RAG_AVAILABLE = True
except ImportError:
    from app.services.rag_service import rag_service
    logger_temp.warning("⚠ Enhanced RAG service not available, using basic RAG")
    ENHANCED_RAG_AVAILABLE = False

# Import audit service
try:
    from app.services.audit_service import audit_service
    logger_temp.info("✓ Audit service loaded")
except ImportError:
    logger_temp.warning("⚠ Audit service not available")
    audit_service = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Helper functions
def get_client_info(request):
    """Extract client IP and user agent from request"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


async def get_anonymous_user_id(db: AsyncSession):
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


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting up application...")

    # Initialize database with retries
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Application starting without database - some features may not work")

    # Initialize services (non-blocking)
    try:
        logger.info("Initializing embedding service...")
        await embedding_service.initialize()
        logger.info("Embedding service initialized")
    except Exception as e:
        logger.warning(f"Embedding service initialization failed: {e}")

    try:
        logger.info(f"Initializing LLM service... (Type: {type(llm_service).__name__})")
        await llm_service.initialize()
        logger.info(f"✓ LLM service initialized successfully (Type: {type(llm_service).__name__})")

        # Log model availability if enhanced service
        if hasattr(llm_service, 'get_available_models'):
            try:
                models_info = llm_service.get_available_models()
                logger.info(f"Available models: {len(models_info.get('models', []))} total")
                logger.info(f"Default model: {models_info.get('default', 'not set')}")
            except Exception as e:
                logger.warning(f"Could not get model info: {e}")
    except Exception as e:
        logger.warning(f"LLM service initialization failed: {e}")

    try:
        logger.info("Initializing document service...")
        await document_service.initialize()
        logger.info("Document service initialized")
    except Exception as e:
        logger.warning(f"Document service initialization failed: {e}")

    logger.info("Application startup complete - API is ready")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        await close_db()
        await embedding_service.close()
        await llm_service.close()
        await scraper_service.close()
        logger.info("All services closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
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
            "audit_logging": audit_service is not None,
            "session_management": ENHANCED_RAG_AVAILABLE
        }
    }


# REST API endpoints
@app.post("/api/v1/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file for processing and associate with session"""
    import time
    import uuid

    start_time = time.time()
    ip_address, user_agent = get_client_info(request)
    user_id = await get_anonymous_user_id(db)

    try:
        # Read file data
        file_data = await file.read()

        # Check for duplicate file in this session
        if session_id and ENHANCED_RAG_AVAILABLE:
            from app.models.database import Document
            from app.models.database_enhanced import SessionDocument, ChatSession
            from sqlalchemy import and_

            # Ensure session exists (create if needed)
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                # Create new session
                session = ChatSession(
                    session_id=session_id,
                    user_id=user_id
                )
                db.add(session)
                await db.flush()  # Get the session ID
                logger.info(f"Created new chat session: {session_id}")

            # Check if a document with same filename and file size already exists in this session
            duplicate_query = select(Document).join(
                SessionDocument, Document.id == SessionDocument.document_id
            ).where(
                and_(
                    SessionDocument.session_id == session.id,
                    Document.filename == file.filename,
                    Document.file_size == len(file_data)
                )
            )
            duplicate_result = await db.execute(duplicate_query)
            existing_document = duplicate_result.scalar_one_or_none()

            if existing_document:
                logger.warning(f"Duplicate file detected: {file.filename} (already in session {session_id})")
                return {
                    "success": False,
                    "message": f"File '{file.filename}' has already been uploaded to this session",
                    "duplicate": True,
                    "existing_document_id": str(existing_document.id),
                    "filename": file.filename
                }

        # Upload and create document
        document = await document_service.upload_file(
            file_data=file_data,
            filename=file.filename,
            file_type=file.content_type,
            source_type="upload",
            db=db
        )

        logger.info(f"Document created: {document.id} - {document.filename}")

        # Process document asynchronously (chunk and embed)
        try:
            chunks = await document_service.process_document(document.id, db)
            logger.info(f"Document processed: {len(chunks)} chunks created")

            # Log embedding status
            if chunks:
                chunks_with_embeddings = sum(1 for c in chunks if c.embedding is not None)
                logger.info(f"Embeddings generated: {chunks_with_embeddings}/{len(chunks)} chunks have embeddings")
                if chunks_with_embeddings == 0:
                    logger.error(f"❌ No embeddings generated for document {document.id}!")
            else:
                logger.warning(f"⚠️ No chunks created for document {document.id}")
        except Exception as e:
            logger.error(f"Error during document processing: {e}", exc_info=True)
            raise

        # Associate document with session for short-term memory
        if session_id and ENHANCED_RAG_AVAILABLE:
            await rag_service.associate_document_with_session(
                session_id=session_id,
                document_id=document.id,
                priority=1,  # Higher priority for recently uploaded docs
                db=db
            )
            logger.info(f"✅ Document '{document.filename}' (ID: {document.id}) associated with session {session_id}")
            logger.info(f"📌 This document will be prioritized in queries for session {session_id}")

        # Commit the transaction explicitly
        await db.commit()
        logger.info(f"Transaction committed for document {document.id}")

        latency_ms = (time.time() - start_time) * 1000

        # Audit logging (after successful commit)
        if audit_service:
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
            await db.commit()  # Commit audit log

        return {
            "success": True,
            "document_id": str(document.id),
            "filename": document.filename,
            "session_id": session_id,
            "in_session_memory": session_id is not None and ENHANCED_RAG_AVAILABLE,
            "message": "File uploaded and processed successfully",
            "latency_ms": latency_ms,
            "chunks_created": len(chunks)
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)

        # Rollback transaction
        await db.rollback()
        logger.info("Transaction rolled back due to error")

        # Audit log the failure (in a new transaction)
        if audit_service:
            try:
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
                await db.commit()  # Commit audit log in separate transaction
            except Exception as audit_error:
                logger.error(f"Failed to log audit entry: {audit_error}")

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/query")
async def query_endpoint(
    request: Request,
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_cache: bool = Form(True),
    model_id: Optional[str] = Form(None),
    conversation_history: Optional[str] = Form(None),  # NEW: Accept conversation history as JSON string
    db: AsyncSession = Depends(get_db)
):
    """Query the RAG system with memory hierarchy and conversation context"""
    import time
    import json

    start_time = time.time()
    ip_address, user_agent = get_client_info(request)
    user_id = await get_anonymous_user_id(db)

    # Parse conversation history if provided
    parsed_history = None
    if conversation_history:
        try:
            parsed_history = json.loads(conversation_history)
            logger.info(f"📜 Received conversation history with {len(parsed_history)} messages")
        except json.JSONDecodeError:
            logger.warning("Failed to parse conversation history JSON")

    try:
        # Use enhanced RAG service with memory hierarchy if available
        if ENHANCED_RAG_AVAILABLE:
            result = await rag_service.query(
                query_text=query,
                session_id=session_id,
                user_id=user_id,
                conversation_history=parsed_history,  # FIXED: Pass parsed history
                use_cache=use_cache,
                model_id=model_id,
                db=db
            )
        else:
            # Fall back to basic RAG service
            result = await rag_service.query(
                query_text=query,
                conversation_history=parsed_history,  # FIXED: Pass parsed history
                use_cache=use_cache,
                model_id=model_id,
                db=db
            )

        latency_ms = (time.time() - start_time) * 1000

        # Audit logging
        if audit_service:
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
        logger.error(f"Error processing query: {e}", exc_info=True)

        # Audit log the failure
        if audit_service:
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
    url: str = Form(...),
    scrape_prompt: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Scrape a URL and process the content"""
    try:
        result = await scraper_service.scrape_url(
            url=url,
            scrape_prompt=scrape_prompt,
            db=db
        )

        return result

    except Exception as e:
        logger.error(f"Error scraping URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/documents")
async def get_documents(db: AsyncSession = Depends(get_db)):
    """Get all documents"""
    try:
        from sqlalchemy import select
        from app.models.database import Document

        result = await db.execute(select(Document).order_by(Document.upload_date.desc()))
        documents = result.scalars().all()

        return [
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "source_type": doc.source_type,
                "source_url": doc.source_url,
                "processed": doc.processed,
                "upload_date": doc.upload_date.isoformat()
            }
            for doc in documents
        ]

    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


# Models API router (safe fallback version)
try:
    # Try enhanced version first
    from app.api.routes import models as models_router
    app.include_router(models_router.router)
    logger.info("✓ Models API router registered (enhanced)")
except ImportError as e:
    logger.warning(f"Enhanced models API not available: {e}")
    try:
        # Fallback to safe version
        from app.api.routes import models_safe as models_router
        app.include_router(models_router.router)
        logger.info("✓ Models API router registered (fallback)")
    except Exception as e2:
        logger.warning(f"Could not register fallback models router: {e2}")
        logger.warning("Continuing without model selection API")
except Exception as e:
    logger.warning(f"Could not register models router: {e}")
    try:
        # Fallback to safe version
        from app.api.routes import models_safe as models_router
        app.include_router(models_router.router)
        logger.info("✓ Models API router registered (fallback)")
    except Exception as e2:
        logger.warning("Continuing without model selection API")


# === Admin API Endpoints ===

@app.get("/api/v1/admin/users")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    """Get all users (admin endpoint)"""
    try:
        from app.models.database_enhanced import User
        from sqlalchemy import select, func

        query = select(User).order_by(User.created_at.desc())
        result = await db.execute(query)
        users = result.scalars().all()

        return [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value if user.role else None,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/sessions")
async def get_all_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get all chat sessions (admin endpoint)"""
    try:
        from app.models.database_enhanced import ChatSession, ConversationMessage
        from sqlalchemy import select, func

        # Get sessions with message counts
        query = select(
            ChatSession,
            func.count(ConversationMessage.id).label('message_count')
        ).outerjoin(
            ConversationMessage, ChatSession.id == ConversationMessage.session_id
        ).group_by(ChatSession.id).order_by(ChatSession.last_activity.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        sessions = result.all()

        return [
            {
                "id": str(session.ChatSession.id),
                "session_id": session.ChatSession.session_id,
                "user_id": str(session.ChatSession.user_id) if session.ChatSession.user_id else None,
                "title": session.ChatSession.title,
                "created_at": session.ChatSession.created_at.isoformat(),
                "last_activity": session.ChatSession.last_activity.isoformat(),
                "is_active": session.ChatSession.is_active,
                "message_count": session.message_count
            }
            for session in sessions
        ]
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filters (admin endpoint)"""
    try:
        from app.models.database_enhanced import AuditLog, User, ChatSession
        from sqlalchemy import select, and_

        # Build query with filters
        conditions = []

        if user_id:
            conditions.append(AuditLog.user_id == uuid.UUID(user_id))

        if session_id:
            # Convert session_id string to UUID
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            if session:
                conditions.append(AuditLog.session_id == session.id)

        if action:
            conditions.append(AuditLog.action == action)

        query = select(AuditLog)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        logs = result.scalars().all()

        return [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "session_id": str(log.session_id) if log.session_id else None,
                "action": log.action.value if log.action else None,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "description": log.description,
                "ip_address": log.ip_address,
                "status_code": log.status_code,
                "error_message": log.error_message,
                "latency_ms": log.latency_ms,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/usage-metrics")
async def get_usage_metrics(
    user_id: Optional[str] = None,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Get usage metrics (admin endpoint)"""
    try:
        from app.models.database_enhanced import UsageMetrics, User
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = select(UsageMetrics).where(
            UsageMetrics.date >= start_date
        )

        if user_id:
            query = query.where(UsageMetrics.user_id == uuid.UUID(user_id))

        query = query.order_by(UsageMetrics.date.desc())

        result = await db.execute(query)
        metrics = result.scalars().all()

        return [
            {
                "id": str(metric.id),
                "user_id": str(metric.user_id) if metric.user_id else None,
                "date": metric.date.isoformat(),
                "model_id": metric.model_id,
                "total_queries": metric.total_queries,
                "total_tokens": metric.total_tokens,
                "total_cost_usd": metric.total_cost_usd,
                "avg_latency_ms": metric.avg_latency_ms,
                "documents_uploaded": metric.documents_uploaded,
                "cache_hits": metric.cache_hits,
                "cache_misses": metric.cache_misses
            }
            for metric in metrics
        ]
    except Exception as e:
        logger.error(f"Error getting usage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions/{session_id}/documents")
async def get_session_documents(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all documents associated with a session"""
    try:
        from app.models.database_enhanced import SessionDocument, ChatSession
        from app.models.database import Document, DocumentChunk

        # Get session
        session_query = select(ChatSession).where(ChatSession.session_id == session_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            # Session doesn't exist yet - return empty list
            return {"documents": []}

        # Get session documents with join
        query = (
            select(Document, SessionDocument, func.count(DocumentChunk.id).label('chunk_count'))
            .join(SessionDocument, Document.id == SessionDocument.document_id)
            .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
            .where(SessionDocument.session_id == session.id)
            .group_by(Document.id, SessionDocument.id)
            .order_by(SessionDocument.added_at.desc())
        )

        result = await db.execute(query)
        rows = result.all()

        documents = []
        for doc, session_doc, chunk_count in rows:
            # Derive processing status from Document model fields
            if doc.processing_error:
                processing_status = 'failed'
            elif doc.processed:
                processing_status = 'completed'
            elif chunk_count > 0:
                processing_status = 'completed'
            else:
                processing_status = 'processing'

            documents.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "file_size": doc.file_size,
                "processing_status": processing_status,
                "has_embeddings": chunk_count > 0,
                "chunk_count": chunk_count,
                "created_at": doc.upload_date.isoformat() if doc.upload_date else None,
                "priority": session_doc.priority
            })

        logger.info(f"Retrieved {len(documents)} documents for session {session_id}")
        return {"documents": documents}

    except Exception as e:
        logger.error(f"Error getting session documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document and all its chunks"""
    try:
        from app.models.database import Document

        # Get document
        query = select(Document).where(Document.id == uuid.UUID(document_id))
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from database (cascades to chunks and session associations)
        await db.delete(document)
        await db.commit()

        logger.info(f"Deleted document {document_id}: {document.filename}")
        return {"success": True, "message": "Document deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/sessions/{session_id}/clear")
async def clear_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Clear session: remove document associations and conversation messages"""
    try:
        from app.models.database_enhanced import SessionDocument, ChatSession, ConversationMessage
        from sqlalchemy import delete as sql_delete

        # Get session
        session_query = select(ChatSession).where(ChatSession.session_id == session_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if session:
            # Delete session document associations (short-term memory)
            await db.execute(
                sql_delete(SessionDocument).where(SessionDocument.session_id == session.id)
            )

            # Delete conversation messages
            await db.execute(
                sql_delete(ConversationMessage).where(ConversationMessage.session_id == session.id)
            )

            # Mark session as cleared
            session.status = 'cleared'
            session.ended_at = func.now()

            await db.commit()
            logger.info(f"Cleared session {session_id}")

        return {"success": True, "message": "Session cleared"}

    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/documents")
async def get_admin_documents(
    search: Optional[str] = None,
    embedded_only: bool = False,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all documents with user, session, and embedding info (admin endpoint)"""
    try:
        from app.models.database import Document, DocumentChunk
        from app.models.database_enhanced import SessionDocument, ChatSession, User

        # Base query with counts
        query = (
            select(
                Document,
                func.count(DocumentChunk.id).label('chunk_count'),
                User.email.label('user_email'),
                User.username.label('username'),
                ChatSession.session_id
            )
            .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
            .outerjoin(SessionDocument, Document.id == SessionDocument.document_id)
            .outerjoin(ChatSession, SessionDocument.session_id == ChatSession.id)
            .outerjoin(User, ChatSession.user_id == User.id)
            .group_by(Document.id, User.email, User.username, ChatSession.session_id)
        )

        # Apply filters
        if search:
            query = query.where(Document.filename.ilike(f'%{search}%'))

        if embedded_only:
            query = query.having(func.count(DocumentChunk.id) > 0)

        query = query.order_by(Document.upload_date.desc()).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        documents = []
        for doc, chunk_count, user_email, username, session_id in rows:
            # Derive processing status from Document model fields
            if doc.processing_error:
                processing_status = 'failed'
            elif doc.processed:
                processing_status = 'completed'
            elif chunk_count > 0:
                processing_status = 'completed'
            else:
                processing_status = 'processing'

            documents.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "file_size": doc.file_size,
                "processing_status": processing_status,
                "chunk_count": chunk_count,
                "user_email": user_email or "anonymous",
                "username": username or "anonymous",
                "session_id": session_id,
                "created_at": doc.upload_date.isoformat() if doc.upload_date else None
            })

        logger.info(f"Retrieved {len(documents)} documents for admin")
        return {"documents": documents}

    except Exception as e:
        logger.error(f"Error getting admin documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admin/users")
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form('user'),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin endpoint)"""
    try:
        from app.models.database_enhanced import User
        import hashlib

        # Check if user already exists
        existing_query = select(User).where(
            (User.username == username) | (User.email == email)
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username or email already exists")

        # Hash password (use proper bcrypt in production!)
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"Created new user: {username} ({email}) with role {role}")
        return {
            "success": True,
            "user_id": str(new_user.id),
            "username": username,
            "email": email,
            "role": role
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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
            "user_id": str(session.user_id) if session.user_id else None,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": len(messages),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "model_name": msg.model_name,
                    "total_tokens": msg.total_tokens,
                    "latency_ms": msg.latency_ms,
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


# OpenTelemetry instrumentation (if enabled)
if settings.ENABLE_TRACING:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        # Set up tracing
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)

        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        logger.info("OpenTelemetry tracing enabled")
    except Exception as e:
        logger.warning(f"Could not enable OpenTelemetry: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
