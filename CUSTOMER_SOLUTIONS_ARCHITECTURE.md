# Customer Solutions Architecture & Deployment Models

**Date:** 2026-01-03
**Purpose:** Comprehensive guide for delivering bespoke RAG solutions to customers
**Business Model:** Multi-tenant SaaS + White-label + API Integration

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Customer Use Cases](#customer-use-cases)
3. [Deployment Models](#deployment-models)
4. [Integration Patterns](#integration-patterns)
5. [Architecture Blueprints](#architecture-blueprints)
6. [Data Isolation Strategies](#data-isolation-strategies)
7. [Pricing Models](#pricing-models)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Security & Compliance](#security--compliance)
10. [Customer Onboarding](#customer-onboarding)

---

## Executive Summary

### Vision
Transform the current RAG chatbot application into a **multi-tenant platform** that enables:
1. **Hosted SaaS** - Customers use our hosted platform via API/widgets
2. **White-label** - Customers deploy isolated instances in their infrastructure
3. **Hybrid** - Mix of shared and dedicated resources

### Key Capabilities
- ✅ Multi-tenant data isolation
- ✅ API-first integration
- ✅ Embeddable widgets (chat, search, recommendations)
- ✅ Customer-specific configurations
- ✅ Usage-based billing
- ✅ White-label branding
- ✅ Self-service onboarding

---

## Customer Use Cases

### Use Case 1: RAG Chat Widget on Website
**Customer:** E-commerce company wants AI chat on product pages

**Requirements:**
- Embed chat widget on website
- Answer product questions using their catalog
- Integrate with existing product database
- Track conversations and analytics

**Solution:** Embedded Widget + API Integration

### Use Case 2: Product Catalog Enrichment
**Customer:** Retailer wants to enrich product descriptions

**Requirements:**
- Batch process 100K+ products
- Generate SEO-friendly descriptions
- Enhance with competitive intelligence
- Daily automated updates

**Solution:** Batch API + Webhook Integration

### Use Case 3: Review Analysis & Insights
**Customer:** Marketplace wants to analyze customer reviews

**Requirements:**
- Real-time review processing
- Sentiment analysis
- Extract feature requests
- Generate summary insights

**Solution:** Streaming API + Event-driven Integration

### Use Case 4: Internal Knowledge Base
**Customer:** Enterprise wants employee Q&A system

**Requirements:**
- Private document upload
- Role-based access control
- Audit logging
- On-premises deployment option

**Solution:** Dedicated Instance or White-label

### Use Case 5: Customer Support Automation
**Customer:** SaaS company wants AI-powered support

**Requirements:**
- Integrate with Zendesk/Intercom
- Auto-respond to common questions
- Escalate to human agents
- Track resolution rates

**Solution:** Integration SDK + Webhook

---

## Deployment Models

### Model 1: Multi-Tenant SaaS (Recommended for Most)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    OUR HOSTED PLATFORM                       │
├─────────────────────────────────────────────────────────────┤
│  API Gateway (tenant routing)                                │
│  ├─ Tenant A: company-a.ourplatform.com                     │
│  ├─ Tenant B: company-b.ourplatform.com                     │
│  └─ Tenant C: company-c.ourplatform.com                     │
├─────────────────────────────────────────────────────────────┤
│  Shared Services:                                            │
│  ├─ LLM Service (OpenAI, Claude) - shared                   │
│  ├─ Embedding Service - shared                              │
│  ├─ Vector DB - logical isolation per tenant                │
│  └─ Object Storage (MinIO/S3) - bucket per tenant           │
└─────────────────────────────────────────────────────────────┘
        ↓ API / Widget
┌──────────────────────┐  ┌──────────────────────┐
│  Customer A Website  │  │  Customer B App      │
│  (embeds our widget) │  │  (calls our API)     │
└──────────────────────┘  └──────────────────────┘
```

**Pros:**
- ✅ Lowest cost per customer
- ✅ Fastest time to market
- ✅ Easy to maintain and upgrade
- ✅ Shared infrastructure cost

**Cons:**
- ⚠️ Less customization flexibility
- ⚠️ Potential noisy neighbor issues
- ⚠️ Data sovereignty concerns for some customers

**Best For:**
- SMBs and startups
- Standard use cases
- Customers OK with shared infrastructure
- Price-sensitive customers

**Pricing:** $99-$999/month based on usage

---

### Model 2: Dedicated Instance (Single-Tenant)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│          CUSTOMER A - DEDICATED DEPLOYMENT                   │
├─────────────────────────────────────────────────────────────┤
│  Dedicated Infrastructure:                                   │
│  ├─ Dedicated API Server                                     │
│  ├─ Dedicated PostgreSQL + pgvector                          │
│  ├─ Dedicated Redis Cache                                    │
│  ├─ Dedicated MinIO/S3 Bucket                                │
│  └─ Dedicated LLM Endpoint (optional)                        │
└─────────────────────────────────────────────────────────────┘
        ↓ Private API
┌──────────────────────────────────────────────────────────────┐
│  Customer A Infrastructure                                    │
│  ├─ Customer Website                                          │
│  ├─ Customer App                                              │
│  └─ Customer Database                                         │
└──────────────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Complete isolation
- ✅ Custom configurations
- ✅ Predictable performance
- ✅ Meets compliance requirements (HIPAA, SOC2)

**Cons:**
- ⚠️ Higher cost per customer
- ⚠️ More complex management
- ⚠️ Slower scaling

**Best For:**
- Enterprise customers
- Regulated industries (healthcare, finance)
- High-volume customers
- Custom infrastructure requirements

**Pricing:** $2,500-$10,000/month + usage

---

### Model 3: White-Label (Customer-Hosted)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│       CUSTOMER INFRASTRUCTURE (Their AWS/Azure/GCP)          │
├─────────────────────────────────────────────────────────────┤
│  OUR SOFTWARE (Deployed by Customer):                        │
│  ├─ Docker Containers / Kubernetes                           │
│  ├─ PostgreSQL + pgvector                                    │
│  ├─ Redis                                                     │
│  ├─ MinIO/S3                                                  │
│  └─ Next.js Frontend (white-labeled)                         │
├─────────────────────────────────────────────────────────────┤
│  Customer Customizations:                                     │
│  ├─ Custom branding                                           │
│  ├─ Custom domain (ai.customer.com)                          │
│  ├─ SSO integration                                           │
│  └─ Custom workflows                                          │
└─────────────────────────────────────────────────────────────┘
        ↑ License Key / Updates
┌──────────────────────────────────────────────────────────────┐
│  OUR CONTROL PLANE (License Management)                      │
│  ├─ License validation                                        │
│  ├─ Update distribution                                       │
│  ├─ Usage telemetry (anonymized)                             │
│  └─ Support portal                                            │
└──────────────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Full customer control
- ✅ Data stays in customer infrastructure
- ✅ Meets strictest compliance requirements
- ✅ Unlimited customization

**Cons:**
- ⚠️ Customer manages infrastructure
- ⚠️ Complex deployment process
- ⚠️ Harder to support
- ⚠️ Version fragmentation

**Best For:**
- Highly regulated industries
- Data sovereignty requirements
- Large enterprises
- Government/defense contracts

**Pricing:** $50,000-$250,000/year license + support

---

## Integration Patterns

### Pattern 1: REST API Integration

**Use Case:** Customer's backend calls our API for RAG queries

**Architecture:**
```python
# Customer's Backend (any language)
import requests

response = requests.post(
    'https://api.ourplatform.com/v1/query',
    headers={
        'Authorization': 'Bearer CUSTOMER_API_KEY',
        'X-Tenant-ID': 'customer-123'
    },
    json={
        'query': 'What is the return policy?',
        'context': {'product_id': 'SKU-12345'},
        'top_k': 5
    }
)

answer = response.json()['answer']
sources = response.json()['sources']
```

**Implementation:**
```python
# Our API (backend/app/api/routes/public_api.py)
from fastapi import APIRouter, Depends, Header
from app.services.tenant_service import get_tenant_from_api_key

router = APIRouter(prefix="/v1", tags=["Public API"])

@router.post("/query")
async def query(
    request: QueryRequest,
    api_key: str = Header(..., alias="Authorization"),
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: Session = Depends(get_db)
):
    # Validate API key and tenant
    tenant = await validate_tenant(api_key, tenant_id, db)

    # Apply tenant-specific configuration
    config = await get_tenant_config(tenant.id, db)

    # Execute RAG query with tenant isolation
    result = await rag_service.query(
        query=request.query,
        tenant_id=tenant.id,
        config=config,
        db=db
    )

    # Track usage for billing
    await track_usage(tenant.id, tokens=result.tokens_used)

    return QueryResponse(
        answer=result.answer,
        sources=result.sources,
        confidence=result.confidence
    )
```

**Features:**
- ✅ RESTful endpoints
- ✅ API key authentication
- ✅ Rate limiting per tenant
- ✅ Usage tracking
- ✅ Webhook callbacks
- ✅ Batch operations

---

### Pattern 2: JavaScript Widget (Embeddable Chat)

**Use Case:** Customer embeds chat widget on their website

**Customer's Website:**
```html
<!-- Customer adds this to their website -->
<!DOCTYPE html>
<html>
<head>
    <title>Customer Website</title>
</head>
<body>
    <!-- Customer's content -->
    <h1>Welcome to Our Store</h1>

    <!-- Our chat widget (single line integration) -->
    <script src="https://cdn.ourplatform.com/widget.js"
            data-api-key="pk_live_abc123"
            data-tenant-id="customer-123"
            data-position="bottom-right"
            data-theme="light"
            data-primary-color="#007bff">
    </script>
</body>
</html>
```

**Our Widget Code:**
```typescript
// frontend/public/widget.js
(function() {
  'use strict';

  // Extract configuration from script tag
  const script = document.currentScript;
  const config = {
    apiKey: script.getAttribute('data-api-key'),
    tenantId: script.getAttribute('data-tenant-id'),
    position: script.getAttribute('data-position') || 'bottom-right',
    theme: script.getAttribute('data-theme') || 'light',
    primaryColor: script.getAttribute('data-primary-color') || '#007bff'
  };

  // Create chat widget UI
  function createWidget() {
    const container = document.createElement('div');
    container.id = 'ourplatform-chat-widget';
    container.innerHTML = `
      <div class="widget-container ${config.position}">
        <div class="widget-button" onclick="toggleChat()">
          <svg>💬</svg>
        </div>
        <div class="widget-chat" style="display:none;">
          <div class="chat-header" style="background:${config.primaryColor}">
            <h3>Ask us anything</h3>
            <button onclick="toggleChat()">×</button>
          </div>
          <div class="chat-messages" id="chat-messages"></div>
          <div class="chat-input">
            <input type="text" id="user-input" placeholder="Type your question..." />
            <button onclick="sendMessage()">Send</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(container);
  }

  // Send message to our API
  async function sendMessage() {
    const input = document.getElementById('user-input');
    const query = input.value.trim();
    if (!query) return;

    // Add user message to UI
    addMessage('user', query);
    input.value = '';

    // Show typing indicator
    addMessage('bot', '...', true);

    // Call our API
    try {
      const response = await fetch('https://api.ourplatform.com/v1/query', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${config.apiKey}`,
          'X-Tenant-ID': config.tenantId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: query,
          context: getPageContext() // Extract product info from page
        })
      });

      const data = await response.json();

      // Remove typing indicator and show answer
      removeTypingIndicator();
      addMessage('bot', data.answer);

      // Show sources if available
      if (data.sources?.length > 0) {
        addSources(data.sources);
      }
    } catch (error) {
      removeTypingIndicator();
      addMessage('bot', 'Sorry, something went wrong. Please try again.');
    }
  }

  // Extract context from customer's page
  function getPageContext() {
    return {
      url: window.location.href,
      title: document.title,
      productId: extractProductId(), // Custom logic per customer
      userAgent: navigator.userAgent
    };
  }

  // Initialize widget when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }
})();
```

**Features:**
- ✅ Single-line embed code
- ✅ Customizable styling
- ✅ Mobile responsive
- ✅ Auto-detects page context
- ✅ GDPR compliant
- ✅ Analytics tracking

---

### Pattern 3: SDK (Client Libraries)

**Use Case:** Customer integrates deeply into their application

**Python SDK:**
```python
# Customer installs: pip install ourplatform-sdk

from ourplatform import RAGClient

# Initialize client
client = RAGClient(
    api_key='pk_live_abc123',
    tenant_id='customer-123'
)

# Upload documents
with open('product_catalog.pdf', 'rb') as f:
    document = client.documents.upload(
        file=f,
        metadata={'type': 'product_catalog', 'version': '2024-01'}
    )

# Query
response = client.query(
    query='What are the top-rated wireless headphones?',
    filters={'category': 'electronics', 'rating': '>4.5'},
    top_k=10
)

print(response.answer)
for source in response.sources:
    print(f"  - {source.title} (score: {source.score})")

# Batch enrichment
products = client.enrich.batch(
    items=[
        {'id': 'SKU-123', 'name': 'Wireless Mouse'},
        {'id': 'SKU-456', 'name': 'Mechanical Keyboard'}
    ],
    fields=['description', 'seo_title', 'features']
)

for product in products:
    print(f"{product.id}: {product.enriched.description}")
```

**JavaScript SDK:**
```javascript
// Customer installs: npm install @ourplatform/sdk

import { RAGClient } from '@ourplatform/sdk';

const client = new RAGClient({
  apiKey: 'pk_live_abc123',
  tenantId: 'customer-123'
});

// Real-time query
const result = await client.query({
  query: 'How do I return a product?',
  context: { userId: 'user-789', orderId: 'ORD-456' }
});

console.log(result.answer);

// Streaming response (for chat UX)
const stream = await client.queryStream({
  query: 'Explain the warranty policy'
});

for await (const chunk of stream) {
  process.stdout.write(chunk.text); // Type-writer effect
}
```

**Features:**
- ✅ Type-safe APIs
- ✅ Automatic retries
- ✅ Connection pooling
- ✅ Streaming support
- ✅ Error handling
- ✅ Telemetry

---

### Pattern 4: Webhook / Event-Driven

**Use Case:** Push notifications to customer's system

**Customer Configuration:**
```json
// Customer configures webhooks in our dashboard
{
  "webhooks": [
    {
      "event": "document.processed",
      "url": "https://customer.com/webhooks/doc-processed",
      "secret": "whsec_abc123"
    },
    {
      "event": "query.low_confidence",
      "url": "https://customer.com/webhooks/escalate",
      "secret": "whsec_abc123"
    }
  ]
}
```

**Our System Sends:**
```python
# backend/app/services/webhook_service.py
import hmac
import hashlib
import httpx

async def send_webhook(tenant_id: str, event: str, payload: dict):
    """Send webhook to customer's endpoint"""
    webhooks = await get_tenant_webhooks(tenant_id, event)

    for webhook in webhooks:
        # Create signature for security
        signature = hmac.new(
            webhook.secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()

        # Send POST request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook.url,
                json={
                    'event': event,
                    'tenant_id': tenant_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': payload
                },
                headers={
                    'X-Webhook-Signature': f'sha256={signature}',
                    'X-Webhook-Event': event
                },
                timeout=10
            )

            # Log delivery
            await log_webhook_delivery(
                webhook.id,
                status=response.status_code,
                response_time=response.elapsed.total_seconds()
            )
```

**Customer Receives:**
```javascript
// Customer's webhook endpoint
app.post('/webhooks/doc-processed', (req, res) => {
  // Verify signature
  const signature = req.headers['x-webhook-signature'];
  const expectedSignature = crypto
    .createHmac('sha256', process.env.WEBHOOK_SECRET)
    .update(JSON.stringify(req.body))
    .digest('hex');

  if (signature !== `sha256=${expectedSignature}`) {
    return res.status(401).send('Invalid signature');
  }

  // Process event
  const { event, data } = req.body;
  console.log(`Document processed: ${data.document_id}`);

  // Update customer's database
  await db.documents.update(data.document_id, {
    status: 'processed',
    embeddings_ready: true
  });

  res.status(200).send('OK');
});
```

**Events:**
- `document.uploaded`
- `document.processed`
- `document.failed`
- `query.completed`
- `query.low_confidence`
- `usage.threshold_reached`
- `billing.usage_limit`

---

## Architecture Blueprints

### Blueprint 1: E-Commerce RAG Chat Widget

**Customer:** Online retailer with 10K products

**Solution Components:**
```
┌─────────────────────────────────────────────────────────────┐
│  CUSTOMER WEBSITE (customer.com)                             │
│  ├─ Product Pages                                            │
│  ├─ Shopping Cart                                            │
│  ├─ Checkout                                                 │
│  └─ OUR CHAT WIDGET (embedded) ←────────────────┐           │
└──────────────────────────────────────────────────│───────────┘
                                                    │
                              ┌─────────────────────┴───────────┐
                              │  OUR PLATFORM API                │
                              ├─────────────────────────────────┤
                              │  RAG Service:                    │
                              │  ├─ Vector Search (products)     │
                              │  ├─ LLM (answer generation)      │
                              │  └─ Context: product page info   │
                              ├─────────────────────────────────┤
                              │  Data:                           │
                              │  ├─ Product catalog (synced)     │
                              │  ├─ FAQs                         │
                              │  ├─ Policies (return, shipping)  │
                              │  └─ Past conversations (learn)   │
                              └─────────────────────────────────┘
```

**Data Flow:**
1. Customer uploads product catalog via API/CSV
2. We process and embed all products
3. Widget embedded on product pages
4. User asks: "Does this come in blue?"
5. Widget extracts product context from page
6. Sends to our API with product ID
7. We search: product variations + related FAQs
8. LLM generates answer with product links
9. Answer displayed in widget
10. Conversation logged for analytics

**Pricing:** $299/month + $0.001 per query

---

### Blueprint 2: Product Catalog Enrichment

**Customer:** B2B wholesaler with 50K SKUs, poor descriptions

**Solution Components:**
```
┌─────────────────────────────────────────────────────────────┐
│  CUSTOMER SYSTEM                                             │
│  ├─ Product Database (PostgreSQL)                           │
│  ├─ E-commerce Platform (Shopify/Custom)                    │
│  └─ Cron Job (daily sync) ──────────────────┐               │
└──────────────────────────────────────────────│───────────────┘
                                                │
                              ┌─────────────────┴───────────────┐
                              │  OUR ENRICHMENT API              │
                              ├─────────────────────────────────┤
                              │  Batch Processor:                │
                              │  ├─ Queue: 1000 products/batch   │
                              │  ├─ Extract: specs from mfg docs │
                              │  ├─ Generate: SEO descriptions   │
                              │  ├─ Enhance: competitive data    │
                              │  └─ Validate: quality checks     │
                              ├─────────────────────────────────┤
                              │  LLM Pipeline:                   │
                              │  ├─ Product description (200ch)  │
                              │  ├─ SEO title (60ch)             │
                              │  ├─ Meta description (160ch)     │
                              │  ├─ Feature bullets (5x)         │
                              │  └─ Category classification      │
                              └─────────────────────────────────┘
                                                │
                                                ↓ Webhook
┌─────────────────────────────────────────────────────────────┐
│  CUSTOMER WEBHOOK RECEIVER                                   │
│  ├─ Receives enriched data                                   │
│  ├─ Updates product database                                 │
│  └─ Triggers cache refresh                                   │
└─────────────────────────────────────────────────────────────┘
```

**API Example:**
```python
# Customer's daily cron job
import requests

# Get products that need enrichment
products = db.query("""
    SELECT id, name, sku, category, manufacturer
    FROM products
    WHERE description IS NULL OR last_enriched < NOW() - INTERVAL '30 days'
    LIMIT 1000
""")

# Send to our API
response = requests.post(
    'https://api.ourplatform.com/v1/enrich/batch',
    headers={'Authorization': 'Bearer API_KEY'},
    json={
        'items': [
            {
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'category': p.category,
                'manufacturer': p.manufacturer
            }
            for p in products
        ],
        'fields': [
            'description',
            'seo_title',
            'meta_description',
            'features',
            'category'
        ],
        'callback_url': 'https://customer.com/webhooks/enrichment'
    }
)

job_id = response.json()['job_id']
print(f"Enrichment job started: {job_id}")
```

**Pricing:** $0.05 per product enriched (volume discounts)

---

### Blueprint 3: Review Analysis Dashboard

**Customer:** Marketplace with 1M+ reviews, needs insights

**Solution Components:**
```
┌─────────────────────────────────────────────────────────────┐
│  CUSTOMER MARKETPLACE                                        │
│  ├─ Review Submission ────────────┐                         │
│  ├─ Product Pages                  │                         │
│  └─ Seller Dashboard               │                         │
└────────────────────────────────────│─────────────────────────┘
                                      │ Real-time stream
                                      ↓
┌─────────────────────────────────────────────────────────────┐
│  OUR REVIEW ANALYSIS PIPELINE                                │
├─────────────────────────────────────────────────────────────┤
│  1. Ingestion:                                               │
│     ├─ Streaming API (Kafka/webhook)                        │
│     └─ Batch upload (CSV/JSON)                              │
├─────────────────────────────────────────────────────────────┤
│  2. Processing:                                              │
│     ├─ Sentiment analysis (pos/neg/neutral)                 │
│     ├─ Topic extraction (quality, shipping, support)        │
│     ├─ Feature mentions (battery life, comfort, design)     │
│     ├─ Issue detection (defects, complaints)                │
│     └─ Fake review detection                                │
├─────────────────────────────────────────────────────────────┤
│  3. Aggregation:                                             │
│     ├─ Per product metrics                                   │
│     ├─ Per seller metrics                                    │
│     ├─ Trending issues                                       │
│     └─ Competitive insights                                  │
├─────────────────────────────────────────────────────────────┤
│  4. Output:                                                  │
│     ├─ API (real-time queries)                              │
│     ├─ Webhooks (alerts)                                     │
│     ├─ Dashboard (embedded iFrame)                           │
│     └─ Reports (daily/weekly PDF)                            │
└─────────────────────────────────────────────────────────────┘
```

**Integration:**
```javascript
// Customer sends reviews to us
const review = {
  id: 'rev-123',
  product_id: 'prod-456',
  seller_id: 'seller-789',
  rating: 4,
  text: 'Great product but shipping was slow',
  reviewer_id: 'user-321',
  timestamp: '2026-01-03T10:00:00Z'
};

await fetch('https://api.ourplatform.com/v1/reviews/ingest', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(review)
});

// Later, get insights
const insights = await fetch(
  'https://api.ourplatform.com/v1/reviews/insights?product_id=prod-456'
);

console.log(insights);
// {
//   "sentiment": { "positive": 0.7, "negative": 0.2, "neutral": 0.1 },
//   "top_features": ["battery life", "comfort", "design"],
//   "top_issues": ["slow shipping", "packaging"],
//   "summary": "Customers love the battery life and comfort..."
// }
```

**Pricing:** $499/month + $0.0001 per review

---

## Data Isolation Strategies

### Strategy 1: Logical Isolation (Multi-Tenant)

**Database Schema:**
```sql
-- All tables have tenant_id column
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,  -- Partition key
    filename VARCHAR(255),
    content TEXT,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Partition by tenant for performance
    PARTITION BY LIST (tenant_id)
);

-- Automatic partition creation per tenant
CREATE TABLE documents_tenant_abc PARTITION OF documents
    FOR VALUES IN ('tenant-abc-uuid');

CREATE TABLE documents_tenant_xyz PARTITION OF documents
    FOR VALUES IN ('tenant-xyz-uuid');

-- Row-level security
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON documents
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

**Application Layer:**
```python
# Set tenant context for all queries
@app.middleware("http")
async def set_tenant_context(request: Request, call_next):
    tenant_id = request.headers.get('X-Tenant-ID')

    # Validate tenant
    if not tenant_id:
        return JSONResponse(
            status_code=400,
            content={'error': 'Missing X-Tenant-ID header'}
        )

    # Set in database session
    async with db.begin():
        await db.execute(
            text(f"SET app.current_tenant = '{tenant_id}'")
        )
        response = await call_next(request)

    return response

# All queries automatically filtered by tenant
documents = await db.execute(
    select(Document).where(Document.status == 'processed')
    # tenant_id filter automatically applied by RLS
)
```

**Vector Search Isolation:**
```python
# pgvector with tenant filtering
async def search_documents(
    query: str,
    tenant_id: str,
    top_k: int = 10
) -> List[Document]:
    query_embedding = await get_embedding(query)

    results = await db.execute(
        select(Document)
        .where(Document.tenant_id == tenant_id)  # Enforce isolation
        .order_by(
            Document.embedding.cosine_distance(query_embedding)
        )
        .limit(top_k)
    )

    return results.scalars().all()
```

**Pros:**
- ✅ Cost-effective (shared infrastructure)
- ✅ Easy to scale (add tenants dynamically)
- ✅ Simpler deployment

**Cons:**
- ⚠️ Risk of data leakage if bugs
- ⚠️ Performance can be affected by noisy neighbors
- ⚠️ Limited customization per tenant

---

### Strategy 2: Physical Isolation (Dedicated Databases)

**Infrastructure:**
```yaml
# docker-compose-tenant-abc.yml
version: '3.8'
services:
  postgres-tenant-abc:
    image: pgvector/pgvector:latest
    environment:
      POSTGRES_DB: tenant_abc
      POSTGRES_USER: tenant_abc_user
      POSTGRES_PASSWORD: ${TENANT_ABC_PASSWORD}
    volumes:
      - tenant_abc_data:/var/lib/postgresql/data
    networks:
      - tenant_abc_network

  redis-tenant-abc:
    image: redis:7
    volumes:
      - tenant_abc_redis:/data
    networks:
      - tenant_abc_network

  minio-tenant-abc:
    image: minio/minio
    environment:
      MINIO_ROOT_USER: tenant_abc
      MINIO_ROOT_PASSWORD: ${TENANT_ABC_MINIO_PASSWORD}
    volumes:
      - tenant_abc_storage:/data
    networks:
      - tenant_abc_network

volumes:
  tenant_abc_data:
  tenant_abc_redis:
  tenant_abc_storage:

networks:
  tenant_abc_network:
    driver: bridge
```

**Connection Routing:**
```python
# Dynamic connection pool per tenant
class TenantDatabaseManager:
    def __init__(self):
        self.pools: Dict[str, AsyncEngine] = {}

    async def get_connection(self, tenant_id: str) -> AsyncEngine:
        if tenant_id not in self.pools:
            # Load tenant DB config from master DB
            tenant_config = await self.get_tenant_config(tenant_id)

            # Create dedicated connection pool
            self.pools[tenant_id] = create_async_engine(
                f"postgresql+asyncpg://{tenant_config.user}:{tenant_config.password}"
                f"@{tenant_config.host}:{tenant_config.port}/{tenant_config.database}",
                pool_size=20,
                max_overflow=40
            )

        return self.pools[tenant_id]

# Usage in endpoints
@router.post("/query")
async def query(
    request: QueryRequest,
    tenant_id: str = Header(..., alias="X-Tenant-ID")
):
    # Get tenant-specific database connection
    engine = await db_manager.get_connection(tenant_id)

    async with AsyncSession(engine) as session:
        # All queries go to tenant's dedicated DB
        documents = await session.execute(
            select(Document).where(Document.status == 'processed')
        )

        # ... rest of the logic
```

**Pros:**
- ✅ Complete data isolation
- ✅ Predictable performance
- ✅ Easy to backup/restore per tenant
- ✅ Can customize DB config per tenant

**Cons:**
- ⚠️ Higher infrastructure cost
- ⚠️ More complex management
- ⚠️ Connection pool overhead

---

### Strategy 3: Hybrid (Shared + Dedicated)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│  SHARED TIER (All Tenants)                                   │
├─────────────────────────────────────────────────────────────┤
│  ├─ LLM Service (OpenAI, Claude) - shared                   │
│  ├─ Embedding Service - shared                              │
│  ├─ Authentication/Authorization - shared                    │
│  └─ Billing/Metering - shared                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  TENANT-SPECIFIC (Per Customer)                              │
├─────────────────────────────────────────────────────────────┤
│  Tenant A:                                                   │
│  ├─ PostgreSQL Database (dedicated)                         │
│  ├─ Redis Cache (dedicated)                                 │
│  └─ MinIO/S3 Bucket (dedicated)                             │
├─────────────────────────────────────────────────────────────┤
│  Tenant B:                                                   │
│  ├─ PostgreSQL Database (dedicated)                         │
│  ├─ Redis Cache (dedicated)                                 │
│  └─ MinIO/S3 Bucket (dedicated)                             │
└─────────────────────────────────────────────────────────────┘
```

**Decision Matrix:**
```python
def get_isolation_strategy(tenant: Tenant) -> str:
    """Determine isolation strategy based on tenant tier"""

    if tenant.plan == 'enterprise':
        # Enterprise: Dedicated everything
        return 'fully_dedicated'

    elif tenant.plan == 'professional':
        # Professional: Dedicated data, shared compute
        return 'hybrid'

    elif tenant.plan == 'starter':
        # Starter: Shared everything
        return 'multi_tenant'

    # Custom logic based on:
    # - Data volume
    # - Compliance requirements
    # - Performance SLA
    # - Budget
```

---

## Pricing Models

### Model 1: Usage-Based (Recommended)

**Metrics:**
- Queries per month
- Documents stored
- Embeddings generated
- API calls
- Bandwidth

**Tiers:**
```
Starter: $99/month
├─ 10,000 queries/month
├─ 1,000 documents
├─ 10 GB storage
└─ Standard support

Professional: $499/month
├─ 100,000 queries/month
├─ 10,000 documents
├─ 100 GB storage
├─ Priority support
└─ Custom branding

Enterprise: $2,499/month
├─ Unlimited queries
├─ Unlimited documents
├─ 1 TB storage
├─ Dedicated support
├─ SLA guarantee
└─ On-premises option
```

### Model 2: Seat-Based

**For Internal Tools:**
```
Per User: $25/month
├─ Unlimited queries
├─ Personal workspace
└─ Shared documents

Teams (10+ users): $20/user/month
├─ Team workspaces
├─ Admin controls
└─ SSO integration

Enterprise (100+ users): Custom pricing
├─ Volume discounts
├─ Dedicated instance
└─ Custom SLA
```

### Model 3: White-Label License

**One-Time or Annual:**
```
SMB License: $25,000/year
├─ Up to 50 users
├─ Standard features
├─ Email support
└─ Quarterly updates

Enterprise License: $100,000/year
├─ Unlimited users
├─ All features
├─ Priority support
├─ Custom development
└─ Source code escrow
```

---

## Implementation Roadmap

### Phase 1: Multi-Tenant Foundation (Month 1-2)

**Weeks 1-2: Database Multi-Tenancy**
- [ ] Add `tenant_id` to all tables
- [ ] Implement row-level security (RLS)
- [ ] Create tenant management tables
- [ ] Database partitioning by tenant
- [ ] Migration scripts

**Weeks 3-4: API Multi-Tenancy**
- [ ] Tenant authentication (API keys)
- [ ] Tenant context middleware
- [ ] Rate limiting per tenant
- [ ] Usage tracking/metering
- [ ] Webhook system

**Weeks 5-6: Billing Integration**
- [ ] Stripe/payment gateway integration
- [ ] Usage-based billing
- [ ] Subscription management
- [ ] Invoice generation
- [ ] Usage dashboards

**Weeks 7-8: Testing**
- [ ] Multi-tenant integration tests
- [ ] Data isolation verification
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation

---

### Phase 2: Public API & SDKs (Month 3-4)

**Weeks 1-2: REST API v1**
- [ ] OpenAPI specification
- [ ] Versioned endpoints (`/v1/`)
- [ ] Authentication (API keys, OAuth)
- [ ] Rate limiting
- [ ] API documentation

**Weeks 3-4: SDKs**
- [ ] Python SDK
- [ ] JavaScript/TypeScript SDK
- [ ] Go SDK (optional)
- [ ] SDK documentation
- [ ] Example applications

**Weeks 5-6: Developer Portal**
- [ ] API key management
- [ ] Usage analytics
- [ ] Documentation site
- [ ] Code examples
- [ ] Playground/sandbox

**Weeks 7-8: Testing**
- [ ] SDK integration tests
- [ ] API stability testing
- [ ] Load testing
- [ ] Security review

---

### Phase 3: Embeddable Widget (Month 5-6)

**Weeks 1-3: Widget Development**
- [ ] Standalone JavaScript widget
- [ ] Customizable UI (theme, colors)
- [ ] Mobile responsive
- [ ] Accessibility (WCAG 2.1)
- [ ] Analytics tracking

**Weeks 4-5: Integration**
- [ ] CDN distribution
- [ ] Version management
- [ ] Embed code generator
- [ ] Configuration UI
- [ ] Testing framework

**Weeks 6-8: Polish**
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] Security hardening
- [ ] Documentation
- [ ] Demo site

---

### Phase 4: White-Label (Month 7-9)

**Weeks 1-3: Packaging**
- [ ] Docker/K8s deployment templates
- [ ] Terraform/CloudFormation scripts
- [ ] Environment configuration
- [ ] Database migrations
- [ ] Backup/restore scripts

**Weeks 4-6: Customization**
- [ ] White-label branding system
- [ ] Custom domain support
- [ ] SSO integration (SAML, OAuth)
- [ ] LDAP/Active Directory
- [ ] License key system

**Weeks 7-9: Documentation**
- [ ] Deployment guide
- [ ] Operations manual
- [ ] Troubleshooting guide
- [ ] Security best practices
- [ ] Training materials

---

## Security & Compliance

### Data Security

**Encryption:**
- ✅ At rest: AES-256
- ✅ In transit: TLS 1.3
- ✅ Database: Column-level encryption for PII
- ✅ Backups: Encrypted with separate keys

**Access Control:**
- ✅ API key authentication
- ✅ OAuth 2.0 / OpenID Connect
- ✅ Role-based access control (RBAC)
- ✅ IP whitelisting
- ✅ MFA for admin access

**Compliance:**
- ✅ GDPR (EU data protection)
- ✅ SOC 2 Type II
- ✅ HIPAA (healthcare) - dedicated instances
- ✅ ISO 27001
- ✅ PCI DSS (if processing payments)

**Data Residency:**
```python
# Support for regional data residency
REGIONS = {
    'us-east': 'United States (Virginia)',
    'eu-west': 'European Union (Ireland)',
    'ap-southeast': 'Asia Pacific (Singapore)',
    'us-gov': 'US Government Cloud'
}

# Tenant config
{
    "tenant_id": "customer-123",
    "region": "eu-west",  # Data stays in EU
    "compliance": ["GDPR", "SOC2"],
    "data_residency": "strict"  # Never leaves region
}
```

---

## Customer Onboarding

### Self-Service Onboarding Flow

**Step 1: Sign Up**
```
1. Email + password OR Google/GitHub OAuth
2. Email verification
3. Company details (optional)
4. Use case selection (template)
5. Plan selection (Starter/Pro/Enterprise)
```

**Step 2: Initial Setup**
```
1. Create first project/workspace
2. Upload sample documents (optional)
3. Configure basic settings
4. Generate API key
5. Test with playground
```

**Step 3: Integration**
```
Option A: API Integration
  → Copy API key
  → View code examples (curl, Python, JS)
  → Test in sandbox
  → Go live

Option B: Widget Embed
  → Customize appearance
  → Generate embed code
  → Copy to website
  → Verify installation

Option C: White-Label
  → Schedule demo call
  → Receive deployment package
  → Installation support
  → Training session
```

**Step 4: Go Live**
```
1. Production checklist
2. Remove sandbox mode
3. Configure webhooks
4. Set up billing
5. Monitor dashboard
```

### Customer Success

**Onboarding Support:**
- 📧 Email onboarding sequence (day 1, 3, 7, 14, 30)
- 📚 Documentation & tutorials
- 🎥 Video walkthroughs
- 💬 Live chat support (Pro+)
- 📞 Dedicated CSM (Enterprise)

**Monitoring:**
- 📊 Usage dashboards
- 🚨 Error rate monitoring
- 📈 Performance metrics
- 💰 Cost tracking
- 📧 Usage alerts

---

## Summary & Recommendations

### Quick Decision Matrix

| Customer Type | Use Case | Recommended Model | Integration | Pricing |
|---------------|----------|-------------------|-------------|---------|
| **SMB E-commerce** | Chat widget | Multi-tenant SaaS | JavaScript embed | $99-$499/mo |
| **Mid-market Retailer** | Catalog enrichment | Multi-tenant SaaS | REST API + Webhook | $499-$2,499/mo |
| **Enterprise SaaS** | Internal KB | Dedicated instance | SDK + SSO | $2,499-$10K/mo |
| **Financial Institution** | Compliance RAG | White-label | On-premises | $50K-$250K/year |
| **Marketplace** | Review analysis | Hybrid | Streaming API | $499/mo + usage |

### Next Steps

**Immediate (Month 1):**
1. ✅ Implement tenant_id across database
2. ✅ Create tenant management system
3. ✅ Build public API v1
4. ✅ Set up billing integration

**Short-term (Months 2-3):**
1. ✅ Release Python & JavaScript SDKs
2. ✅ Launch developer portal
3. ✅ Beta test with 3-5 pilot customers
4. ✅ Iterate based on feedback

**Medium-term (Months 4-6):**
1. ✅ Release embeddable widget
2. ✅ Expand to 20-30 customers
3. ✅ Achieve SOC 2 compliance
4. ✅ Add regional deployments (EU, Asia)

**Long-term (Months 7-12):**
1. ✅ White-label offering
2. ✅ Enterprise features (SSO, SAML, LDAP)
3. ✅ Partner program
4. ✅ Marketplace of pre-built solutions

---

**Last Updated:** 2026-01-03
**Status:** Strategic Planning Document
**Next Action:** Review with stakeholders, prioritize Phase 1 tasks

