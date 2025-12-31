# BidRadar - Tender Intelligence

AI-powered tender discovery and intelligence platform for UK public sector procurement.

## What This Skill Does

This skill helps you work with BidRadar (tender_intelligence directory) - an AI-powered platform that helps businesses discover, analyze, and track procurement opportunities in the UK public sector using smart search, ML recommendations, and AI assistance.

## When to Use This Skill

- Understanding tender intelligence systems
- Implementing procurement opportunity platforms
- Working with AI-powered tender matching
- Building recommendation engines for procurement
- Analyzing tender documents with AI
- Creating market intelligence dashboards

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/tender_intelligence/
```

## Key Files

- `app.py` - Main Streamlit application
- `utils/database.py` - Database operations (SQLite/PostgreSQL)
- `utils/ml_engine.py` - ML recommendation engine
- `utils/ai_assistant.py` - AI chatbot with GPT-4o
- `utils/web_scraper.py` - Tender data scraper
- `utils/data_processor.py` - Data processing pipeline
- `pages/` - Multi-page Streamlit application
- `create_demo_data.py` - Demo data generator
- `documentation/` - Comprehensive 5-document suite

## Core Capabilities

### 1. Smart Search
- **Natural Language Queries**: "Find IT tenders in London over £100k"
- **Advanced Filters**: Industry, value, location, deadline, status
- **Semantic Search**: Context-aware matching beyond keywords
- **Full-text Search**: Fast text-based search across all fields
- **Combined Search**: Hybrid approach for best results

### 2. AI Assistant
- **Conversational Interface**: Chat with GPT-4o about tenders
- **Document Analysis**: AI-powered tender document insights
- **Market Intelligence**: Questions about procurement trends
- **Bid Guidance**: Help with tender responses
- **Multi-mode**: General, Document Analysis, Market Intelligence

### 3. Personalized Recommendations
- **ML-Powered Matching**: Scikit-learn based recommendations
- **Vendor Profiling**: Match tenders to vendor capabilities
- **Relevance Scoring**: 0-100 match scores with justifications
- **Continuous Learning**: Improves with usage patterns
- **Clustering**: Groups similar tenders for insights

### 4. Analytics Dashboard
- **Real-time Metrics**: Total tenders, values, industries
- **Trend Analysis**: Historical patterns and forecasts
- **Geographic Insights**: Tender distribution by region
- **Industry Breakdown**: Sector-wise analysis
- **Opportunity Tracking**: Monitor high-value tenders

### 5. Alert Center
- **Automated Notifications**: Never miss relevant opportunities
- **Custom Filters**: Define alert criteria
- **Email Integration**: (planned for production)
- **Priority Scoring**: Urgency and relevance indicators

### 6. Web Scraping
- **Automated Collection**: Scrape LUPC and other sources
- **Data Extraction**: Parse tender details, documents
- **Regular Updates**: Scheduled scraping jobs
- **Content Cleaning**: Process and normalize data

## Technical Stack

- **Frontend**: Streamlit (Python-based web framework)
- **Backend**: Python 3.11+
- **Database**: SQLite (dev), PostgreSQL (production)
- **ML/AI**: scikit-learn, spaCy, OpenAI GPT-4o
- **Web Scraping**: BeautifulSoup, trafilatura
- **Visualization**: Plotly for interactive charts
- **NLP**: Natural language processing for text analysis

## Common Tasks

### Review Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/tender_intelligence
cat documentation/02_TECHNICAL_ARCHITECTURE.md
```

### Examine Components
```bash
# Database API
cat utils/database.py

# ML recommendation engine
cat utils/ml_engine.py

# AI assistant
cat utils/ai_assistant.py

# Web scraper
cat utils/web_scraper.py
```

### Review API Reference
```bash
cat documentation/05_API_DEVELOPER_REFERENCE.md
```

### Run Application
```bash
streamlit run app.py
```

### Create Demo Data
```bash
python create_demo_data.py
```

## Database Schema

### Tenders Table
```sql
CREATE TABLE tenders (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    industry TEXT,
    estimated_value REAL,
    deadline DATE,
    publish_date DATE,
    status TEXT,
    location TEXT,
    buyer_organization TEXT,
    contact_email TEXT,
    url TEXT,
    semantic_tags TEXT,
    urgency_score REAL,
    complexity_score REAL
)
```

### Vendors Table
```sql
CREATE TABLE vendors (
    id INTEGER PRIMARY KEY,
    name TEXT,
    industries TEXT,
    capabilities TEXT,
    certifications TEXT,
    past_wins TEXT,
    size TEXT,
    location TEXT
)
```

## Machine Learning Features

### Recommendation Algorithm
1. **Feature Engineering**: Extract relevant features from tenders
2. **TF-IDF Vectorization**: Convert text to numerical features
3. **Similarity Calculation**: Cosine similarity between vendor and tenders
4. **Scoring**: Calculate match scores (0-100)
5. **Ranking**: Sort by relevance and other factors

### Clustering
- **Algorithm**: K-Means clustering
- **Purpose**: Group similar tenders
- **Features**: Industry, value, location, complexity
- **Use**: Market segmentation, trend analysis

### Natural Language Processing
- **Named Entity Recognition**: Extract organizations, locations, amounts
- **Keyword Extraction**: Identify key terms
- **Sentiment Analysis**: Assess tender tone
- **Topic Modeling**: Categorize tenders

## AI Assistant Modes

### General Mode
- Answer questions about platform usage
- Provide tender search guidance
- Explain features and workflows
- General procurement knowledge

### Document Analysis Mode
- Analyze tender documents
- Extract key requirements
- Identify compliance needs
- Assess complexity

### Market Intelligence Mode
- Analyze procurement trends
- Industry insights
- Competitive landscape
- Strategic recommendations

## Use Cases

### For Vendors/Suppliers
- Discover relevant tender opportunities
- Get AI-powered bid recommendations
- Analyze tender requirements
- Track competitors and market trends
- Improve win rates with insights

### For Procurement Professionals
- Market intelligence and analysis
- Benchmark tender values
- Track procurement patterns
- Competitive analysis
- Strategic sourcing insights

### For Business Development
- Identify new opportunities
- Prioritize pursuits
- Analyze success factors
- Pipeline management
- Market expansion planning

## Key Metrics

### Tender Metrics
- **Urgency Score** (0-1): Time until deadline
- **Complexity Score** (0-1): Tender difficulty
- **Match Score** (0-100): Vendor fit
- **Estimated Value**: Financial opportunity
- **Competition Level**: Number of expected bidders

### Platform Metrics
- Total tenders tracked
- Industries covered
- Geographic coverage
- Average match accuracy
- User engagement

## Search Examples

### Natural Language Queries
```
"Find IT tenders worth over £100,000 in London"
"Show me construction tenders closing next week"
"What healthcare procurement opportunities are available?"
"Find tenders similar to what I won last year"
"Show high-value urgent opportunities"
```

### Advanced Filters
- Industry: IT, Construction, Healthcare, etc.
- Value range: Min-max £
- Location: City, region, or nationwide
- Deadline: Date range
- Status: Open, Closed, Awarded
- Complexity: Low, Medium, High
- Urgency: By days remaining

## Vendor Profile Structure

```python
{
    "name": "Company Name",
    "industries": ["IT", "Cybersecurity"],
    "capabilities": [
        "Cloud infrastructure",
        "Network security",
        "Compliance management"
    ],
    "certifications": ["ISO 27001", "Cyber Essentials Plus"],
    "past_wins": ["NHS Trust project", "Council IT upgrade"],
    "size": "SME",
    "location": "London"
}
```

## Integration Points

- OpenAI API for GPT-4o (AI Assistant)
- Web scraping APIs (BeautifulSoup, trafilatura)
- Database (SQLite/PostgreSQL)
- scikit-learn for ML
- spaCy for NLP
- Plotly for visualizations

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_key
DATABASE_URL=sqlite:///tender_platform.db
SCRAPING_SCHEDULE=daily
```

### Streamlit Config
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## Best Practices

1. **Vendor Profile**: Keep profile detailed and up-to-date
2. **Search Strategy**: Combine natural language with filters
3. **Alert Setup**: Configure alerts for critical criteria
4. **Regular Checks**: Monitor dashboard for new opportunities
5. **AI Assistant**: Leverage for document analysis
6. **Trend Analysis**: Review analytics for strategic insights

## Limitations

- Prototype status (not production-ready)
- Limited to UK public sector (currently)
- Requires OpenAI API access
- Demo data for testing
- Single-user deployment
- No authentication in prototype

## Example Workflows

### Tender Discovery Workflow
1. Open dashboard to view latest opportunities
2. Apply filters (industry, value, location)
3. Use smart search for specific needs
4. Review tender details
5. Check match score against vendor profile
6. Add to watchlist or proceed to bid

### AI Analysis Workflow
1. Find tender of interest
2. Open AI Assistant
3. Switch to Document Analysis mode
4. Upload or reference tender document
5. Ask specific questions about requirements
6. Review AI-generated insights
7. Use insights for bid preparation

### Recommendation Workflow
1. Complete vendor profile thoroughly
2. System analyzes profile
3. ML engine generates recommendations
4. Review top-matched tenders
5. Check match justifications
6. Prioritize opportunities
7. Track selected tenders

## Performance Considerations

- Database: Indexed for fast queries
- Search: <1 second for most queries
- ML Recommendations: 2-5 seconds
- AI Assistant: 3-10 seconds per query
- Scraping: Scheduled off-peak hours
- Dashboard: Real-time updates

## Security Considerations

- API keys in environment variables
- Database access controls
- Input sanitization
- SQL injection prevention
- HTTPS for production
- User authentication (planned)

## Documentation Structure

1. **01_PROJECT_OVERVIEW.md** - Business context and features
2. **02_TECHNICAL_ARCHITECTURE.md** - System design and architecture
3. **03_USER_GUIDE.md** - End-user instructions and workflows
4. **04_DEPLOYMENT_GUIDE.md** - Deployment and operations
5. **05_API_DEVELOPER_REFERENCE.md** - Complete API documentation

## Related Prototypes

- **SpendSmart** - Procurement intelligence with knowledge graphs
- **Procurement Matcher** - Vendor matching system
- **Vendor Recommendation** - Similar recommendation logic

## Quick Reference

**Primary Function**: Tender discovery and intelligence platform
**Key Features**: Smart search, AI assistant, ML recommendations, analytics
**AI Models**: GPT-4o (assistant), scikit-learn (recommendations), spaCy (NLP)
**Data Sources**: Web scraping (LUPC, Contracts Finder)
**Target Sector**: UK public sector procurement
**Database**: SQLite (dev), PostgreSQL (production)
**Visualizations**: Plotly interactive charts
**Tech Stack**: Python, Streamlit, OpenAI, scikit-learn, spaCy, BeautifulSoup
