# Zero-Shot NER

Flexible AI-powered Named Entity Recognition and Relation Extraction without task-specific training.

## What This Skill Does

This skill helps you work with the Zero-Shot NER prototype - a flexible AI system that extracts entities and relationships from text using custom labels defined at runtime, without requiring model training or fine-tuning.

## When to Use This Skill

- Understanding zero-shot learning for NER
- Implementing flexible entity extraction systems
- Working with GLiNER and NuNER models
- Building relation extraction pipelines
- Creating custom NER applications
- Analyzing domain-specific entities without training data

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/zero_shot_ner/
```

## Key Files

- `launch.py` - Streamlit entry point
- `entity_extraction.py` - Alternative entry point
- `api/model_api.py` - Flask API application
- `api/zero_shot_ner.py` - NER logic with GLiNER
- `api/zero_shot_relation.py` - Relation extraction
- `api/input_validators.py` - Input validation with Pydantic
- `interface/streamlit_app.py` - Streamlit UI
- `interface/inference.py` - Model inference logic
- `config.ini` - Configuration settings
- `documentation/` - Comprehensive 5-document suite

## Core Capabilities

### Zero-Shot Entity Extraction
- Define custom entity labels at runtime
- No training or fine-tuning required
- Support for any entity types
- Multiple entities per text
- Confidence scores for each extraction

### Relation Extraction
- Identify relationships between entities
- Custom relation types
- Directed relationships (source → target)
- Confidence scoring
- Multiple relations per text

### Dual Architecture
- **Streamlit Interface**: User-friendly web UI
- **Flask API**: RESTful API for integration
- Both share same ML models
- Separate deployment options

### Model Support
- **GLiNER**: Primary model for entity and relation extraction
- **NuNER Zero**: Optional secondary model (configurable)
- Model switching via configuration
- Extensible to other models

## Technical Stack

- **Frontend**: Streamlit 1.35.0, spaCy displacy for visualization
- **API**: Flask 3.0.3, Flask-HTTPAuth 4.8.0
- **ML Framework**: UTCA 0.1.2, GLiNER 0.2.2
- **NLP**: spaCy 3.7.5, NLTK 3.8.1
- **Validation**: Pydantic 2.7.2 for schemas
- **Language**: Python 3.8+
- **Optional**: Docker for containerization

## Common Tasks

### Review Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/zero_shot_ner
cat documentation/02_architecture.md
```

### Examine Components
```bash
# NER logic
cat api/zero_shot_ner.py

# Relation extraction
cat api/zero_shot_relation.py

# Streamlit UI
cat interface/streamlit_app.py

# Flask API
cat api/model_api.py
```

### Run Streamlit Interface
```bash
streamlit run launch.py
# Access at http://localhost:8501
```

### Run Flask API
```bash
python api/model_api.py
# Access at http://localhost:5000
```

### Check API Reference
```bash
cat documentation/03_api_reference.md
```

## Zero-Shot Learning Concept

### What is Zero-Shot NER?
Traditional NER requires training on labeled data for specific entity types. Zero-shot NER allows extraction of any entity type defined at runtime without training.

### Example
**Traditional NER**: Pre-trained to recognize "PERSON", "ORG", "LOC"
**Zero-Shot NER**: Can recognize any custom labels like "product", "chemical", "disease" instantly

### Advantages
- Extreme flexibility
- No training data required
- Rapid prototyping
- Domain adaptation
- Cost-effective
- Easy customization

## Usage Examples

### Entity Extraction Example

**Input Text:**
```
Apple Inc. CEO Tim Cook announced new products in Cupertino.
```

**Custom Labels:**
```
["organization", "person", "location", "product"]
```

**Output:**
```json
[
    {
        "text": "Apple Inc.",
        "label": "organization",
        "start": 0,
        "end": 10,
        "score": 0.95
    },
    {
        "text": "Tim Cook",
        "label": "person",
        "start": 15,
        "end": 23,
        "score": 0.92
    },
    {
        "text": "Cupertino",
        "label": "location",
        "start": 52,
        "end": 61,
        "score": 0.88
    }
]
```

### Relation Extraction Example

**Input Text:**
```
John works at Microsoft in Seattle.
```

**Entities:** John, Microsoft, Seattle
**Relation Labels:** ["works_at", "located_in"]

**Output:**
```json
[
    {
        "source": "John",
        "relation": "works_at",
        "target": "Microsoft",
        "score": 0.94
    },
    {
        "source": "Microsoft",
        "relation": "located_in",
        "target": "Seattle",
        "score": 0.91
    }
]
```

## API Endpoints

### Entity Extraction Endpoint
```http
POST /extract_entities
Content-Type: application/json

{
    "text": "Your text here",
    "labels": ["label1", "label2", "label3"]
}
```

### Relation Extraction Endpoint
```http
POST /extract_relations
Content-Type: application/json

{
    "text": "Your text here",
    "entities": ["entity1", "entity2"],
    "relation_labels": ["relation1", "relation2"]
}
```

## Use Cases

### Document Analysis
- Extract custom entities from legal documents
- Identify domain-specific terms in contracts
- Process financial reports for entities
- Analyze medical records

### Information Extraction
- Pull structured data from unstructured text
- Create knowledge bases from documents
- Populate databases from text sources
- Enrich datasets with entities

### Relationship Mapping
- Discover connections in text
- Build knowledge graphs
- Analyze organizational structures
- Map citation networks

### Content Classification
- Tag content with extracted entities
- Categorize based on entity types
- Support search and filtering
- Enable entity-based navigation

### Research and Prototyping
- Quickly test entity extraction hypotheses
- Prototype NER for new domains
- Validate extraction approaches
- Compare different entity schemas

### Domain-Specific Applications
- **Legal**: Extract parties, clauses, obligations
- **Medical**: Identify diseases, medications, procedures
- **Financial**: Extract companies, amounts, dates
- **Scientific**: Identify chemicals, organisms, methods
- **News**: Extract people, organizations, events

## Key Components

### GLiNER Model
- Pre-trained zero-shot NER model
- Supports any entity labels
- High accuracy across domains
- Fast inference
- Model file auto-downloaded on first run

### NuNER Zero Model (Optional)
- Alternative zero-shot model
- Configurable in settings
- Comparison testing capability

### Streamlit Interface
- User-friendly web interface
- Two tabs: NER and Relation Extraction
- Real-time visualization with spaCy displacy
- Color-coded entity highlighting
- Interactive input and output

### Flask API
- RESTful API for programmatic access
- JSON input/output
- Authentication support (optional)
- Error handling and validation
- Scalable deployment

### Input Validators
- Pydantic schemas for request validation
- Type checking
- Required field validation
- Error messages for invalid input

## Configuration

### config.ini
```ini
[model]
ner_model = gliner_multi_pii-v1
relation_model = gliner_multi-v2.1
device = cpu

[api]
host = 0.0.0.0
port = 5000
debug = False

[streamlit]
port = 8501
theme = light
```

### Model Download
Models are automatically downloaded on first use to `models/` directory.

## Best Practices

1. **Label Design**: Use clear, descriptive entity labels
2. **Label Consistency**: Keep labels consistent across requests
3. **Text Quality**: Provide clean, well-formatted text
4. **Label Specificity**: Use specific labels (e.g., "software_product" vs "product")
5. **Validation**: Review extracted entities for accuracy
6. **Performance**: Limit text length for faster processing

## Limitations

- Prototype application (not production-ready)
- No persistent storage
- Limited to English text (model dependent)
- CPU inference slower than GPU
- Model accuracy varies by domain
- No built-in authentication in prototype
- Single request processing (no batching in UI)

## Performance Considerations

- **Entity Extraction**: 0.5-2 seconds per request
- **Relation Extraction**: 1-3 seconds per request
- **Model Loading**: 10-30 seconds on first run
- **Memory Usage**: ~2-4GB RAM
- **GPU Support**: Configurable for faster inference
- **Text Length**: Longer texts require more processing time

## Deployment Options

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run Streamlit
streamlit run launch.py

# Or run Flask API
python api/model_api.py
```

### Docker Deployment
```bash
# Build container
docker build -t zero-shot-ner .

# Run container
docker run -p 8501:8501 -p 5000:5000 zero-shot-ner
```

### Production Considerations
- Use GPU for faster inference
- Add authentication to API
- Implement rate limiting
- Set up monitoring and logging
- Use load balancer for scaling
- Database for request logging

## Visualization

### spaCy Displacy
- Color-coded entity highlighting
- Interactive HTML display
- Entity labels shown
- Clean, professional appearance
- Embedded in Streamlit UI

## Error Handling

### Common Errors
- Invalid input format
- Missing required fields
- Empty text input
- Unsupported entity labels
- Model loading failures

### Error Responses
```json
{
    "error": "Invalid input",
    "message": "Text field is required",
    "status_code": 400
}
```

## Documentation Structure

1. **README.md** - Documentation index and quick start
2. **01_overview.md** - System overview and capabilities (6KB)
3. **02_architecture.md** - Technical architecture and design (12KB)
4. **03_api_reference.md** - Complete API documentation (15KB)
5. **04_deployment_guide.md** - Deployment and operations (18KB)
6. **05_user_guide.md** - Usage instructions and examples (20KB)

## Related Prototypes

- **Relation Extractor** - Focused relation extraction with LangChain
- **Taxonomy Classification** - Classification systems
- **Document Extract** - Document processing

## Comparison with Relation Extractor Prototype

### Zero-Shot NER
- Uses GLiNER/NuNER models
- True zero-shot (no examples needed)
- Fast inference
- Limited to supported relation types

### Relation Extractor
- Uses OpenAI GPT-4o-mini via LangChain
- Few-shot learning with examples
- More flexible relation types
- Slower but more adaptable

## Quick Reference

**Primary Function**: Extract entities and relations with custom labels at runtime
**Key Features**: Zero-shot learning, no training required, flexible labels
**Models**: GLiNER (primary), NuNER Zero (optional)
**Interfaces**: Streamlit UI + Flask REST API
**Input**: Text + custom entity/relation labels
**Output**: Extracted entities/relations with confidence scores
**Visualization**: spaCy displacy for entity highlighting
**Deployment**: Local, Docker, Cloud
**Tech Stack**: Python, Streamlit, Flask, GLiNER, spaCy, Pydantic
