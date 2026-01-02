"""
Elasticsearch Service for Keyword-Based Retrieval

Provides BM25 keyword search to complement pgvector semantic search.
Supports filters, aggregations, and bulk indexing.

Integration with Merit POCs:
- CRU: Mining document keyword search
- GT Motive: Part code exact matching
- Solera: VIN and claim number search

Author: Claude Code
Date: 2026-01-02
"""

from elasticsearch import AsyncElasticsearch, helpers
from typing import List, Dict, Any, Optional
import os
import logging
import json

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """
    Elasticsearch integration for keyword-based retrieval.

    Complements pgvector semantic search with BM25 keyword matching.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
        self.client = None
        self._initialized = True

        logger.info(f"📊 ElasticsearchService initialized (URL: {self.es_url})")

    async def _ensure_client(self):
        """Lazy initialization of Elasticsearch client"""
        if self.client is None:
            try:
                self.client = AsyncElasticsearch(
                    hosts=[self.es_url],
                    request_timeout=30,
                    max_retries=3,
                    retry_on_timeout=True
                )

                # Verify connection
                info = await self.client.info()
                logger.info(f"✅ Connected to Elasticsearch {info['version']['number']}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
                raise

    async def create_index(
        self,
        index_name: str,
        mappings: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create Elasticsearch index with custom mappings and settings.

        Args:
            index_name: Name of the index
            mappings: Field mappings (optional, uses defaults if not provided)
            settings: Index settings (optional)

        Returns:
            True if created successfully, False if already exists

        Example:
            await es.create_index(
                "merit_cru_documents",
                mappings={
                    "properties": {
                        "content": {"type": "text"},
                        "document_type": {"type": "keyword"},
                        "company": {"type": "keyword"},
                        "usecase": {"type": "keyword"},
                        "year": {"type": "integer"}
                    }
                }
            )
        """
        await self._ensure_client()

        # Default mappings for document chunks
        if mappings is None:
            mappings = {
                "properties": {
                    "content": {"type": "text", "analyzer": "standard"},
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "company": {"type": "keyword"},
                    "usecase": {"type": "keyword"},
                    "document_type": {"type": "keyword"},
                    "metadata": {"type": "object", "enabled": True}
                }
            }

        # Default settings
        if settings is None:
            settings = {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "default": {
                            "type": "standard"
                        }
                    }
                }
            }

        try:
            exists = await self.client.indices.exists(index=index_name)

            if not exists:
                await self.client.indices.create(
                    index=index_name,
                    body={
                        "mappings": mappings,
                        "settings": settings
                    }
                )
                logger.info(f"✅ Created Elasticsearch index: {index_name}")
                return True
            else:
                logger.info(f"ℹ️ Index already exists: {index_name}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to create index {index_name}: {e}")
            raise

    async def index_document(
        self,
        index_name: str,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Index a single document.

        Args:
            index_name: Elasticsearch index
            document_id: Unique document ID
            content: Document text content
            metadata: Additional metadata fields

        Returns:
            True if indexed successfully
        """
        await self._ensure_client()

        doc = {
            "content": content,
            "chunk_id": document_id,
            **(metadata or {})
        }

        try:
            result = await self.client.index(
                index=index_name,
                id=document_id,
                document=doc
            )

            logger.debug(f"📝 Indexed document {document_id} to {index_name}")
            return result["result"] in ["created", "updated"]

        except Exception as e:
            logger.error(f"❌ Failed to index document {document_id}: {e}")
            return False

    async def bulk_index(
        self,
        index_name: str,
        documents: List[Dict[str, Any]],
        chunk_size: int = 500
    ) -> Dict[str, int]:
        """
        Bulk index multiple documents.

        Args:
            index_name: Elasticsearch index
            documents: List of documents to index
                Expected format: [
                    {
                        "document_id": "uuid",
                        "content": "text",
                        "company": "Grant Thornton",
                        "usecase": "financial_analysis",
                        "metadata": {...}
                    }
                ]
            chunk_size: Batch size for bulk operations

        Returns:
            {"success": int, "failed": int}

        Example:
            results = await es.bulk_index(
                "merit_british_council_courses",
                documents=[
                    {
                        "document_id": "course_123",
                        "content": "IELTS Preparation Course",
                        "company": "British Council",
                        "usecase": "course_recommendation"
                    }
                ]
            )
        """
        await self._ensure_client()

        actions = []
        for doc in documents:
            action = {
                "_index": index_name,
                "_id": doc.get("document_id") or doc.get("chunk_id"),
                "_source": {
                    "content": doc.get("content", ""),
                    "chunk_id": doc.get("document_id") or doc.get("chunk_id"),
                    **doc.get("metadata", {})
                }
            }
            actions.append(action)

        success_count = 0
        failed_count = 0

        try:
            # Use bulk helper for efficient indexing
            async for ok, result in helpers.async_streaming_bulk(
                self.client,
                actions,
                chunk_size=chunk_size,
                raise_on_error=False
            ):
                if ok:
                    success_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Failed to index: {result}")

            logger.info(f"📦 Bulk indexed {success_count} docs to {index_name} ({failed_count} failed)")

            # Refresh index to make documents searchable
            await self.client.indices.refresh(index=index_name)

            return {"success": success_count, "failed": failed_count}

        except Exception as e:
            logger.error(f"❌ Bulk indexing failed: {e}")
            return {"success": success_count, "failed": len(documents) - success_count}

    async def search(
        self,
        index_name: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        BM25 keyword search with optional filters.

        Args:
            index_name: Elasticsearch index to search
            query: Search query text
            filters: Field filters (e.g., {"company": "CRU", "usecase": "mining"})
            top_k: Number of results to return
            fields: Fields to search (default: ["content"])

        Returns:
            List of search results with scores

        Example:
            results = await es.search(
                "merit_cru_documents",
                query="capex Gold Valley 2024",
                filters={"company": "CRU", "usecase": "mining"},
                top_k=10
            )
        """
        await self._ensure_client()

        if fields is None:
            fields = ["content^2", "metadata.title", "metadata.section"]

        # Build query
        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": fields,
                    "type": "best_fields",
                    "operator": "or"
                }
            }
        ]

        # Add filters
        filter_clauses = []
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {field: value}})
                else:
                    filter_clauses.append({"term": {field: value}})

        es_query = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        }

        try:
            response = await self.client.search(
                index=index_name,
                query=es_query,
                size=top_k,
                _source=True
            )

            # Format results
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "document_id": hit["_id"],
                    "content": hit["_source"].get("content", ""),
                    "score": float(hit["_score"]),
                    "metadata": {
                        k: v for k, v in hit["_source"].items()
                        if k not in ["content", "chunk_id"]
                    }
                })

            logger.info(f"🔍 ES search returned {len(results)} results for '{query[:50]}'")
            return results

        except Exception as e:
            logger.error(f"❌ Search failed for index {index_name}: {e}")
            return []

    async def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        await self._ensure_client()

        try:
            exists = await self.client.indices.exists(index=index_name)
            if exists:
                await self.client.indices.delete(index=index_name)
                logger.info(f"🗑️ Deleted index: {index_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete index {index_name}: {e}")
            return False

    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get statistics about an index"""
        await self._ensure_client()

        try:
            stats = await self.client.indices.stats(index=index_name)
            index_stats = stats["indices"][index_name]

            return {
                "doc_count": index_stats["total"]["docs"]["count"],
                "size_bytes": index_stats["total"]["store"]["size_in_bytes"],
                "size_mb": round(index_stats["total"]["store"]["size_in_bytes"] / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats for {index_name}: {e}")
            return {}

    async def close(self):
        """Close Elasticsearch connection"""
        if self.client:
            await self.client.close()
            logger.info("🔌 Closed Elasticsearch connection")


# Singleton instance
_elasticsearch_service = None

def get_elasticsearch() -> ElasticsearchService:
    """Get singleton Elasticsearch service instance"""
    global _elasticsearch_service
    if _elasticsearch_service is None:
        _elasticsearch_service = ElasticsearchService()
    return _elasticsearch_service
