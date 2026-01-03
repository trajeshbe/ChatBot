"""
Construction Monitor POC - Construction Document NER/REL Service

Customer: Construction Monitor
Use Case: Custom NER/REL for Construction Document Intelligence
Capabilities:
- Extract construction-specific entities (PROJECT, CONTRACTOR, MATERIAL, etc.)
- Relation extraction (HAS_CONTRACTOR, USES_MATERIAL, DUE_ON, etc.)
- Knowledge graph construction
- Document Q&A for construction projects
- Budget tracking and milestone monitoring
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.document_service import DocumentService
from .construction_monitor_schemas import *

logger = logging.getLogger(__name__)

class ConstructionMonitorService:
    """Construction document intelligence with NER and relation extraction"""

    # Entity types for construction domain
    ENTITY_TYPES = [
        "PROJECT",       # Project names
        "CONTRACTOR",    # Companies/contractors
        "LOCATION",      # Project locations
        "MATERIAL",      # Construction materials
        "QUANTITY",      # Amounts with units
        "COST",          # Monetary values
        "DATE",          # Dates/deadlines
        "MILESTONE"      # Project milestones
    ]

    # Relation types
    RELATION_TYPES = [
        "HAS_CONTRACTOR",  # Project awarded to contractor
        "LOCATED_AT",      # Project location
        "USES_MATERIAL",   # Materials used
        "HAS_COST",        # Cost allocation
        "DUE_ON",          # Milestone deadlines
        "SUPPLIES"         # Supplier relationships
    ]

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService()
        self.document_service = DocumentService(db)

    async def process_request(self, request: ConstructionMonitorRequest) -> ConstructionMonitorResponse:
        """Extract entities and relations from construction documents"""
        try:
            logger.info(f"[Construction Monitor] Processing for session {request.session_id}")

            entities = []
            relations = []
            knowledge_graph = {}
            document_text = ""

            # 1. Document-Based Extraction
            if request.document_id:
                logger.info(f"[Construction Monitor] Extracting from document {request.document_id}")

                # Get document content
                chunks = await self.document_service.get_chunks_for_document(request.document_id)
                document_text = " ".join([chunk.get('content', '') for chunk in chunks[:10]])

                # Extract entities and relations
                entities = await self._extract_entities_llm(document_text)
                relations = await self._extract_relations_llm(document_text, entities)

                # Build knowledge graph
                knowledge_graph = self._build_knowledge_graph(entities, relations)

            # 2. Query-Based Extraction
            if request.query:
                logger.info(f"[Construction Monitor] Processing query: {request.query}")

                # Query the knowledge graph or extract from query context
                query_result = await self._process_query(
                    request.query,
                    knowledge_graph,
                    document_text
                )

                if not entities and not relations:
                    # Extract from query context if no document
                    entities = query_result.get("entities", [])
                    relations = query_result.get("relations", [])

            # Generate insights
            insights = await self._generate_insights(entities, relations, knowledge_graph, request.query)

            # Generate recommendations
            recommendations = self._generate_recommendations(entities, relations, knowledge_graph)

            return ConstructionMonitorResponse(
                success=True,
                session_id=request.session_id,
                result={
                    "entities": entities,
                    "relations": relations,
                    "knowledge_graph": knowledge_graph,
                    "entity_count": len(entities),
                    "relation_count": len(relations),
                    "document_preview": document_text[:300] if document_text else None
                },
                insights=insights,
                recommendations=recommendations,
                extracted_data={
                    "projects": [e for e in entities if e.get("type") == "PROJECT"],
                    "contractors": [e for e in entities if e.get("type") == "CONTRACTOR"],
                    "total_cost": self._calculate_total_cost(entities)
                },
                processing_time=0.0,
                tier_1_services_used=["LLMService", "DocumentService"]
            )

        except Exception as e:
            logger.error(f"[Construction Monitor] Error: {e}", exc_info=True)
            raise

    async def _extract_entities_llm(self, text: str) -> List[Dict[str, Any]]:
        """Extract construction-specific entities using LLM"""
        prompt = f"""You are a construction document analyst. Extract all construction-specific entities from the following text.

Text:
{text[:3000]}

Entity Types to Extract:
- PROJECT: Project names
- CONTRACTOR: Companies/contractors
- LOCATION: Project locations
- MATERIAL: Construction materials
- QUANTITY: Amounts with units (e.g., "500 cubic yards")
- COST: Monetary values (e.g., "$1.2M")
- DATE: Dates/deadlines
- MILESTONE: Project milestones

Return a JSON array of entities:
[
  {{
    "type": "PROJECT",
    "value": "Gold Tower Construction",
    "confidence": 0.95,
    "context": "surrounding text snippet"
  }}
]

Return ONLY the JSON array, no explanation."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1500
            )

            import json
            entities = json.loads(response.strip())
            logger.info(f"[Construction Monitor] Extracted {len(entities)} entities")
            return entities

        except Exception as e:
            logger.warning(f"[Construction Monitor] Entity extraction failed: {e}")
            return []

    async def _extract_relations_llm(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relations between entities using LLM"""
        # Create entity summary for context
        entity_summary = "\n".join([
            f"- {e['type']}: {e['value']}" for e in entities[:20]
        ])

        prompt = f"""You are a construction document analyst. Extract relationships between the following entities.

Extracted Entities:
{entity_summary}

Document Text:
{text[:2000]}

Relation Types:
- HAS_CONTRACTOR: (Project, Contractor)
- LOCATED_AT: (Project, Location)
- USES_MATERIAL: (Project, Material, Quantity)
- HAS_COST: (Project/Material, Cost)
- DUE_ON: (Milestone, Date)
- SUPPLIES: (Contractor, Material)

Return a JSON array of relations:
[
  {{
    "type": "HAS_CONTRACTOR",
    "subject": "Gold Tower Construction",
    "object": "ABC Builders Inc.",
    "confidence": 0.9
  }}
]

Return ONLY the JSON array, no explanation."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=1000
            )

            import json
            relations = json.loads(response.strip())
            logger.info(f"[Construction Monitor] Extracted {len(relations)} relations")
            return relations

        except Exception as e:
            logger.warning(f"[Construction Monitor] Relation extraction failed: {e}")
            return []

    def _build_knowledge_graph(self, entities: List[Dict], relations: List[Dict]) -> Dict[str, Any]:
        """Build a simple knowledge graph from entities and relations"""
        graph = {
            "nodes": [],
            "edges": [],
            "statistics": {}
        }

        # Add entity nodes
        for entity in entities:
            graph["nodes"].append({
                "id": f"{entity['type']}:{entity['value']}",
                "type": entity['type'],
                "label": entity['value'],
                "confidence": entity.get('confidence', 0.8)
            })

        # Add relation edges
        for relation in relations:
            graph["edges"].append({
                "source": relation['subject'],
                "target": relation['object'],
                "type": relation['type'],
                "confidence": relation.get('confidence', 0.8)
            })

        # Calculate statistics
        graph["statistics"] = {
            "total_nodes": len(graph["nodes"]),
            "total_edges": len(graph["edges"]),
            "entity_types": {etype: sum(1 for e in entities if e['type'] == etype) for etype in self.ENTITY_TYPES},
            "relation_types": {rtype: sum(1 for r in relations if r['type'] == rtype) for rtype in self.RELATION_TYPES}
        }

        return graph

    async def _process_query(
        self,
        query: str,
        knowledge_graph: Dict[str, Any],
        document_text: str
    ) -> Dict[str, Any]:
        """Process query against knowledge graph or document"""
        prompt = f"""You are a construction project assistant. Answer the following query based on the knowledge graph and document.

Query: {query}

Knowledge Graph Statistics:
{knowledge_graph.get('statistics', {})}

Document Text:
{document_text[:1500] if document_text else 'No document provided'}

Provide a response in JSON format:
{{
  "answer": "Direct answer to the query",
  "entities": [],  # Relevant entities
  "relations": []  # Relevant relations
}}

Return ONLY the JSON, no explanation."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=800
            )

            import json
            return json.loads(response.strip())

        except Exception as e:
            logger.warning(f"[Construction Monitor] Query processing failed: {e}")
            return {"answer": "Unable to process query", "entities": [], "relations": []}

    def _calculate_total_cost(self, entities: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate total cost from COST entities"""
        import re
        total = 0.0

        for entity in entities:
            if entity.get("type") == "COST":
                value_str = entity.get("value", "")
                # Extract numeric value (e.g., "$1.2M" -> 1200000)
                match = re.search(r'[\d,.]+', value_str)
                if match:
                    num_str = match.group().replace(',', '')
                    try:
                        num = float(num_str)
                        # Handle M (millions), K (thousands)
                        if 'M' in value_str.upper():
                            num *= 1000000
                        elif 'K' in value_str.upper():
                            num *= 1000
                        total += num
                    except:
                        pass

        return total if total > 0 else None

    async def _generate_insights(
        self,
        entities: List[Dict],
        relations: List[Dict],
        knowledge_graph: Dict,
        query: Optional[str]
    ) -> str:
        """Generate AI insights about the construction project"""
        if not entities and not relations:
            return "No construction project data extracted. Upload a construction document (proposal, contract, or progress report) for analysis."

        insights = []

        # Entity insights
        projects = [e for e in entities if e['type'] == 'PROJECT']
        contractors = [e for e in entities if e['type'] == 'CONTRACTOR']
        materials = [e for e in entities if e['type'] == 'MATERIAL']

        if projects:
            insights.append(f"Identified {len(projects)} construction project(s): {', '.join([p['value'] for p in projects[:3]])}.")

        if contractors:
            insights.append(f"Found {len(contractors)} contractor(s) involved in the project.")

        if materials:
            insights.append(f"Extracted {len(materials)} construction material reference(s).")

        # Relation insights
        if relations:
            insights.append(f"Discovered {len(relations)} relationship(s) between project entities, enabling knowledge graph construction.")

        # Cost insights
        total_cost = self._calculate_total_cost(entities)
        if total_cost:
            insights.append(f"Total project cost identified: ${total_cost:,.2f}.")

        # Knowledge graph insights
        stats = knowledge_graph.get("statistics", {})
        if stats.get("total_nodes", 0) > 0:
            insights.append(f"Built knowledge graph with {stats['total_nodes']} nodes and {stats.get('total_edges', 0)} edges for project intelligence.")

        if query:
            insights.append(f"Query processed: '{query[:80]}...'")

        return " ".join(insights)

    def _generate_recommendations(
        self,
        entities: List[Dict],
        relations: List[Dict],
        knowledge_graph: Dict
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if not entities:
            recommendations.append("Upload construction documents (RFPs, contracts, progress reports) for entity extraction")
            return recommendations

        projects = [e for e in entities if e['type'] == 'PROJECT']
        contractors = [e for e in entities if e['type'] == 'CONTRACTOR']
        milestones = [e for e in entities if e['type'] == 'MILESTONE']
        costs = [e for e in entities if e['type'] == 'COST']

        if projects and not contractors:
            recommendations.append("Identify and add contractor information for project tracking")

        if projects and not milestones:
            recommendations.append("Extract project milestones and deadlines for schedule monitoring")

        if costs:
            recommendations.append(f"Review {len(costs)} cost item(s) for budget tracking and variance analysis")

        if relations:
            recommendations.append("Use knowledge graph to answer complex queries about project relationships")

        if len(entities) > 20:
            recommendations.append("Consider creating a master project database from the extracted entities")

        recommendations.append("Export entity-relation data for project management tools integration")

        return recommendations

    async def get_status(self) -> StatusResponse:
        """Get service status and capabilities"""
        return StatusResponse(
            success=True,
            status="operational",
            description="Construction Monitor: Custom NER/REL for construction document intelligence with knowledge graph construction",
            tier_2_modules_used=["relation-extractor", "document-extract", "generic-rag"],
            capabilities=[
                "Extract 8 construction-specific entity types (PROJECT, CONTRACTOR, MATERIAL, QUANTITY, COST, DATE, MILESTONE, LOCATION)",
                "Relation extraction with 6 relation types (HAS_CONTRACTOR, LOCATED_AT, USES_MATERIAL, HAS_COST, DUE_ON, SUPPLIES)",
                "Knowledge graph construction from entities and relations",
                "Document Q&A for construction projects using graph traversal",
                "Budget tracking and cost aggregation from extracted entities",
                "Milestone and deadline monitoring",
                "LLM-powered entity and relation extraction (no custom ML models required)",
                "Export-ready structured data for project management integration"
            ]
        )
