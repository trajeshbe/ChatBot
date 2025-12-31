# Planning Document Classifier

AI-powered planning document classification system for urban planning applications.

## What This Skill Does

This skill helps you work with the Planning Document Classifier prototype - an AI system that automatically categorizes urban planning documents into structured taxonomies using GPT-4o.

## When to Use This Skill

- Understanding planning document classification architecture
- Working with PDF processing and text extraction
- Implementing AI-powered document categorization
- Building Streamlit interfaces for classification tasks
- Analyzing urban planning documents
- Reviewing classification taxonomies and outputs

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/planning_classifier/
```

## Key Files

- `app.py` - Main Streamlit application interface
- `classifier.py` - Document classification logic with LangChain
- `pdf_processor.py` - PDF text extraction utilities
- `documentation/` - Comprehensive technical documentation

## Core Capabilities

### Document Classification
- Classifies planning documents into 5 main categories
- 27 detailed sub-classifications
- Categories: Residential, Commercial, Institutional, Infrastructure, Recreational
- AI-generated justifications for classifications

### PDF Processing
- Extracts text from planning document PDFs
- Handles large documents with text truncation
- Cleans and preprocesses text for LLM analysis

### Classification Taxonomy
- **Residential** (6 sub-classes): Single-family, Multi-family, Mixed-use, etc.
- **Commercial** (8 sub-classes): Retail, Office, Industrial, etc.
- **Institutional** (5 sub-classes): Educational, Healthcare, Government, etc.
- **Infrastructure** (6 sub-classes): Transportation, Utilities, Telecommunications, etc.
- **Recreational** (4 sub-classes): Parks, Sports facilities, Cultural, etc.

## Technical Stack

- **Framework**: Streamlit for web interface
- **AI Model**: OpenAI GPT-4o via LangChain
- **PDF Processing**: PyMuPDF (fitz)
- **Language**: Python 3.11+
- **Deployment**: Replit, local, or cloud

## Common Tasks

### Review Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/planning_classifier
cat documentation/02_technical_architecture.md
```

### Examine Classification Logic
```bash
# Review the classifier module
cat classifier.py

# Check PDF processing
cat pdf_processor.py
```

### Understand API Reference
```bash
# Review API documentation
cat documentation/03_api_reference.md
```

### Run the Application
```bash
streamlit run app.py
```

## Key Components

### Classifier Module
- `classify_document()` - Main classification function
- `create_classification_prompt()` - Generates LLM prompts
- `validate_classification_result()` - Validates AI outputs

### PDF Processor Module
- `extract_text_from_pdf()` - Extracts text from PDF files
- `clean_text()` - Cleans extracted text
- `truncate_text_for_llm()` - Handles token limits

### Application Module
- Streamlit UI for file upload
- Real-time classification display
- Results visualization and export

## Documentation Structure

1. **01_overview.md** - Business context and features
2. **02_technical_architecture.md** - System design and architecture
3. **03_api_reference.md** - Complete API documentation
4. **04_user_guide.md** - End-user instructions
5. **05_deployment_guide.md** - Deployment and configuration

## Use Cases

- **Urban Planning Offices**: Automatically categorize incoming planning applications
- **Document Management**: Organize planning document archives
- **Compliance Review**: Quickly identify document types for regulatory review
- **Research**: Analyze patterns in planning document submissions

## Integration Points

- OpenAI API for GPT-4o model access
- PDF file processing pipeline
- Streamlit session state management
- LangChain for LLM orchestration

## Configuration

- API keys via environment variables
- Streamlit configuration in `.streamlit/config.toml`
- Project dependencies in `pyproject.toml`

## Best Practices

1. **Document Preparation**: Use text-based PDFs (not scanned images)
2. **API Usage**: Monitor OpenAI API costs and rate limits
3. **Validation**: Review AI classifications for accuracy
4. **Error Handling**: Check logs for processing errors
5. **Taxonomy Updates**: Keep classification categories aligned with local regulations

## Limitations

- Prototype/MVP status (not production-ready)
- No user authentication
- Session-based (no persistent storage)
- Requires internet for OpenAI API
- English language only

## Example Workflow

1. User uploads planning document PDF
2. System extracts text from PDF
3. Text is cleaned and truncated if needed
4. LLM analyzes document and assigns categories
5. System displays primary and sub-classification
6. User reviews justification and exports results

## Performance Considerations

- PDF processing time depends on document size
- LLM API calls add 2-5 seconds per classification
- Text truncation for documents >8000 tokens
- Concurrent user sessions limited by resources

## Related Prototypes

- **Taxonomy Classification** - General-purpose taxonomy classification
- **Document Extract** - Advanced document processing
- **Procurement Matcher** - Similar AI-powered matching logic

## Quick Reference

**Main Categories**: Residential, Commercial, Institutional, Infrastructure, Recreational
**Total Sub-categories**: 27
**AI Model**: GPT-4o
**Max Document Size**: 10MB recommended
**Tech Stack**: Python, Streamlit, LangChain, OpenAI
