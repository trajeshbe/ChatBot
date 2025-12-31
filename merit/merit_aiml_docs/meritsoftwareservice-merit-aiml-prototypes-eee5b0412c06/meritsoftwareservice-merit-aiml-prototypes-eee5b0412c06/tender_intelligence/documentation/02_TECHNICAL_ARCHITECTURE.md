# BidRadar - Technical Architecture Documentation

**Version:** 1.0
**Last Updated:** December 2025
**Audience:** Developers, Technical Architects, DevOps Engineers

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Component Design](#component-design)
3. [Data Layer Architecture](#data-layer-architecture)
4. [Machine Learning Pipeline](#machine-learning-pipeline)
5. [AI Integration Architecture](#ai-integration-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [API & Integration Patterns](#api-integration-patterns)
8. [Performance Optimization](#performance-optimization)
9. [Error Handling & Logging](#error-handling-logging)
10. [Testing Strategy](#testing-strategy)

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
│                      (Streamlit Multi-Page App)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │Dashboard │ │  Search  │ │Assistant │ │  Vendor Profile   │  │
│  │  Page    │ │  Page    │ │  Page    │ │     Page          │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      Business Logic Layer                        │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │   Database    │  │  ML Engine   │  │   AI Assistant    │    │
│  │   Manager     │  │ (MLEngine)   │  │   (GPT-4o)        │    │
│  │  (Database)   │  │              │  │                   │    │
│  └───────────────┘  └──────────────┘  └──────────────────┘    │
│  ┌───────────────┐  ┌──────────────┐                          │
│  │ Web Scraper   │  │     Data     │                          │
│  │(TenderScraper)│  │  Processor   │                          │
│  │               │  │(DataProcessor)│                          │
│  └───────────────┘  └──────────────┘                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                        Data Layer                                │
│                  SQLite Database (ACID)                          │
│  ┌──────────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │  Tenders Table   │  │ Vendors Table │  │  Interests &    │ │
│  │  (20+ columns)   │  │ (17 columns)  │  │  Feedback Tables│ │
│  └──────────────────┘  └───────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Separation of Concerns**: Clear boundaries between presentation, business logic, and data layers
2. **Modularity**: Independent, loosely-coupled components
3. **Scalability**: Designed for horizontal scaling through stateless components
4. **Maintainability**: Clean code, comprehensive logging, and documentation
5. **Performance**: Caching strategies, optimized queries, and lazy loading
6. **Security**: Environment-based configuration, input validation, SQL injection protection

### Technology Stack Rationale

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Frontend** | Streamlit | Rapid prototyping, built-in widgets, native Python integration |
| **Database** | SQLite | Lightweight, zero-configuration, ACID compliance, sufficient for prototype |
| **ML Framework** | scikit-learn | Industry standard, excellent documentation, broad algorithm support |
| **NLP** | spaCy | Fast, accurate entity extraction, production-ready |
| **AI** | OpenAI GPT-4o | State-of-the-art language understanding, robust API |
| **Web Scraping** | BeautifulSoup + trafilatura | Robust HTML parsing, content extraction |
| **Visualization** | Plotly | Interactive charts, good Streamlit integration |
| **Data Processing** | Pandas + NumPy | Efficient data manipulation, scientific computing |

---

## Component Design

### 1. Database Component (`utils/database.py`)

**Purpose**: Centralized data access layer with CRUD operations

**Class**: `Database`

#### Key Methods

```python
class Database:
    def __init__(self, db_path: str = "tender_platform.db")
    def init_database() -> None
    def get_connection() -> ContextManager[sqlite3.Connection]

    # Tender Operations
    def store_tenders(tenders: List[Dict]) -> bool
    def get_all_tenders() -> List[Dict]
    def get_recent_tenders(limit: int) -> List[Dict]
    def get_tenders_by_category(category: str) -> List[Dict]
    def search_tenders(query: str, filters: Dict) -> List[Dict]

    # Vendor Operations
    def create_vendor(vendor_data: Dict) -> bool
    def update_vendor(vendor_data: Dict) -> bool
    def get_all_vendors() -> List[Dict]
    def get_vendor_by_name(name: str) -> Optional[Dict]

    # Interaction Tracking
    def record_vendor_interest(vendor_name, tender_id, interest_type) -> bool
    def record_recommendation_feedback(...) -> bool
    def get_vendor_interests(vendor_name: str) -> List[Dict]

    # Analytics & Maintenance
    def get_database_stats() -> Dict[str, Any]
    def cleanup_old_data(days_old: int) -> bool
```

#### Design Patterns

**Pattern**: Repository Pattern
- Abstracts data access logic from business logic
- Single source of truth for database operations
- Enables easy testing through mocking

**Pattern**: Context Manager
- Automatic connection management
- Guaranteed resource cleanup
- Transaction support with rollback

**Pattern**: Data Transfer Objects (DTOs)
- Consistent dictionary-based data exchange
- JSON serialization for complex fields
- Type safety through validation

#### Database Schema Design

**Tenders Table Schema**:
```sql
CREATE TABLE IF NOT EXISTS tenders (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    value REAL DEFAULT 0,
    deadline TEXT,
    status TEXT DEFAULT 'Active',
    organization TEXT,
    location TEXT,
    url TEXT,
    source TEXT,
    scraped_date TEXT,
    semantic_tags TEXT,          -- JSON array
    tag_scores TEXT,             -- JSON object
    extracted_entities TEXT,     -- JSON object
    urgency_score REAL DEFAULT 0.5,
    complexity_score REAL DEFAULT 0.5,
    cluster_id INTEGER DEFAULT 0,
    cluster_similarity REAL DEFAULT 0.5,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indices for query optimization
CREATE INDEX idx_tenders_category ON tenders (category);
CREATE INDEX idx_tenders_status ON tenders (status);
CREATE INDEX idx_tenders_deadline ON tenders (deadline);
```

**Vendors Table Schema**:
```sql
CREATE TABLE IF NOT EXISTS vendors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    contact_person TEXT,
    email TEXT,
    phone TEXT,
    website TEXT,
    company_size TEXT,
    address TEXT,              -- JSON object
    categories TEXT,           -- JSON array
    keywords TEXT,
    years_experience INTEGER DEFAULT 0,
    annual_turnover TEXT,
    certifications TEXT,
    preferences TEXT,          -- JSON object
    notifications TEXT,        -- JSON object
    created_date TEXT,
    updated_date TEXT
);

CREATE INDEX idx_vendors_name ON vendors (name);
```

#### Performance Optimizations

1. **Connection Pooling**: Context manager ensures efficient connection reuse
2. **Prepared Statements**: Parameterized queries prevent SQL injection and improve performance
3. **Index Usage**: Strategic indices on frequently queried columns
4. **Batch Operations**: Bulk insert/update support for efficiency
5. **Query Optimization**: WHERE clause pushdown, LIMIT clauses

---

### 2. Web Scraper Component (`utils/web_scraper.py`)

**Purpose**: Extract tender data from procurement portals

**Class**: `TenderScraper`

#### Architecture

```python
class TenderScraper:
    def __init__(self)

    # Core scraping methods
    def scrape_lupc_tenders() -> List[Dict]
    def get_website_text_content(url: str) -> str
    def scrape_tender_page(url: str) -> Optional[Dict]

    # Data extraction methods
    def extract_tender_details(content, soup, url) -> Dict
    def extract_title(soup, content) -> str
    def extract_description(content) -> str
    def extract_category(content, title) -> str
    def extract_value(content) -> int
    def extract_deadline(content) -> str
    def extract_status(content) -> str

    # Helper methods
    def find_tender_links(soup) -> List[str]
    def looks_like_tender_title(text: str) -> bool
    def generate_tender_id(identifier: str) -> str
```

#### Scraping Strategy

**Dual-Mode Extraction**:
1. **Trafilatura**: Main content extraction (clean text)
2. **BeautifulSoup**: Structured data and link extraction

**Fallback Mechanism**:
```
Try Specific Tender Pages
    ↓ (if no links found)
Extract from Main Content
    ↓ (if extraction fails)
Generate Sample Tenders
```

#### Ethical Scraping Practices

1. **Rate Limiting**: 1-second delay between requests
2. **User-Agent**: Identifies as legitimate browser
3. **Respect robots.txt**: Compliance with website policies
4. **Timeout Handling**: 10-second timeout to prevent hanging
5. **Error Recovery**: Graceful fallbacks on failures

#### Data Extraction Patterns

**Regex Patterns for Value**:
```python
patterns = [
    r'£([\d,]+)',
    r'GBP\s*([\d,]+)',
    r'value.*?£([\d,]+)',
    r'worth.*?£([\d,]+)',
    r'budget.*?£([\d,]+)'
]
```

**Category Inference**:
```python
categories = {
    'IT Services & Software': ['software', 'technology', 'digital', ...],
    'Professional Services': ['consulting', 'advisory', 'legal', ...],
    'Facilities Management': ['facilities', 'cleaning', 'maintenance', ...],
    # ... more categories
}
```

---

### 3. Data Processor Component (`utils/data_processor.py`)

**Purpose**: Semantic enhancement and feature engineering

**Class**: `DataProcessor`

#### Processing Pipeline

```
Raw Tender Data
    ↓
1. Text Cleaning & Normalization
    ↓
2. Semantic Tagging (Category Keywords)
    ↓
3. Entity Extraction (spaCy NER)
    ↓
4. Category Enhancement (Multi-label Classification)
    ↓
5. Feature Engineering (Urgency, Complexity)
    ↓
6. Batch Processing (Clustering, Percentiles)
    ↓
Enhanced Tender Data
```

#### Key Processing Methods

```python
class DataProcessor:
    def process_tender_batch(tenders: List[Dict]) -> List[Dict]
    def process_single_tender(tender: Dict) -> Dict

    # Text processing
    def clean_text_fields(tender: Dict) -> Dict

    # Semantic enhancement
    def add_semantic_tags(tender: Dict) -> Dict
    def enhance_category(tender: Dict) -> Dict
    def extract_entities(tender: Dict) -> Dict

    # Feature engineering
    def add_derived_features(tender: Dict) -> Dict
    def calculate_readability(text: str) -> float

    # Batch processing
    def add_batch_features(tenders: List[Dict]) -> List[Dict]
    def create_tender_clusters(tenders, n_clusters) -> List[Dict]
    def analyze_tender_patterns(tenders) -> Dict
```

#### Semantic Tagging Algorithm

**Multi-label Classification**:
```python
for category, keywords in self.category_keywords.items():
    score = 0
    matched_keywords = []

    for keyword in keywords:
        if keyword in content:
            score += 1
            matched_keywords.append(keyword)

    if score > 0:
        tags.append(category)
        tag_scores[category] = {
            'score': score,
            'matched_keywords': matched_keywords,
            'relevance': score / len(keywords)
        }
```

#### Feature Engineering

**Urgency Score Calculation**:
```python
if days_until_deadline <= 7:
    urgency = 1.0  # Very urgent
elif days_until_deadline <= 14:
    urgency = 0.8  # Urgent
elif days_until_deadline <= 30:
    urgency = 0.5  # Moderate
else:
    urgency = 0.2  # Low urgency
```

**Complexity Score Calculation**:
```python
complexity_indicators = {
    'long_description': len(description) > 1000,
    'high_value': value > 100000,
    'multiple_categories': len(semantic_tags) > 2,
    'technical_terms': len(technologies) > 0
}

complexity_score = sum(indicators.values()) / len(indicators)
```

#### Entity Extraction

**spaCy NER Integration**:
```python
doc = self.nlp(text)

for ent in doc.ents:
    if ent.label_ == "ORG":
        entities['organizations'].append(ent.text)
    elif ent.label_ in ["GPE", "LOC"]:
        entities['locations'].append(ent.text)
    elif ent.label_ == "DATE":
        entities['dates'].append(ent.text)
    elif ent.label_ == "MONEY":
        entities['money'].append(ent.text)
```

---

### 4. ML Engine Component (`utils/ml_engine.py`)

**Purpose**: Personalized tender recommendations using machine learning

**Class**: `MLEngine`

#### Recommendation Architecture

```
Vendor Profile Input
    ↓
┌─────────────────────────────────────┐
│  Multi-Algorithm Matching           │
│  ┌─────────────────────────────┐   │
│  │ 1. Category-Based (40%)     │   │
│  │ 2. Content-Based (30%)      │   │
│  │ 3. Value-Based (20%)        │   │
│  │ 4. Preference-Based (10%)   │   │
│  └─────────────────────────────┘   │
└─────────────────┬───────────────────┘
                  ↓
         Score Combination
                  ↓
      Ranked Recommendations
```

#### Algorithm Details

**1. Category-Based Matching (40% weight)**

```python
def _category_based_matching(vendor_profile, tenders_df):
    # Direct category match
    if tender_category in vendor_categories:
        score += 0.8

    # Semantic tag overlap
    common_categories = set(vendor_categories) & set(tender_tags)
    if common_categories:
        score += 0.6 * len(common_categories) / max(len(vendor_categories), len(tender_tags))

    # Keyword matching
    keyword_matches = count_keyword_matches(vendor_keywords, tender_text)
    score += 0.4 * (keyword_matches / len(vendor_keywords))

    return score
```

**2. Content-Based Filtering (30% weight)**

Uses **TF-IDF + Cosine Similarity**:

```python
def _content_based_filtering(vendor_profile, tenders_df):
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=1
    )

    # Vendor profile text
    vendor_text = create_vendor_text_profile(vendor_profile)

    # Tender texts
    tender_texts = [create_tender_text(t) for t in tenders]

    # Combine and vectorize
    all_texts = [vendor_text] + tender_texts
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # Calculate cosine similarity
    vendor_vector = tfidf_matrix[0]
    tender_vectors = tfidf_matrix[1:]
    similarities = cosine_similarity(vendor_vector, tender_vectors)

    return similarities
```

**3. Value-Based Filtering (20% weight)**

```python
def _value_based_filtering(vendor_profile, tenders_df):
    min_value = preferences.get('min_value', 0)
    max_value = preferences.get('max_value', float('inf'))

    # Perfect match
    if min_value <= tender_value <= max_value:
        score = 1.0

        # Bonus for sweet spot (middle 40% of range)
        range_position = (tender_value - min_value) / (max_value - min_value)
        if 0.3 <= range_position <= 0.7:
            score += 0.2

    # Partial match (with tolerance)
    elif tender_value < min_value:
        ratio = tender_value / min_value
        if ratio > 0.5:
            score = 0.3 * ratio
    elif tender_value > max_value:
        ratio = max_value / tender_value
        if ratio > 0.3:
            score = 0.4 * ratio

    return score
```

**4. Preference-Based Filtering (10% weight)**

```python
def _preference_based_filtering(vendor_profile, tenders_df):
    # Location preference
    if region in preferred_regions:
        score += 0.6

    # Timeline preference (adequate preparation time)
    if days_until_deadline > 7:
        score += 0.4
    elif days_until_deadline > 0:
        score += 0.2

    # Status preference
    if status == 'active':
        score += 0.3

    # Organization type match
    if organization_matches_vendor_background:
        score += 0.2

    return score
```

#### Score Combination

**Weighted Average with Confidence**:

```python
def _combine_scores(score_dicts):
    method_weights = {
        'category_based': 0.4,
        'content_based': 0.3,
        'value_based': 0.2,
        'preference_based': 0.1
    }

    for tender_id in all_tender_ids:
        total_score = 0
        method_count = 0

        for method, weight in method_weights.items():
            if tender_id in method_scores[method]:
                total_score += method_scores[method][tender_id] * weight
                method_count += 1

        # Confidence based on how many methods matched
        confidence = method_count / len(method_weights)

        # Normalize score
        normalized_score = total_score / sum(method_weights.values())

        combined[tender_id] = {
            'total_score': normalized_score,
            'confidence': confidence
        }

    return combined
```

#### Caching Strategy

```python
def get_recommendations(vendor_profile, limit):
    cache_key = f"{vendor_profile['name']}_{limit}"

    # Check cache validity (1 hour timeout)
    if self._is_cache_valid(cache_key):
        return self.recommendation_cache[cache_key]['data']

    # Generate fresh recommendations
    recommendations = self._generate_recommendations(...)

    # Cache results
    self.recommendation_cache[cache_key] = {
        'data': recommendations,
        'timestamp': datetime.now()
    }

    return recommendations
```

---

### 5. AI Assistant Component (`utils/ai_assistant.py`)

**Purpose**: Conversational AI for tender analysis and guidance

**Class**: `AIAssistant`

#### Architecture

```
User Query
    ↓
┌─────────────────────────────┐
│  Context Preparation        │
│  - Recent tenders           │
│  - Tender statistics        │
│  - Vendor profiles          │
│  - Conversation history     │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Mode-Specific System       │
│  Prompt Selection           │
│  - General Assistant        │
│  - Tender Analysis          │
│  - Compliance Helper        │
│  - Market Research          │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  OpenAI GPT-4o API          │
│  - max_tokens: 1500         │
│  - temperature: 0.7         │
│  - model: gpt-4o            │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Response Processing        │
│  - Format cleanup           │
│  - History update           │
│  - Error handling           │
└─────────────────────────────┘
             ↓
      AI Response
```

#### System Prompts

**General Assistant Mode**:
```python
"""You are an AI assistant for a tender discovery platform. You help vendors
understand procurement opportunities, navigate the tendering process, and provide
insights about market trends.

Your expertise includes:
- Public and private sector procurement processes
- Tender compliance and documentation requirements
- Market analysis and competitive positioning
- Business development strategies for vendors
- UK procurement regulations and best practices

Always provide practical, actionable advice."""
```

**Tender Analysis Mode**:
```python
"""You are a specialized tender analysis expert. Your role is to analyze tender
documents, requirements, and help vendors understand:

- Tender specifications and requirements
- Evaluation criteria and scoring mechanisms
- Compliance requirements and documentation needed
- Risk assessment and mitigation strategies
- Competitive positioning and differentiation opportunities
- Bid writing best practices and strategies

When analyzing tenders, be thorough and systematic."""
```

#### Context Injection

```python
def _format_context(context):
    context_parts = []

    # Recent tenders
    if context.get('recent_tenders'):
        tenders = context['recent_tenders'][:5]
        context_parts.append("Recent Available Tenders:")
        for tender in tenders:
            context_parts.append(
                f"- {tender['title']} | {tender['category']} | "
                f"£{tender['value']:,.0f} | {tender['deadline']}"
            )

    # Statistics
    if context.get('tender_stats'):
        stats = context['tender_stats']
        context_parts.append(f"Total tenders: {stats['total_count']}")
        context_parts.append(f"Active tenders: {stats['active_count']}")

    return "\n".join(context_parts)
```

#### Conversation Management

```python
def chat_with_context(user_message, conversation_id, context):
    # Initialize or retrieve conversation history
    if conversation_id not in self.conversation_history:
        self.conversation_history[conversation_id] = []

    # Add user message
    self.conversation_history[conversation_id].append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })

    # Get AI response with history
    response = self.get_response(
        user_message,
        context=context,
        chat_history=self.conversation_history[conversation_id][-6:]  # Last 6 messages
    )

    # Add assistant response
    self.conversation_history[conversation_id].append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat()
    })

    # Limit history size
    if len(self.conversation_history[conversation_id]) > 20:
        self.conversation_history[conversation_id] = \
            self.conversation_history[conversation_id][-20:]

    return response
```

#### Document Analysis

```python
def analyze_tender_document(document_text, analysis_type="general"):
    analysis_prompts = {
        "general": """Analyze this tender document and provide:
        1. Key requirements and scope of work
        2. Evaluation criteria and scoring methodology
        3. Important deadlines and milestones
        4. Compliance requirements
        5. Value/budget information
        6. Key risks and challenges
        7. Success factors and recommendations""",

        "compliance": """Focus on compliance requirements:
        1. Mandatory requirements that could lead to disqualification
        2. Documentation required for submission
        3. Technical specifications and standards
        4. Legal and regulatory requirements
        5. Social value and sustainability requirements
        6. Insurance and financial requirements
        7. Quality assurance and accreditation needs"""
    }

    # Call OpenAI with specific prompt
    response = self.client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert tender analyst..."},
            {"role": "user", "content": f"{prompt}\n\nTender Document:\n{document_text[:3000]}"}
        ],
        max_tokens=2000,
        temperature=0.3  # Lower temperature for focused analysis
    )

    return response
```

---

## Frontend Architecture

### Streamlit Multi-Page Application

**Application Structure**:
```
app.py (Main entry point)
├── pages/
│   ├── 1_📊_Dashboard.py
│   ├── 2_🔍_Smart_Search.py
│   ├── 3_🤖_AI_Assistant.py
│   ├── 4_🔔_Alert_Center.py
│   ├── 6_🎯_Recommendations.py
│   ├── 7_👤_Vendor_Dashboard.py
│   └── 8_📄_Tender_Documents.py
```

### State Management

**Session State Architecture**:
```python
# Initialized in app.py
st.session_state.db = Database()
st.session_state.scraper = TenderScraper()
st.session_state.processor = DataProcessor()
st.session_state.ai_assistant = AIAssistant()
st.session_state.ml_engine = MLEngine()

# Page-specific state
st.session_state.search_history = []
st.session_state.conversation_history = {}
st.session_state.current_vendor = None
st.session_state.alerts = []
```

### Component Initialization Pattern

```python
@st.cache_resource
def init_components():
    """Initialize heavy components once and cache"""
    db = Database()
    scraper = TenderScraper()
    processor = DataProcessor()
    return db, scraper, processor

def main():
    # Get cached components
    db, scraper, processor = init_components()

    # Store in session state for page access
    if "db" not in st.session_state:
        st.session_state.db = db
    # ... similar for other components
```

### Error Handling Pattern

```python
try:
    # Attempt operation
    result = perform_operation()

    if result:
        st.success("Operation completed successfully!")
    else:
        st.warning("Operation completed with warnings.")

except DatabaseError as e:
    st.error(f"Database error: {str(e)}")
    logger.error(f"DB Error: {str(e)}", exc_info=True)

except APIError as e:
    st.error(f"API error: {str(e)}")
    st.info("Please check your API configuration.")

except Exception as e:
    st.error(f"Unexpected error: {str(e)}")
    logger.critical(f"Critical error: {str(e)}", exc_info=True)
```

---

## Performance Optimization

### Database Optimization

1. **Indexing Strategy**:
   - category, status, deadline for tenders table
   - name for vendors table
   - Composite indices for common query patterns

2. **Query Optimization**:
   - Use LIMIT clauses for pagination
   - WHERE clause pushdown
   - Avoid SELECT * when possible
   - Use EXISTS instead of COUNT(*) for existence checks

3. **Connection Management**:
   - Context managers for automatic cleanup
   - Connection pooling through session state
   - Timeout configuration (30 seconds)

### Caching Strategy

1. **Component-level caching**:
   ```python
   @st.cache_resource
   def init_components():
       # Heavy initialization once per session
   ```

2. **Data-level caching**:
   ```python
   @st.cache_data(ttl=3600)
   def get_tender_statistics():
       # Cache expensive calculations
   ```

3. **ML Model caching**:
   ```python
   # In MLEngine class
   self.recommendation_cache = {}
   self.cache_timeout = 3600  # 1 hour
   ```

### Lazy Loading

- Load tender details on-demand (not all at once)
- Paginated results for large datasets
- Incremental loading for search results

---

## Error Handling & Logging

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tender_platform.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Error Handling Hierarchy

```
┌─────────────────────────────┐
│  User-Facing Errors         │
│  (Streamlit UI messages)    │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Application Errors         │
│  (Logged with context)      │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  System Errors              │
│  (Critical logging)         │
└─────────────────────────────┘
```

### Graceful Degradation

```python
# AI Assistant fallback
if not ai_assistant:
    st.warning("AI features unavailable - using basic search")
    return perform_basic_search(query, tenders)

# spaCy model fallback
try:
    self.nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found - limited NLP features")
    self.nlp = None
```

---

## Testing Strategy

### Unit Testing
- Test individual component methods
- Mock external dependencies (DB, API)
- Coverage target: 70%+

### Integration Testing
- Test component interactions
- Database operations with test DB
- API integration with mock responses

### End-to-End Testing
- User journey testing
- Multi-page navigation
- Data flow validation

### Performance Testing
- Load testing with large datasets (1000+ tenders)
- Response time benchmarks
- Memory profiling

---

## Deployment Architecture

### Current Deployment (Replit)

```
┌─────────────────────────────┐
│    Replit Container         │
│  ┌───────────────────────┐  │
│  │  Python 3.11+         │  │
│  │  Streamlit Server     │  │
│  │  Port: 8501           │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │  SQLite Database      │  │
│  │  (File-based)         │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │  Environment Config   │  │
│  │  (.env file)          │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

### Production Deployment Recommendations

```
┌─────────────────────────────────────────────┐
│             Load Balancer (NGINX)            │
└──────────────┬──────────────┬────────────────┘
               │              │
    ┌──────────▼─────┐  ┌────▼──────────┐
    │ Streamlit      │  │ Streamlit     │
    │ Instance 1     │  │ Instance 2    │
    └──────────┬─────┘  └────┬──────────┘
               │              │
    ┌──────────▼──────────────▼──────────┐
    │      PostgreSQL Database           │
    │      (with connection pooling)     │
    └────────────────────────────────────┘
    ┌────────────────────────────────────┐
    │         Redis Cache                │
    │    (for session & ML cache)        │
    └────────────────────────────────────┘
```

---

## Security Considerations

### Input Validation
```python
def validate_vendor_input(vendor_data):
    required_fields = ['name', 'email', 'categories']

    for field in required_fields:
        if not vendor_data.get(field):
            raise ValidationError(f"Missing required field: {field}")

    # Email validation
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_pattern, vendor_data['email']):
        raise ValidationError("Invalid email format")

    return True
```

### SQL Injection Prevention
- Always use parameterized queries
- No string concatenation for SQL
- Input sanitization

### API Key Management
```python
# Never commit API keys
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not configured")
```

### Data Privacy
- Minimal data collection
- No PII without consent
- Secure storage of vendor profiles
- Right to deletion

---

## Monitoring & Observability

### Recommended Metrics
- Request latency (p50, p95, p99)
- Error rates by component
- Database query performance
- API call success/failure rates
- User engagement metrics

### Logging Best Practices
```python
# Structured logging
logger.info(
    "Tender scraped",
    extra={
        'tender_id': tender_id,
        'source': 'LUPC',
        'duration_ms': duration
    }
)
```

---

## Conclusion

The BidRadar technical architecture is designed for modularity, maintainability, and scalability. The component-based design enables independent development and testing, while the multi-layered architecture ensures clear separation of concerns. With comprehensive error handling, logging, and optimization strategies, the platform is production-ready and extensible for future enhancements.
