# SpendSmart

AI-powered procurement intelligence platform with knowledge graphs and semantic search.

## What This Skill Does

This skill helps you work with SpendSmart - an advanced procurement analytics platform that uses knowledge graphs, semantic search, and AI to provide deep insights into procurement data.

## When to Use This Skill

- Understanding procurement intelligence architectures
- Working with knowledge graph implementations
- Implementing semantic search with OpenAI embeddings
- Building interactive data visualization dashboards
- Analyzing procurement spend patterns
- Creating AI-powered business analytics platforms

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/spend_smart/
```

## Key Files

- `app.py` - Main Streamlit application (27KB)
- `data_generator.py` - Synthetic procurement data generation
- `graph_builder.py` - Knowledge graph construction
- `semantic_search.py` - AI-powered search functionality
- `visualizations.py` - Interactive charts and graphs
- `utils.py` - Utility functions
- `documentation/` - Comprehensive 5-document suite (124 pages)

## Core Capabilities

### 1. Knowledge Graph Analytics
- In-memory graph construction with NetworkX
- Entity relationships: suppliers, categories, frameworks, buyers
- Graph algorithms for analysis and insights
- Interactive network visualization

### 2. Semantic Search
- Natural language query processing with GPT-4o-mini
- OpenAI embeddings for semantic understanding
- SQL query generation from natural language
- Contextual search across all procurement data

### 3. Interactive Dashboard
- Real-time procurement analytics
- Multi-dimensional filtering
- Spend analysis visualizations
- Framework efficiency metrics
- Supplier performance tracking

### 4. AI-Powered Insights
- Automated anomaly detection
- Procurement pattern analysis
- Supplier risk assessment
- Framework optimization recommendations

### 5. Data Management
- Synthetic data generation for testing
- SQLite database storage
- Data export functionality
- Real-time updates and filtering

## Technical Stack

- **Frontend**: Streamlit, Plotly for visualizations
- **Backend**: Python 3.11+, Pandas for data manipulation
- **AI/ML**: OpenAI GPT-4o-mini, embeddings
- **Graph**: NetworkX for knowledge graph
- **Database**: SQLite (in-memory)
- **Deployment**: Replit, cloud-native design

## Common Tasks

### Review Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/spend_smart
cat documentation/02_Technical_Architecture.md
```

### Examine Key Modules
```bash
# Knowledge graph builder
cat graph_builder.py

# Semantic search engine
cat semantic_search.py

# Visualization components
cat visualizations.py
```

### Check Business Value
```bash
# ROI and business case
cat documentation/05_Business_Value.md
```

### Run Application
```bash
streamlit run app.py
```

## Knowledge Graph Schema

### Node Types
- **Suppliers**: Vendor entities
- **Categories**: Procurement categories
- **Frameworks**: Procurement frameworks
- **Buyers**: Purchasing organizations
- **Contracts**: Individual contracts

### Relationship Types
- Supplier → supplies → Category
- Contract → under → Framework
- Buyer → purchases → Category
- Supplier → participates_in → Framework

## Semantic Search Capabilities

### Natural Language Queries
```
"Show me suppliers with spend over £1M"
"Which frameworks have the best efficiency?"
"Find all IT procurement in London"
"Compare supplier performance by region"
```

### Query Processing Pipeline
1. User enters natural language query
2. GPT-4o-mini parses intent and entities
3. System generates SQL or filters
4. Query executes against database/graph
5. Results displayed with visualizations
6. AI generates insights summary

## Dashboard Components

### Overview Dashboard
- Total spend metrics
- Active suppliers count
- Framework utilization
- Geographic distribution
- Trend analysis

### Supplier Analysis
- Spend by supplier ranking
- Performance metrics
- Risk indicators
- Geographic coverage

### Category Analysis
- Spend by category breakdown
- Category trends over time
- Framework alignment
- Efficiency metrics

### Framework Analysis
- Framework efficiency scores
- Utilization rates
- Supplier participation
- Cost comparisons

## Visualizations

### Interactive Charts
- Spend trend line charts
- Supplier spend bar charts
- Category distribution pie charts
- Geographic heatmaps
- Network graph visualizations
- Framework comparison charts

### Network Graph Features
- Interactive node exploration
- Relationship highlighting
- Zoom and pan capabilities
- Entity filtering
- Layout algorithms (force-directed, hierarchical)

## Use Cases

### Procurement Teams
- Analyze spend patterns and trends
- Identify cost-saving opportunities
- Monitor framework efficiency
- Track supplier performance

### Finance Departments
- Budget tracking and forecasting
- Spend analysis by category
- Framework ROI analysis
- Variance analysis

### Compliance Officers
- Framework compliance monitoring
- Audit trail analysis
- Supplier certification tracking
- Risk assessment

### Strategic Planning
- Supplier consolidation opportunities
- Framework optimization
- Category management
- Market intelligence

## Business Value

### Quantified Benefits (from documentation)
- **Annual Value**: £10M+
- **ROI**: 1,742% over 5 years
- **Benefit-Cost Ratio**: 18.4:1
- **Payback Period**: 1.5 months
- **Direct Savings**: £4.92M
- **Efficiency Gains**: £1.04M
- **Strategic Value**: £2.2M

### Key Value Drivers
1. Automated data analysis (90% time savings)
2. Framework efficiency improvements
3. Supplier consolidation opportunities
4. Anomaly detection and risk mitigation
5. Strategic procurement intelligence

## Integration Points

- OpenAI API for GPT-4o-mini and embeddings
- SQLite for data persistence
- NetworkX for graph analytics
- Plotly for interactive visualizations
- Streamlit for real-time UI updates

## Configuration

### Data Generation
- Customizable number of records
- Configurable date ranges
- Industry-specific taxonomies
- Geographic distributions

### Search Settings
- Embedding model selection
- Similarity thresholds
- Result limits
- Query context window

## Best Practices

1. **Data Quality**: Ensure clean, consistent procurement data
2. **Query Design**: Use clear, specific natural language queries
3. **Visualization Selection**: Choose appropriate charts for insights
4. **Graph Exploration**: Leverage network visualization for relationships
5. **Performance**: Limit large dataset operations for responsiveness

## Limitations

- Prototype status (not production-ready)
- In-memory database (no persistence across sessions)
- Synthetic data for demonstration
- Single-user application
- No authentication or access control

## Example Workflows

### Spend Analysis Workflow
1. Load procurement data
2. Apply filters (date, category, supplier)
3. Review dashboard metrics
4. Explore visualizations
5. Export insights

### Semantic Search Workflow
1. Enter natural language query
2. System processes and understands intent
3. AI generates appropriate query
4. Results displayed with context
5. Drill down into specific entities

### Framework Efficiency Workflow
1. Navigate to framework analysis
2. Review efficiency scores
3. Compare frameworks
4. Identify optimization opportunities
5. Generate recommendations

### Supplier Network Workflow
1. Open network graph view
2. Filter by category or framework
3. Explore supplier relationships
4. Identify consolidation opportunities
5. Export network data

## Performance Considerations

- In-memory graph limits: ~100K nodes
- Semantic search response: 2-5 seconds
- Visualization rendering: <1 second
- Data generation: Configurable batch sizes

## Documentation Highlights

### 5 Comprehensive Documents
1. **Business Use Case** (14 pages) - Use cases, personas, objectives
2. **Technical Architecture** (23 pages) - System design, components
3. **Functional Architecture** (30 pages) - Features, flows, requirements
4. **User Guide** (30 pages) - Instructions, examples, FAQ
5. **Business Value** (27 pages) - ROI analysis, value quantification

### Total Documentation
- 124 pages
- 23 diagrams
- 55,500 words
- 3 hours 20 minutes reading time

## Related Prototypes

- **Dashboard** - Analytics and visualization patterns
- **Tender Intelligence** - Procurement opportunity analysis
- **Vendor Recommendation** - Supplier matching

## Quick Reference

**Primary Function**: Procurement intelligence with AI and knowledge graphs
**Key Features**: Semantic search, knowledge graphs, analytics, visualizations
**AI Model**: GPT-4o-mini with embeddings
**Data Structure**: NetworkX graph + SQLite database
**Visualizations**: Plotly interactive charts
**Business Value**: £10M+ annual value, 1,742% ROI
**Tech Stack**: Python, Streamlit, NetworkX, OpenAI, Plotly
