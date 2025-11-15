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

    # Create default admin user if it doesn't exist
    try:
        logger.info("Checking for default admin user...")
        from app.models.database_enhanced import User, UserRole
        from app.core.database import AsyncSessionLocal
        import hashlib

        async with AsyncSessionLocal() as session:
            query = select(User).where(User.username == 'admin')
            result = await session.execute(query)
            existing_admin = result.scalar_one_or_none()

            if not existing_admin:
                # Create default admin user
                default_password = 'admin123'
                hashed_password = hashlib.sha256(default_password.encode()).hexdigest()

                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    full_name='System Administrator',
                    hashed_password=hashed_password,
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True
                )

                session.add(admin_user)
                await session.commit()
                logger.info("✓ Default admin user created (username: admin, password: admin123)")
                logger.warning("⚠️  IMPORTANT: Change the default admin password!")
            else:
                logger.info("✓ Admin user already exists")
    except Exception as e:
        logger.warning(f"Could not create default admin user: {e}")

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
    # RAG configuration parameters
    top_k: Optional[int] = Form(None),
    similarity_threshold: Optional[float] = Form(None),
    min_similarity_threshold: Optional[float] = Form(None),
    no_relevant_docs_threshold: Optional[float] = Form(None),
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
                db=db,
                # Pass RAG configuration parameters
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                min_similarity_threshold=min_similarity_threshold,
                no_relevant_docs_threshold=no_relevant_docs_threshold
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


# Robust RAG Pipeline API router
try:
    from app.api.routes import rag_pipeline_routes
    app.include_router(rag_pipeline_routes.router)
    logger.info("✓ Robust RAG Pipeline API router registered")
except ImportError as e:
    logger.warning(f"Robust RAG Pipeline API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register RAG Pipeline router: {e}")


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


@app.post("/api/v1/admin/users")
async def create_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin endpoint)"""
    try:
        from app.models.database_enhanced import User, UserRole
        from sqlalchemy import select
        import hashlib

        # Get JSON body
        body = await request.json()
        username = body.get('username')
        email = body.get('email')
        password = body.get('password')
        full_name = body.get('full_name')
        role = body.get('role', 'user')

        # Validate required fields
        if not username or not email or not password:
            raise HTTPException(status_code=400, detail="Username, email, and password are required")

        # Check if user already exists
        query = select(User).where((User.username == username) | (User.email == email))
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")

        # Hash password (simple hash for demo - use bcrypt in production)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Create user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=UserRole[role.upper()] if hasattr(UserRole, role.upper()) else UserRole.USER,
            is_active=True,
            is_verified=True
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"✓ Created user: {username} ({role})")

        return {
            "id": str(new_user.id),
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role.value if new_user.role else None,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
            "last_login": new_user.last_login.isoformat() if new_user.last_login else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await db.rollback()
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


@app.get("/api/v1/debug/session/{session_id}")
async def debug_session_query(
    session_id: str,
    test_query: str = "test query",
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to diagnose session document retrieval issues"""
    try:
        from app.models.database_enhanced import SessionDocument, ChatSession
        from app.models.database import Document, DocumentChunk
        from sqlalchemy import text as sql_text

        debug_info = {"session_id": session_id}

        # 1. Check if session exists
        session_query = select(ChatSession).where(ChatSession.session_id == session_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            debug_info["session_exists"] = False
            debug_info["error"] = "Session not found"
            return debug_info

        debug_info["session_exists"] = True
        debug_info["session_uuid"] = str(session.id)

        # 2. Check session documents count
        count_query = select(func.count()).select_from(SessionDocument).where(
            SessionDocument.session_id == session.id
        )
        count_result = await db.execute(count_query)
        session_doc_count = count_result.scalar()
        debug_info["session_documents_count"] = session_doc_count

        if session_doc_count == 0:
            debug_info["error"] = "No documents associated with session"
            return debug_info

        # 3. Get session documents details
        doc_query = select(SessionDocument, Document).join(
            Document, SessionDocument.document_id == Document.id
        ).where(SessionDocument.session_id == session.id)
        doc_result = await db.execute(doc_query)
        doc_rows = doc_result.all()

        documents = []
        for sd, doc in doc_rows:
            # Count chunks for this document
            chunk_count_query = select(func.count()).select_from(DocumentChunk).where(
                DocumentChunk.document_id == doc.id
            )
            chunk_count_result = await db.execute(chunk_count_query)
            chunk_count = chunk_count_result.scalar()

            # Count chunks with embeddings
            embed_count_query = select(func.count()).select_from(DocumentChunk).where(
                and_(
                    DocumentChunk.document_id == doc.id,
                    DocumentChunk.embedding.isnot(None)
                )
            )
            embed_count_result = await db.execute(embed_count_query)
            embed_count = embed_count_result.scalar()

            documents.append({
                "document_id": str(doc.id),
                "filename": doc.filename,
                "priority": sd.priority,
                "processed": doc.processed,
                "chunk_count": chunk_count,
                "chunks_with_embeddings": embed_count
            })

        debug_info["documents"] = documents

        # 4. Generate test embedding and run vector search query
        query_embedding = await embedding_service.get_embedding(test_query)
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        threshold = 0.5  # Lower threshold for debugging

        search_query = sql_text(f"""
            SELECT
                dc.id,
                dc.document_id,
                dc.content,
                d.filename,
                sd.priority,
                1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            JOIN session_documents sd ON d.id = sd.document_id
            WHERE sd.session_id = :session_id
                AND dc.embedding IS NOT NULL
                AND 1 - (dc.embedding <=> '{embedding_str}'::vector) > :threshold
            ORDER BY sd.priority DESC, similarity DESC
            LIMIT 10
        """)

        search_result = await db.execute(
            search_query,
            {"session_id": session.id, "threshold": threshold}
        )
        search_rows = search_result.fetchall()

        debug_info["test_query"] = test_query
        debug_info["threshold"] = threshold
        debug_info["chunks_found"] = len(search_rows)

        if search_rows:
            debug_info["sample_results"] = [
                {
                    "filename": row.filename,
                    "priority": row.priority,
                    "similarity": float(row.similarity),
                    "content_preview": row.content[:100] + "..."
                }
                for row in search_rows[:3]
            ]
        else:
            debug_info["warning"] = "No chunks found despite having documents with embeddings"

        return debug_info

    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}", exc_info=True)
        return {
            "error": str(e),
            "traceback": str(e.__traceback__)
        }


@app.post("/api/v1/admin/regenerate-embeddings")
async def regenerate_embeddings_endpoint(
    document_id: Optional[str] = None,
    batch_size: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to regenerate embeddings for documents missing them

    Args:
        document_id: Optional specific document ID to process
        batch_size: Number of chunks to process per batch
    """
    try:
        from app.models.database import Document, DocumentChunk
        from app.services.embedding_service import embedding_service
        import uuid as uuid_module

        logger.info("Starting embedding regeneration via API")

        # Parse document ID if provided
        doc_uuid = None
        if document_id:
            try:
                doc_uuid = uuid_module.UUID(document_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid document ID: {document_id}")

        # Count chunks without embeddings
        count_query = sql_text("""
            SELECT COUNT(*) FROM document_chunks WHERE embedding IS NULL
        """)
        if doc_uuid:
            count_query = sql_text(f"""
                SELECT COUNT(*) FROM document_chunks
                WHERE embedding IS NULL AND document_id = '{doc_uuid}'
            """)

        count_result = await db.execute(count_query)
        missing_count = count_result.scalar()

        if missing_count == 0:
            return {
                "status": "already_complete",
                "message": "All chunks already have embeddings",
                "chunks_processed": 0
            }

        # Get documents with missing embeddings
        if doc_uuid:
            docs_query = select(Document).where(Document.id == doc_uuid)
        else:
            docs_query = select(Document).where(
                Document.id.in_(
                    select(DocumentChunk.document_id)
                    .where(DocumentChunk.embedding == None)
                    .distinct()
                )
            )

        docs_result = await db.execute(docs_query)
        documents = docs_result.scalars().all()

        logger.info(f"Found {len(documents)} documents to process ({missing_count} chunks)")

        # Process each document
        total_processed = 0
        errors = []

        for doc in documents:
            try:
                # Get chunks without embeddings for this document
                chunks_query = select(DocumentChunk).where(
                    DocumentChunk.document_id == doc.id,
                    DocumentChunk.embedding == None
                )
                chunks_result = await db.execute(chunks_query)
                chunks = chunks_result.scalars().all()

                if not chunks:
                    continue

                logger.info(f"Processing {doc.filename}: {len(chunks)} chunks")

                # Process in batches
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    chunk_texts = [chunk.content for chunk in batch]

                    # Generate embeddings
                    embeddings = await embedding_service.get_embeddings_batch(chunk_texts)

                    if not embeddings or len(embeddings) != len(batch):
                        error_msg = f"Embedding generation failed for {doc.filename}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue

                    # Update chunks
                    for chunk, embedding in zip(batch, embeddings):
                        chunk.embedding = embedding

                    await db.flush()
                    total_processed += len(batch)

                logger.info(f"✅ Completed {doc.filename}")

            except Exception as e:
                error_msg = f"Error processing {doc.filename}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                await db.rollback()
                # Create new session for next document
                continue

        # Final commit
        await db.commit()

        return {
            "status": "completed" if not errors else "partial",
            "documents_processed": len(documents),
            "chunks_processed": total_processed,
            "chunks_remaining": missing_count - total_processed,
            "errors": errors if errors else None
        }

    except Exception as e:
        logger.error(f"Error in embedding regeneration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/db-console/documents")
async def db_console_documents(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Database console: Get all documents with detailed chunk and embedding information"""
    try:
        from app.models.database import Document, DocumentChunk
        from app.models.database_enhanced import SessionDocument, ChatSession
        from sqlalchemy import text as sql_text

        # Build complex query with all the details we need
        # If no search term provided, use '%%' to match everything
        search_pattern = f"%{search}%" if search else "%%"

        query = sql_text("""
            SELECT
                d.id,
                d.filename,
                d.file_type,
                d.file_size,
                d.source_type,
                d.source_url,
                d.upload_date,
                d.processed,
                d.processing_error,
                COUNT(DISTINCT dc.id) as total_chunks,
                COUNT(DISTINCT CASE WHEN dc.embedding IS NOT NULL THEN dc.id END) as chunks_with_embeddings,
                COUNT(DISTINCT sd.session_id) as session_count,
                STRING_AGG(DISTINCT cs.session_id, ', ') as session_ids
            FROM documents d
            LEFT JOIN document_chunks dc ON d.id = dc.document_id
            LEFT JOIN session_documents sd ON d.id = sd.document_id
            LEFT JOIN chat_sessions cs ON sd.session_id = cs.id
            WHERE d.filename ILIKE :search_pattern
            GROUP BY d.id, d.filename, d.file_type, d.file_size, d.source_type, d.source_url, d.upload_date, d.processed, d.processing_error
            ORDER BY d.upload_date DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await db.execute(
            query,
            {
                "search_pattern": search_pattern,
                "limit": limit,
                "offset": offset
            }
        )
        rows = result.fetchall()

        documents = []
        for row in rows:
            embedding_percentage = 0
            if row.total_chunks > 0:
                embedding_percentage = (row.chunks_with_embeddings / row.total_chunks) * 100

            documents.append({
                "id": str(row.id),
                "filename": row.filename,
                "file_type": row.file_type,
                "file_size": row.file_size,
                "source_type": row.source_type,
                "source_url": row.source_url,
                "upload_date": row.upload_date.isoformat() if row.upload_date else None,
                "processed": row.processed,
                "processing_error": row.processing_error,
                "total_chunks": row.total_chunks,
                "chunks_with_embeddings": row.chunks_with_embeddings,
                "embedding_percentage": round(embedding_percentage, 2),
                "session_count": row.session_count,
                "session_ids": row.session_ids.split(", ") if row.session_ids else []
            })

        # Get total count
        count_query = sql_text("""
            SELECT COUNT(DISTINCT d.id)
            FROM documents d
            WHERE d.filename ILIKE :search_pattern
        """)
        count_result = await db.execute(
            count_query,
            {"search_pattern": search_pattern}
        )
        total = count_result.scalar()

        return {
            "documents": documents,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error in DB console documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/db-console/document/{document_id}/chunks")
async def db_console_document_chunks(
    document_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Database console: Get all chunks for a specific document with embedding details"""
    try:
        from app.models.database import Document, DocumentChunk
        from sqlalchemy import text as sql_text

        # Verify document exists
        doc_query = select(Document).where(Document.id == uuid.UUID(document_id))
        doc_result = await db.execute(doc_query)
        document = doc_result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get chunks with embedding information
        chunks_query = sql_text("""
            SELECT
                id,
                chunk_index,
                content,
                embedding IS NOT NULL as has_embedding,
                CASE WHEN embedding IS NOT NULL
                     THEN 384
                     ELSE NULL
                END as embedding_dimensions,
                meta_info,
                created_at
            FROM document_chunks
            WHERE document_id = :document_id
            ORDER BY chunk_index
            LIMIT :limit OFFSET :offset
        """)

        result = await db.execute(
            chunks_query,
            {"document_id": uuid.UUID(document_id), "limit": limit, "offset": offset}
        )
        rows = result.fetchall()

        chunks = []
        for row in rows:
            chunks.append({
                "id": str(row.id),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "content_length": len(row.content),
                "has_embedding": row.has_embedding,
                "embedding_dimensions": row.embedding_dimensions,
                "meta_info": row.meta_info,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })

        # Get total chunk count
        count_query = sql_text("""
            SELECT COUNT(*) FROM document_chunks WHERE document_id = :document_id
        """)
        count_result = await db.execute(count_query, {"document_id": uuid.UUID(document_id)})
        total = count_result.scalar()

        return {
            "document": {
                "id": str(document.id),
                "filename": document.filename,
                "file_type": document.file_type,
                "upload_date": document.upload_date.isoformat() if document.upload_date else None
            },
            "chunks": chunks,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/db-console/stats")
async def db_console_stats(db: AsyncSession = Depends(get_db)):
    """Database console: Get database statistics"""
    try:
        from sqlalchemy import text as sql_text

        stats_query = sql_text("""
            SELECT
                (SELECT COUNT(*) FROM documents) as total_documents,
                (SELECT COUNT(*) FROM documents WHERE processed = true) as processed_documents,
                (SELECT COUNT(*) FROM documents WHERE processing_error IS NOT NULL) as failed_documents,
                (SELECT COUNT(*) FROM document_chunks) as total_chunks,
                (SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL) as chunks_with_embeddings,
                (SELECT COUNT(DISTINCT session_id) FROM session_documents) as total_sessions,
                (SELECT COUNT(DISTINCT session_id) FROM chat_sessions WHERE is_active = true) as active_sessions,
                (SELECT SUM(file_size) FROM documents) as total_storage_bytes,
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM audit_logs) as total_audit_logs
        """)

        result = await db.execute(stats_query)
        row = result.fetchone()

        embedding_coverage = 0
        if row.total_chunks > 0:
            embedding_coverage = (row.chunks_with_embeddings / row.total_chunks) * 100

        return {
            "documents": {
                "total": row.total_documents,
                "processed": row.processed_documents,
                "failed": row.failed_documents
            },
            "chunks": {
                "total": row.total_chunks,
                "with_embeddings": row.chunks_with_embeddings,
                "coverage_percentage": round(embedding_coverage, 2)
            },
            "sessions": {
                "total": row.total_sessions,
                "active": row.active_sessions
            },
            "storage": {
                "total_bytes": row.total_storage_bytes or 0,
                "total_mb": round((row.total_storage_bytes or 0) / (1024 * 1024), 2),
                "total_gb": round((row.total_storage_bytes or 0) / (1024 * 1024 * 1024), 2)
            },
            "users": {
                "total": row.total_users
            },
            "audit": {
                "total_logs": row.total_audit_logs
            }
        }

    except Exception as e:
        logger.error(f"Error getting DB stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/debug/embeddings")
async def debug_embeddings(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive diagnostic endpoint to check embedding status
    Returns detailed information about documents, chunks, and embeddings
    """
    try:
        from app.models.database import Document, DocumentChunk
        from sqlalchemy import text as sql_text, func, select

        diagnostic_info = {}

        # 1. Count total documents
        doc_count_query = select(func.count()).select_from(Document)
        doc_count_result = await db.execute(doc_count_query)
        total_documents = doc_count_result.scalar()
        diagnostic_info['total_documents'] = total_documents

        # 2. Count total chunks
        chunk_count_query = select(func.count()).select_from(DocumentChunk)
        chunk_count_result = await db.execute(chunk_count_query)
        total_chunks = chunk_count_result.scalar()
        diagnostic_info['total_chunks'] = total_chunks

        # 3. Count chunks with embeddings
        embedding_query = sql_text("""
            SELECT
                COUNT(*) as total_chunks,
                COUNT(embedding) as chunks_with_embeddings,
                COUNT(*) FILTER (WHERE embedding IS NULL) as chunks_without_embeddings
            FROM document_chunks
        """)
        embedding_result = await db.execute(embedding_query)
        embedding_row = embedding_result.fetchone()

        diagnostic_info['chunks_with_embeddings'] = embedding_row[1]
        diagnostic_info['chunks_without_embeddings'] = embedding_row[2]
        diagnostic_info['embedding_coverage_percentage'] = (
            (embedding_row[1] / embedding_row[0] * 100) if embedding_row[0] > 0 else 0
        )

        # 4. Check embedding dimensions
        # All embeddings are 384-dimensional (from sentence-transformers model)
        if embedding_row[1] > 0:
            diagnostic_info['embedding_dimensions'] = 384
        else:
            diagnostic_info['embedding_dimensions'] = None

        # 5. Check for processing errors
        error_query = select(Document).where(Document.processing_error != None)
        error_result = await db.execute(error_query)
        error_docs = error_result.scalars().all()
        diagnostic_info['documents_with_errors'] = len(error_docs)
        diagnostic_info['error_details'] = [
            {
                'filename': doc.filename,
                'error': doc.processing_error[:200]  # Truncate long errors
            }
            for doc in error_docs[:5]  # Limit to 5 examples
        ]

        # 6. Check pgvector extension
        extension_query = sql_text("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'vector'
        """)
        extension_result = await db.execute(extension_query)
        extension_row = extension_result.fetchone()
        diagnostic_info['pgvector_installed'] = extension_row is not None
        if extension_row:
            diagnostic_info['pgvector_version'] = extension_row[1]

        # 7. Check vector indexes
        index_query = sql_text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'document_chunks'
            AND indexdef LIKE '%embedding%'
        """)
        index_result = await db.execute(index_query)
        indexes = index_result.fetchall()
        diagnostic_info['vector_indexes'] = [
            {'name': row[0], 'definition': row[1][:100]}
            for row in indexes
        ]

        # 8. Sample document chunk details
        if total_chunks > 0:
            sample_query = sql_text("""
                SELECT
                    dc.id,
                    d.filename,
                    dc.chunk_index,
                    LENGTH(dc.content) as content_length,
                    dc.embedding IS NOT NULL as has_embedding,
                    CASE WHEN dc.embedding IS NOT NULL
                         THEN 384
                         ELSE NULL
                    END as embedding_dimensions
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                ORDER BY d.upload_date DESC, dc.chunk_index
                LIMIT 5
            """)
            sample_result = await db.execute(sample_query)
            samples = sample_result.fetchall()
            diagnostic_info['sample_chunks'] = [
                {
                    'filename': row[1],
                    'chunk_index': row[2],
                    'content_length': row[3],
                    'has_embedding': row[4],
                    'embedding_dimensions': row[5]
                }
                for row in samples
            ]
        else:
            diagnostic_info['sample_chunks'] = []

        # 9. Test vector search (if embeddings exist)
        if embedding_row[1] > 0:
            # Generate a test embedding (all zeros for testing)
            test_embedding = [0.0] * 384
            embedding_str = f"[{','.join(map(str, test_embedding))}]"

            # Try a very low threshold to see if ANY results come back
            test_query = sql_text(f"""
                SELECT COUNT(*) as count
                FROM document_chunks
                WHERE embedding IS NOT NULL
                AND 1 - (embedding <=> '{embedding_str}'::vector) > 0.0
            """)
            test_result = await db.execute(test_query)
            test_row = test_result.fetchone()
            diagnostic_info['test_vector_search_results'] = test_row[0]
        else:
            diagnostic_info['test_vector_search_results'] = 0

        # 10. Current configuration
        diagnostic_info['config'] = {
            'similarity_threshold': settings.SIMILARITY_THRESHOLD,
            'top_k_results': settings.TOP_K_RESULTS,
            'chunk_size': settings.CHUNK_SIZE,
            'chunk_overlap': settings.CHUNK_OVERLAP
        }

        # 11. Diagnosis and recommendations
        issues = []
        recommendations = []

        if total_documents == 0:
            issues.append("No documents uploaded")
            recommendations.append("Upload documents using the /api/v1/upload endpoint")
        elif total_chunks == 0:
            issues.append("Documents exist but not processed into chunks")
            recommendations.append("Check document processing pipeline and logs")
        elif embedding_row[2] > 0:  # Some chunks without embeddings
            issues.append(f"{embedding_row[2]} chunks missing embeddings")
            recommendations.append("Run embedding regeneration script or re-upload documents")

        if embedding_row[1] == 0 and total_chunks > 0:
            issues.append("No embeddings found - RAG queries will fail")
            recommendations.append("Check embedding service and regenerate embeddings")

        if not extension_row:
            issues.append("pgvector extension not installed")
            recommendations.append("Install pgvector: CREATE EXTENSION vector;")

        if not indexes:
            issues.append("No vector indexes found - searches will be slow")
            recommendations.append("Create vector index on document_chunks.embedding")

        diagnostic_info['issues'] = issues
        diagnostic_info['recommendations'] = recommendations
        diagnostic_info['status'] = 'healthy' if not issues else 'degraded'

        return diagnostic_info

    except Exception as e:
        logger.error(f"Error in embeddings diagnostic: {e}", exc_info=True)
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
