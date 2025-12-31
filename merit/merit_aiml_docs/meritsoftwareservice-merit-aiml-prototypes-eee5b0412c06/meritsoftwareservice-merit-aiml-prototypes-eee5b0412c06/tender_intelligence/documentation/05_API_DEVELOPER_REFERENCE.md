# BidRadar - API & Developer Reference

**Version:** 1.0
**Last Updated:** December 2025
**Audience:** Developers, Integration Engineers, Technical Contributors

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components API](#core-components-api)
3. [Database API](#database-api)
4. [Machine Learning API](#machine-learning-api)
5. [AI Assistant API](#ai-assistant-api)
6. [Web Scraper API](#web-scraper-api)
7. [Data Processor API](#data-processor-api)
8. [Frontend Integration](#frontend-integration)
9. [Extension Points](#extension-points)
10. [Code Examples](#code-examples)
11. [Testing](#testing)
12. [Contributing Guidelines](#contributing-guidelines)

---

## Architecture Overview

### Module Structure

```
tender_intelligence/
├── app.py                          # Main Streamlit application
├── create_demo_data.py             # Demo data generator
├── utils/                          # Core utilities
│   ├── database.py                 # Database abstraction layer
│   ├── ml_engine.py                # Machine learning engine
│   ├── ai_assistant.py             # AI assistant integration
│   ├── web_scraper.py              # Web scraping utilities
│   └── data_processor.py           # Data processing pipeline
├── pages/                          # Streamlit pages
│   ├── 1_📊_Dashboard.py
│   ├── 2_🔍_Smart_Search.py
│   ├── 3_🤖_AI_Assistant.py
│   ├── 4_🔔_Alert_Center.py
│   ├── 6_🎯_Recommendations.py
│   ├── 7_👤_Vendor_Dashboard.py
│   └── 8_📄_Tender_Documents.py
└── .streamlit/                     # Streamlit configuration
    └── config.toml
```

### Import Conventions

```python
# Database operations
from utils.database import Database

# Machine learning
from utils.ml_engine import MLEngine

# AI assistance
from utils.ai_assistant import AIAssistant

# Web scraping
from utils.web_scraper import TenderScraper

# Data processing
from utils.data_processor import DataProcessor

# Standard libraries
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
```

---

## Core Components API

### Application Initialization

```python
import streamlit as st
from utils.database import Database
from utils.web_scraper import TenderScraper
from utils.data_processor import DataProcessor

@st.cache_resource
def init_components():
    """
    Initialize core components with caching.

    Returns:
        tuple: (Database, TenderScraper, DataProcessor)

    Example:
        >>> db, scraper, processor = init_components()
        >>> tenders = db.get_all_tenders()
    """
    db = Database()
    scraper = TenderScraper()
    processor = DataProcessor()
    return db, scraper, processor
```

### Session State Management

```python
# Initialize in app.py
def initialize_session_state():
    """Initialize Streamlit session state with components."""
    if "db" not in st.session_state:
        st.session_state.db = Database()

    if "scraper" not in st.session_state:
        st.session_state.scraper = TenderScraper()

    if "processor" not in st.session_state:
        st.session_state.processor = DataProcessor()

    if "ai_assistant" not in st.session_state:
        try:
            st.session_state.ai_assistant = AIAssistant()
        except Exception as e:
            st.session_state.ai_assistant = None
            st.error(f"AI Assistant unavailable: {e}")

    if "ml_engine" not in st.session_state:
        st.session_state.ml_engine = MLEngine()

# Access in pages
db = st.session_state.db
tenders = db.get_all_tenders()
```

---

## Database API

### Class: `Database`

**Location**: `utils/database.py`

#### Constructor

```python
Database(db_path: str = "tender_platform.db")
```

**Parameters**:
- `db_path` (str): Path to SQLite database file. Default: "tender_platform.db"

**Example**:
```python
# Default database
db = Database()

# Custom database path
db = Database("/path/to/custom.db")
```

#### Tender Operations

##### `store_tenders(tenders: List[Dict]) -> bool`

Store or update tender records in database.

**Parameters**:
- `tenders` (List[Dict]): List of tender dictionaries

**Returns**:
- `bool`: True if successful, False otherwise

**Example**:
```python
tenders = [
    {
        'id': 'TENDER-001',
        'title': 'IT Services Framework',
        'description': 'Comprehensive IT services...',
        'category': 'IT Services & Software',
        'value': 500000,
        'deadline': '2025-03-15',
        'status': 'Active',
        'organization': 'LUPC',
        'location': 'UK'
    }
]

success = db.store_tenders(tenders)
if success:
    print("Tenders stored successfully")
```

##### `get_all_tenders() -> List[Dict]`

Retrieve all tenders from database.

**Returns**:
- `List[Dict]`: List of tender dictionaries

**Example**:
```python
tenders = db.get_all_tenders()
print(f"Total tenders: {len(tenders)}")

for tender in tenders[:5]:
    print(f"{tender['title']} - £{tender['value']:,}")
```

##### `get_recent_tenders(limit: int = 10) -> List[Dict]`

Get most recently added tenders.

**Parameters**:
- `limit` (int): Maximum number of tenders to return. Default: 10

**Returns**:
- `List[Dict]`: List of recent tender dictionaries

**Example**:
```python
recent = db.get_recent_tenders(limit=5)
for tender in recent:
    print(f"{tender['created_at']}: {tender['title']}")
```

##### `get_tenders_by_category(category: str) -> List[Dict]`

Get tenders filtered by category.

**Parameters**:
- `category` (str): Category name (e.g., "IT Services & Software")

**Returns**:
- `List[Dict]`: List of matching tender dictionaries

**Example**:
```python
it_tenders = db.get_tenders_by_category("IT Services & Software")
total_value = sum(t['value'] for t in it_tenders)
print(f"IT tenders: {len(it_tenders)}, Total value: £{total_value:,}")
```

##### `search_tenders(query: str, filters: Dict = None) -> List[Dict]`

Search tenders with text query and optional filters.

**Parameters**:
- `query` (str): Search query string
- `filters` (Dict, optional): Additional filters
  - `category` (str): Filter by category
  - `status` (str): Filter by status
  - `min_value` (float): Minimum contract value
  - `max_value` (float): Maximum contract value

**Returns**:
- `List[Dict]`: List of matching tender dictionaries

**Example**:
```python
# Simple search
results = db.search_tenders("cloud computing")

# Search with filters
results = db.search_tenders(
    "software development",
    filters={
        'category': 'IT Services & Software',
        'status': 'Active',
        'min_value': 100000,
        'max_value': 1000000
    }
)

print(f"Found {len(results)} matching tenders")
```

#### Vendor Operations

##### `create_vendor(vendor_data: Dict) -> bool`

Create a new vendor profile.

**Parameters**:
- `vendor_data` (Dict): Vendor information dictionary

**Required Fields**:
- `name` (str): Company name
- `email` (str): Contact email
- `categories` (List[str]): Business categories

**Optional Fields**:
- `contact_person`, `phone`, `website`, `company_size`, `address`, `keywords`, `years_experience`, `annual_turnover`, `certifications`, `preferences`, `notifications`

**Returns**:
- `bool`: True if successful, False otherwise

**Example**:
```python
vendor_data = {
    'name': 'TechCorp Solutions',
    'contact_person': 'John Doe',
    'email': 'john@techcorp.com',
    'phone': '+44 20 1234 5678',
    'website': 'https://techcorp.com',
    'company_size': 'Medium (50-249 employees)',
    'categories': ['IT Services & Software', 'Professional Services'],
    'keywords': 'cloud computing, cybersecurity, DevOps',
    'years_experience': 10,
    'annual_turnover': '£5M - £10M',
    'certifications': 'ISO 27001, Cyber Essentials',
    'preferences': {
        'min_value': 50000,
        'max_value': 2000000,
        'regions': ['London', 'South East']
    },
    'notifications': {
        'email': True,
        'frequency': 'Daily'
    }
}

success = db.create_vendor(vendor_data)
```

##### `update_vendor(vendor_data: Dict) -> bool`

Update existing vendor profile.

**Parameters**:
- `vendor_data` (Dict): Updated vendor information (must include `name`)

**Returns**:
- `bool`: True if successful, False otherwise

**Example**:
```python
updated_data = {
    'name': 'TechCorp Solutions',  # Required for lookup
    'keywords': 'cloud computing, AI, machine learning, cybersecurity',
    'certifications': 'ISO 27001, ISO 9001, Cyber Essentials Plus',
    'preferences': {
        'min_value': 100000,
        'max_value': 5000000,
        'regions': ['London', 'South East', 'East of England']
    }
}

success = db.update_vendor(updated_data)
```

##### `get_all_vendors() -> List[Dict]`

Retrieve all vendor profiles.

**Returns**:
- `List[Dict]`: List of vendor dictionaries

**Example**:
```python
vendors = db.get_all_vendors()
for vendor in vendors:
    print(f"{vendor['name']} - {vendor['categories']}")
```

##### `get_vendor_by_name(name: str) -> Optional[Dict]`

Retrieve specific vendor by name.

**Parameters**:
- `name` (str): Vendor company name

**Returns**:
- `Dict` or `None`: Vendor dictionary if found, None otherwise

**Example**:
```python
vendor = db.get_vendor_by_name("TechCorp Solutions")
if vendor:
    print(f"Contact: {vendor['contact_person']}")
    print(f"Email: {vendor['email']}")
else:
    print("Vendor not found")
```

#### Interaction Tracking

##### `record_vendor_interest(vendor_name: str, tender_id: str, interest_type: str) -> bool`

Record vendor interest in a tender.

**Parameters**:
- `vendor_name` (str): Vendor company name
- `tender_id` (str): Tender ID
- `interest_type` (str): One of: "interested", "not_relevant", "applied"

**Returns**:
- `bool`: True if successful, False otherwise

**Example**:
```python
# Mark as interested
db.record_vendor_interest(
    "TechCorp Solutions",
    "LUPC-2024-001",
    "interested"
)

# Mark as not relevant
db.record_vendor_interest(
    "TechCorp Solutions",
    "LUPC-2024-002",
    "not_relevant"
)

# Mark as applied
db.record_vendor_interest(
    "TechCorp Solutions",
    "LUPC-2024-003",
    "applied"
)
```

##### `get_vendor_interests(vendor_name: str) -> List[Dict]`

Get vendor's recorded interests.

**Parameters**:
- `vendor_name` (str): Vendor company name

**Returns**:
- `List[Dict]`: List of interest records with tender details

**Example**:
```python
interests = db.get_vendor_interests("TechCorp Solutions")

# Group by interest type
from collections import defaultdict
by_type = defaultdict(list)

for interest in interests:
    by_type[interest['interest_type']].append(interest)

print(f"Interested: {len(by_type['interested'])}")
print(f"Applied: {len(by_type['applied'])}")
```

#### Analytics

##### `get_database_stats() -> Dict[str, Any]`

Get comprehensive database statistics.

**Returns**:
- `Dict`: Statistics dictionary containing:
  - `total_tenders`: Total tender count
  - `active_tenders`: Active tender count
  - `total_vendors`: Total vendor count
  - `total_interests`: Total interest records
  - `top_categories`: List of top 5 categories with counts
  - `average_value`: Average tender value
  - `total_value`: Total tender value

**Example**:
```python
stats = db.get_database_stats()

print(f"Total Tenders: {stats['total_tenders']}")
print(f"Active Tenders: {stats['active_tenders']}")
print(f"Total Value: £{stats['total_value']:,.0f}")
print(f"Average Value: £{stats['average_value']:,.0f}")

print("\nTop Categories:")
for category_info in stats['top_categories']:
    print(f"  {category_info['category']}: {category_info['count']}")
```

---

## Machine Learning API

### Class: `MLEngine`

**Location**: `utils/ml_engine.py`

#### Constructor

```python
MLEngine()
```

**Example**:
```python
from utils.ml_engine import MLEngine

ml_engine = MLEngine()
```

#### Recommendation Methods

##### `get_recommendations(vendor_profile: Dict, limit: int = 20) -> List[Dict]`

Generate personalized tender recommendations for a vendor.

**Parameters**:
- `vendor_profile` (Dict): Vendor profile dictionary (from database)
- `limit` (int): Maximum number of recommendations. Default: 20

**Returns**:
- `List[Dict]`: List of recommended tenders with match scores

**Each recommendation includes**:
- All tender fields
- `match_score` (float): 0-1 overall match score
- `match_reasons` (List[str]): Specific reasons for match
- `recommendation_confidence` (float): 0-1 confidence level

**Example**:
```python
import streamlit as st

# Get vendor profile
vendor = db.get_vendor_by_name("TechCorp Solutions")

# Generate recommendations
ml_engine = MLEngine()
recommendations = ml_engine.get_recommendations(vendor, limit=10)

# Display results
for rec in recommendations:
    score = rec['match_score']
    print(f"\nTender: {rec['title']}")
    print(f"Match Score: {score:.1%}")
    print(f"Value: £{rec['value']:,}")
    print("Reasons:")
    for reason in rec['match_reasons']:
        print(f"  - {reason}")
```

##### `get_similar_tenders(tender_id: str, limit: int = 5) -> List[Dict]`

Find tenders similar to a given tender.

**Parameters**:
- `tender_id` (str): Target tender ID
- `limit` (int): Maximum number of similar tenders. Default: 5

**Returns**:
- `List[Dict]`: List of similar tenders with similarity scores

**Each result includes**:
- All tender fields
- `similarity_score` (float): 0-1 similarity score

**Example**:
```python
# Find tenders similar to a specific tender
similar = ml_engine.get_similar_tenders("LUPC-2024-001", limit=5)

for tender in similar:
    print(f"{tender['title']}: {tender['similarity_score']:.2f}")
```

##### `get_vendor_insights(vendor_name: str) -> Dict[str, Any]`

Generate insights about vendor's tender matching patterns.

**Parameters**:
- `vendor_name` (str): Vendor company name

**Returns**:
- `Dict`: Insights dictionary containing:
  - `vendor_name`: Vendor name
  - `total_recommendations`: Total recommendation count
  - `high_match_count`: Count of high-quality matches (>70%)
  - `average_match_score`: Mean match score
  - `top_categories`: Top matching categories
  - `value_range_analysis`: Value range statistics

**Example**:
```python
insights = ml_engine.get_vendor_insights("TechCorp Solutions")

print(f"Average Match Score: {insights['average_match_score']:.1%}")
print(f"High Matches: {insights['high_match_count']}")

print("\nTop Categories:")
for category, count in insights['top_categories'].items():
    print(f"  {category}: {count}")

print("\nValue Range Analysis:")
value_analysis = insights['value_range_analysis']
print(f"  Min: £{value_analysis['min_value']:,}")
print(f"  Max: £{value_analysis['max_value']:,}")
print(f"  Average: £{value_analysis['avg_value']:,}")
```

#### Model Training

##### `train_recommendation_model(tenders: List[Dict], vendor_interactions: List[Dict] = None)`

Train or update the recommendation model with new data.

**Parameters**:
- `tenders` (List[Dict]): List of tender dictionaries
- `vendor_interactions` (List[Dict], optional): Historical interaction data

**Example**:
```python
# Get all tenders
tenders = db.get_all_tenders()

# Train model
ml_engine.train_recommendation_model(tenders)
print("Model training completed")
```

---

## AI Assistant API

### Class: `AIAssistant`

**Location**: `utils/ai_assistant.py`

#### Constructor

```python
AIAssistant()
```

**Raises**:
- `ValueError`: If OPENAI_API_KEY environment variable is not set

**Example**:
```python
import os
from utils.ai_assistant import AIAssistant

# Ensure API key is set
os.environ['OPENAI_API_KEY'] = 'sk-...'

# Initialize assistant
ai = AIAssistant()
```

#### Response Generation

##### `get_response(user_input: str, context: Dict = None, mode: str = "General Assistant", chat_history: List[Dict] = None) -> str`

Generate AI response based on user input and context.

**Parameters**:
- `user_input` (str): User's question or message
- `context` (Dict, optional): Additional context including:
  - `current_time`: Current date/time
  - `recent_tenders`: List of recent tenders
  - `tender_stats`: Tender statistics
  - `vendor_profiles`: Vendor information
- `mode` (str): Assistant mode. Options:
  - "General Assistant" (default)
  - "Tender Analysis"
  - "Compliance Helper"
  - "Market Research"
- `chat_history` (List[Dict], optional): Recent chat messages for context

**Returns**:
- `str`: AI assistant response

**Example**:
```python
# Basic usage
response = ai.get_response("What is a framework agreement?")
print(response)

# With context
context = {
    'current_time': datetime.now().isoformat(),
    'recent_tenders': db.get_recent_tenders(5),
    'tender_stats': {
        'total_count': 150,
        'active_count': 45
    }
}

response = ai.get_response(
    "What tender opportunities are currently available?",
    context=context
)

# With specific mode
response = ai.get_response(
    "What are the Public Contract Regulations 2015?",
    mode="Compliance Helper"
)

# With conversation history
chat_history = [
    {"role": "user", "content": "Tell me about IT tenders"},
    {"role": "assistant", "content": "IT tenders typically..."}
]

response = ai.get_response(
    "What about values?",
    chat_history=chat_history
)
```

##### `chat_with_context(user_message: str, conversation_id: str, context: Dict = None) -> str`

Handle contextual chat with conversation memory.

**Parameters**:
- `user_message` (str): User's message
- `conversation_id` (str): Unique identifier for conversation
- `context` (Dict, optional): Current context information

**Returns**:
- `str`: AI response

**Conversation history automatically maintained for each conversation_id (last 20 messages)**

**Example**:
```python
# Start a conversation
conversation_id = "user123_session1"

response1 = ai.chat_with_context(
    "Tell me about the cloud computing tender",
    conversation_id=conversation_id
)

# Continue conversation (history is remembered)
response2 = ai.chat_with_context(
    "What are the compliance requirements?",
    conversation_id=conversation_id
)

# Response will reference previous context
```

#### Document Analysis

##### `analyze_tender_document(document_text: str, analysis_type: str = "general") -> Dict[str, Any]`

Analyze a tender document and extract key information.

**Parameters**:
- `document_text` (str): Full text of tender document
- `analysis_type` (str): Type of analysis. Options:
  - "general": Comprehensive overview
  - "compliance": Compliance requirements
  - "evaluation": Evaluation methodology

**Returns**:
- `Dict`: Analysis results containing:
  - `analysis_type`: Type of analysis performed
  - `analysis_text`: Full analysis text
  - `document_length`: Length of document
  - `analysis_date`: Timestamp
  - `key_insights`: List of key insights

**Example**:
```python
# Read tender document
with open('tender_document.txt', 'r') as f:
    document_text = f.read()

# Perform general analysis
analysis = ai.analyze_tender_document(document_text, "general")

print(f"Analysis Type: {analysis['analysis_type']}")
print(f"Document Length: {analysis['document_length']}")
print(f"\nAnalysis:\n{analysis['analysis_text']}")

print("\nKey Insights:")
for insight in analysis['key_insights']:
    print(f"  - {insight}")

# Perform compliance analysis
compliance_analysis = ai.analyze_tender_document(
    document_text,
    "compliance"
)
print(compliance_analysis['analysis_text'])
```

#### Market Intelligence

##### `generate_market_insights(tender_data: List[Dict], timeframe: str = "recent") -> str`

Generate market insights based on tender data.

**Parameters**:
- `tender_data` (List[Dict]): List of tender dictionaries
- `timeframe` (str): Analysis timeframe ("recent", "quarterly", "annual")

**Returns**:
- `str`: Market insights text

**Example**:
```python
# Get tender data
tenders = db.get_all_tenders()

# Generate market insights
insights = ai.generate_market_insights(tenders, "recent")

print("Market Insights:")
print(insights)

# Save to file
with open('market_insights.txt', 'w') as f:
    f.write(insights)
```

##### `get_tender_recommendations_explanation(vendor_profile: Dict, recommendations: List[Dict]) -> str`

Explain why specific tenders were recommended.

**Parameters**:
- `vendor_profile` (Dict): Vendor profile dictionary
- `recommendations` (List[Dict]): List of recommended tenders

**Returns**:
- `str`: Explanation text

**Example**:
```python
# Get vendor and recommendations
vendor = db.get_vendor_by_name("TechCorp Solutions")
recommendations = ml_engine.get_recommendations(vendor, limit=5)

# Get explanation
explanation = ai.get_tender_recommendations_explanation(
    vendor,
    recommendations
)

print("Why These Tenders Were Recommended:")
print(explanation)
```

---

## Web Scraper API

### Class: `TenderScraper`

**Location**: `utils/web_scraper.py`

#### Constructor

```python
TenderScraper()
```

**Example**:
```python
from utils.web_scraper import TenderScraper

scraper = TenderScraper()
```

#### Scraping Methods

##### `scrape_lupc_tenders() -> List[Dict]`

Scrape tender data from LUPC procurement portal.

**Returns**:
- `List[Dict]`: List of scraped tender dictionaries

**Each tender includes**:
- `id`, `title`, `description`, `category`, `value`, `deadline`, `status`, `organization`, `location`, `url`, `source`, `scraped_date`

**Example**:
```python
# Scrape LUPC tenders
scraper = TenderScraper()
tenders = scraper.scrape_lupc_tenders()

print(f"Scraped {len(tenders)} tenders")

# Process and store
processor = DataProcessor()
processed_tenders = processor.process_tender_batch(tenders)

db = Database()
db.store_tenders(processed_tenders)
```

##### `get_website_text_content(url: str) -> str`

Extract clean text content from a website URL.

**Parameters**:
- `url` (str): Website URL

**Returns**:
- `str`: Extracted text content

**Example**:
```python
url = "https://www.lupc.ac.uk/procurement/tender-123"
content = scraper.get_website_text_content(url)

print(f"Content length: {len(content)} characters")
print(content[:200])  # First 200 characters
```

#### Utility Methods

##### `generate_tender_id(identifier: str) -> str`

Generate a unique tender ID from an identifier string.

**Parameters**:
- `identifier` (str): Source identifier (URL or unique string)

**Returns**:
- `str`: 8-character MD5 hash

**Example**:
```python
url = "https://www.lupc.ac.uk/tender/12345"
tender_id = scraper.generate_tender_id(url)
print(f"Tender ID: {tender_id}")  # e.g., "a1b2c3d4"
```

---

## Data Processor API

### Class: `DataProcessor`

**Location**: `utils/data_processor.py`

#### Constructor

```python
DataProcessor()
```

**Example**:
```python
from utils.data_processor import DataProcessor

processor = DataProcessor()
```

#### Processing Methods

##### `process_tender_batch(tenders: List[Dict]) -> List[Dict]`

Process a batch of tender data with semantic enhancement.

**Parameters**:
- `tenders` (List[Dict]): List of raw tender dictionaries

**Returns**:
- `List[Dict]`: List of processed and enhanced tender dictionaries

**Enhancements applied**:
- Text cleaning and normalization
- Semantic tagging (multi-label classification)
- Entity extraction (organizations, locations, technologies)
- Category enhancement
- Feature engineering (urgency, complexity scores)
- Batch features (clustering, percentiles)

**Example**:
```python
# Scrape raw tenders
scraper = TenderScraper()
raw_tenders = scraper.scrape_lupc_tenders()

# Process batch
processor = DataProcessor()
processed_tenders = processor.process_tender_batch(raw_tenders)

# Compare before/after
print("Before processing:")
print(f"  Semantic tags: {raw_tenders[0].get('semantic_tags', 'None')}")

print("\nAfter processing:")
print(f"  Semantic tags: {processed_tenders[0]['semantic_tags']}")
print(f"  Urgency score: {processed_tenders[0]['urgency_score']}")
print(f"  Complexity score: {processed_tenders[0]['complexity_score']}")
```

##### `process_single_tender(tender: Dict) -> Dict`

Process a single tender with semantic enhancement.

**Parameters**:
- `tender` (Dict): Raw tender dictionary

**Returns**:
- `Dict`: Processed tender dictionary

**Example**:
```python
raw_tender = {
    'id': 'TEST-001',
    'title': 'Cloud Computing Services  ',  # Extra spaces
    'description': 'We need cloud infrastructure...',
    'value': '500000',  # String instead of number
    'deadline': '15/03/2025'  # Non-standard date format
}

processed = processor.process_single_tender(raw_tender)

print(f"Title cleaned: '{processed['title']}'")
print(f"Value converted: {processed['value']} (type: {type(processed['value'])})")
print(f"Deadline standardized: {processed['deadline']}")
print(f"Semantic tags: {processed['semantic_tags']}")
```

##### `create_tender_clusters(tenders: List[Dict], n_clusters: int = 5) -> List[Dict]`

Create clusters of similar tenders using K-Means.

**Parameters**:
- `tenders` (List[Dict]): List of tender dictionaries
- `n_clusters` (int): Number of clusters. Default: 5

**Returns**:
- `List[Dict]`: Tenders with cluster assignments

**Each tender gets**:
- `cluster_id` (int): Cluster assignment (0 to n_clusters-1)
- `cluster_similarity` (float): Similarity to cluster center

**Example**:
```python
tenders = db.get_all_tenders()

# Create clusters
clustered_tenders = processor.create_tender_clusters(tenders, n_clusters=3)

# Group by cluster
from collections import defaultdict
clusters = defaultdict(list)

for tender in clustered_tenders:
    clusters[tender['cluster_id']].append(tender)

for cluster_id, members in clusters.items():
    print(f"\nCluster {cluster_id}: {len(members)} tenders")
    print(f"  Examples:")
    for tender in members[:3]:
        print(f"    - {tender['title']}")
```

##### `analyze_tender_patterns(tenders: List[Dict]) -> Dict`

Analyze patterns across tenders.

**Parameters**:
- `tenders` (List[Dict]): List of tender dictionaries

**Returns**:
- `Dict`: Pattern analysis containing:
  - `total_tenders`: Total count
  - `category_distribution`: Count by category
  - `value_statistics`: Value stats (mean, median, std, min, max)
  - `temporal_patterns`: Timeline analysis
  - `complexity_distribution`: Complexity breakdown

**Example**:
```python
tenders = db.get_all_tenders()

patterns = processor.analyze_tender_patterns(tenders)

print(f"Total Tenders: {patterns['total_tenders']}")

print("\nCategory Distribution:")
for category, count in patterns['category_distribution'].items():
    print(f"  {category}: {count}")

print("\nValue Statistics:")
stats = patterns['value_statistics']
print(f"  Mean: £{stats['mean']:,.0f}")
print(f"  Median: £{stats['median']:,.0f}")
print(f"  Range: £{stats['min']:,.0f} - £{stats['max']:,.0f}")

print("\nComplexity Distribution:")
complexity = patterns['complexity_distribution']
print(f"  Low: {complexity['low']}")
print(f"  Medium: {complexity['medium']}")
print(f"  High: {complexity['high']}")
```

---

## Frontend Integration

### Streamlit Page Development

#### Page Template

```python
import streamlit as st
import pandas as pd
from utils.database import Database

# Page configuration
st.set_page_config(
    page_title="My Page",
    page_icon="📄",
    layout="wide"
)

def main():
    st.title("📄 My Page Title")
    st.markdown("---")

    # Check component initialization
    if 'db' not in st.session_state:
        st.error("Database not initialized. Return to main page.")
        return

    # Get components from session state
    db = st.session_state.db

    # Page logic
    tenders = db.get_all_tenders()
    st.write(f"Total tenders: {len(tenders)}")

if __name__ == "__main__":
    main()
```

#### Common Patterns

**Loading data with caching**:
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_tender_data():
    """Load and cache tender data."""
    db = Database()
    return db.get_all_tenders()

# Use in page
tenders = load_tender_data()
```

**Displaying data with Plotly**:
```python
import plotly.express as px

# Prepare data
df = pd.DataFrame(tenders)

# Create chart
fig = px.bar(
    df.groupby('category').size().reset_index(name='count'),
    x='category',
    y='count',
    title='Tenders by Category'
)

# Display
st.plotly_chart(fig, use_container_width=True)
```

**User input forms**:
```python
with st.form("vendor_form"):
    name = st.text_input("Company Name", key="company_name")
    email = st.text_input("Email", key="email")
    categories = st.multiselect(
        "Business Categories",
        options=['IT Services', 'Professional Services', 'Facilities Management']
    )

    submitted = st.form_submit_button("Submit")

    if submitted:
        vendor_data = {
            'name': name,
            'email': email,
            'categories': categories
        }
        success = db.create_vendor(vendor_data)
        if success:
            st.success("Vendor created successfully!")
```

---

## Extension Points

### Adding New Data Sources

**Create new scraper**:
```python
# utils/new_scraper.py
from utils.web_scraper import TenderScraper

class ContractsFinderScraper(TenderScraper):
    """Scraper for UK Contracts Finder portal."""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.contractsfinder.service.gov.uk"

    def scrape_contracts_finder(self) -> List[Dict]:
        """Scrape from Contracts Finder."""
        # Implementation here
        pass
```

**Integrate into application**:
```python
# app.py
from utils.new_scraper import ContractsFinderScraper

if st.button("🔄 Refresh from Contracts Finder"):
    cf_scraper = ContractsFinderScraper()
    tenders = cf_scraper.scrape_contracts_finder()
    processed = processor.process_tender_batch(tenders)
    db.store_tenders(processed)
```

### Adding New ML Algorithms

**Extend MLEngine**:
```python
# utils/ml_engine.py

class MLEngine:
    # ... existing methods ...

    def _collaborative_filtering(self, vendor_profile: Dict, tenders_df: pd.DataFrame) -> Dict:
        """
        Add collaborative filtering recommendations.

        Based on what similar vendors found relevant.
        """
        matches = {}

        # Get vendors with similar profiles
        similar_vendors = self._find_similar_vendors(vendor_profile)

        # Get their interests
        for similar_vendor in similar_vendors:
            interests = db.get_vendor_interests(similar_vendor['name'])

            # Score tenders based on similar vendor interest
            for interest in interests:
                if interest['interest_type'] == 'interested':
                    tender_id = interest['tender_id']
                    if tender_id not in matches:
                        matches[tender_id] = {
                            'score': 0,
                            'reasons': [],
                            'method': 'collaborative_filtering'
                        }
                    matches[tender_id]['score'] += 0.2
                    matches[tender_id]['reasons'].append(
                        f"Similar vendors found this relevant"
                    )

        return matches

    def _generate_recommendations(self, vendor_profile: Dict, tenders: List[Dict], limit: int):
        # ... existing code ...

        # Add new algorithm
        collaborative_matches = self._collaborative_filtering(vendor_profile, df)

        # Include in score combination
        combined_scores = self._combine_scores([
            category_matches,
            content_matches,
            value_matches,
            preference_matches,
            collaborative_matches  # New algorithm
        ])

        # ... rest of method ...
```

### Adding New Page

**Create page file**:
```python
# pages/9_📈_Analytics.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

def main():
    st.title("📈 Advanced Analytics")

    db = st.session_state.db
    tenders = db.get_all_tenders()

    # Your analytics logic here
    df = pd.DataFrame(tenders)

    # Example: Trend analysis
    df['created_date'] = pd.to_datetime(df['created_at'])
    monthly = df.groupby(df['created_date'].dt.to_period('M')).size()

    fig = go.Figure(data=[
        go.Scatter(x=monthly.index.astype(str), y=monthly.values, mode='lines+markers')
    ])
    fig.update_layout(title='Tender Volume Trend', xaxis_title='Month', yaxis_title='Count')

    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
```

---

## Code Examples

### Complete Workflow Example

```python
"""
Complete workflow: Scrape, Process, Store, Recommend
"""
from utils.database import Database
from utils.web_scraper import TenderScraper
from utils.data_processor import DataProcessor
from utils.ml_engine import MLEngine

# 1. Initialize components
db = Database()
scraper = TenderScraper()
processor = DataProcessor()
ml_engine = MLEngine()

# 2. Scrape new tenders
print("Scraping tenders...")
raw_tenders = scraper.scrape_lupc_tenders()
print(f"Scraped {len(raw_tenders)} tenders")

# 3. Process tenders
print("Processing tenders...")
processed_tenders = processor.process_tender_batch(raw_tenders)
print(f"Processed with {len(processed_tenders[0]['semantic_tags'])} semantic tags")

# 4. Store in database
print("Storing tenders...")
db.store_tenders(processed_tenders)
print("Tenders stored")

# 5. Generate recommendations for a vendor
vendor = db.get_vendor_by_name("TechCorp Solutions")
if vendor:
    print(f"\nGenerating recommendations for {vendor['name']}...")
    recommendations = ml_engine.get_recommendations(vendor, limit=10)

    print(f"Top 5 Recommendations:")
    for i, rec in enumerate(recommendations[:5], 1):
        print(f"{i}. {rec['title']}")
        print(f"   Match: {rec['match_score']:.1%}")
        print(f"   Value: £{rec['value']:,}")
        print(f"   Reasons: {', '.join(rec['match_reasons'][:2])}")
        print()
```

### Batch Processing Example

```python
"""
Batch process multiple vendors and generate alerts
"""
from utils.database import Database
from utils.ml_engine import MLEngine
from datetime import datetime

db = Database()
ml_engine = MLEngine()

# Get all vendors
vendors = db.get_all_vendors()

# Process each vendor
for vendor in vendors:
    print(f"\nProcessing {vendor['name']}...")

    # Generate recommendations
    recommendations = ml_engine.get_recommendations(vendor, limit=20)

    # Filter high-quality matches
    high_matches = [r for r in recommendations if r['match_score'] > 0.7]

    print(f"  Found {len(high_matches)} high-quality matches")

    # Record interests for ML improvement
    for rec in high_matches[:5]:
        db.record_vendor_interest(
            vendor['name'],
            rec['id'],
            'interested'
        )

    # Send email alert (pseudo-code)
    if high_matches and vendor.get('notifications', {}).get('email'):
        # send_email_alert(vendor['email'], high_matches)
        print(f"  Email alert sent to {vendor['email']}")
```

### Custom Analysis Example

```python
"""
Custom tender analysis and reporting
"""
import pandas as pd
from utils.database import Database
from utils.ai_assistant import AIAssistant

db = Database()
ai = AIAssistant()

# Get tenders from specific category
it_tenders = db.get_tenders_by_category("IT Services & Software")

# Convert to DataFrame for analysis
df = pd.DataFrame(it_tenders)

# Statistical analysis
print("IT Services & Software Analysis")
print("=" * 50)
print(f"Total Tenders: {len(df)}")
print(f"Active Tenders: {len(df[df['status'] == 'Active'])}")
print(f"Total Value: £{df['value'].sum():,.0f}")
print(f"Average Value: £{df['value'].mean():,.0f}")
print(f"Median Value: £{df['value'].median():,.0f}")

# Value distribution
print("\nValue Distribution:")
bins = [0, 100000, 500000, 1000000, float('inf')]
labels = ['<£100k', '£100k-£500k', '£500k-£1M', '>£1M']
df['value_range'] = pd.cut(df['value'], bins=bins, labels=labels)
print(df['value_range'].value_counts())

# Generate AI insights
insights = ai.generate_market_insights(it_tenders, "recent")
print("\nAI Market Insights:")
print(insights)

# Export report
with open('it_services_report.txt', 'w') as f:
    f.write("IT Services & Software Market Report\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write(insights)

print("\nReport saved to it_services_report.txt")
```

---

## Testing

### Unit Test Example

```python
# tests/test_database.py
import unittest
from utils.database import Database
import os

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Create test database before each test."""
        self.test_db_path = "test_tender.db"
        self.db = Database(self.test_db_path)

    def tearDown(self):
        """Clean up test database after each test."""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_store_and_retrieve_tender(self):
        """Test storing and retrieving a tender."""
        test_tender = {
            'id': 'TEST-001',
            'title': 'Test Tender',
            'description': 'Test Description',
            'category': 'IT Services & Software',
            'value': 100000,
            'deadline': '2025-12-31',
            'status': 'Active',
            'organization': 'Test Org',
            'location': 'UK'
        }

        # Store tender
        success = self.db.store_tenders([test_tender])
        self.assertTrue(success)

        # Retrieve tender
        tenders = self.db.get_all_tenders()
        self.assertEqual(len(tenders), 1)
        self.assertEqual(tenders[0]['title'], 'Test Tender')

    def test_search_tenders(self):
        """Test tender search functionality."""
        # Add test tenders
        tenders = [
            {'id': '1', 'title': 'Cloud Services', 'description': 'AWS cloud', 'category': 'IT', 'value': 100000, 'status': 'Active'},
            {'id': '2', 'title': 'Database Services', 'description': 'PostgreSQL', 'category': 'IT', 'value': 50000, 'status': 'Active'},
        ]
        self.db.store_tenders(tenders)

        # Search
        results = self.db.search_tenders("cloud")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], '1')

if __name__ == '__main__':
    unittest.main()
```

### Integration Test Example

```python
# tests/test_integration.py
import unittest
from utils.database import Database
from utils.web_scraper import TenderScraper
from utils.data_processor import DataProcessor

class TestIntegration(unittest.TestCase):
    def test_scrape_process_store_workflow(self):
        """Test complete workflow from scraping to storage."""
        # Initialize components
        db = Database("test_integration.db")
        scraper = TenderScraper()
        processor = DataProcessor()

        # Scrape (using mock or real data)
        tenders = scraper.scrape_lupc_tenders()

        # Process
        processed = processor.process_tender_batch(tenders)

        # Verify processing added semantic tags
        self.assertTrue('semantic_tags' in processed[0])
        self.assertTrue('urgency_score' in processed[0])

        # Store
        success = db.store_tenders(processed)
        self.assertTrue(success)

        # Verify storage
        retrieved = db.get_all_tenders()
        self.assertGreater(len(retrieved), 0)

        # Cleanup
        import os
        os.remove("test_integration.db")
```

---

## Contributing Guidelines

### Code Style

**Follow PEP 8**:
```python
# Good
def calculate_match_score(vendor_profile, tender):
    """
    Calculate match score between vendor and tender.

    Args:
        vendor_profile (dict): Vendor information
        tender (dict): Tender information

    Returns:
        float: Match score between 0 and 1
    """
    score = 0.0
    # Implementation
    return score

# Bad
def calc_score(v,t):
    s=0.0
    return s
```

**Type Hints**:
```python
from typing import List, Dict, Optional

def get_recommendations(
    vendor_profile: Dict,
    limit: int = 20
) -> List[Dict]:
    """Generate recommendations."""
    pass
```

**Docstrings**:
```python
def complex_function(param1, param2):
    """
    Brief description of function.

    Detailed description if needed.

    Args:
        param1 (type): Description
        param2 (type): Description

    Returns:
        type: Description

    Raises:
        ValueError: When parameter is invalid

    Example:
        >>> result = complex_function('test', 123)
        >>> print(result)
        Expected output
    """
    pass
```

### Pull Request Process

1. **Fork and Branch**: Create feature branch from `main`
2. **Implement**: Write code with tests
3. **Test**: Run all tests locally
4. **Document**: Update relevant documentation
5. **Commit**: Use clear commit messages
6. **PR**: Submit pull request with description

**Commit Message Format**:
```
type(scope): brief description

Detailed explanation if needed.

Fixes #123
```

**Types**: feat, fix, docs, style, refactor, test, chore

### Adding New Features

**Checklist**:
- [ ] Feature implementation
- [ ] Unit tests (>70% coverage)
- [ ] Integration tests
- [ ] Documentation (docstrings, README updates)
- [ ] Example usage
- [ ] Performance considerations
- [ ] Security review
- [ ] Backward compatibility

---

## Appendix

### Data Structures

**Tender Dictionary Structure**:
```python
{
    # Core fields
    'id': str,                          # Unique identifier
    'title': str,                       # Tender title
    'description': str,                 # Full description
    'category': str,                    # Primary category
    'value': float,                     # Contract value in GBP
    'deadline': str,                    # ISO date format
    'status': str,                      # Active|Closed|Upcoming
    'organization': str,                # Procuring organization
    'location': str,                    # Geographic location
    'url': str,                        # Source URL
    'source': str,                     # Data source name
    'scraped_date': str,               # ISO datetime

    # Enrichment fields (added by DataProcessor)
    'semantic_tags': List[str],         # AI-identified categories
    'tag_scores': Dict,                 # Relevance scores per tag
    'extracted_entities': Dict,         # NER results
    'urgency_score': float,            # 0-1
    'complexity_score': float,          # 0-1
    'cluster_id': int,                 # Cluster assignment
    'cluster_similarity': float,        # 0-1

    # Recommendation fields (added by MLEngine)
    'match_score': float,              # 0-1 (in recommendations)
    'match_reasons': List[str],        # Explanation
    'recommendation_confidence': float  # 0-1
}
```

**Vendor Dictionary Structure**:
```python
{
    'id': str,
    'name': str,
    'contact_person': str,
    'email': str,
    'phone': str,
    'website': str,
    'company_size': str,
    'address': {
        'line1': str,
        'city': str,
        'postcode': str,
        'country': str
    },
    'categories': List[str],
    'keywords': str,
    'years_experience': int,
    'annual_turnover': str,
    'certifications': str,
    'preferences': {
        'min_value': float,
        'max_value': float,
        'regions': List[str]
    },
    'notifications': {
        'email': bool,
        'frequency': str  # Daily|Weekly|Immediate
    },
    'created_date': str,  # ISO datetime
    'updated_date': str   # ISO datetime
}
```

---

## Document Control

**Version**: 1.0
**Last Updated**: December 2025
**Next Review**: March 2026
**Maintained by**: Development Team
**Feedback**: Submit via GitHub issues or pull requests
