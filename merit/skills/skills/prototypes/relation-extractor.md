# Relation Extractor

AI-powered relationship extraction from unstructured text using LangChain and OpenAI.

## What This Skill Does

This skill helps you work with the Relation Extractor prototype - an AI system that automatically identifies and extracts semantic relationships between entities in text.

## When to Use This Skill

- Understanding relationship extraction architectures
- Implementing entity-relationship extraction systems
- Working with LangChain for structured output
- Building NLP applications with Pydantic models
- Analyzing text for semantic relationships
- Processing unstructured data into structured formats

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/relation_extractor/
```

## Key Files

- `app.py` - Main Streamlit application
- `utils/output_schema.py` - Pydantic models for structured output
- `utils/config_reader.py` - Configuration management
- `utils/log_writer.py` - Logging utilities
- `config.yaml` - Application configuration
- `documentation/` - Comprehensive 5-document suite

## Core Capabilities

### Relationship Extraction
- Automatically identifies relationships between entities
- Extracts: source, relation, target, type, nature, confidence score
- Supports various relationship types (professional, personal, organizational)
- Returns structured JSON output with Pydantic validation

### Relationship Components
- **Source**: The originating entity
- **Relation**: The connecting relationship verb/phrase
- **Target**: The destination entity
- **Type**: Category of relationship (e.g., employment, location, ownership)
- **Nature**: Characteristic (e.g., professional, familial, geographic)
- **Score**: Confidence level (0.0 to 1.0)

## Technical Stack

- **Framework**: Streamlit for web interface
- **AI Model**: OpenAI GPT-4o-mini via LangChain
- **Orchestration**: LangChain for prompt management
- **Validation**: Pydantic for structured output
- **Monitoring**: LangSmith for LLM debugging
- **Language**: Python 3.8+

## Common Tasks

### Review Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/relation_extractor
cat documentation/5_Architecture_Design.md
```

### Examine Data Models
```bash
# Review Pydantic schemas
cat utils/output_schema.py
```

### Check API Reference
```bash
cat documentation/4_API_Reference.md
```

### Run Application
```bash
streamlit run app.py
```

## Data Model

### Relationship Output Schema
```python
{
    "source": "John",
    "relation": "works at",
    "target": "Microsoft",
    "score": 0.95,
    "type": "employment",
    "nature": "professional"
}
```

### Example Extraction
**Input Text:**
```
John works at Microsoft in Seattle.
```

**Extracted Relationships:**
1. John → works at → Microsoft (employment, 0.95)
2. Microsoft → located in → Seattle (location, 0.92)

## Key Components

### Output Schema Module
- Pydantic models for data validation
- Structured relationship representation
- Type safety and validation
- JSON serialization support

### Config Reader Module
- YAML configuration loading
- Environment variable management
- Settings validation

### Log Writer Module
- Structured logging with date-based organization
- Hourly log rotation
- JSON log format
- Error and info level separation

### Application Module
- Streamlit interface for text input
- Real-time relationship extraction
- Results display and visualization
- Export functionality

## Documentation Structure

1. **README.md** - Documentation index
2. **1_Overview.md** - System overview and capabilities
3. **2_Setup_Guide.md** - Installation and configuration
4. **3_User_Guide.md** - Usage instructions and examples
5. **4_API_Reference.md** - Complete API documentation
6. **5_Architecture_Design.md** - System architecture and design

## Use Cases

### Business Intelligence
- Extract organizational relationships from documents
- Map company hierarchies and partnerships
- Analyze business relationships

### Knowledge Graphs
- Build knowledge graphs from unstructured text
- Create entity-relationship databases
- Support graph analytics

### Document Analysis
- Analyze legal documents for party relationships
- Extract relationships from contracts
- Process research papers for citations

### Data Enrichment
- Enhance datasets with relationship data
- Connect disparate data sources
- Build comprehensive entity profiles

## Integration Points

- OpenAI API for GPT-4o-mini model
- LangChain for LLM orchestration
- LangSmith for monitoring and debugging
- Pydantic for data validation
- Streamlit for user interface

## Configuration

### config.yaml
```yaml
llm:
  model: gpt-4o-mini
  temperature: 0.0
  max_tokens: 2000

logging:
  level: INFO
  path: logs/
```

### Environment Variables
```bash
OPENAI_API_KEY=your_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
```

## Best Practices

1. **Input Quality**: Provide clear, well-structured text
2. **Prompt Engineering**: Customize prompts for domain-specific relationships
3. **Validation**: Always validate extracted relationships
4. **Logging**: Monitor logs for extraction quality
5. **API Management**: Track API costs and usage

## Limitations

- Prototype application (single-user)
- No built-in authentication
- Limited input validation
- No persistent storage
- Synchronous processing only
- English language optimized

## Example Workflows

### Basic Extraction Workflow
1. User inputs text in Streamlit interface
2. System sends text to LangChain pipeline
3. GPT-4o-mini extracts relationships
4. Pydantic validates output structure
5. Results displayed in structured format
6. User reviews and exports results

### Batch Processing Workflow
1. Load multiple documents
2. Extract relationships from each
3. Aggregate results
4. Build relationship network
5. Visualize or export to database

## Performance Considerations

- Processing time: 2-5 seconds per text sample
- Large texts may require chunking
- API rate limits apply
- Memory efficient with streaming processing

## Logging and Monitoring

### Log Structure
```
logs/
└── DD-MM-YY/
    └── HH.log
```

### Log Contents
- Timestamp for each extraction
- Input text length
- Number of relationships extracted
- Processing time
- Errors and warnings

### LangSmith Monitoring
- Trace all LLM calls
- Debug prompt performance
- Analyze extraction quality
- Monitor costs

## Related Prototypes

- **Zero-Shot NER** - Named entity recognition
- **Taxonomy Classification** - Entity classification
- **Procurement Matcher** - Relationship matching

## Quick Reference

**Primary Function**: Extract semantic relationships from text
**AI Model**: GPT-4o-mini
**Output Format**: Structured JSON with Pydantic validation
**Relationship Fields**: source, relation, target, type, nature, score
**Tech Stack**: Python, Streamlit, LangChain, OpenAI, Pydantic
**Monitoring**: LangSmith integration
