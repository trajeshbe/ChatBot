# Taxonomy Classification - Project Overview

## Executive Summary

The Taxonomy Classification prototype is an AI-powered content classification system designed to automatically categorize articles and text content against multiple taxonomies using OpenAI's GPT-4o-mini model. The system leverages LangChain for orchestration and provides an interactive Streamlit web interface for real-time classification.

## Project Purpose

The primary purpose of this prototype is to:
- Automatically classify textual content (articles, news, documents) against predefined taxonomies
- Provide relevancy scores for each classification
- Return the top 5 most relevant taxonomy categories for any given text
- Enable efficient content organization and categorization for various domains

## Key Features

### 1. Multi-Taxonomy Classification
The system supports multiple taxonomy types including:
- **Topic-Based Taxonomies**: Technology, Science, Health, Entertainment, Politics, Business, Sports
- **Geographical Taxonomies**: By Continent, Country, and Region
- **Event-Based Taxonomies**: Natural Disasters, Political Events, Sporting Events, Cultural Events
- **Audience-Based Taxonomies**: By Age Group, Interest, and Professional Categories
- **Sentiment-Based Taxonomies**: Positive, Negative, Neutral News
- **Format-Based Taxonomies**: Breaking News, Editorials, Features, Interviews, Opinion Pieces
- **Time-Based Taxonomies**: Daily News, Weekly Highlights, Historical Retrospectives
- **Industry/Domain-Specific Taxonomies**: Technology, Business, Health sectors
- **Behavioral/Engagement-Based Taxonomies**: Most Shared, Trending Topics
- **Language-Based Taxonomies**: By Language and Regional Dialects
- **Action-Oriented Taxonomies**: Awareness, Advocacy, Call to Action
- **Tag-Based Taxonomies**: Specific topics like Climate Change, Blockchain, Inflation
- **Agricultural Taxonomies** (in agri version): Crops, Livestock, Agribusiness, AgTech, Sustainability

### 2. Relevancy Scoring
Each classification includes a relevancy score (0-10) indicating how well the content matches the taxonomy category.

### 3. Interactive Web Interface
Built with Streamlit, providing an easy-to-use interface for:
- Text input via text area
- Real-time classification results
- Tabular display of classifications with scores

### 4. Structured Output
Returns classifications in a structured format with:
- Taxonomy Type (main category)
- Category (sub-category)
- Sub-Category (specific value)
- Score (relevancy rating)

## Use Cases

### News and Media
- Automatically categorize news articles for content management systems
- Tag articles for recommendation engines
- Organize content libraries by topic and relevance

### Content Management
- Classify documents in enterprise knowledge bases
- Auto-tag user-generated content
- Organize research papers and publications

### Agricultural Content (with agri taxonomies)
- Categorize farming and agriculture-related articles
- Classify crop reports and livestock information
- Organize agribusiness news and market updates

### Marketing and Communications
- Categorize marketing content by audience segments
- Classify press releases by topic and sentiment
- Organize campaign materials by format and purpose

## Technical Approach

The system uses a Large Language Model (LLM)-based approach rather than traditional machine learning classification. This offers several advantages:
- No training data required
- Flexible taxonomy modifications without retraining
- Context-aware classification
- Multi-label classification capability
- Understanding of nuanced content

## Architecture Overview

```
User Input (Article Text)
    ↓
Streamlit Web Interface
    ↓
ContentClassification Class
    ↓
Prompt Template + Taxonomy Data
    ↓
LangChain Pipeline
    ↓
OpenAI GPT-4o-mini Model
    ↓
JSON Output Parser
    ↓
DataFrame Conversion
    ↓
Display Results
```

## Technology Stack

- **Python**: Core programming language
- **LangChain**: LLM orchestration framework
- **OpenAI API**: GPT-4o-mini model for classification
- **Streamlit**: Web interface framework
- **Pydantic**: Data validation and modeling
- **Pandas**: Data manipulation and display

## Project Structure

```
taxonomy_classification/
├── taxonomy.py              # Main application code
├── taxonomies.json         # General taxonomies definition
├── taxonomies_agri.json    # Agricultural-specific taxonomies
├── requirements.txt        # Python dependencies
└── documentation/          # Project documentation
    ├── 01_project_overview.md
    ├── 02_technical_architecture.md
    ├── 03_api_reference.md
    ├── 04_user_guide.md
    └── 05_deployment_guide.md
```

## Current Status

This is a functional prototype demonstrating:
- Working classification system
- Interactive web interface
- Multiple taxonomy support
- Two taxonomy configurations (general and agriculture-focused)

## Limitations and Future Considerations

### Current Limitations
- Requires OpenAI API key and internet connectivity
- Processing time depends on text length and API response time
- Limited to top 5 classifications
- No batch processing capability
- No persistence or history of classifications
- Hard-coded taxonomy file path

### Potential Enhancements
- Batch processing support
- Custom taxonomy upload via UI
- Classification history and export
- Multiple LLM provider support
- Confidence thresholds configuration
- API endpoint for programmatic access
- Caching for repeated classifications
- Support for document upload (PDF, DOCX)

## Target Audience

This prototype is designed for:
- Content managers and editors
- Data scientists and ML engineers
- Product managers evaluating classification solutions
- Developers integrating classification into larger systems
- Research teams exploring LLM-based classification

## Success Metrics

The prototype demonstrates value through:
- Accurate multi-label classification
- Fast processing time (typically under 5 seconds)
- Easy taxonomy customization
- Minimal setup requirements
- Intuitive user interface

## Next Steps

To move from prototype to production:
1. Implement error handling and validation
2. Add configuration management
3. Implement batch processing
4. Add user authentication
5. Create REST API endpoints
6. Implement logging and monitoring
7. Add unit and integration tests
8. Deploy to cloud infrastructure
9. Implement caching strategy
10. Add performance optimization
