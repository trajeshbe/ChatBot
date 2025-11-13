import strawberry
from typing import List, Optional
from datetime import datetime
import logging
from app.services.rag_service import rag_service
from app.services.document_service import document_service
from app.services.scraper_service import scraper_service
from app.core.database import AsyncSessionLocal
from app.agents.rag_agent import rag_agent, document_ingestion_flow, web_scraping_flow

logger = logging.getLogger(__name__)


# GraphQL Types
@strawberry.type
class Source:
    id: str
    filename: str
    source_type: str
    source_url: Optional[str]
    relevance: float
    excerpt: str


@strawberry.type
class QueryResponse:
    answer: str
    sources: List[Source]
    model: str
    tokens_used: int
    latency_ms: float
    num_sources: int
    cached: bool


@strawberry.type
class Document:
    id: str
    filename: str
    file_type: str
    file_size: int
    source_type: str
    source_url: Optional[str]
    processed: bool
    upload_date: datetime


@strawberry.type
class ScrapeJobResult:
    success: bool
    job_id: Optional[str]
    document_id: Optional[str]
    title: Optional[str]
    content_length: Optional[int]
    url: str
    error: Optional[str] = None


@strawberry.type
class UploadResult:
    success: bool
    document_id: str
    filename: str
    message: str


@strawberry.type
class Message:
    id: str
    role: str
    content: str
    sources: Optional[List[Source]]
    created_at: datetime


@strawberry.type
class Conversation:
    id: str
    session_id: str
    messages: List[Message]
    created_at: datetime


# GraphQL Inputs
@strawberry.input
class QueryInput:
    query: str
    session_id: Optional[str] = None
    use_cache: bool = True


@strawberry.input
class ScrapeInput:
    url: str
    scrape_prompt: Optional[str] = None


@strawberry.input
class MultiScrapeInput:
    urls: List[str]
    scrape_prompt: Optional[str] = None


# Query resolvers
@strawberry.type
class Query:
    @strawberry.field
    async def query(self, input: QueryInput) -> QueryResponse:
        """Query the RAG system (simple, fast query)"""
        try:
            async with AsyncSessionLocal() as db:
                result = await rag_service.query(
                    query_text=input.query,
                    conversation_history=None,
                    use_cache=input.use_cache,
                    db=db
                )

            sources = [
                Source(
                    id=s['id'],
                    filename=s['filename'],
                    source_type=s['source_type'],
                    source_url=s.get('source_url'),
                    relevance=s['relevance'],
                    excerpt=s['excerpt']
                )
                for s in result['sources']
            ]

            return QueryResponse(
                answer=result['answer'],
                sources=sources,
                model=result['model'],
                tokens_used=result['tokens_used'],
                latency_ms=result['latency_ms'],
                num_sources=result['num_sources'],
                cached=result['cached']
            )

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    @strawberry.field
    async def agentic_query(self, input: QueryInput) -> QueryResponse:
        """Query using LangGraph agent workflow for complex queries"""
        try:
            # Use the LangGraph agent for orchestrated query processing
            result = await rag_agent.run(input.query)

            sources = [
                Source(
                    id=s['id'],
                    filename=s['filename'],
                    source_type=s['source_type'],
                    source_url=s.get('source_url'),
                    relevance=s['relevance'],
                    excerpt=s['excerpt']
                )
                for s in result.get('sources', [])
            ]

            return QueryResponse(
                answer=result.get('answer', ''),
                sources=sources,
                model='langgraph-agent',
                tokens_used=0,  # TODO: Track tokens in agent
                latency_ms=0,   # TODO: Track latency in agent
                num_sources=result.get('retrieved_docs', 0),
                cached=False
            )

        except Exception as e:
            logger.error(f"Error processing agentic query: {e}")
            raise

    @strawberry.field
    async def documents(self) -> List[Document]:
        """Get all documents"""
        try:
            from sqlalchemy import select
            from app.models.database import Document as DBDocument

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(DBDocument).order_by(DBDocument.upload_date.desc()))
                docs = result.scalars().all()

            return [
                Document(
                    id=str(doc.id),
                    filename=doc.filename,
                    file_type=doc.file_type,
                    file_size=doc.file_size,
                    source_type=doc.source_type,
                    source_url=doc.source_url,
                    processed=doc.processed,
                    upload_date=doc.upload_date
                )
                for doc in docs
            ]

        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            raise

    @strawberry.field
    async def health(self) -> str:
        """Health check endpoint"""
        return "OK"


# Mutation resolvers
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def scrape_url(self, input: ScrapeInput) -> ScrapeJobResult:
        """Scrape a URL and process the content"""
        try:
            async with AsyncSessionLocal() as db:
                result = await scraper_service.scrape_url(
                    url=input.url,
                    scrape_prompt=input.scrape_prompt,
                    db=db
                )

            return ScrapeJobResult(
                success=result['success'],
                job_id=result.get('job_id'),
                document_id=result.get('document_id'),
                title=result.get('title'),
                content_length=result.get('content_length'),
                url=result['url']
            )

        except Exception as e:
            logger.error(f"Error scraping URL: {e}")
            return ScrapeJobResult(
                success=False,
                url=input.url,
                error=str(e)
            )

    @strawberry.mutation
    async def scrape_multiple_urls(self, input: MultiScrapeInput) -> List[ScrapeJobResult]:
        """Scrape multiple URLs using Prefect orchestration"""
        try:
            # Use Prefect flow for orchestrated web scraping
            results = await web_scraping_flow(input.urls, input.scrape_prompt)

            return [
                ScrapeJobResult(
                    success=r.get('success', False),
                    job_id=r.get('job_id'),
                    document_id=r.get('document_id'),
                    title=r.get('title'),
                    content_length=r.get('content_length'),
                    url=r.get('url', ''),
                    error=r.get('error')
                )
                for r in results
            ]

        except Exception as e:
            logger.error(f"Error scraping URLs: {e}")
            raise


# Schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
