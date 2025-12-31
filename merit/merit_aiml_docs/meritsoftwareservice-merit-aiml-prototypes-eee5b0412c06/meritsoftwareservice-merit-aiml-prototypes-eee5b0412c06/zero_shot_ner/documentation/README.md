# Zero-Shot NER Prototype - Documentation

## Welcome

This documentation provides comprehensive information about the Zero-Shot Named Entity Recognition (NER) prototype, a flexible AI/ML application for entity extraction and relation identification without requiring task-specific training.

## Documentation Structure

The documentation is organized into five main documents, each covering a specific aspect of the prototype:

### 1. [Overview](01_overview.md)
**Start here if you're new to the project**

- Introduction to zero-shot NER
- Key features and capabilities
- Technology stack overview
- Use cases and applications
- System requirements
- Quick start guide
- Project structure

**Best for**: Product managers, stakeholders, new users, and anyone wanting a high-level understanding.

### 2. [Architecture Documentation](02_architecture.md)
**For developers and technical architects**

- System architecture and design
- Component interaction diagrams
- Data flow and processing pipelines
- Model architecture details
- Class structure and inheritance
- Design patterns used
- Security and performance considerations

**Best for**: Developers, architects, technical leads, and anyone implementing or extending the system.

### 3. [API Reference](03_api_reference.md)
**For integration developers**

- Complete API endpoint documentation
- Request/response formats and schemas
- Authentication and security
- Error handling and status codes
- Code examples in Python, JavaScript, and cURL
- Client library usage
- Integration best practices

**Best for**: Backend developers, integration engineers, and API consumers.

### 4. [Deployment Guide](04_deployment_guide.md)
**For DevOps and system administrators**

- Prerequisites and system requirements
- Installation instructions (development and production)
- Configuration options and best practices
- Docker and container deployment
- Cloud deployment (AWS, GCP, Azure)
- Kubernetes deployment
- Troubleshooting common issues
- Maintenance and monitoring

**Best for**: DevOps engineers, system administrators, and deployment teams.

### 5. [User Guide](05_user_guide.md)
**For end users and analysts**

- Getting started with the web interface
- Step-by-step usage examples
- Entity extraction scenarios
- Relation extraction scenarios
- Advanced features and parameters
- Best practices for label design
- Use case scenarios across domains
- Tips, tricks, and FAQ

**Best for**: End users, data analysts, researchers, and anyone using the application.

## Quick Navigation

### I want to...

- **Understand what this prototype does** → [Overview](01_overview.md)
- **Install and run the application** → [Deployment Guide](04_deployment_guide.md) → Installation section
- **Use the web interface** → [User Guide](05_user_guide.md) → Getting Started
- **Integrate with the API** → [API Reference](03_api_reference.md)
- **Understand the technical design** → [Architecture Documentation](02_architecture.md)
- **Deploy to production** → [Deployment Guide](04_deployment_guide.md) → Production Deployment
- **Troubleshoot an issue** → [Deployment Guide](04_deployment_guide.md) → Troubleshooting
- **See usage examples** → [User Guide](05_user_guide.md) → Examples sections
- **Learn best practices** → [User Guide](05_user_guide.md) → Best Practices

## Key Concepts

### Zero-Shot Learning
The ability to extract entities and relations using custom labels defined at runtime, without requiring model training or fine-tuning. This makes the system extremely flexible for diverse use cases.

### Entity Extraction (NER)
Identifying and classifying named entities in text based on user-defined labels. For example, extracting "person", "organization", "location" from a news article.

### Relation Extraction
Identifying relationships between extracted entities. For example, finding "works_for" relationships between person and organization entities.

### Supported Models
- **GLiNER**: Primary model for entity and relation extraction
- **NuNER Zero**: Optional secondary model for comparison (configurable)

## Getting Started - 5 Minute Quick Start

### Prerequisites
- Python 3.8+
- 8GB RAM minimum
- Internet connection (for initial setup)

### Installation
```bash
# Navigate to project directory
cd zero_shot_ner

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Launch the application
streamlit run launch.py
```

### First Extraction
1. Open http://localhost:8501 in your browser
2. Go to the "NER" tab
3. Enter text: `Apple Inc. CEO Tim Cook announced new products in Cupertino.`
4. Enter labels: `organization, person, location`
5. Click "Predict"
6. See color-coded entities in the output!

For more detailed instructions, see the [User Guide](05_user_guide.md).

## Architecture Overview

```
┌─────────────────┐
│   Web Browser   │
│  (User Interface)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Streamlit     │
│   Frontend      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Flask API     │
│   (Port 5000)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GLiNER/NuNER   │
│  Model Pipeline │
└─────────────────┘
```

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Streamlit 1.35.0, spaCy displacy |
| **API** | Flask 3.0.3, Flask-HTTPAuth 4.8.0 |
| **ML Framework** | UTCA 0.1.2, GLiNER 0.2.2 |
| **NLP** | spaCy 3.7.5, NLTK 3.8.1 |
| **Validation** | Pydantic 2.7.2 |
| **Infrastructure** | Python 3.8+, Docker (optional) |

## Common Use Cases

1. **Document Analysis**: Extract custom entities from legal, financial, or medical documents
2. **Information Extraction**: Pull structured data from unstructured text
3. **Relationship Mapping**: Discover connections between entities in text
4. **Content Classification**: Tag and categorize content based on extracted entities
5. **Data Enrichment**: Enhance datasets with additional structured information
6. **Research Analysis**: Quickly prototype entity extraction for research projects

## Project File Structure

```
zero_shot_ner/
├── documentation/           # This documentation
│   ├── README.md           # This file
│   ├── 01_overview.md
│   ├── 02_architecture.md
│   ├── 03_api_reference.md
│   ├── 04_deployment_guide.md
│   └── 05_user_guide.md
├── api/                    # Backend API
│   ├── model_api.py       # Flask application
│   ├── zero_shot_ner.py   # NER logic
│   ├── zero_shot_relation.py
│   ├── input_validators.py
│   └── helpers.py
├── interface/             # Frontend UI
│   ├── streamlit_app.py
│   ├── inference.py
│   └── check_api.py
├── models/                # Downloaded models (auto-created)
├── logs/                  # Application logs (auto-created)
├── config.ini            # Configuration
├── requirements.txt      # Python dependencies
├── launch.py            # Streamlit entry point
├── entity_extraction.py # Alternative entry point
└── utils.py            # Utilities
```

## Support and Contribution

### Getting Help

1. **Check the documentation**: Most questions are answered in the guides above
2. **Review the FAQ**: See [User Guide - FAQ](05_user_guide.md#faq)
3. **Check troubleshooting**: See [Deployment Guide - Troubleshooting](04_deployment_guide.md#troubleshooting)
4. **Contact the team**: Reach out to the development team for support

### Reporting Issues

When reporting issues, please include:
- Operating system and Python version
- Relevant log files from `logs/` directory
- Steps to reproduce the issue
- Error messages or unexpected behavior
- Configuration settings (sanitize credentials)

### Contributing

For contributions, please:
- Follow the existing code structure and style
- Add tests for new functionality
- Update documentation for changes
- Submit changes through proper channels

## License and Credits

**Prototype Status**: Active Development

**Key Technologies**:
- GLiNER by Knowledgator
- NuNER by Numind
- UTCA (Universal Text Classification Architecture)
- spaCy by Explosion AI
- Flask by Pallets
- Streamlit

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 2025 | Initial documentation release |

## Additional Resources

### External Documentation
- [spaCy Documentation](https://spacy.io/docs)
- [GLiNER GitHub](https://github.com/urchade/GLiNER)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Flask Documentation](https://flask.palletsprojects.com)

### Related Prototypes
Check the parent directory for other AI/ML prototypes in the Merit AIML collection.

---

**Last Updated**: December 2025
**Documentation Version**: 1.0

For the latest updates and information, please refer to the project repository.
