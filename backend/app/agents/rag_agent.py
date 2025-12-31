from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from prefect import flow, task
import logging
from app.services.rag_service import rag_service
from app.services.document_service import document_service
from app.services.embedding_service import embedding_service
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the RAG agent"""
    messages: Sequence[BaseMessage]
    query: str
    retrieved_docs: list
    answer: str
    sources: list
    next_action: str


class RAGAgent:
    """LangGraph-based RAG Agent for document Q&A"""

    def __init__(self):
        self.graph = None
        self._build_graph()

    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("retrieve_documents", self.retrieve_documents)
        workflow.add_node("generate_answer", self.generate_answer)
        workflow.add_node("validate_answer", self.validate_answer)

        # Add edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "generate_answer")
        workflow.add_edge("generate_answer", "validate_answer")

        # Add conditional edge from validation
        workflow.add_conditional_edges(
            "validate_answer",
            self.should_regenerate,
            {
                "regenerate": "generate_answer",
                "complete": END
            }
        )

        self.graph = workflow.compile()

    async def analyze_query(self, state: AgentState) -> AgentState:
        """Analyze the user query to determine intent"""
        logger.info(f"Analyzing query: {state['query']}")

        # Simple intent detection - can be enhanced with LLM
        query_lower = state['query'].lower()

        if any(word in query_lower for word in ['upload', 'add', 'submit']):
            state['next_action'] = 'upload'
        elif any(word in query_lower for word in ['scrape', 'fetch', 'get from']):
            state['next_action'] = 'scrape'
        else:
            state['next_action'] = 'query'

        return state

    async def retrieve_documents(self, state: AgentState) -> AgentState:
        """Retrieve relevant documents"""
        logger.info("Retrieving relevant documents")

        try:
            # Generate embedding
            query_embedding = await embedding_service.get_embedding(state['query'])

            # Search for similar chunks
            async with AsyncSessionLocal() as db:
                chunks = await document_service.search_similar_chunks(
                    query_embedding=query_embedding,
                    top_k=5,
                    threshold=0.7,
                    db=db
                )

            state['retrieved_docs'] = chunks
            logger.info(f"Retrieved {len(chunks)} relevant documents")

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            state['retrieved_docs'] = []

        return state

    async def generate_answer(self, state: AgentState) -> AgentState:
        """Generate answer using RAG"""
        logger.info("Generating answer")

        try:
            async with AsyncSessionLocal() as db:
                result = await rag_service.query(
                    query_text=state['query'],
                    conversation_history=[],
                    use_cache=True,
                    db=db
                )

            state['answer'] = result['answer']
            state['sources'] = result['sources']

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            state['answer'] = f"Error generating answer: {str(e)}"
            state['sources'] = []

        return state

    async def validate_answer(self, state: AgentState) -> AgentState:
        """Validate the generated answer"""
        logger.info("Validating answer")

        # Simple validation - can be enhanced
        answer = state.get('answer', '')

        if len(answer) < 10:
            state['validation_result'] = 'regenerate'
        elif 'error' in answer.lower():
            state['validation_result'] = 'regenerate'
        else:
            state['validation_result'] = 'complete'

        return state

    def should_regenerate(self, state: AgentState) -> str:
        """Decide whether to regenerate answer"""
        return state.get('validation_result', 'complete')

    async def run(self, query: str) -> dict:
        """Execute the agent workflow"""
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "retrieved_docs": [],
            "answer": "",
            "sources": [],
            "next_action": ""
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "retrieved_docs": len(result.get("retrieved_docs", []))
        }


# Prefect flows for orchestration
@task(name="process_document_task", retries=2)
async def process_document_task(document_id: str):
    """Prefect task to process a document"""
    logger.info(f"Processing document: {document_id}")

    try:
        from uuid import UUID
        async with AsyncSessionLocal() as db:
            await document_service.process_document(UUID(document_id), db)
        logger.info(f"Successfully processed document {document_id}")
        return {"success": True, "document_id": document_id}
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise


@task(name="scrape_url_task", retries=2)
async def scrape_url_task(url: str, scrape_prompt: str = None):
    """Prefect task to scrape a URL"""
    logger.info(f"Scraping URL: {url}")

    try:
        from app.services.scraper_service import scraper_service
        async with AsyncSessionLocal() as db:
            result = await scraper_service.scrape_url(url, scrape_prompt, db)
        logger.info(f"Successfully scraped {url}")
        return result
    except Exception as e:
        logger.error(f"Error scraping URL: {e}")
        raise


@flow(name="document_ingestion_flow")
async def document_ingestion_flow(document_ids: list):
    """Prefect flow to process multiple documents"""
    logger.info(f"Starting document ingestion flow for {len(document_ids)} documents")

    results = []
    for doc_id in document_ids:
        result = await process_document_task(doc_id)
        results.append(result)

    return results


@flow(name="web_scraping_flow")
async def web_scraping_flow(urls: list, scrape_prompt: str = None):
    """Prefect flow to scrape multiple URLs"""
    logger.info(f"Starting web scraping flow for {len(urls)} URLs")

    results = []
    for url in urls:
        result = await scrape_url_task(url, scrape_prompt)
        results.append(result)

    return results


# Global agent instance
rag_agent = RAGAgent()
