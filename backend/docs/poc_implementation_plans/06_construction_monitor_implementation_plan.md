# Construction Monitor POC - Implementation Plan

> **Customer:** Construction Monitor
> **Use Case:** Custom NER/REL for Construction Document Intelligence
> **Priority:** Tier 3 (Complex - 50% code reuse, custom ML models required)
> **Estimated Effort:** 4-5 weeks
> **Created:** 2026-01-02

---

## Table of Contents
1. [Business Requirements](#1-business-requirements)
2. [Technical Architecture](#2-technical-architecture)
3. [Reusable Components](#3-reusable-components)
4. [New Components](#4-new-components)
5. [Data Flow](#5-data-flow)
6. [API Endpoints](#6-api-endpoints)
7. [Database Schema](#7-database-schema)
8. [Frontend UI](#8-frontend-ui)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment](#10-deployment)
11. [Timeline](#11-timeline)

---

## 1. Business Requirements

### 1.1 Core Functionality
- **Custom Named Entity Recognition (NER)**: Extract construction-specific entities
  - Project names, locations, contractors
  - Material types, quantities, specifications
  - Dates (milestones, deadlines, completion)
  - Budget items, cost estimates
- **Relation Extraction (REL)**: Link entities together
  - Contractor → Project
  - Material → Quantity
  - Milestone → Date
- **Document Q&A**: Answer questions about construction projects
- **Knowledge Graph**: Build construction project knowledge graphs

### 1.2 Document Types
- **Project Proposals**: RFPs, bids, proposals
- **Contracts**: Construction contracts, subcontracts
- **Progress Reports**: Daily logs, weekly reports, monthly summaries
- **Blueprints/Drawings**: Technical drawings (OCR + vision)
- **Invoices**: Material invoices, labor invoices

### 1.3 Custom Entity Types

| Entity Type | Examples | Description |
|-------------|----------|-------------|
| **PROJECT** | "Gold Tower Construction", "Highway 101 Expansion" | Project names |
| **CONTRACTOR** | "ABC Builders Inc.", "XYZ Steel" | Companies/contractors |
| **LOCATION** | "Downtown Los Angeles", "Mile Marker 45" | Project locations |
| **MATERIAL** | "Concrete", "Rebar", "Steel I-Beams" | Construction materials |
| **QUANTITY** | "500 cubic yards", "10 tons", "2000 square feet" | Amounts with units |
| **COST** | "$1.2M", "€450,000", "Budget: $50K" | Monetary values |
| **DATE** | "Q3 2024", "By March 15", "Completion: 2025-06-30" | Dates/deadlines |
| **MILESTONE** | "Foundation Complete", "Steel Erection Start" | Project milestones |

### 1.4 Relation Types

| Relation | Example | Description |
|----------|---------|-------------|
| **HAS_CONTRACTOR** | (Project, Contractor) | Project awarded to contractor |
| **LOCATED_AT** | (Project, Location) | Project location |
| **USES_MATERIAL** | (Project, Material, Quantity) | Materials used |
| **HAS_COST** | (Project/Material, Cost) | Cost allocation |
| **DUE_ON** | (Milestone, Date) | Milestone deadlines |
| **SUPPLIES** | (Contractor, Material) | Supplier relationships |

### 1.5 Key Use Cases

**Use Case 1: Entity Extraction**
```
Input: "ABC Builders Inc. will supply 500 cubic yards of concrete for the Gold Tower Construction project in downtown LA."

Output:
- CONTRACTOR: "ABC Builders Inc."
- QUANTITY: "500 cubic yards"
- MATERIAL: "concrete"
- PROJECT: "Gold Tower Construction"
- LOCATION: "downtown LA"

Relations:
- (ABC Builders Inc., SUPPLIES, concrete)
- (Gold Tower Construction, USES_MATERIAL, concrete, 500 cubic yards)
- (Gold Tower Construction, LOCATED_AT, downtown LA)
```

**Use Case 2: Knowledge Graph Query**
```
Query: "Which contractors are supplying materials for Highway 101 Expansion?"

Knowledge Graph Traversal:
- Find PROJECT: "Highway 101 Expansion"
- Find all (Contractor, SUPPLIES, Material) where Material is USES_MATERIAL by Project
- Return: ["ABC Builders Inc. (concrete)", "XYZ Steel (rebar)"]
```

**Use Case 3: Budget Tracking**
```
Query: "What is the total cost for the Gold Tower project?"

Extraction:
- Find all (Gold Tower, HAS_COST, $X)
- Sum costs
- Return: "$5.2M total budget"
```

### 1.6 Success Metrics
- NER F1 score: >90% on construction entities
- REL F1 score: >85% on relation extraction
- Knowledge graph accuracy: >90%
- Query response time: <5 seconds
- Entity linking precision: >95%

---

## 2. Technical Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSTRUCTION MONITOR POC STACK                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          DOCUMENT UPLOAD (Construction Docs)             │  │
│  │  - Proposals, Contracts, Reports, Blueprints             │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          TEXT EXTRACTION (Docling + OCR)                 │  │
│  │  - PDF text + tables                                     │  │
│  │  - Blueprint OCR                                         │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          CUSTOM NER MODEL (SpaCy)                        │  │
│  │  - Trained on construction documents                     │  │
│  │  - 8 entity types (PROJECT, CONTRACTOR, MATERIAL, ...)   │  │
│  │  - GPU-accelerated inference                             │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          RELATION EXTRACTION MODEL                       │  │
│  │  - Identify relationships between entities               │  │
│  │  - 6 relation types (HAS_CONTRACTOR, USES_MATERIAL, ...) │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          KNOWLEDGE GRAPH BUILDER (Neo4j)                 │  │
│  │  - Nodes: Entities (Projects, Contractors, Materials)    │  │
│  │  - Edges: Relations (HAS_CONTRACTOR, SUPPLIES, ...)      │  │
│  │  - Cypher queries for traversal                          │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          HYBRID RAG (Infrastructure)                     │  │
│  │  - Semantic search (ChromaDB)                            │  │
│  │  - Keyword search (Elasticsearch)                        │  │
│  │  - Knowledge graph search (Neo4j)                        │  │
│  │  - Re-ranker (BAAI)                                      │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          LLM SYNTHESIS + Q&A                             │  │
│  │  - Answer questions with entity context                  │  │
│  │  - Generate project summaries                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **NER Model** | SpaCy 3.x + Custom Training | Industry-standard, fast inference |
| **REL Model** | SpaCy REL Component | Built-in relation extraction |
| **Knowledge Graph** | Neo4j | Best-in-class graph database |
| **Text Extraction** | Docling (existing) | PDF + table extraction |
| **OCR** | Tesseract + PaddleOCR (existing) | Blueprint text extraction |
| **Vector DB** | ChromaDB (existing) | Semantic search |
| **Keyword DB** | Elasticsearch (infrastructure) | Keyword search |
| **Re-ranker** | BAAI/bge-reranker-large (infrastructure) | Precision boost |
| **LLM** | GPT-4o-mini | Q&A synthesis |
| **Backend** | FastAPI + Pydantic | Existing stack |
| **Storage** | MinIO + PostgreSQL | Existing infrastructure |

---

## 3. Reusable Components

### 3.1 From Core Platform (50% Reuse)

| Component | Source | Reuse % | Usage |
|-----------|--------|---------|-------|
| **Document Service** | `app/services/document_service.py` | 80% | Upload construction docs |
| **Docling Analyzer** | `app/utils/docling_analyzer.py` | 100% | PDF text + table extraction |
| **OCR Service** | `app/services/ocr_service.py` | 100% | Blueprint OCR |
| **Embedding Service** | `app/services/embedding_service.py` | 100% | Semantic search |
| **LLM Service** | `app/services/llm_service.py` | 100% | Q&A synthesis |

### 3.2 From Infrastructure

| Component | Source | Usage |
|-----------|--------|-------|
| **Elasticsearch Service** | `infrastructure/elasticsearch_service.py` | Keyword search |
| **Multi-Pipeline Router** | `infrastructure/multi_pipeline_router.py` | Route to semantic/keyword/graph |
| **Re-ranker Service** | `infrastructure/reranker_service.py` | Improve search precision |

---

## 4. New Components

### 4.1 Custom NER Model Training

**File:** `backend/app/services/construction_monitor/ner_model_trainer.py`

**Purpose:** Train SpaCy NER model on construction documents

```python
import spacy
from spacy.training import Example
from typing import List, Dict, Any
import random

class ConstructionNERTrainer:
    """Train custom NER model for construction entities."""

    ENTITY_LABELS = [
        "PROJECT",
        "CONTRACTOR",
        "LOCATION",
        "MATERIAL",
        "QUANTITY",
        "COST",
        "DATE",
        "MILESTONE"
    ]

    def __init__(self):
        self.nlp = spacy.blank("en")
        self.ner = self.nlp.add_pipe("ner")

        # Add entity labels
        for label in self.ENTITY_LABELS:
            self.ner.add_label(label)

    def train(
        self,
        training_data: List[Dict[str, Any]],
        epochs: int = 30
    ):
        """
        Train NER model.

        Args:
            training_data: List of annotated examples
                [
                    {
                        "text": "ABC Builders will supply 500 cubic yards of concrete",
                        "entities": [
                            (0, 12, "CONTRACTOR"),  # ABC Builders
                            (25, 42, "QUANTITY"),   # 500 cubic yards
                            (46, 54, "MATERIAL")    # concrete
                        ]
                    },
                    ...
                ]
            epochs: Number of training epochs
        """
        # Disable other pipeline components
        other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != "ner"]
        with self.nlp.disable_pipes(*other_pipes):
            # Create optimizer
            optimizer = self.nlp.begin_training()

            # Training loop
            for epoch in range(epochs):
                random.shuffle(training_data)
                losses = {}

                for example_data in training_data:
                    text = example_data["text"]
                    annotations = {"entities": example_data["entities"]}

                    doc = self.nlp.make_doc(text)
                    example = Example.from_dict(doc, annotations)

                    self.nlp.update([example], drop=0.5, losses=losses)

                print(f"Epoch {epoch + 1}, Loss: {losses['ner']:.4f}")

    def save_model(self, output_path: str):
        """Save trained model to disk."""
        self.nlp.to_disk(output_path)

    @staticmethod
    def load_model(model_path: str):
        """Load trained model."""
        return spacy.load(model_path)
```

### 4.2 NER Inference Service

**File:** `backend/app/services/construction_monitor/ner_service.py`

**Purpose:** Extract entities from construction documents

```python
import spacy
from typing import List, Dict, Any
from pathlib import Path

class ConstructionNERService:
    """Extract construction-specific entities using custom NER model."""

    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = Path(__file__).parent / "models" / "construction_ner"

        self.nlp = spacy.load(model_path)

    async def extract_entities(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Extract entities from text.

        Returns:
            [
                {
                    "text": "ABC Builders Inc.",
                    "label": "CONTRACTOR",
                    "start": 0,
                    "end": 17
                },
                ...
            ]
        """
        doc = self.nlp(text)

        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })

        return entities

    async def extract_entities_batch(
        self,
        texts: List[str]
    ) -> List[List[Dict[str, Any]]]:
        """Extract entities from multiple texts in batch."""
        results = []
        for doc in self.nlp.pipe(texts):
            entities = [
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                }
                for ent in doc.ents
            ]
            results.append(entities)

        return results
```

### 4.3 Relation Extraction Service

**File:** `backend/app/services/construction_monitor/relation_extractor.py`

**Purpose:** Extract relationships between entities

```python
from typing import List, Dict, Any, Tuple

class RelationExtractor:
    """Extract relationships between construction entities."""

    RELATION_PATTERNS = {
        "HAS_CONTRACTOR": [
            r"(PROJECT) .* awarded to (CONTRACTOR)",
            r"(PROJECT) .* contractor:? (CONTRACTOR)",
        ],
        "USES_MATERIAL": [
            r"(PROJECT) .* use (QUANTITY) of (MATERIAL)",
            r"(PROJECT) .* supply (QUANTITY) (MATERIAL)",
        ],
        "LOCATED_AT": [
            r"(PROJECT) .* in (LOCATION)",
            r"(PROJECT) .* at (LOCATION)",
        ],
        "HAS_COST": [
            r"(PROJECT|MATERIAL) .* cost (COST)",
            r"(PROJECT|MATERIAL) .* budget:? (COST)",
        ],
        "DUE_ON": [
            r"(MILESTONE) .* by (DATE)",
            r"(MILESTONE) .* deadline:? (DATE)",
        ]
    }

    async def extract_relations(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relations between entities using pattern matching.

        Args:
            text: Source text
            entities: Extracted entities from NER

        Returns:
            [
                {
                    "relation": "HAS_CONTRACTOR",
                    "subject": {"text": "Gold Tower", "label": "PROJECT"},
                    "object": {"text": "ABC Builders", "label": "CONTRACTOR"}
                },
                ...
            ]
        """
        relations = []

        # Group entities by label
        entity_map = {}
        for ent in entities:
            label = ent["label"]
            if label not in entity_map:
                entity_map[label] = []
            entity_map[label].append(ent)

        # Pattern-based relation extraction
        for relation_type, patterns in self.RELATION_PATTERNS.items():
            for pattern in patterns:
                # Extract entity types from pattern
                # e.g., "(PROJECT) .* (CONTRACTOR)" → ["PROJECT", "CONTRACTOR"]
                entity_types = self._extract_entity_types_from_pattern(pattern)

                # Find entity pairs that match pattern
                pairs = self._find_entity_pairs(text, entity_map, entity_types, pattern)

                for subject, obj in pairs:
                    relations.append({
                        "relation": relation_type,
                        "subject": subject,
                        "object": obj
                    })

        return relations

    def _extract_entity_types_from_pattern(self, pattern: str) -> List[str]:
        """Extract entity types from regex pattern."""
        import re
        matches = re.findall(r"\(([A-Z_|]+)\)", pattern)
        entity_types = []
        for match in matches:
            # Handle OR patterns like "PROJECT|MATERIAL"
            types = match.split("|")
            entity_types.append(types)
        return entity_types

    def _find_entity_pairs(
        self,
        text: str,
        entity_map: Dict[str, List[Dict]],
        entity_types: List[List[str]],
        pattern: str
    ) -> List[Tuple[Dict, Dict]]:
        """Find entity pairs matching pattern."""
        pairs = []

        # Get entities of required types
        subject_entities = []
        for et in entity_types[0]:
            subject_entities.extend(entity_map.get(et, []))

        object_entities = []
        if len(entity_types) > 1:
            for et in entity_types[1]:
                object_entities.extend(entity_map.get(et, []))

        # Check proximity in text (simple heuristic)
        for subj in subject_entities:
            for obj in object_entities:
                # If entities are within 100 characters, consider them related
                if abs(subj["start"] - obj["start"]) < 100:
                    pairs.append((subj, obj))

        return pairs
```

### 4.4 Knowledge Graph Builder

**File:** `backend/app/services/construction_monitor/knowledge_graph_builder.py`

**Purpose:** Build Neo4j knowledge graph from entities and relations

```python
from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any
import os

class KnowledgeGraphBuilder:
    """Build construction project knowledge graph using Neo4j."""

    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def add_entities(
        self,
        entities: List[Dict[str, Any]],
        document_id: str
    ):
        """
        Add entities as nodes to knowledge graph.

        Args:
            entities: Extracted entities
            document_id: Source document ID
        """
        async with self.driver.session() as session:
            for entity in entities:
                label = entity["label"]
                text = entity["text"]

                # Create node with label
                query = f"""
                MERGE (e:{label} {{name: $text}})
                ON CREATE SET e.source = $document_id
                RETURN e
                """

                await session.run(query, text=text, document_id=document_id)

    async def add_relations(
        self,
        relations: List[Dict[str, Any]]
    ):
        """
        Add relations as edges to knowledge graph.

        Args:
            relations: Extracted relations
        """
        async with self.driver.session() as session:
            for rel in relations:
                relation_type = rel["relation"]
                subject = rel["subject"]
                obj = rel["object"]

                # Create relationship
                query = f"""
                MATCH (s:{subject["label"]} {{name: $subject_text}})
                MATCH (o:{obj["label"]} {{name: $object_text}})
                MERGE (s)-[r:{relation_type}]->(o)
                RETURN r
                """

                await session.run(
                    query,
                    subject_text=subject["text"],
                    object_text=obj["text"]
                )

    async def query_graph(
        self,
        cypher_query: str,
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query on knowledge graph.

        Example:
            query = '''
            MATCH (p:PROJECT {name: $project_name})-[:HAS_CONTRACTOR]->(c:CONTRACTOR)
            RETURN c.name as contractor
            '''
            results = await kg.query_graph(query, {"project_name": "Gold Tower"})
        """
        async with self.driver.session() as session:
            result = await session.run(cypher_query, parameters or {})
            return [record.data() async for record in result]

    async def close(self):
        """Close Neo4j connection."""
        await self.driver.close()
```

### 4.5 Construction Q&A Service

**File:** `backend/app/services/construction_monitor/construction_qa_service.py`

**Purpose:** Answer questions using entities + knowledge graph

```python
from typing import Dict, Any, List

class ConstructionQAService:
    """Answer questions about construction projects using NER + Knowledge Graph."""

    def __init__(
        self,
        ner_service,
        kg_builder,
        retrieval_service,
        llm_service
    ):
        self.ner = ner_service
        self.kg = kg_builder
        self.retrieval = retrieval_service
        self.llm = llm_service

    async def answer_question(
        self,
        question: str,
        project_id: str = None
    ) -> Dict[str, Any]:
        """
        Answer question using hybrid approach:
        1. Extract entities from question
        2. Query knowledge graph for structured data
        3. Semantic search for context
        4. LLM synthesis

        Returns:
            {
                "answer": str,
                "entities_found": List[dict],
                "graph_results": List[dict],
                "sources": List[dict]
            }
        """
        # 1. Extract entities from question
        entities = await self.ner.extract_entities(question)

        # 2. Build Cypher query for knowledge graph
        cypher_query = self._build_cypher_query(question, entities)

        graph_results = []
        if cypher_query:
            graph_results = await self.kg.query_graph(cypher_query)

        # 3. Semantic search for additional context
        semantic_results = await self.retrieval.search(
            query=question,
            collection="construction_documents",
            top_k=5
        )

        # 4. LLM synthesis
        context = self._build_context(graph_results, semantic_results)

        prompt = f"""Answer this question about a construction project:

Question: {question}

Knowledge Graph Data:
{graph_results}

Document Context:
{context}

Provide a concise answer with specific details (names, dates, numbers)."""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        return {
            "answer": response["content"],
            "entities_found": entities,
            "graph_results": graph_results,
            "sources": [r.get("metadata", {}) for r in semantic_results]
        }

    def _build_cypher_query(
        self,
        question: str,
        entities: List[Dict[str, Any]]
    ) -> str:
        """Build Cypher query based on question and entities."""
        # Simple heuristic-based query generation
        question_lower = question.lower()

        if "contractor" in question_lower:
            # Find contractors for a project
            project_entities = [e for e in entities if e["label"] == "PROJECT"]
            if project_entities:
                project_name = project_entities[0]["text"]
                return f"""
                MATCH (p:PROJECT {{name: '{project_name}'}})-[:HAS_CONTRACTOR]->(c:CONTRACTOR)
                RETURN c.name as contractor
                """

        elif "material" in question_lower:
            # Find materials used
            project_entities = [e for e in entities if e["label"] == "PROJECT"]
            if project_entities:
                project_name = project_entities[0]["text"]
                return f"""
                MATCH (p:PROJECT {{name: '{project_name}'}})-[:USES_MATERIAL]->(m:MATERIAL)
                RETURN m.name as material
                """

        return None

    def _build_context(
        self,
        graph_results: List[Dict],
        semantic_results: List[Dict]
    ) -> str:
        """Combine graph + semantic results into context string."""
        context_parts = []

        if graph_results:
            context_parts.append("Structured Data:")
            for result in graph_results:
                context_parts.append(str(result))

        if semantic_results:
            context_parts.append("\nDocument Excerpts:")
            for result in semantic_results:
                context_parts.append(result["content"])

        return "\n".join(context_parts)
```

---

## 5. Data Flow

### 5.1 Document Processing Flow

```
CONSTRUCTION DOCUMENT UPLOAD
  ↓
TEXT EXTRACTION (Docling)
  ├─ Text content
  └─ Tables
  ↓
CUSTOM NER (SpaCy)
  └─ Extract 8 entity types
  ↓
RELATION EXTRACTION
  └─ Link entities with 6 relation types
  ↓
KNOWLEDGE GRAPH STORAGE (Neo4j)
  ├─ Entities → Nodes
  └─ Relations → Edges
  ↓
DUAL INDEXING (PARALLEL)
  ├─ ChromaDB: Semantic search
  └─ Elasticsearch: Keyword search
```

### 5.2 Q&A Flow

```
USER QUESTION: "Which contractors are working on Highway 101?"
  ↓
NER ON QUESTION
  └─ Extract: PROJECT="Highway 101", entity type hint="CONTRACTOR"
  ↓
KNOWLEDGE GRAPH QUERY (Cypher)
  └─ MATCH (p:PROJECT {name: "Highway 101"})-[:HAS_CONTRACTOR]->(c)
  └─ RETURN c.name
  ↓
SEMANTIC SEARCH (backup)
  └─ ChromaDB search for context
  ↓
LLM SYNTHESIS
  └─ Combine graph data + semantic context
  ↓
ANSWER: "ABC Builders Inc. and XYZ Steel"
```

---

## 6. API Endpoints

### 6.1 Upload Construction Document

```http
POST /api/v1/construction-monitor/documents/upload
Content-Type: multipart/form-data

{
  "file": <construction_doc.pdf>,
  "project_id": "highway-101"
}

Response:
{
  "document_id": "uuid-here",
  "status": "processing"
}
```

### 6.2 Extract Entities

```http
POST /api/v1/construction-monitor/documents/{document_id}/extract

Response:
{
  "document_id": "uuid-here",
  "entities": [
    {"text": "ABC Builders Inc.", "label": "CONTRACTOR"},
    {"text": "500 cubic yards", "label": "QUANTITY"},
    ...
  ],
  "relations": [
    {
      "relation": "HAS_CONTRACTOR",
      "subject": {"text": "Highway 101", "label": "PROJECT"},
      "object": {"text": "ABC Builders", "label": "CONTRACTOR"}
    },
    ...
  ]
}
```

### 6.3 Query Knowledge Graph

```http
POST /api/v1/construction-monitor/graph/query
Content-Type: application/json

{
  "cypher_query": "MATCH (p:PROJECT)-[:HAS_CONTRACTOR]->(c) RETURN p.name, c.name",
  "parameters": {}
}

Response:
{
  "results": [
    {"p.name": "Highway 101", "c.name": "ABC Builders"},
    ...
  ]
}
```

### 6.4 Q&A

```http
POST /api/v1/construction-monitor/qa
Content-Type: application/json

{
  "question": "Which contractors are working on Highway 101?",
  "project_id": "highway-101"
}

Response:
{
  "answer": "ABC Builders Inc. (general contractor) and XYZ Steel (steel supplier)",
  "entities_found": [...],
  "graph_results": [...],
  "sources": [...]
}
```

---

## 7. Database Schema

```sql
-- Construction projects
CREATE TABLE construction_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name TEXT NOT NULL,
    location TEXT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Extracted entities
CREATE TABLE construction_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    entity_text TEXT NOT NULL,
    entity_label TEXT NOT NULL,
    start_pos INT,
    end_pos INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Extracted relations
CREATE TABLE construction_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    relation_type TEXT NOT NULL,
    subject_entity_id UUID REFERENCES construction_entities(id),
    object_entity_id UUID REFERENCES construction_entities(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_entities_label ON construction_entities(entity_label);
CREATE INDEX idx_relations_type ON construction_relations(relation_type);
```

---

## 8. Frontend UI

**File:** `frontend/src/components/ConstructionMonitorKnowledgeGraph.tsx`

```typescript
export const KnowledgeGraphViewer: React.FC = () => {
  const [graph, setGraph] = useState<GraphData | null>(null);

  return (
    <div className="knowledge-graph-container">
      <ForceGraph2D
        graphData={graph}
        nodeLabel="name"
        nodeColor={(node) => getNodeColor(node.label)}
        linkDirectionalArrowLength={3.5}
      />
    </div>
  );
};
```

---

## 9. Testing Strategy

```python
# tests/services/construction_monitor/test_ner.py
async def test_ner_extracts_contractor():
    ner = ConstructionNERService()

    text = "ABC Builders Inc. will construct the project"
    entities = await ner.extract_entities(text)

    contractors = [e for e in entities if e["label"] == "CONTRACTOR"]
    assert len(contractors) == 1
    assert contractors[0]["text"] == "ABC Builders Inc."
```

---

## 10. Deployment

### 10.1 Add Neo4j to docker-compose.yml

```yaml
services:
  neo4j:
    image: neo4j:5.15
    environment:
      - NEO4J_AUTH=neo4j/password
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
    networks:
      - app_network

volumes:
  neo4j_data:
```

### 10.2 Environment Variables

```bash
# Construction Monitor Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
CONSTRUCTION_NER_MODEL_PATH=/models/construction_ner
```

---

## 11. Timeline

### Week 1: NER Model Training (Jan 2-8, 2026)
- Collect training data
- Annotate construction entities
- Train SpaCy NER model

### Week 2: Relation Extraction (Jan 9-15, 2026)
- Pattern-based REL
- Knowledge graph builder

### Week 3: Neo4j Integration (Jan 16-22, 2026)
- Set up Neo4j
- Entity + relation storage
- Cypher queries

### Week 4-5: Q&A + Testing (Jan 23-Feb 5, 2026)
- Construction Q&A service
- Frontend knowledge graph viewer
- Testing + deployment

**Total: 5 weeks**

---

## 12. Success Criteria

- [ ] Custom NER model achieves >90% F1 score
- [ ] Relation extraction achieves >85% F1 score
- [ ] Knowledge graph contains >1000 nodes
- [ ] Q&A response time <5 seconds
- [ ] Frontend knowledge graph visualization working

---

**Status:** Ready for implementation
**Dependencies:** Infrastructure (Elasticsearch), Neo4j, SpaCy
**Reuse:** 50% from core platform + infrastructure
