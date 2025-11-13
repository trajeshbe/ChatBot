from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
import logging
from typing import Optional
import uvicorn

from app.core.config import settings
from app.core.database import init_db, close_db, get_db
from app.api.graphql.schema import schema
from app.services.embedding_service import embedding_service

# Try to import enhanced LLM service, fallback to basic if it fails
try:
    from app.services.llm_service_enhanced import llm_service
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("Using Enhanced LLM Service with multi-model support")
except ImportError as e:
    from app.services.llm_service import llm_service
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"Enhanced LLM service not available: {e}. Using basic service.")

from app.services.document_service import document_service
from app.services.scraper_service import scraper_service
from app.services.rag_service import rag_service
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        logger.info("Initializing LLM service...")
        await llm_service.initialize()
        logger.info("LLM service initialized")
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
        "version": settings.APP_VERSION
    }


# REST API endpoints
@app.post("/api/v1/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file for processing"""
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

        return {
            "success": True,
            "document_id": str(document.id),
            "filename": document.filename,
            "message": "File uploaded and processed successfully"
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/query")
async def query_endpoint(
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_cache: bool = Form(True),
    model_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Query the RAG system"""
    try:
        result = await rag_service.query(
            query_text=query,
            conversation_history=None,
            use_cache=use_cache,
            model_id=model_id,
            db=db
        )

        return result

    except Exception as e:
        logger.error(f"Error processing query: {e}")
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
