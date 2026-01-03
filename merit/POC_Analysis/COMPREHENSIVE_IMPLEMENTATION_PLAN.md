# Comprehensive Leveraged Implementation Plan
## 23 Merit AIML POCs → Tier 2 Enterprise Platform Integration

> **Last Updated**: 2026-01-02
> **Author**: AI Assistant
> **Purpose**: Actionable implementation plan leveraging existing Tier 1 stack for all 23 POCs

---

## Executive Summary

This plan outlines a **5-phase, 22-week implementation strategy** to integrate all 23 Merit AIML POC prototypes into the existing Tier 1 enterprise platform, maximizing component reuse (**77% average reusability**) and minimizing development effort.

### Key Metrics

| Metric | Value |
|--------|-------|
| **Total POCs** | 23 |
| **Implementation Duration** | 22 weeks (5.5 months) |
| **Team Size** | 4 developers |
| **New Tier 1 Services** | 6 services |
| **Average Component Reuse** | 77% |
| **Estimated Cost Savings** | 60% vs. from-scratch development |

### Strategic Approach

✅ **Leverage First**: Use existing Tier 1 services (LLM, Embedding, RAG, Document, Export)
✅ **Build Minimal**: Only create POC-specific business logic
✅ **Standardize**: Unified patterns for services, routes, schemas, and frontend components
✅ **Iterate Fast**: Start with high-reusability POCs for quick wins

---

## Table of Contents

1. [Phase 0: Prerequisites](#phase-0-prerequisites-week-0)
2. [Phase 1: Infrastructure](#phase-1-infrastructure-weeks-1-4)
3. [Phase 2: Quick Wins](#phase-2-quick-wins-weeks-5-8)
4. [Phase 3: Medium Complexity](#phase-3-medium-complexity-weeks-9-14)
5. [Phase 4: Complex POCs](#phase-4-complex-pocs-weeks-15-20)
6. [Phase 5: Integration & Launch](#phase-5-integration--launch-weeks-21-22)
7. [POC Implementation Guides](#poc-implementation-guides)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Strategy](#deployment-strategy)

---

## Phase 0: Prerequisites (Week 0)

### Setup & Validation

**Objectives**:
- Validate existing Tier 1 stack
- Set up development environment
- Create implementation templates

**Tasks**:

| # | Task | Owner | Duration |
|---|------|-------|----------|
| 1 | **Environment Setup** | DevOps | 1 day |
| | - Clone repository | | |
| | - Verify Docker Compose stack | | |
| | - Test database migrations | | |
| | - Validate services health | | |
| 2 | **Tier 1 Service Validation** | Backend Lead | 2 days |
| | - Test LLMService (all providers) | | |
| | - Test EmbeddingService | | |
| | - Test RAGService | | |
| | - Test DocumentService | | |
| | - Test ExportService | | |
| | - Test ScraperService | | |
| 3 | **Template Creation** | Full Stack Dev | 2 days |
| | - POC service template | | |
| | - POC route template | | |
| | - POC schema template | | |
| | - Frontend component template | | |
| | - Database migration template | | |

**Deliverables**:
- ✅ All Tier 1 services operational
- ✅ Development environment ready
- ✅ Implementation templates in `backend/app/tier_2/_templates/`
- ✅ Documentation reviewed

---

## Phase 1: Infrastructure (Weeks 1-4)

### Build New Tier 1 Services

**Objectives**:
- Create 6 new Tier 1 services to support all POCs
- Ensure services are reusable across multiple POCs
- Maintain >80% test coverage

### Week 1-2: ML Model Service

**Service**: `backend/app/tier_1/ml_models/ml_model_service.py`

**Requirements**:
- Scikit-learn model hosting (RandomForest, GradientBoosting, Logistic Regression)
- Model training, persistence, versioning
- Prediction API
- MinIO integration for model storage
- PostgreSQL metadata storage

**Implementation**:

```python
# File: backend/app/tier_1/ml_models/ml_model_service.py

import joblib
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sqlalchemy.orm import Session
import uuid
from app.tier_1.infrastructure.config import settings
from app.tier_1.infrastructure.minio_path_builder import MinIOPathBuilder

class MLModelService:
    """Service for hosting and serving Scikit-learn ML models"""

    def __init__(self, db: Session):
        self.db = db
        self.minio_client = MinIOPathBuilder().get_client()
        self.models_cache: Dict[str, Any] = {}

    async def train_model(
        self,
        model_type: str,  # "random_forest", "gradient_boosting", "logistic_regression"
        X_train: np.ndarray,
        y_train: np.ndarray,
        hyperparameters: Optional[Dict[str, Any]] = None,
        model_name: str = None
    ) -> str:
        """Train a new ML model"""

        # Create model instance
        if model_type == "random_forest":
            model = RandomForestClassifier(**(hyperparameters or {}))
        elif model_type == "gradient_boosting":
            model = GradientBoostingClassifier(**(hyperparameters or {}))
        elif model_type == "logistic_regression":
            model = LogisticRegression(**(hyperparameters or {}))
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        # Train model
        model.fit(X_train, y_train)

        # Save model
        model_id = str(uuid.uuid4())
        model_path = f"ml_models/{model_name or model_id}.joblib"

        # Save to MinIO
        joblib.dump(model, f"/tmp/{model_id}.joblib")
        self.minio_client.fput_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=model_path,
            file_path=f"/tmp/{model_id}.joblib"
        )

        # Save metadata to DB
        from app.models.ml_models import MLModel
        db_model = MLModel(
            id=uuid.UUID(model_id),
            name=model_name or model_id,
            model_type=model_type,
            model_path=model_path,
            hyperparameters=hyperparameters,
            status="trained"
        )
        self.db.add(db_model)
        self.db.commit()

        return model_id

    async def predict(
        self,
        model_id: str,
        features: List[List[float]]
    ) -> List[Any]:
        """Make predictions using a trained model"""

        # Load model from cache or MinIO
        if model_id not in self.models_cache:
            model = await self._load_model(model_id)
            self.models_cache[model_id] = model
        else:
            model = self.models_cache[model_id]

        # Make predictions
        X = np.array(features)
        predictions = model.predict(X)
        probabilities = model.predict_proba(X) if hasattr(model, "predict_proba") else None

        return {
            "predictions": predictions.tolist(),
            "probabilities": probabilities.tolist() if probabilities is not None else None
        }

    async def _load_model(self, model_id: str) -> Any:
        """Load model from MinIO"""
        from app.models.ml_models import MLModel

        db_model = self.db.query(MLModel).filter(MLModel.id == uuid.UUID(model_id)).first()
        if not db_model:
            raise ValueError(f"Model not found: {model_id}")

        # Download from MinIO
        self.minio_client.fget_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=db_model.model_path,
            file_path=f"/tmp/{model_id}.joblib"
        )

        # Load model
        model = joblib.load(f"/tmp/{model_id}.joblib")
        return model

    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get model metadata"""
        from app.models.ml_models import MLModel

        db_model = self.db.query(MLModel).filter(MLModel.id == uuid.UUID(model_id)).first()
        if not db_model:
            raise ValueError(f"Model not found: {model_id}")

        return {
            "id": str(db_model.id),
            "name": db_model.name,
            "model_type": db_model.model_type,
            "hyperparameters": db_model.hyperparameters,
            "status": db_model.status,
            "created_at": db_model.created_at.isoformat()
        }
```

**Database Migration**:

```sql
-- File: backend/migrations/025_ml_models.sql

CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- random_forest, gradient_boosting, etc.
    model_path VARCHAR(512) NOT NULL,  -- MinIO path
    hyperparameters JSONB,
    status VARCHAR(50) DEFAULT 'trained',  -- training, trained, failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ml_models_name ON ml_models(name);
CREATE INDEX idx_ml_models_type ON ml_models(model_type);
```

**API Routes**:

```python
# File: backend/app/api/routes/ml_model_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.database import get_db
from app.tier_1.ml_models.ml_model_service import MLModelService

router = APIRouter(prefix="/api/v1/ml", tags=["Machine Learning"])

@router.post("/train")
async def train_model(request: TrainModelRequest, db: Session = Depends(get_db)):
    service = MLModelService(db)
    model_id = await service.train_model(
        model_type=request.model_type,
        X_train=request.training_data,
        y_train=request.labels,
        hyperparameters=request.hyperparameters,
        model_name=request.model_name
    )
    return {"model_id": model_id}

@router.post("/predict")
async def predict(request: PredictRequest, db: Session = Depends(get_db)):
    service = MLModelService(db)
    result = await service.predict(
        model_id=request.model_id,
        features=request.features
    )
    return result

@router.get("/models/{model_id}")
async def get_model_info(model_id: str, db: Session = Depends(get_db)):
    service = MLModelService(db)
    return await service.get_model_info(model_id)
```

**POCs Using**: Agronomy Decision, Bot Detect, Email Bounce Intelligence, Email Campaign, Planning Classifier

**Effort**: 10 days (2 weeks)

---

### Week 2: Vision Service

**Service**: `backend/app/tier_1/llm/vision_service.py`

**Requirements**:
- GPT-4 Vision API integration
- Image-to-text description
- Attribute extraction from images
- Batch processing

**Implementation**:

```python
# File: backend/app/tier_1/llm/vision_service.py

import base64
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from app.tier_1.infrastructure.config import settings
import logging

logger = logging.getLogger(__name__)

class VisionService:
    """GPT-4 Vision service for image analysis"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: str = "gpt-4o",
        max_tokens: int = 500
    ) -> str:
        """Analyze a single image"""

        # Encode image to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Call GPT-4 Vision API
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    async def extract_attributes(
        self,
        image_path: str,
        attribute_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract structured attributes from image"""

        # Build prompt from schema
        prompt = self._build_extraction_prompt(attribute_schema)

        # Analyze image
        result = await self.analyze_image(image_path, prompt)

        # Parse JSON response
        import json
        try:
            attributes = json.loads(result.strip())
            return attributes
        except json.JSONDecodeError:
            logger.error(f"Failed to parse vision response: {result}")
            return {}

    def _build_extraction_prompt(self, schema: Dict[str, Any]) -> str:
        """Build extraction prompt from schema"""
        fields = "\n".join([f"- {field}: {details.get('description', '')}"
                            for field, details in schema.items()])

        prompt = f"""Analyze this image and extract the following attributes:

{fields}

Return ONLY valid JSON with these exact field names. If an attribute is not visible or applicable, use null.

Example output format:
{{
    "field1": "value1",
    "field2": ["value2a", "value2b"],
    "field3": null
}}
"""
        return prompt

    async def batch_analyze(
        self,
        image_paths: List[str],
        prompt: str
    ) -> List[str]:
        """Analyze multiple images"""
        import asyncio

        tasks = [self.analyze_image(path, prompt) for path in image_paths]
        results = await asyncio.gather(*tasks)
        return results
```

**POCs Using**: Fashion Tagging

**Effort**: 3 days (0.5 week)

---

### Week 3: Template Engine Service

**Service**: `backend/app/tier_1/export/template_engine_service.py`

**Requirements**:
- Jinja2 template rendering
- DOCX generation (python-docx + docxtpl)
- PDF generation (WeasyPrint)
- Template management (CRUD)

**Implementation**:

```python
# File: backend/app/tier_1/export/template_engine_service.py

from jinja2 import Environment, FileSystemLoader, Template
from docxtpl import DocxTemplate
from weasyprint import HTML
from typing import Dict, Any, Optional
import os
from app.tier_1.infrastructure.config import settings
from app.tier_1.infrastructure.minio_path_builder import MinIOPathBuilder
import uuid

class TemplateEngineService:
    """Service for template-based document generation"""

    def __init__(self):
        self.template_dir = os.path.join(settings.BASE_DIR, "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_dir))
        self.minio_client = MinIOPathBuilder().get_client()

    async def render_docx(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_filename: Optional[str] = None
    ) -> str:
        """Render DOCX from Jinja2 template"""

        template_path = os.path.join(self.template_dir, f"{template_name}.docx")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_name}.docx")

        # Load template
        doc = DocxTemplate(template_path)

        # Render with context
        doc.render(context)

        # Save to temp file
        output_filename = output_filename or f"{uuid.uuid4()}.docx"
        output_path = f"/tmp/{output_filename}"
        doc.save(output_path)

        # Upload to MinIO
        minio_path = f"exports/{output_filename}"
        self.minio_client.fput_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=minio_path,
            file_path=output_path
        )

        return minio_path

    async def render_pdf(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_filename: Optional[str] = None
    ) -> str:
        """Render PDF from HTML template"""

        # Render HTML from Jinja2 template
        template = self.jinja_env.get_template(f"{template_name}.html")
        html_content = template.render(context)

        # Convert HTML to PDF
        output_filename = output_filename or f"{uuid.uuid4()}.pdf"
        output_path = f"/tmp/{output_filename}"
        HTML(string=html_content).write_pdf(output_path)

        # Upload to MinIO
        minio_path = f"exports/{output_filename}"
        self.minio_client.fput_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=minio_path,
            file_path=output_path
        )

        return minio_path

    async def save_template(
        self,
        template_name: str,
        template_content: bytes,
        template_type: str  # "docx" or "html"
    ) -> str:
        """Save a new template"""

        extension = "docx" if template_type == "docx" else "html"
        template_path = os.path.join(self.template_dir, f"{template_name}.{extension}")

        with open(template_path, "wb") as f:
            f.write(template_content)

        return template_name

    async def list_templates(self) -> List[str]:
        """List available templates"""

        templates = []
        for filename in os.listdir(self.template_dir):
            if filename.endswith((".docx", ".html")):
                templates.append(os.path.splitext(filename)[0])

        return templates
```

**POCs Using**: Credit Profile Analyzer, Maritime Report Generation

**Effort**: 4 days (0.5 week)

---

### Week 3: Email Parser Service

**Service**: `backend/app/tier_1/data_extraction/email_parser_service.py`

**Requirements**:
- MIME message parsing
- Bounce classification (hard/soft/transient)
- Header extraction
- Attachment handling

**Implementation**:

```python
# File: backend/app/tier_1/data_extraction/email_parser_service.py

import email
from email import policy
from email.parser import BytesParser
from typing import Dict, List, Any, Optional
import re
from dataclasses import dataclass

@dataclass
class BounceClassification:
    category: str  # "hard", "soft", "transient"
    subcategory: str
    confidence: float
    reason: str

class EmailParserService:
    """Service for parsing and analyzing email messages"""

    HARD_BOUNCE_PATTERNS = [
        r"user unknown",
        r"mailbox not found",
        r"no such user",
        r"invalid recipient",
        r"address rejected",
        r"recipient address rejected"
    ]

    SOFT_BOUNCE_PATTERNS = [
        r"mailbox full",
        r"quota exceeded",
        r"over quota",
        r"mailbox is full"
    ]

    TRANSIENT_PATTERNS = [
        r"temporarily unavailable",
        r"try again later",
        r"deferred",
        r"connection timed out"
    ]

    def parse_mime(self, raw_email: bytes) -> Dict[str, Any]:
        """Parse MIME email message"""

        msg = BytesParser(policy=policy.default).parsebytes(raw_email)

        return {
            "subject": msg.get("Subject", ""),
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "date": msg.get("Date", ""),
            "message_id": msg.get("Message-ID", ""),
            "body": self._extract_body(msg),
            "headers": dict(msg.items()),
            "attachments": self._extract_attachments(msg)
        }

    def classify_bounce(self, email_body: str, headers: Dict[str, str]) -> BounceClassification:
        """Classify email bounce type"""

        text = email_body.lower()

        # Check for hard bounces
        for pattern in self.HARD_BOUNCE_PATTERNS:
            if re.search(pattern, text):
                return BounceClassification(
                    category="hard",
                    subcategory="invalid_address",
                    confidence=0.9,
                    reason=f"Matched pattern: {pattern}"
                )

        # Check for soft bounces
        for pattern in self.SOFT_BOUNCE_PATTERNS:
            if re.search(pattern, text):
                return BounceClassification(
                    category="soft",
                    subcategory="mailbox_full",
                    confidence=0.85,
                    reason=f"Matched pattern: {pattern}"
                )

        # Check for transient
        for pattern in self.TRANSIENT_PATTERNS:
            if re.search(pattern, text):
                return BounceClassification(
                    category="transient",
                    subcategory="temporary_failure",
                    confidence=0.8,
                    reason=f"Matched pattern: {pattern}"
                )

        return BounceClassification(
            category="unknown",
            subcategory="unclassified",
            confidence=0.5,
            reason="No matching patterns"
        )

    def _extract_body(self, msg) -> str:
        """Extract email body"""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_content()
        else:
            return msg.get_content()
        return ""

    def _extract_attachments(self, msg) -> List[Dict[str, Any]]:
        """Extract attachment metadata"""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    attachments.append({
                        "filename": part.get_filename(),
                        "content_type": part.get_content_type(),
                        "size": len(part.get_content())
                    })
        return attachments
```

**POCs Using**: Email Bounce Intelligence, Email Campaign Analyzer

**Effort**: 3 days (0.5 week)

---

### Week 4: OpenAI Embeddings + Reference Data Service

**Enhancements**:

1. **OpenAI Embeddings** (2 days):
```python
# Add to backend/app/tier_1/embeddings/embedding_service.py

async def generate_embedding_openai(self, text: str) -> List[float]:
    """Generate OpenAI embeddings"""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )

    return response.data[0].embedding  # 1536 dimensions
```

2. **Reference Data Service** (3 days):
```python
# File: backend/app/tier_1/platform_services/reference_data_service.py

class ReferenceDataService:
    """Manage reference datasets (companies, commodities, assets)"""

    async def get_companies(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get company reference data"""

    async def get_commodities(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get commodity reference data"""

    async def add_reference_data(self, data_type: str, records: List[Dict]):
        """Bulk import reference data"""
```

**Effort**: 5 days (1 week)

---

### Phase 1 Summary

**Deliverables**:
- ✅ MLModelService (Scikit-learn hosting)
- ✅ VisionService (GPT-4 Vision)
- ✅ TemplateEngineService (Jinja2 + DOCX/PDF)
- ✅ EmailParserService (MIME parsing)
- ✅ OpenAI embeddings support
- ✅ ReferenceDataService (master data)
- ✅ Database migrations (ml_models, reference tables)
- ✅ API routes for all services
- ✅ Unit tests (>80% coverage)
- ✅ Integration tests
- ✅ API documentation

**Effort**: 4 weeks (25 developer-days)

**Team**: 2 backend developers

---

## Phase 2: Quick Wins (Weeks 5-8)

### Implement 8 High-Reusability POCs

**Strategy**: Start with POCs that have 75-90% reusability to deliver quick value and validate patterns

### Week 5: Generic RAG (90% Reusability)

**POC**: #10 - Generic RAG

**Implementation**:

1. **Backend Service**: `backend/app/tier_2/document_intelligence/generic_rag_service.py`

```python
from app.tier_1.rag.rag_service import RAGService
from app.tier_1.document_processing.document_service import document_service
from sqlalchemy.orm import Session

class GenericRAGService:
    """Generic RAG query service - leverages Tier 1 RAGService"""

    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService()  # ✅ Reuse Tier 1

    async def query(self, query_text: str, session_id: str, top_k: int = 5):
        """Execute RAG query"""

        # ✅ Direct delegation to Tier 1
        result = await self.rag_service.query(
            query_text=query_text,
            session_id=session_id,
            top_k=top_k
        )

        # Store query log (POC-specific)
        await self._log_query(session_id, query_text, result)

        return result

    async def _log_query(self, session_id: str, query: str, result: Dict):
        """Log RAG query"""
        from app.models.poc_results import POCResult

        poc_result = POCResult(
            poc_name="generic_rag",
            session_id=session_id,
            input_data={"query": query},
            output_data=result
        )
        self.db.add(poc_result)
        self.db.commit()
```

2. **API Route**: `backend/app/tier_2/document_intelligence/generic_rag_routes.py` (already exists - validate)

3. **Frontend Component**: `frontend/src/components/GenericRAGPanel.tsx`

```typescript
export const GenericRAGPanel: React.FC = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    setLoading(true);
    try {
      const response = await axios.post("/api/v2/document-intelligence/generic-rag/query", {
        query_text: query,
        session_id: sessionStorage.getItem("sessionId"),
        top_k: 5
      });
      setResults(response.data);
    } catch (error) {
      console.error("Query failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Generic RAG Query</h2>
      <textarea
        className="w-full p-2 border rounded"
        rows={4}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your question..."
      />
      <button onClick={handleQuery} disabled={loading}>
        {loading ? "Querying..." : "Submit Query"}
      </button>
      {results && <ExtractionResults results={results} />}
    </div>
  );
};
```

**Effort**: 2 days

---

### Week 5: Docu Extract (85% Reusability)

**POC**: #6 - Document Extraction (Planning Documents)

**Implementation**: Similar pattern to Generic RAG

```python
class DocuExtractService:
    """Extract entities from planning documents"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()  # ✅ Reuse Tier 1
        self.document_service = document_service  # ✅ Reuse Tier 1

    async def extract_entities(self, document_id: str):
        """Extract entities from planning document"""

        # Get document content
        chunks = await self.document_service.get_document_chunks(document_id)
        full_text = " ".join([chunk.content for chunk in chunks])

        # Extract using LLM
        prompt = self._build_extraction_prompt(full_text)
        result = await self.llm_service.generate_response(
            prompt=prompt,
            model="gpt-4o-mini",
            temperature=0.0
        )

        # Parse and store
        entities = json.loads(result)
        await self._store_extraction(document_id, entities)

        return entities

    def _build_extraction_prompt(self, text: str) -> str:
        return f"""Extract the following entities from this planning document:

Document:
{text}

Extract:
- Applicant name
- Application number
- Project address
- Development type
- Planning status
- Decision date

Return ONLY valid JSON."""
```

**Effort**: 3 days

---

### Week 6: Relation Extractor (85%) + Procurement Matcher (85%)

**Similar implementation patterns** - leverage LLMService + RAGService

**Effort**: 4 days each = 8 days total

---

### Week 7: Taxonomy Classification (80%) + Tender Intelligence (80%)

**Effort**: 5 days each = 10 days total

---

### Week 8: Talent Pulse (75%) + Planning Classifier (75%)

**Effort**: 5 days each = 10 days total

---

### Phase 2 Summary

**POCs Delivered**:
1. ✅ Generic RAG
2. ✅ Docu Extract
3. ✅ Relation Extractor
4. ✅ Procurement Matcher
5. ✅ Taxonomy Classification
6. ✅ Tender Intelligence
7. ✅ Talent Pulse
8. ✅ Planning Classifier

**Effort**: 4 weeks (47 developer-days)

**Team**: 2 developers

---

## Phase 3: Medium Complexity (Weeks 9-14)

### 7 Medium-Reusability POCs

**POCs**: Agri Taxonomy, MineScope CRU, Maritime Report, Credit Profile, Talent Search, Vendor Recommendation, Zero Shot NER

**Effort**: 6 weeks (45 developer-days)

**Team**: 2 developers

---

## Phase 4: Complex POCs (Weeks 15-20)

### 6 Low-Reusability POCs

**POCs**: Agronomy Decision (3 modules), Spend Smart, Fashion Tagging, Email Bounce, Email Campaign, Bot Detect

**Special Requirements**:
- Week 16-17: Neo4j setup for Spend Smart
- Week 18: Vision service integration for Fashion Tagging
- Weeks 19-20: ML model training for email/bot detection

**Effort**: 6 weeks (54 developer-days)

**Team**: 2 developers

---

## Phase 5: Integration & Launch (Weeks 21-22)

### Central Dashboard + System Integration

**Week 21**: Dashboard Development

**Components**:
1. Backend aggregation API
2. Frontend dashboard (module grid)
3. User role management
4. Analytics integration

**Week 22**: Testing & Launch

**Tasks**:
1. End-to-end testing (all 23 POCs)
2. Performance optimization
3. Security audit
4. Documentation finalization
5. User training
6. Production deployment

**Effort**: 2 weeks (20 developer-days)

**Team**: 4 developers (full team)

---

## POC Implementation Guides

### Standard Implementation Pattern

Each POC follows this structure:

```
backend/app/tier_2/{category}/{poc_name}/
├── {poc_name}_service.py      # Business logic
├── {poc_name}_routes.py        # API endpoints
├── {poc_name}_schemas.py       # Pydantic models
└── __init__.py

frontend/src/components/
└── {POCName}Panel.tsx          # React component

backend/migrations/
└── 026_{poc_name}_tables.sql   # Database schema
```

### Service Template

```python
# backend/app/tier_2/{category}/{poc_name}_service.py

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.embeddings.embedding_service import embedding_service
from app.tier_1.rag.rag_service import RAGService
from app.tier_1.infrastructure.config import settings
import logging

logger = logging.getLogger(__name__)

class {POCName}Service:
    """Service for {POC description}"""

    def __init__(self, db: Session):
        self.db = db
        # ✅ Inject Tier 1 services
        self.llm_service = LLMService()
        self.rag_service = RAGService()
        # Add others as needed

    async def process(self, request: {POCName}Request) -> {POCName}Response:
        """Main processing logic"""

        # 1. Pre-processing
        input_data = self._preprocess(request)

        # 2. Core logic (LLM, RAG, etc.)
        result = await self._execute_core_logic(input_data)

        # 3. Post-processing
        output = self._postprocess(result)

        # 4. Store results
        await self._store_results(request, output)

        return output

    def _preprocess(self, request):
        """POC-specific preprocessing"""
        pass

    async def _execute_core_logic(self, data):
        """Core business logic - leverage Tier 1 services"""
        pass

    def _postprocess(self, result):
        """POC-specific postprocessing"""
        pass

    async def _store_results(self, request, output):
        """Store to database"""
        from app.models.poc_results import POCResult

        poc_result = POCResult(
            poc_name="{poc_name}",
            session_id=request.session_id,
            input_data=request.dict(),
            output_data=output
        )
        self.db.add(poc_result)
        self.db.commit()
```

### Route Template

```python
# backend/app/tier_2/{category}/{poc_name}_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.database import get_db
from .{poc_name}_service import {POCName}Service
from .{poc_name}_schemas import {POCName}Request, {POCName}Response

router = APIRouter(
    prefix="/api/v2/{category}/{poc-name}",
    tags=["{POC Name}"]
)

@router.post("/process", response_model={POCName}Response)
async def process_{poc_name}(
    request: {POCName}Request,
    db: Session = Depends(get_db)
):
    """Process {POC name} request"""
    service = {POCName}Service(db)
    return await service.process(request)

@router.get("/results/{session_id}")
async def get_results(session_id: str, db: Session = Depends(get_db)):
    """Get historical results"""
    from app.models.poc_results import POCResult

    results = db.query(POCResult).filter(
        POCResult.poc_name == "{poc_name}",
        POCResult.session_id == session_id
    ).all()

    return results
```

### Frontend Component Template

```typescript
// frontend/src/components/{POCName}Panel.tsx

import React, { useState } from 'react';
import axios from 'axios';
import { ExtractionResults } from './ExtractionResults';

interface {POCName}Request {
  // Define request fields
}

interface {POCName}Response {
  // Define response fields
}

export const {POCName}Panel: React.FC = () => {
  const [input, setInput] = useState<{POCName}Request>({});
  const [results, setResults] = useState<{POCName}Response | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post<{POCName}Response>(
        '/api/v2/{category}/{poc-name}/process',
        {
          ...input,
          session_id: sessionStorage.getItem('sessionId')
        }
      );
      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Processing failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">{POC Display Name}</h2>

      {/* Input form */}
      <div className="mb-4">
        {/* Add input fields */}
      </div>

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {loading ? 'Processing...' : 'Submit'}
      </button>

      {/* Error display */}
      {error && (
        <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Results display */}
      {results && (
        <div className="mt-6">
          <ExtractionResults results={results} />
        </div>
      )}
    </div>
  );
};
```

---

## Testing Strategy

### Unit Tests

**Requirements**: >80% coverage for all services

**Pattern**:
```python
# backend/tests/tier_2/test_{poc_name}_service.py

import pytest
from app.tier_2.{category}.{poc_name}_service import {POCName}Service
from app.tier_2.{category}.{poc_name}_schemas import {POCName}Request

@pytest.fixture
def service(db_session):
    return {POCName}Service(db_session)

@pytest.mark.asyncio
async def test_process_success(service):
    request = {POCName}Request(
        # Test data
    )

    result = await service.process(request)

    assert result is not None
    assert hasattr(result, 'expected_field')

@pytest.mark.asyncio
async def test_process_invalid_input(service):
    request = {POCName}Request(
        # Invalid data
    )

    with pytest.raises(ValueError):
        await service.process(request)
```

### Integration Tests

**Test end-to-end flows**:
```python
# backend/tests/integration/test_{poc_name}_integration.py

@pytest.mark.integration
async def test_{poc_name}_full_flow(client, db_session):
    # 1. Upload document (if needed)
    # 2. Call processing endpoint
    # 3. Verify results
    # 4. Check database records

    response = client.post("/api/v2/{category}/{poc-name}/process", json={...})

    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### Frontend Tests

**Jest + React Testing Library**:
```typescript
// frontend/src/components/__tests__/{POCName}Panel.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { {POCName}Panel } from '../{POCName}Panel';

test('renders POC panel', () => {
  render(<{POCName}Panel />);
  expect(screen.getByText('{POC Display Name}')).toBeInTheDocument();
});

test('submits form successfully', async () => {
  render(<{POCName}Panel />);

  // Fill form
  fireEvent.change(screen.getByLabelText('Input Field'), {
    target: { value: 'test input' }
  });

  // Submit
  fireEvent.click(screen.getByText('Submit'));

  // Verify results
  await waitFor(() => {
    expect(screen.getByText(/results/i)).toBeInTheDocument();
  });
});
```

---

## Deployment Strategy

### Development Environment

**Docker Compose** (existing):
```bash
# Start all services
docker-compose up -d

# Verify POC endpoints
curl http://localhost:8000/api/v2/{category}/{poc-name}/health
```

### Staging Environment

**Kubernetes + Argo CD**:
```yaml
# infrastructure/k8s/tier2/{poc-name}-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {poc-name}-service
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: backend
        image: chatbot-backend:latest
        env:
        - name: POC_MODULE
          value: "{poc_name}"
```

### Production Deployment

**Phases**:
1. **Week 8**: Deploy Phase 2 POCs to staging
2. **Week 14**: Deploy Phase 3 POCs to staging
3. **Week 20**: Deploy Phase 4 POCs to staging
4. **Week 22**: Production rollout (all 23 POCs)

**Blue-Green Deployment**:
- Maintain existing Tier 1 services
- Deploy new Tier 2 POCs alongside
- Progressive rollout (10% → 50% → 100%)

---

## Success Metrics

### Technical KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Code Reusability** | >75% | LOC from Tier 1 / Total LOC |
| **Test Coverage** | >80% | pytest --cov report |
| **API Response Time** | <500ms (p95) | OpenTelemetry metrics |
| **System Uptime** | >99.5% | Prometheus uptime |
| **Build Time** | <10 min | CI/CD pipeline |

### Business KPIs

| Metric | Target |
|--------|--------|
| **POCs Delivered** | 23/23 (100%) |
| **On-Time Delivery** | >90% of milestones |
| **User Adoption** | >70% of target users |
| **Bug Density** | <5 bugs per 1000 LOC |

---

## Risk Management

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Tier 1 service instability** | Medium | High | Comprehensive testing before Phase 2 |
| **ML model training delays** | Medium | Medium | Pre-train models in Phase 1 |
| **Neo4j integration complexity** | Low | High | Prototype in Week 15 before Spend Smart |
| **Frontend component conflicts** | Low | Medium | Component library + style guide |
| **Resource constraints** | Medium | Medium | Priority-based scheduling |

---

## Next Steps

1. ✅ **Review & Approve Plan**: Stakeholder sign-off
2. ✅ **Team Assignment**: Allocate 4 developers
3. ✅ **Environment Setup**: Week 0 prerequisites
4. ▶️ **Begin Phase 1**: Week 1 - ML Model Service development

---

**End of Implementation Plan**
