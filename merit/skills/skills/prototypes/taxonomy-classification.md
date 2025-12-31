# Taxonomy Classification

AI-powered content classification system using customizable taxonomies with OpenAI GPT-4o-mini.

## What This Skill Does

This skill helps you work with the Taxonomy Classification prototype - an AI system that automatically categorizes text content against predefined taxonomies, providing top 5 matches with relevancy scores.

## When to Use This Skill

- Understanding taxonomy-based classification systems
- Implementing customizable content categorization
- Working with Pydantic for structured LLM outputs
- Building domain-specific classification tools
- Analyzing text against hierarchical taxonomies
- Creating flexible classification prototypes

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/taxonomy_classification/
```

## Key Files

- `taxonomy.py` - Main application (95 lines)
- `taxonomies.json` - General taxonomies definition
- `taxonomies_agri.json` - Agricultural-specific taxonomies
- `requirements.txt` - Python dependencies
- `documentation/` - Comprehensive 5-document suite (~96KB)

## Core Capabilities

### Content Classification
- Classifies text against predefined taxonomies
- Returns top 5 most relevant categories
- Provides relevancy scores (0.0-1.0)
- Supports custom taxonomy definitions
- Real-time classification via Streamlit UI

### Taxonomy Support
- **General Taxonomy**: Broad content categories
- **Agricultural Taxonomy**: Domain-specific classification
- **Custom Taxonomies**: User-defined classification schemas
- **Multi-level Hierarchies**: Nested category structures

### Output Format
- Ranked list of top 5 matches
- Relevancy score for each match
- Category path through hierarchy
- Justification for classification

## Technical Stack

- **Framework**: Streamlit 1.40.2 for web interface
- **AI Model**: OpenAI GPT-4o-mini via LangChain 0.3.10
- **Validation**: Pydantic for structured output
- **Data**: Pandas for results display
- **Language**: Python 3.8+

## Common Tasks

### Review Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/taxonomy_classification
cat documentation/02_technical_architecture.md
```

### Examine Classification Code
```bash
# Main classification logic
cat taxonomy.py
```

### Review Taxonomies
```bash
# General taxonomy
cat taxonomies.json

# Agricultural taxonomy
cat taxonomies_agri.json
```

### Check API Reference
```bash
cat documentation/03_api_reference.md
```

### Run Application
```bash
streamlit run taxonomy.py
```

## Data Models

### Taxonomy Output Model
```python
{
    "category_level_1": str,  # Top-level category
    "category_level_2": str,  # Second-level category
    "category_level_3": str,  # Third-level category
    "relevancy_score": float  # 0.0 to 1.0
}
```

### Classification Result
```python
{
    "results": [
        {
            "category_level_1": "Technology",
            "category_level_2": "Software",
            "category_level_3": "Web Development",
            "relevancy_score": 0.92
        },
        # ... top 5 matches
    ]
}
```

## Taxonomy Structure

### General Taxonomy Example
```json
{
    "Technology": {
        "Software": ["Web Development", "Mobile Apps", "Enterprise"],
        "Hardware": ["Computers", "Networking", "IoT"],
        "Services": ["Consulting", "Support", "Training"]
    },
    "Business": {
        "Finance": ["Accounting", "Investment", "Banking"],
        "Marketing": ["Digital", "Traditional", "Analytics"],
        "Operations": ["Supply Chain", "Manufacturing", "Logistics"]
    }
}
```

### Agricultural Taxonomy Example
```json
{
    "Crops": {
        "Cereals": ["Wheat", "Rice", "Corn"],
        "Vegetables": ["Leafy Greens", "Root Vegetables", "Fruits"],
        "Cash Crops": ["Cotton", "Sugarcane", "Tea"]
    },
    "Livestock": {
        "Cattle": ["Dairy", "Beef", "Breeding"],
        "Poultry": ["Chickens", "Ducks", "Turkeys"],
        "Small Animals": ["Sheep", "Goats", "Pigs"]
    }
}
```

## Use Cases

### Content Management
- Automatically tag articles and documents
- Organize content libraries
- Enable faceted search and filtering
- Support content discovery

### E-commerce
- Product categorization
- Automatic tagging for inventory
- Improved search and navigation
- Personalized recommendations

### Knowledge Management
- Document classification
- Information architecture
- Metadata generation
- Semantic organization

### Research and Analysis
- Academic paper classification
- Research topic categorization
- Literature review organization
- Trend analysis

### Agricultural Applications
- Crop classification from descriptions
- Farm activity categorization
- Agricultural product taxonomy
- Research paper classification

## Key Components

### ContentClassification Class
- **Methods**:
  - `__init__()` - Initialize with API key and model
  - `classify()` - Main classification function
  - `validate_output()` - Validate LLM response

### TaxonomyOutputModel (Pydantic)
- Structured output schema
- Data validation
- Type safety
- JSON serialization

### TaxonomyOutputParser
- Parses LLM output
- Handles list of classifications
- Ensures format compliance

## Integration Points

- OpenAI API for GPT-4o-mini
- LangChain for LLM orchestration
- Streamlit for web interface
- Pydantic for data validation
- Pandas for results display

## Configuration

### Taxonomy Selection
- Choose from predefined taxonomies (General, Agricultural)
- Load custom taxonomy JSON files
- Configure via Streamlit UI

### Model Settings
```python
model = "gpt-4o-mini"
temperature = 0.0
max_tokens = 2000
```

### Custom Taxonomy Format
```json
{
    "Level1_Category": {
        "Level2_Category": [
            "Level3_Item1",
            "Level3_Item2"
        ]
    }
}
```

## Best Practices

1. **Content Quality**: Provide clear, descriptive text for classification
2. **Taxonomy Design**: Create logical, mutually exclusive categories
3. **Hierarchy Depth**: Limit to 3-4 levels for best results
4. **Validation**: Review AI classifications for accuracy
5. **Iterative Refinement**: Adjust taxonomies based on results

## Limitations

- Prototype status (not production-ready)
- No persistent storage
- Limited to top 5 results
- Single taxonomy selection per session
- No batch processing in UI
- English language optimized

## Example Workflows

### Basic Classification Workflow
1. Select taxonomy (General or Agricultural)
2. Enter text content to classify
3. Click "Classify"
4. Review top 5 category matches with scores
5. Export results if needed

### Custom Taxonomy Workflow
1. Create custom taxonomy JSON file
2. Modify code to load custom taxonomy
3. Run classification with custom categories
4. Validate results against expectations
5. Refine taxonomy as needed

### Batch Processing Workflow (Programmatic)
1. Prepare list of texts to classify
2. Load taxonomy
3. Initialize classifier
4. Loop through texts
5. Collect and aggregate results
6. Export to CSV or database

## Performance Considerations

- Classification time: 2-5 seconds per text
- API rate limits apply
- Large texts may require truncation
- Concurrent requests limited by API

## Customization Options

### Prompt Customization
- Modify classification instructions
- Add domain-specific context
- Adjust scoring criteria
- Include examples

### Output Customization
- Change number of results (default: top 5)
- Add additional metadata
- Modify relevancy score calculation
- Include classification confidence

### UI Customization
- Streamlit themes and styling
- Additional input fields
- Results visualization
- Export formats

## Documentation Structure

1. **01_project_overview.md** - Project introduction and goals (6.4KB)
2. **02_technical_architecture.md** - System design and architecture (23KB)
3. **03_api_reference.md** - Complete API documentation (19KB)
4. **04_user_guide.md** - Usage instructions and examples (25KB)
5. **05_deployment_guide.md** - Deployment and operations (23KB)

**Total**: ~96KB, ~3,500 lines of comprehensive documentation

## Deployment Options

### Local Development
```bash
pip install -r requirements.txt
streamlit run taxonomy.py
```

### Streamlit Cloud
- Deploy to Streamlit Community Cloud
- Configure secrets for API keys
- Share with team

### Docker
- Containerize application
- Deploy to any environment
- Scale as needed

### API Wrapper
- Wrap in FastAPI for REST API
- Enable programmatic access
- Support batch processing

## Related Prototypes

- **Taxonomy SkillMatch** - Skills-based taxonomy matching
- **Planning Classifier** - Document classification
- **Agricultural Taxonomy** - Domain-specific classification

## Quick Reference

**Primary Function**: Classify text against customizable taxonomies
**Output**: Top 5 category matches with relevancy scores
**AI Model**: GPT-4o-mini via LangChain
**Taxonomies**: General, Agricultural, Custom
**Input**: Text content (any length)
**Output Format**: Pandas DataFrame with ranked categories
**Code Size**: 95 lines (main application)
**Documentation**: 5 comprehensive documents (~96KB)
**Tech Stack**: Python, Streamlit, LangChain, OpenAI, Pydantic
