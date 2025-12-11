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
import re  # 🆕 For URL detection
import json  # Already imported below but moving here for clarity

from app.core.config import settings
from app.core.database import init_db, close_db, get_db
from app.api.graphql.schema import schema
from app.services.embedding_service import embedding_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# Import consolidated LLM service with multi-model support
from app.services.llm_service import llm_service
logger_temp = logging.getLogger(__name__)
logger_temp.info("✓ Using LLM Service with multi-model support and Claude integration")

from app.services.document_service import document_service
from app.services.scraper_service import scraper_service

# Import consolidated RAG service with memory hierarchy
from app.services.rag_service import rag_service
logger_temp.info("✓ Using RAG Service with memory hierarchy")
ENHANCED_RAG_AVAILABLE = True  # Always true now (consolidated)

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Override any existing configuration (e.g., from Uvicorn)
)
# Ensure root logger is set to INFO
logging.getLogger().setLevel(logging.INFO)
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

    # Initialize MCP integration (optional - graceful fallback if not available)
    try:
        logger.info("Initializing MCP integration...")
        from app.agents.tool_registry import get_tool_registry
        from app.mcp.server import get_mcp_server
        from app.mcp.client import initialize_mcp_client
        from app.mcp.server_registry import get_mcp_server_registry
        from app.api.routes.mcp_routes import initialize_mcp_instances

        # Initialize components
        tool_registry = get_tool_registry()
        mcp_server = await get_mcp_server(tool_registry)
        mcp_client = await initialize_mcp_client(tool_registry)
        mcp_registry = get_mcp_server_registry(mcp_client)

        # Initialize route dependencies
        initialize_mcp_instances(mcp_server, mcp_client, mcp_registry)

        logger.info("✓ MCP integration initialized successfully")
    except ImportError as e:
        logger.warning(f"⚠ MCP integration not available: {e}")
        logger.warning("⚠ Install MCP SDK: pip install mcp")
    except Exception as e:
        logger.warning(f"⚠ MCP initialization failed (non-critical): {e}")

    # Create default admin user if it doesn't exist
    try:
        logger.info("Checking for default admin user...")
        from app.models.database_enhanced import User, UserRole
        from app.core.database import AsyncSessionLocal
        from app.core.security import get_password_hash  # 🔧 FIX: Use bcrypt hashing

        async with AsyncSessionLocal() as session:
            query = select(User).where(User.username == 'admin')
            result = await session.execute(query)
            existing_admin = result.scalar_one_or_none()

            if not existing_admin:
                # Create default admin user
                default_password = 'admin123'
                # 🔧 FIX: Changed from hashlib.sha256 to bcrypt
                hashed_password = get_password_hash(default_password)

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

# Comprehensive Audit Logging Middleware
# Integrates with OpenTelemetry (Tempo) and Prometheus (Grafana)
try:
    from app.middleware import setup_audit_middleware
    setup_audit_middleware(app)
    logger.info("✓ Comprehensive audit middleware enabled (OTEL + Prometheus)")
except Exception as e:
    logger.warning(f"Could not enable audit middleware: {e}")


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint for audit logging and system metrics.
    Exports metrics collected by the audit middleware.
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import Response

        metrics_output = generate_latest()
        return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return JSONResponse(
            status_code=503,
            content={"error": "Prometheus client not available"}
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


# Direct LLM test endpoint (bypasses RAG pipeline)
@app.post("/api/v1/llm/test")
async def test_llm_direct(
    prompt: str = Form(...),
    model_id: Optional[str] = Form("qwen2.5:1.5b")
):
    """
    Direct LLM test endpoint - bypasses RAG pipeline for debugging.
    Useful for testing Ollama integration without document retrieval.
    """
    print(f"========== ENDPOINT CALLED: prompt={prompt}, model={model_id} ==========", flush=True)
    try:
        print(f"About to call llm_service.generate()", flush=True)
        logger.info(f"🧪 Direct LLM test: prompt='{prompt[:50]}...', model={model_id}")

        # Ensure llm_service is initialized (lazy init)
        if hasattr(llm_service, '_initialized') and not llm_service._initialized:
            print("LLM service not initialized, initializing now...", flush=True)
            logger.info("Initializing llm_service for direct test...")
            await llm_service.initialize()

        print(f"Calling llm_service.generate with model_id={model_id}", flush=True)
        # Call LLM directly
        response = await llm_service.generate(
            prompt=prompt,
            model_id=model_id,
            max_tokens=200,
            temperature=0.7
        )

        print(f"Got response: {response.get('content', '')[:50]}...", flush=True)
        return {
            "success": True,
            "answer": response['content'],
            "model": response['model'],
            "model_name": response.get('model_name', response['model']),
            "tokens": response.get('tokens', 0),
            "provider": response.get('provider', 'unknown')
        }
    except Exception as e:
        print(f"========== EXCEPTION: {type(e).__name__}: {e} ==========", flush=True)
        import traceback
        traceback.print_exc()
        logger.error(f"❌ Direct LLM test failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# REST API endpoints
@app.post("/api/v1/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),  # Link upload to project
    db: AsyncSession = Depends(get_db)
):
    """Upload a file for processing and associate with session"""
    import time
    import uuid
    from app.core.security import get_current_user_from_request
    from app.services.document_service import construct_minio_path

    start_time = time.time()
    ip_address, user_agent = get_client_info(request)

    # DEBUG: Log all form parameters received
    logger.info(f"🔍 DEBUG - session_id received: {repr(session_id)}")
    logger.info(f"🔍 DEBUG - project_id received: {repr(project_id)}")

    # Try to get authenticated user first, fallback to anonymous
    auth_header = request.headers.get("Authorization")
    logger.info(f"🔑 Authorization header present: {bool(auth_header)}")
    if auth_header:
        logger.info(f"🔑 Authorization header value: {auth_header[:20]}...")  # Log first 20 chars only

    current_user = await get_current_user_from_request(request, db)
    if current_user:
        user_id = current_user.id
        username = current_user.username
        logger.info(f"👤 Authenticated upload by user: {username}")
    else:
        user_id = await get_anonymous_user_id(db)
        username = "anonymous"
        logger.info(f"👤 Anonymous upload (no authentication)")

    # Fetch user's organizational details if authenticated
    department_name = None
    team_name = None
    # DON'T reset project_id - it may have been passed from the form!
    # project_id is already set from Form parameter
    project_name = "Global"  # Default fallback

    if current_user:
        from app.models.rbac import Department, Team
        from app.models.database_enhanced import UserTeam

        # Get department
        if current_user.department_id:
            dept_query = select(Department).where(Department.id == current_user.department_id)
            dept_result = await db.execute(dept_query)
            dept = dept_result.scalar_one_or_none()
            if dept:
                department_name = dept.name
                logger.info(f"📁 Department: {department_name}")

        # Get primary team
        teams_query = select(UserTeam, Team).join(
            Team, UserTeam.team_id == Team.id
        ).where(
            UserTeam.user_id == current_user.id,
            UserTeam.is_primary == True
        ).limit(1)
        teams_result = await db.execute(teams_query)
        user_team_data = teams_result.first()
        if user_team_data:
            team_name = user_team_data[1].name  # Team.name
            logger.info(f"👥 Team: {team_name}")

        # Get user's default project (if not overridden by form)
        if not project_id and current_user.default_project_id:
            project_id = current_user.default_project_id

    # CRITICAL FIX: If project_id was provided (from form or user default), fetch its name
    if project_id:
        from app.models.database_enhanced import Project
        try:
            # Convert string to UUID if needed
            project_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

            # Fetch project name from database
            project_query = select(Project).where(Project.id == project_uuid)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()

            if project:
                project_name = project.name
                logger.info(f"📂 Project (from {'form' if isinstance(project_id, str) else 'user default'}): {project_name}")
            else:
                logger.warning(f"Project ID {project_id} not found in database, using default: Global")
                project_name = "Global"
        except (ValueError, Exception) as e:
            logger.warning(f"Invalid project_id {project_id}: {e}, using default: Global")
            project_name = "Global"

    # Construct MinIO path with NEW format: dept/team/project/user/folder/file
    minio_path = construct_minio_path(
        department=department_name,
        team=team_name,
        username=username,
        project=project_name,  # ← Now uses actual project name!
        filename=file.filename,
        folder="documents"  # Default folder type
    )
    logger.info(f"📍 MinIO path: {minio_path}")

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
                    user_id=user_id,
                    project_id=uuid.UUID(project_id) if project_id else None
                )
                db.add(session)
                await db.flush()  # Get the session ID
                logger.info(f"Created new chat session: {session_id}" + (f" in project {project_id}" if project_id else ""))

            # Check if a document with same filename and file size already exists in this session
            duplicate_query = select(Document).join(
                SessionDocument, Document.id == SessionDocument.document_id
            ).where(
                and_(
                    SessionDocument.session_id == session.session_id,
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
        # Convert project_id to UUID if provided (handle both string and UUID types)
        logger.info(f"📁 Received project_id from form: {repr(project_id)}")
        if project_id:
            # Handle both string and UUID types
            if isinstance(project_id, uuid.UUID):
                project_uuid = project_id
            elif isinstance(project_id, str):
                project_uuid = uuid.UUID(project_id)
            else:
                project_uuid = None
        else:
            project_uuid = None
        logger.info(f"📁 Converted to project_uuid: {project_uuid}")

        document = await document_service.upload_file(
            file_data=file_data,
            filename=file.filename,
            file_type=file.content_type,
            source_type="upload",
            db=db,
            user_id=user_id,
            department=department_name,
            team=team_name,
            project_id=project_uuid,
            minio_path=minio_path,
            user_role=current_user.role if current_user else None
        )

        logger.info(f"Document created: {document.id} - {document.filename}")
        # NOTE: Files are stored in MinIO and agent runtime fetches them as needed

        # Process document asynchronously (chunk and embed)
        try:
            chunks = await document_service.process_document(
                document.id,
                db,
                user_id=user_id,
                department=department_name,
                team=team_name,
                project_id=project_uuid
            )
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
    project_id: Optional[str] = Form(None),  # Link query to project
    use_cache: bool = Form(True),
    model_id: Optional[str] = Form(None),
    conversation_history: Optional[str] = Form(None),  # NEW: Accept conversation history as JSON string
    # 🆕 Unified configuration - ALL 48 parameters for dynamic per-query control
    unified_config: Optional[str] = Form(None),  # JSON string with complete configuration
    # RAG configuration parameters (fallback if unified_config not provided)
    top_k: Optional[int] = Form(None),
    similarity_threshold: Optional[float] = Form(None),
    min_similarity_threshold: Optional[float] = Form(None),
    no_relevant_docs_threshold: Optional[float] = Form(None),
    semantic_weight: Optional[float] = Form(None),  # Hybrid search semantic weight
    keyword_weight: Optional[float] = Form(None),   # Hybrid search keyword weight
    # Metrics and evaluation control
    enable_evaluation: bool = Form(False),  # Control whether to run RAG evaluation metrics
    # 🆕 Tool & Agent Selection
    enabled_tools: Optional[str] = Form(None),  # JSON array of enabled tool IDs
    selected_agent: Optional[str] = Form('auto'),  # Selected agent: 'auto', 'rag_agent', 'enhanced_rag_agent', etc.
    db: AsyncSession = Depends(get_db)
):
    """Query the RAG system with memory hierarchy and conversation context"""
    import time
    import json

    start_time = time.time()
    ip_address, user_agent = get_client_info(request)
    user_id = await get_anonymous_user_id(db)

    # 🔍 DEBUG: Log project_id received from frontend
    logger.info(f"🔍 DEBUG [API /query endpoint]: project_id from Form = {project_id}")

    # 🧠 DEBUG: Log unified_config received from frontend
    logger.info(f"🧠 DEBUG [API /query endpoint]: unified_config received = {unified_config is not None}")
    if unified_config:
        logger.info(f"🧠 DEBUG [API /query endpoint]: unified_config value (first 200 chars) = {unified_config[:200]}")

    # Parse conversation history if provided
    parsed_history = None
    if conversation_history:
        try:
            parsed_history = json.loads(conversation_history)
            logger.info(f"📜 Received conversation history with {len(parsed_history)} messages")
        except json.JSONDecodeError:
            logger.warning("Failed to parse conversation history JSON")

    try:
        # 🔄 Smart Query Waiting: Wait for documents to finish processing
        if session_id:
            from sqlalchemy import select
            from app.models.database import SessionDocument, Document
            import asyncio

            max_wait_seconds = 30
            poll_interval_seconds = 2
            elapsed_seconds = 0

            logger.info(f"⏳ Checking if session documents are ready for query...")

            while elapsed_seconds < max_wait_seconds:
                # Check if any session documents are still processing
                processing_docs_query = select(Document).join(
                    SessionDocument,
                    Document.id == SessionDocument.document_id
                ).where(
                    SessionDocument.session_id == session_id,
                    Document.processing_status == 'processing'
                )

                result = await db.execute(processing_docs_query)
                processing_docs = result.scalars().all()

                if not processing_docs:
                    logger.info(f"✅ All session documents are ready!")
                    break

                # Documents still processing
                doc_names = [doc.filename for doc in processing_docs]
                logger.info(f"⏳ Waiting for {len(processing_docs)} document(s) to finish processing: {doc_names[:3]}...")
                logger.info(f"   Elapsed: {elapsed_seconds}s / {max_wait_seconds}s")

                await asyncio.sleep(poll_interval_seconds)
                elapsed_seconds += poll_interval_seconds

            # Final check after timeout
            if elapsed_seconds >= max_wait_seconds:
                result = await db.execute(processing_docs_query)
                still_processing = result.scalars().all()

                if still_processing:
                    doc_names = [doc.filename for doc in still_processing]
                    logger.warning(f"⚠️ Query timeout: {len(still_processing)} document(s) still processing after {max_wait_seconds}s")

                    # Return friendly message instead of error
                    return {
                        "answer": f"⏳ Your document(s) are still being processed: {', '.join(doc_names[:3])}{'...' if len(doc_names) > 3 else ''}. This usually takes 1-2 minutes for large documents with technical drawings. Please try your query again in a moment.",
                        "sources": [],
                        "model": "system",
                        "processing_status": "documents_not_ready",
                        "documents_processing": doc_names
                    }

        # Phase 7: Use EnhancedRAGAgent for multi-tool orchestration
        # The agent will:
        # 1. Classify the query (detect URLs, intents)
        # 2. Select appropriate tools (document_rag, smart_extraction, web_scraper, etc.)
        # 3. Execute tools (in parallel if needed)
        # 4. Return results with comprehensive metadata

        from app.agents.enhanced_rag_agent import enhanced_rag_agent

        logger.info(f"🤖 Using EnhancedRAGAgent for query: {query[:100]}...")

        # 🆕 Parse unified configuration (ALL 48 parameters for dynamic control)
        unified_config_dict = {}
        if unified_config:
            try:
                unified_config_dict = json.loads(unified_config)
                logger.info(f"✅ Received unified config with strategy_weights: {unified_config_dict.get('strategy_weights', {})}")
                logger.info(f"   📊 Total config groups: {len(unified_config_dict)}")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Failed to parse unified_config JSON: {e}")

        # 🆕 URL DETECTION + UI SETTINGS OVERRIDE LAYER (BEFORE AGENT ROUTING)
        # Extract navigation threshold from unified_config
        tool_navigation_threshold = None
        if unified_config_dict and 'strategy_weights' in unified_config_dict:
            strategy_weights = unified_config_dict.get('strategy_weights', {})
            tool_navigation_threshold = strategy_weights.get('tool_navigation')

        # URL regex pattern (matches http:// and https:// with full paths, query strings, fragments)
        # Captures: https://example.com/path/to/page?query=value#fragment
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        detected_urls = re.findall(url_pattern, query)

        # Check if we should force route to web scraper
        if detected_urls and tool_navigation_threshold is not None and tool_navigation_threshold > 0.8:
            logger.info(f"🔍 URL Detection: Found {len(detected_urls)} URL(s): {detected_urls}")
            logger.info(f"🎚️ Navigation threshold from UI: {tool_navigation_threshold}")
            logger.info(f"🌐 UI OVERRIDE: tool_navigation ({tool_navigation_threshold}) > 0.8 AND URL detected")
            logger.info(f"   → Triggering web scraper BEFORE agent routing (UI settings override)")

            try:
                # Trigger web scraper for each URL
                scrape_results = []
                for url in detected_urls:
                    logger.info(f"🔍 Scraping URL: {url}")
                    scrape_result = await scraper_service.scrape_url(
                        url=url,
                        session_id=session_id,
                        project_id=project_id,
                        scrape_prompt=query,
                        strategy="auto",
                        db=db
                    )
                    scrape_results.append({
                        'url': url,
                        'status': 'success',
                        'document_id': scrape_result.get('document_id'),
                        'filename': scrape_result.get('filename'),
                        'content': scrape_result.get('content', '')[:500] + '...' if scrape_result.get('content') else 'Processing...'
                    })
                    logger.info(f"✅ Successfully scraped: {url} → {scrape_result.get('filename')}")

                # Build response
                answer = f"✅ I successfully scraped {len(scrape_results)} URL(s) based on your tool_navigation threshold ({tool_navigation_threshold:.2f}):\n\n"
                for result in scrape_results:
                    answer += f"• {result['url']}\n  → Saved as: {result.get('filename', 'Unknown')}\n  → Preview: {result.get('content', 'No preview')}\n\n"

                return {
                    "answer": answer,
                    "sources": [],
                    "model": "url_detection_override",
                    "num_sources": 0,
                    "cached": False,
                    "ui_override_triggered": True,
                    "detected_urls": detected_urls,
                    "tool_navigation_threshold": tool_navigation_threshold,
                    "scrape_results": scrape_results
                }

            except Exception as scrape_error:
                logger.error(f"❌ Web scraper failed: {scrape_error}")
                logger.error(f"   Error type: {type(scrape_error).__name__}")
                logger.error(f"   URL detection and override worked, but scraping execution failed")
                logger.error(f"   Falling back to normal agent routing...")

                # Return error message instead of falling through
                return {
                    "answer": f"⚠️ I detected your URL and tried to scrape it (your tool_navigation threshold is {tool_navigation_threshold:.2f}), but encountered an error:\n\n{str(scrape_error)}\n\nThe scraper was triggered correctly by your UI settings, but failed during execution. Please check the logs for details.",
                    "sources": [],
                    "model": "url_detection_override_error",
                    "num_sources": 0,
                    "cached": False,
                    "ui_override_triggered": True,
                    "scraper_error": str(scrape_error),
                    "detected_urls": detected_urls,
                    "tool_navigation_threshold": tool_navigation_threshold
                }

        elif detected_urls and tool_navigation_threshold is not None:
            logger.info(f"🔍 URL detected but threshold ({tool_navigation_threshold}) <= 0.8, using normal agent routing")
        elif detected_urls:
            logger.info(f"🔍 URL detected but no tool_navigation threshold in unified_config, using normal agent routing")

        # 🆕 Parse enabled tools and selected agent
        enabled_tools_list = []
        if enabled_tools:
            try:
                enabled_tools_list = json.loads(enabled_tools)
                logger.info(f"🔧 Enabled tools ({len(enabled_tools_list)}): {enabled_tools_list}")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Failed to parse enabled_tools JSON: {e}")

        logger.info(f"🤖 Selected agent: {selected_agent}")

        # Build user preferences - merge unified_config with individual parameters
        # Unified config takes precedence, individual parameters are fallback
        user_preferences = {
            # Start with unified config if provided (contains all 48 parameters)
            **unified_config_dict,
            # 🆕 FIXED: Extract from correct nested structure (rag_settings, not retrieval_and_search)
            # Backward compatibility: Individual parameters override if explicitly provided
            "top_k": top_k if top_k is not None else unified_config_dict.get("rag_settings", {}).get("top_k"),
            "similarity_threshold": similarity_threshold if similarity_threshold is not None else unified_config_dict.get("similarity_thresholds", {}).get("default"),
            "min_similarity_threshold": min_similarity_threshold if min_similarity_threshold is not None else unified_config_dict.get("rag_settings", {}).get("min_similarity_threshold"),
            "no_relevant_docs_threshold": no_relevant_docs_threshold if no_relevant_docs_threshold is not None else unified_config_dict.get("rag_settings", {}).get("no_relevant_docs_threshold"),
            "semantic_weight": semantic_weight if semantic_weight is not None else unified_config_dict.get("reranking_weights", {}).get("semantic"),
            "keyword_weight": keyword_weight if keyword_weight is not None else unified_config_dict.get("reranking_weights", {}).get("keyword"),
            # Always include these
            "use_cache": use_cache,
            "model_id": model_id,
            "conversation_history": parsed_history,
            "enable_evaluation": enable_evaluation,  # Pass evaluation flag to agent
            "user_id": user_id,
            "project_id": project_id,  # Link to project for scoped retrieval
            "db": db,
            # 🆕 Tool & Agent Selection
            "enabled_tools": enabled_tools_list,  # List of enabled tool IDs
            "selected_agent": selected_agent,  # Agent orchestration type
            # 🧠 Brain View: Pass entire unified_config to agent
            "unified_config": unified_config_dict  # Contains all 48 RAG parameters including enable_brain_view
        }

        # Call enhanced agent
        result = await enhanced_rag_agent.run(
            query=query,
            session_id=session_id,
            user_preferences=user_preferences
        )

        latency_ms = (time.time() - start_time) * 1000

        # Auto-evaluation: Check if enabled and trigger async evaluation
        if session_id and result.get('quality_metrics'):
            try:
                from app.models.database_enhanced import EvaluationConfig as DBEvaluationConfig, ChatSession
                import asyncio

                # Check if session has auto-evaluation enabled
                chat_session_query = select(ChatSession).where(ChatSession.session_id == session_id)
                chat_session_result = await db.execute(chat_session_query)
                chat_session = chat_session_result.scalar_one_or_none()

                if chat_session:
                    eval_config_query = select(DBEvaluationConfig).where(
                        DBEvaluationConfig.session_id == chat_session.id
                    )
                    eval_config_result = await db.execute(eval_config_query)
                    eval_config = eval_config_result.scalar_one_or_none()

                    if eval_config and eval_config.auto_evaluate:
                        logger.info(f"🔄 Auto-evaluation enabled for session {session_id}, triggering evaluation...")

                        # Trigger evaluation asynchronously (don't block response)
                        asyncio.create_task(
                            _save_evaluation_async(
                                db=db,
                                session_id=chat_session.id,
                                query=query,
                                response=result.get('answer', ''),
                                quality_metrics=result.get('quality_metrics', {}),
                                sources=result.get('sources', []),
                                model_used=result.get('model', 'unknown'),
                                latency_ms=latency_ms
                            )
                        )
            except Exception as eval_error:
                # Don't fail the request if evaluation fails
                logger.warning(f"Auto-evaluation failed (non-critical): {eval_error}")

        # 🆕 ADD PERFORMANCE METRICS TO RESPONSE (for frontend display)
        result['latency_ms'] = latency_ms
        result['tokens_used'] = result.get('metadata', {}).get('tokens', 0)  # Extract tokens from metadata if available
        result['num_sources'] = len(result.get('sources', []))
        result['cached'] = result.get('metadata', {}).get('cache_hit', False)

        # 🆕 EXPOSE MODEL INFORMATION AT TOP LEVEL (fix for missing model name display)
        # IMPORTANT: This must happen BEFORE audit logging so the audit has the correct model info
        result['model'] = result.get('model', result.get('metadata', {}).get('model', 'unknown'))
        result['model_used'] = result.get('model_name', result.get('model', 'unknown'))

        # Audit logging (must happen AFTER model info extraction)
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

        # 🆕 MESSAGE PERSISTENCE: Save messages to database (DB-First with localStorage cache)
        if session_id:
            try:
                from app.models.database_enhanced import ChatSession, ConversationMessage
                from datetime import datetime
                import uuid as uuid_lib

                # 1. Get or create chat session
                chat_session_query = select(ChatSession).where(ChatSession.session_id == session_id)
                chat_session_result = await db.execute(chat_session_query)
                chat_session = chat_session_result.scalar_one_or_none()

                if not chat_session:
                    # Create new chat session if it doesn't exist
                    chat_session = ChatSession(
                        id=uuid_lib.uuid4(),
                        session_id=session_id,
                        user_id=user_id,
                        created_at=datetime.utcnow(),
                        last_activity=datetime.utcnow(),
                        is_active=True
                    )
                    db.add(chat_session)
                    await db.flush()  # Get the ID
                    logger.info(f"📝 Created new chat session: {session_id}")
                else:
                    # Update last activity
                    chat_session.last_activity = datetime.utcnow()
                    await db.flush()

                # 2. Save user message to conversation_messages table
                # Note: ConversationMessage.session_id is a foreign key to chat_sessions.id (UUID)
                user_message = ConversationMessage(
                    id=uuid_lib.uuid4(),
                    session_id=chat_session.id,  # UUID from chat_sessions table
                    role='user',
                    content=query,
                    created_at=datetime.utcnow()
                )
                db.add(user_message)

                # 3. Save assistant response
                assistant_message = ConversationMessage(
                    id=uuid_lib.uuid4(),
                    session_id=chat_session.id,  # UUID from chat_sessions table
                    role='assistant',
                    content=result.get('answer', ''),
                    sources=result.get('sources'),  # Already JSON serializable
                    model_id=result.get('model', 'unknown'),
                    model_name=result.get('model_used', result.get('model', 'unknown')),
                    total_tokens=result.get('tokens_used', 0),
                    latency_ms=latency_ms,
                    created_at=datetime.utcnow()
                )
                db.add(assistant_message)

                await db.commit()
                logger.info(f"💾 Saved 2 messages to conversation_messages for session {session_id}")

            except Exception as msg_error:
                # Don't fail the request if message persistence fails
                logger.error(f"Failed to save messages to DB (non-critical): {msg_error}", exc_info=True)
                await db.rollback()

        # 🆕 EXPOSE QUALITY METRICS AT TOP LEVEL (if present in metadata)
        if 'metadata' in result and 'quality_metrics' in result['metadata']:
            result['quality_metrics'] = result['metadata']['quality_metrics']

        # 🆕 EXPOSE TOOLS_USED AT TOP LEVEL (for frontend tool display)
        if 'metadata' in result and 'tool_usage' in result['metadata']:
            tool_usage = result['metadata']['tool_usage']
            # Convert tool_usage format to tools_used format expected by frontend
            if 'tools_used' in tool_usage and 'tool_timing' in tool_usage:
                tools_used_list = []
                for tool_name in tool_usage['tools_used']:
                    timing_ms = tool_usage['tool_timing'].get(tool_name, 0)
                    tool_entry = {
                        'tool': tool_name,
                        'timestamp_ms': timing_ms,
                        'details': tool_usage.get('tool_execution_summary', {}).get(tool_name, {}).get('error') or f"execution time: {timing_ms:.2f}ms"
                    }
                    tools_used_list.append(tool_entry)
                result['tools_used'] = tools_used_list
                logger.debug(f"✅ Exposed {len(tools_used_list)} tools to frontend")

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
async def get_documents(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all documents, optionally filtered by project_id"""
    try:
        from sqlalchemy import select
        from app.models.database import Document

        # Build query with optional project filter
        query = select(Document).order_by(Document.created_at.desc())

        if project_id:
            # Filter by project_id
            import uuid
            try:
                project_uuid = uuid.UUID(project_id)
                query = query.where(Document.project_id == project_uuid)
                logger.info(f"📁 Filtering documents by project_id: {project_id}")
            except ValueError:
                logger.warning(f"Invalid project_id format: {project_id}")
                raise HTTPException(status_code=400, detail="Invalid project_id format")

        result = await db.execute(query)
        documents = result.scalars().all()

        logger.info(f"📁 Found {len(documents)} documents" + (f" for project {project_id}" if project_id else ""))

        return [
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "source_type": doc.source_type,
                "source_url": doc.source_url,
                "processed": doc.processing_status == 'completed',
                "upload_date": doc.created_at.isoformat(),
                "project_id": str(doc.project_id) if doc.project_id else None
            }
            for doc in documents
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and all its associated chunks/embeddings

    This endpoint:
    1. Deletes all document chunks (embeddings cascade automatically)
    2. Deletes the document record
    3. Optionally removes file from MinIO storage

    Note: Document chunks have ON DELETE CASCADE, so deleting the document
    automatically removes all associated chunks and embeddings.
    """
    try:
        from sqlalchemy import select, delete
        from app.models.database import Document, DocumentChunk, SessionDocument
        import uuid

        # Convert to UUID
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format")

        # Check if document exists
        result = await db.execute(
            select(Document).where(Document.id == doc_uuid)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        filename = document.filename

        # Get chunk count before deletion (for logging)
        chunk_count_result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc_uuid)
        )
        chunks = chunk_count_result.scalars().all()
        chunk_count = len(chunks)

        # Delete session associations (if they exist)
        await db.execute(
            delete(SessionDocument).where(SessionDocument.document_id == doc_uuid)
        )

        # Delete document (chunks will cascade automatically due to FK constraint)
        await db.execute(
            delete(Document).where(Document.id == doc_uuid)
        )

        await db.commit()

        logger.info(
            f"🗑️  Document deleted successfully:\n"
            f"   Document: {filename}\n"
            f"   ID: {document_id}\n"
            f"   Chunks deleted: {chunk_count}\n"
            f"   Embeddings removed: {chunk_count}"
        )

        return {
            "message": "Document and all embeddings deleted successfully",
            "document_id": document_id,
            "filename": filename,
            "chunks_deleted": chunk_count,
            "embeddings_deleted": chunk_count
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get("/api/v1/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get processing status of a document

    Returns:
        - processing_status: "processing", "completed", "failed"
        - filename: str
        - error_message: str (if failed)
    """
    try:
        from app.models.database import Document
        from sqlalchemy import select
        import uuid

        # Convert to UUID
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format")

        # Query document
        result = await db.execute(
            select(Document).where(Document.id == doc_uuid)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "document_id": str(document.id),
            "filename": document.filename,
            "processing_status": document.processing_status if hasattr(document, 'processing_status') else 'completed',
            "error_message": document.processing_error if hasattr(document, 'processing_error') else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document status: {str(e)}")


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

# Multi-Strategy RAG with Answer Fusion API (evaluates multiple strategies in parallel)
try:
    from app.api.routes import multi_strategy_routes
    app.include_router(multi_strategy_routes.router)
    logger.info("✓ Multi-Strategy RAG API router registered (answer fusion with short/long-term memory prioritization)")
except ImportError as e:
    logger.warning(f"Multi-Strategy RAG API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Multi-Strategy RAG router: {e}")


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
        logger.warning(f"Could not register fallback models router: {e2}")
        logger.warning("Continuing without model selection API")

# Enhanced Web Scraper API router
try:
    from app.api.routes import scraper_routes
    app.include_router(scraper_routes.router)
    logger.info("✓ Enhanced Web Scraper API router registered")
except ImportError as e:
    logger.warning(f"Enhanced Web Scraper API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Enhanced Web Scraper router: {e}")
    logger.warning("Continuing with basic scraper endpoints only")

# Also import the enhanced scraper service (with fallback to basic)
try:
    from app.services.scraper_service import scraper_service
    logger.info("✓ Enhanced Scraper Service loaded")
except ImportError as e:
    logger.warning(f"Enhanced Scraper Service not available: {e}")
except Exception as e2:
    logger.warning(f"Could not load Enhanced Scraper Service: {e2}")
    logger.warning("Continuing with basic scraper service")

# Enterprise Web Scraper with Compliance Engine
try:
    from app.api.routes import scraper_enhanced
    app.include_router(scraper_enhanced.router)
    logger.info("✓ Enterprise Web Scraper API router registered (compliance engine, LLM integration)")
except ImportError as e:
    logger.warning(f"Enterprise Web Scraper API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Enterprise Web Scraper router: {e}")

# Phase 3: Extraction Workflow API (LangGraph-based)
try:
    from app.api.routes import extraction_routes
    app.include_router(extraction_routes.router)
    logger.info("✓ Extraction Workflow API router registered (Phase 3: LangGraph workflows)")
except ImportError as e:
    logger.warning(f"Extraction Workflow API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Extraction Workflow router: {e}")
    logger.warning("Continuing without enterprise scraper features")

# Template-based Extraction API
try:
    from app.api.routes import template_extraction_routes
    app.include_router(template_extraction_routes.router)
    logger.info("✓ Template Extraction API router registered (Excel export, preset templates)")
except ImportError as e:
    logger.warning(f"Template Extraction API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Template Extraction router: {e}")

# Project Estimator API (BRD and Cost Estimation)
try:
    from app.api.routes import project_estimator_routes
    app.include_router(project_estimator_routes.router)
    logger.info("✓ Project Estimator API router registered (BRD and cost estimation generation)")
except ImportError as e:
    logger.warning(f"Project Estimator API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Project Estimator router: {e}")

# Construction Metrics Extraction API
try:
    from app.api.routes import construction_metrics_routes
    app.include_router(construction_metrics_routes.router)
    logger.info("✓ Construction Metrics API router registered (building metrics extraction from ZIP files)")
except ImportError as e:
    logger.warning(f"Construction Metrics API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Construction Metrics router: {e}")

# Playwright test routes (for debugging)
try:
    from app.api.routes import playwright_test_routes
    app.include_router(playwright_test_routes.router)
    logger.info("✓ Playwright test routes registered (debugging endpoint)")
except ImportError as e:
    logger.warning(f"Playwright test routes not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Playwright test router: {e}")

# Secrets Management API (encrypted API keys storage)
try:
    from app.api.routes import secrets
    app.include_router(secrets.router)
    logger.info("✓ Secrets Management API router registered (encrypted API keys storage)")
except ImportError as e:
    logger.warning(f"Secrets Management API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Secrets Management router: {e}")

# Ollama Model Management API (Phase 1 - Read-Only)
try:
    from app.api.routes import ollama_models
    app.include_router(ollama_models.router, prefix="/api/v1")
    logger.info("✓ Ollama Model Management API router registered (Phase 1: read-only operations)")
except ImportError as e:
    logger.warning(f"Ollama Model Management API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Ollama Model Management router: {e}")

# Evaluation Metrics API (RAG system analytics and performance monitoring)
try:
    from app.api.routes import evaluation
    app.include_router(evaluation.router)
    logger.info("✓ Evaluation Metrics API router registered (real-time analytics and performance insights)")
except ImportError as e:
    logger.warning(f"Evaluation Metrics API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Evaluation Metrics router: {e}")

# Weights Configuration API (configurable weights for RAG system)
try:
    from app.api.routes import weights_config_routes
    app.include_router(weights_config_routes.router)
    logger.info("✓ Weights Configuration API router registered (configurable scoring and strategy weights)")
except ImportError as e:
    logger.warning(f"Weights Configuration API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Weights Configuration router: {e}")

# 🆕 Tool Usage Statistics API (comprehensive tool tracking and analytics)
try:
    from app.api.routes import tool_stats_routes
    app.include_router(tool_stats_routes.router)
    logger.info("✓ Tool Usage Statistics API router registered (tracks all tools: Docling, Playwright, LLM, RAG, MCP)")
except ImportError as e:
    logger.warning(f"Tool Usage Statistics API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Tool Usage Statistics router: {e}")

# MCP Management API (Model Context Protocol - bidirectional tool integration)
try:
    from app.api.routes import mcp_routes
    app.include_router(mcp_routes.router)
    logger.info("✓ MCP Management API router registered (provider + consumer management)")
except ImportError as e:
    logger.warning(f"⚠ MCP Management API not available: {e}")
    logger.warning("⚠ Install MCP SDK: pip install mcp")
except Exception as e:
    logger.warning(f"Could not register MCP Management router: {e}")

# Tool Discovery API (Multi-Tool Agent - tool listing and management)
try:
    from app.api.routes import tool_routes
    app.include_router(tool_routes.router)
    logger.info("✓ Tool Discovery API router registered (list, search, and manage tools)")
except Exception as e:
    logger.warning(f"Could not register Tool Discovery router: {e}")

# Scraping Configuration & Compliance API (Admin-level scraping policy management)
try:
    from app.api.routes import scraping_config_routes
    app.include_router(
        scraping_config_routes.router,
        prefix="/api/v1/admin",
        tags=["admin", "scraping-configs"]
    )
    logger.info("✓ Scraping Configuration API router registered (domain policies, compliance, audit)")
except ImportError as e:
    logger.warning(f"⚠ Scraping Configuration API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Scraping Configuration router: {e}")

# Authentication API
try:
    from app.api.routes import auth
    app.include_router(auth.router)
    logger.info("✓ Authentication API router registered (login, register, token management)")
except ImportError as e:
    logger.warning(f"⚠ Authentication API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register Authentication router: {e}")

# RBAC Management API (Role-Based Access Control)
try:
    from app.api.routes import rbac_routes
    app.include_router(rbac_routes.router)
    logger.info("✓ RBAC Management API router registered (roles, departments, modules, permissions)")
except ImportError as e:
    logger.warning(f"⚠ RBAC Management API not available: {e}")
except Exception as e:
    logger.warning(f"Could not register RBAC Management router: {e}")

# Simple Modules API (workaround for RBAC table conflicts)
try:
    from app.api.routes import modules_simple
    app.include_router(modules_simple.router)
    logger.info("✓ Simple Modules API router registered (user module access)")
except Exception as e:
    logger.warning(f"Could not register Simple Modules router: {e}")

# Teams & Projects Management API
try:
    from app.api.routes import teams_projects_routes
    app.include_router(teams_projects_routes.router)
    logger.info("✓ Teams & Projects Management API router registered")
except Exception as e:
    logger.warning(f"Could not register Teams & Projects router: {e}")

# Library Management API
try:
    from app.api.routes import library_routes
    app.include_router(library_routes.router)
    logger.info("✓ Library Management API router registered")
except Exception as e:
    logger.warning(f"Could not register Library router: {e}")

# Prompt Library and Output Templates API
try:
    from app.api.routes import prompt_library_routes
    app.include_router(prompt_library_routes.router)
    logger.info("✓ Prompt Library & Output Templates API router registered")
except Exception as e:
    logger.warning(f"Could not register Prompt Library router: {e}")

# Export Service API
try:
    from app.api.routes import export_routes
    app.include_router(export_routes.router)
    logger.info("✓ Export Service API router registered (Excel, Word, Markdown, JSON)")
except Exception as e:
    logger.warning(f"Could not register Export Service router: {e}")

# Agent Task Management API
try:
    from app.api.routes import agent_routes
    app.include_router(agent_routes.router)
    logger.info("✓ Agent Task Management API router registered (LLM-driven autonomous agent)")
except Exception as e:
    logger.warning(f"Could not register Agent router: {e}")


# === Admin API Endpoints ===

@app.get("/api/v1/admin/users")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    """Get all users (admin endpoint)"""
    try:
        from app.models.database_enhanced import User
        from app.models.rbac import Department
        from sqlalchemy import select, func
        from sqlalchemy.orm import joinedload

        # Fetch users with department relationship
        query = select(User).outerjoin(Department, User.department_id == Department.id).order_by(User.created_at.desc())
        result = await db.execute(query)
        users = result.scalars().all()

        # For each user, fetch their teams
        user_list = []
        for user in users:
            # Get department name
            dept_name = None
            if user.department_id:
                dept_result = await db.execute(select(Department).where(Department.id == user.department_id))
                dept = dept_result.scalar_one_or_none()
                if dept:
                    dept_name = dept.name

            # Get user's teams from user_teams junction table
            from app.models.database_enhanced import UserTeam
            try:
                teams_query = select(UserTeam).where(UserTeam.user_id == user.id)
                teams_result = await db.execute(teams_query)
                user_teams = teams_result.scalars().all()

                # Get team details
                team_ids = [str(ut.team_id) for ut in user_teams]
                team_names = []
                if team_ids:
                    from app.models.rbac import Team
                    for team_id in team_ids:
                        team_result = await db.execute(select(Team).where(Team.id == team_id))
                        team = team_result.scalar_one_or_none()
                        if team:
                            team_names.append(team.name)
            except:
                # UserTeam table might not exist yet
                team_ids = []
                team_names = []

            user_list.append({
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value if user.role else None,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "department_id": str(user.department_id) if user.department_id else None,
                "department_name": dept_name,
                "function": user.function,
                "team_ids": team_ids,
                "team_names": team_names
            })

        return user_list
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
        from app.models.database_enhanced import User, UserRole, Project, ProjectMember
        from sqlalchemy import select
        from app.core.security import get_password_hash
        import uuid as uuid_module

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

        # Hash password using bcrypt (production-ready)
        hashed_password = get_password_hash(password)

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

        # Auto-add user to Global project
        try:
            global_project_query = select(Project).where(Project.name == 'Global')
            global_result = await db.execute(global_project_query)
            global_project = global_result.scalar_one_or_none()

            if global_project:
                # Check if already a member
                member_check = select(ProjectMember).where(
                    (ProjectMember.project_id == global_project.id) &
                    (ProjectMember.user_id == new_user.id)
                )
                existing_member = await db.execute(member_check)
                if not existing_member.scalar_one_or_none():
                    # Add as member
                    project_member = ProjectMember(
                        id=uuid_module.uuid4(),
                        project_id=global_project.id,
                        user_id=new_user.id,
                        role='member'
                    )
                    db.add(project_member)
                    await db.commit()
                    logger.info(f"✓ Added {username} to Global project")
        except Exception as e:
            logger.warning(f"Could not add user to Global project: {e}")

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


@app.patch("/api/v1/admin/users/{user_id}")
async def update_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Update user organizational fields (admin endpoint)"""
    try:
        from app.models.database_enhanced import User, UserRole, UserTeam
        from app.models.rbac import Department, Team
        from sqlalchemy import select, delete
        import uuid

        # Get JSON body
        body = await request.json()

        # Find user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update fields if provided
        if 'department_id' in body:
            dept_id = body['department_id']
            if dept_id:
                # Verify department exists
                dept_query = select(Department).where(Department.id == dept_id)
                dept_result = await db.execute(dept_query)
                dept = dept_result.scalar_one_or_none()
                if not dept:
                    raise HTTPException(status_code=400, detail="Department not found")
                user.department_id = uuid.UUID(dept_id)
            else:
                user.department_id = None

        if 'function' in body:
            user.function = body['function']

        if 'team_ids' in body:
            # Delete existing team assignments
            delete_query = delete(UserTeam).where(UserTeam.user_id == user.id)
            await db.execute(delete_query)

            # Add new team assignments
            team_ids = body['team_ids']
            if team_ids:
                for idx, team_id in enumerate(team_ids):
                    # Verify team exists
                    team_query = select(Team).where(Team.id == team_id)
                    team_result = await db.execute(team_query)
                    team = team_result.scalar_one_or_none()
                    if not team:
                        continue  # Skip invalid team IDs

                    # Create team assignment
                    user_team = UserTeam(
                        user_id=user.id,
                        team_id=uuid.UUID(team_id),
                        is_primary=(idx == 0)  # First team is primary
                    )
                    db.add(user_team)

        if 'role' in body:
            role = body['role']
            user.role = UserRole[role.upper()] if hasattr(UserRole, role.upper()) else user.role

        if 'is_active' in body:
            user.is_active = body['is_active']

        await db.commit()
        await db.refresh(user)

        # Get updated user info
        dept_name = None
        if user.department_id:
            dept_result = await db.execute(select(Department).where(Department.id == user.department_id))
            dept = dept_result.scalar_one_or_none()
            if dept:
                dept_name = dept.name

        # Get teams
        teams_query = select(UserTeam).where(UserTeam.user_id == user.id)
        teams_result = await db.execute(teams_query)
        user_teams = teams_result.scalars().all()
        team_ids = [str(ut.team_id) for ut in user_teams]
        team_names = []
        for team_id in team_ids:
            team_result = await db.execute(select(Team).where(Team.id == team_id))
            team = team_result.scalar_one_or_none()
            if team:
                team_names.append(team.name)

        logger.info(f"✓ Updated user: {user.username}")

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if user.role else None,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "department_id": str(user.department_id) if user.department_id else None,
            "department_name": dept_name,
            "function": user.function,
            "team_ids": team_ids,
            "team_names": team_names
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# === User Session Endpoints ===

@app.get("/api/v1/sessions")
async def get_user_sessions(
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,  # 🆕 Add project_id filter
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get chat sessions for a user and/or project"""
    try:
        from app.models.database_enhanced import ChatSession, ConversationMessage
        from sqlalchemy import select, func, and_

        # Build query
        query = select(
            ChatSession,
            func.count(ConversationMessage.id).label('message_count')
        ).outerjoin(
            ConversationMessage, ChatSession.id == ConversationMessage.session_id
        ).group_by(ChatSession.id)

        # Apply filters
        filters = []
        if user_id:
            from uuid import UUID
            filters.append(ChatSession.user_id == UUID(user_id))

        if project_id:
            from uuid import UUID
            filters.append(ChatSession.project_id == UUID(project_id))

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(ChatSession.last_activity.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        sessions = result.all()

        # 🆕 Fetch most used model for each session
        sessions_with_models = []
        for session in sessions:
            session_data = {
                "id": str(session.ChatSession.id),
                "session_id": session.ChatSession.session_id,
                "user_id": str(session.ChatSession.user_id) if session.ChatSession.user_id else None,
                "project_id": str(session.ChatSession.project_id) if session.ChatSession.project_id else None,
                "title": session.ChatSession.title,
                "created_at": session.ChatSession.created_at.isoformat(),
                "last_activity": session.ChatSession.last_activity.isoformat(),
                "is_active": session.ChatSession.is_active,
                "message_count": session.message_count
            }

            # Get most used model from messages
            try:
                model_query = select(
                    ConversationMessage.model_used,
                    func.count(ConversationMessage.id).label('usage_count')
                ).where(
                    and_(
                        ConversationMessage.session_id == session.ChatSession.id,
                        ConversationMessage.model_used.isnot(None)
                    )
                ).group_by(ConversationMessage.model_used).order_by(func.count(ConversationMessage.id).desc()).limit(1)

                model_result = await db.execute(model_query)
                most_used = model_result.first()

                if most_used and most_used.model_used:
                    session_data["most_used_model"] = most_used.model_used
                else:
                    session_data["most_used_model"] = None
            except Exception as model_err:
                logger.warning(f"Could not fetch model for session {session.ChatSession.session_id}: {model_err}")
                session_data["most_used_model"] = None

            sessions_with_models.append(session_data)

        return {
            "sessions": sessions_with_models
        }
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    try:
        from app.models.database_enhanced import ChatSession
        from sqlalchemy import select

        # Find session
        query = select(ChatSession).where(ChatSession.session_id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Delete session (messages will cascade delete)
        await db.delete(session)
        await db.commit()

        return {"message": "Session deleted successfully", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str = None,
    auto_generate: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Update session title (auto-generate or manual)"""
    try:
        from app.models.database_enhanced import ChatSession, ConversationMessage
        from sqlalchemy import select

        # Find session
        query = select(ChatSession).where(ChatSession.session_id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Auto-generate title using LLM (2-3 words max)
        if auto_generate:
            msg_query = select(ConversationMessage).where(
                ConversationMessage.session_id == session.id
            ).order_by(ConversationMessage.created_at.asc()).limit(3)

            msg_result = await db.execute(msg_query)
            messages = msg_result.scalars().all()

            if messages:
                try:
                    # Use LLM to generate concise 2-3 word title
                    conversation_text = "\n".join([
                        f"{msg.role.upper()}: {msg.content[:300]}"
                        for msg in messages
                    ])

                    title_prompt = f"""Extract the main topic from this conversation in EXACTLY 2-3 words.

Conversation:
{conversation_text}

Rules:
- EXACTLY 2-3 words (e.g., "RAG Systems", "Vector Databases", "Project Estimation")
- Topic only, NO questions
- NO full sentences
- Title case (e.g., "Machine Learning" not "machine learning")

Topic:"""

                    response = await llm_service.generate(
                        prompt=title_prompt,
                        max_tokens=50,  # ✅ Increased from 15 to allow proper responses
                        temperature=0.3
                    )

                    title = response.get('answer', '').strip()
                    title = title.replace('"', '').replace("'", '').strip()

                    # Validate: 2-3 words only
                    if title:
                        word_count = len(title.split())
                        if word_count > 3:
                            # Take first 3 words
                            title = ' '.join(title.split()[:3])
                        logger.info(f"✅ Generated title: '{title}'")
                    else:
                        # Empty response - use fallback
                        logger.warning("LLM returned empty title, using fallback")
                        raise ValueError("Empty LLM response")

                except Exception as e:
                    logger.warning(f"LLM title generation failed: {e}, using fallback")
                    # Fallback: extract key nouns from first message
                    first_content = messages[0].content.lower()
                    words = first_content.split()
                    # Skip common words
                    skip_words = {'what', 'how', 'why', 'when', 'where', 'which', 'who', 'can', 'could', 'would', 'should', 'you', 'help', 'explain', 'tell', 'me', 'about', 'the', 'a', 'an', 'is', 'are', 'was', 'were'}
                    keywords = [w.strip('.,!?:;').title() for w in words if len(w) > 3 and w.lower() not in skip_words]
                    title = ' '.join(keywords[:2]) if len(keywords) >= 2 else (keywords[0] if keywords else "Chat")
            else:
                title = "New Chat"

        # Update title
        session.title = title
        await db.commit()
        await db.refresh(session)

        return {
            "session_id": session.session_id,
            "title": session.title,
            "message": "Title updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session title: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a specific session"""
    try:
        from app.models.database_enhanced import ChatSession, ConversationMessage
        from sqlalchemy import select

        # Find session
        session_query = select(ChatSession).where(ChatSession.session_id == session_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get messages
        messages_query = select(ConversationMessage).where(
            ConversationMessage.session_id == session.id
        ).order_by(ConversationMessage.created_at.asc()).limit(limit).offset(offset)

        messages_result = await db.execute(messages_query)
        messages = messages_result.scalars().all()

        # Determine most used model from messages
        model_usage = {}
        for msg in messages:
            if msg.model_id:
                model_usage[msg.model_id] = model_usage.get(msg.model_id, 0) + 1
        most_used_model = max(model_usage.items(), key=lambda x: x[1])[0] if model_usage else None

        return {
            "session_id": session_id,
            "title": session.title,
            "project_id": str(session.project_id) if session.project_id else None,  # 🆕 Include project context
            "most_used_model": most_used_model,  # 🆕 Include most frequently used model
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "sources": msg.sources,
                    "model_used": msg.model_name or msg.model_id,  # Use model_name (display name)
                    "tokens_used": msg.total_tokens,  # Map to frontend field name
                    "latency_ms": msg.latency_ms,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Admin Endpoints ===

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
            .where(SessionDocument.session_id == session.session_id)
            .group_by(Document.id, SessionDocument.id)
            .order_by(SessionDocument.added_at.desc())
        )

        result = await db.execute(query)
        rows = result.all()

        documents = []
        for doc, session_doc, chunk_count in rows:
            # Derive processing status from Document model fields
            if doc.error_message:
                processing_status = 'failed'
            elif doc.processing_status == 'completed':
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
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
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
                sql_delete(SessionDocument).where(SessionDocument.session_id == session.session_id)
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

        query = query.order_by(Document.created_at.desc()).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        documents = []
        for doc, chunk_count, user_email, username, session_id in rows:
            # Derive processing status from Document model fields
            if doc.error_message:
                processing_status = 'failed'
            elif doc.processing_status == 'completed':
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
                "created_at": doc.created_at.isoformat() if doc.created_at else None
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
            SessionDocument.session_id == session.session_id
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
        ).where(SessionDocument.session_id == session.session_id)
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
                "processed": doc.processing_status == 'completed',
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
                d.created_at,
                d.processing_status,
                d.error_message,
                COUNT(DISTINCT dc.id) as total_chunks,
                COUNT(DISTINCT CASE WHEN dc.embedding IS NOT NULL THEN dc.id END) as chunks_with_embeddings,
                COUNT(DISTINCT sd.session_id) as session_count,
                STRING_AGG(DISTINCT cs.session_id, ', ') as session_ids
            FROM documents d
            LEFT JOIN document_chunks dc ON d.id = dc.document_id
            LEFT JOIN session_documents sd ON d.id = sd.document_id
            LEFT JOIN chat_sessions cs ON sd.session_id = cs.session_id
            WHERE d.filename ILIKE :search_pattern
            GROUP BY d.id, d.filename, d.file_type, d.file_size, d.source_type, d.source_url, d.created_at, d.processing_status, d.error_message
            ORDER BY d.created_at DESC
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
                "upload_date": row.created_at.isoformat() if row.created_at else None,
                "processed": row.processing_status == 'completed',
                "processing_error": row.error_message,
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
                "upload_date": document.created_at.isoformat() if document.created_at else None
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
                (SELECT COUNT(*) FROM documents WHERE processing_status = 'completed') as processed_documents,
                (SELECT COUNT(*) FROM documents WHERE error_message IS NOT NULL) as failed_documents,
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
        error_query = select(Document).where(Document.error_message != None)
        error_result = await db.execute(error_query)
        error_docs = error_result.scalars().all()
        diagnostic_info['documents_with_errors'] = len(error_docs)
        diagnostic_info['error_details'] = [
            {
                'filename': doc.filename,
                'error': doc.error_message[:200]  # Truncate long errors
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
                ORDER BY d.created_at DESC, dc.chunk_index
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


async def _save_evaluation_async(
    db: AsyncSession,
    session_id: uuid.UUID,
    query: str,
    response: str,
    quality_metrics: dict,
    sources: list,
    model_used: str,
    latency_ms: float
):
    """
    Save evaluation results to database asynchronously

    This runs in the background and doesn't block the API response.
    """
    try:
        from app.models.database_enhanced import EvaluationResult
        import json

        # Get a new database session for async task
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as eval_db:
            # Calculate overall score from available metrics
            scores = []
            if 'rag_score' in quality_metrics:
                scores.append(quality_metrics['rag_score'])
            if 'faithfulness' in quality_metrics:
                scores.append(quality_metrics['faithfulness'])
            if 'answer_relevancy' in quality_metrics:
                scores.append(quality_metrics['answer_relevancy'])
            if 'context_relevancy' in quality_metrics:
                scores.append(quality_metrics['context_relevancy'])

            overall_score = sum(scores) / len(scores) if scores else 0.5

            # Create evaluation result
            eval_result = EvaluationResult(
                session_id=session_id,
                query=query,
                response=response,
                overall_score=overall_score,
                scores=quality_metrics,  # Store all metrics as JSON
                evaluation_time_ms=quality_metrics.get('evaluation_time_ms', 0),
                enabled_methods=quality_metrics.get('enabled_methods', []),
                metadata={
                    'model_used': model_used,
                    'query_latency_ms': latency_ms,
                    'num_sources': len(sources),
                    'auto_evaluated': True
                }
            )

            eval_db.add(eval_result)
            await eval_db.commit()

            logger.info(f"✅ Auto-evaluation saved for session {session_id} (score: {overall_score:.2f})")

    except Exception as e:
        logger.error(f"Failed to save auto-evaluation: {e}", exc_info=True)


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
