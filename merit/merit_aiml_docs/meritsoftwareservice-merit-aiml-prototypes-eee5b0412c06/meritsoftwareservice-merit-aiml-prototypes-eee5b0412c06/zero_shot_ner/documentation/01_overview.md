# Zero-Shot NER Prototype - Overview

## Table of Contents
- [Introduction](#introduction)
- [Purpose and Scope](#purpose-and-scope)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Use Cases](#use-cases)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)

## Introduction

The Zero-Shot Named Entity Recognition (NER) prototype is an advanced AI/ML application that enables flexible entity extraction and relation identification from text without requiring task-specific training data. The system leverages state-of-the-art zero-shot learning models to identify entities and relationships based on user-defined labels provided at runtime.

This prototype is built under the "Flexitag" branding and provides both entity extraction and relation extraction capabilities through an intuitive web interface and RESTful API.

## Purpose and Scope

### Primary Objectives

1. **Flexible Entity Extraction**: Enable users to extract custom entities from text by simply providing label definitions, without the need for model training or fine-tuning.

2. **Relation Extraction**: Identify and extract relationships between entities in text based on user-specified relation types and label pairs.

3. **Multi-Model Support**: Provide access to multiple zero-shot NER models (GLiNER and NuNER) for comparative analysis and optimal results.

4. **User-Friendly Interface**: Offer both a web-based UI (Streamlit) and RESTful API for different usage scenarios.

5. **Enterprise-Ready**: Include authentication, logging, and resource management features suitable for production environments.

### Scope

The prototype supports:
- Zero-shot named entity recognition with custom labels
- Zero-shot relation extraction between identified entities
- Interactive web interface for testing and demonstration
- RESTful API for integration with other systems
- Multiple model backends (GLiNER and optionally NuNER)
- Configurable thresholds and parameters
- Automatic model downloading and caching
- Resource management with automatic API shutdown on inactivity

## Key Features

### 1. Zero-Shot Learning
- **No Training Required**: Extract entities using custom labels without model training
- **Dynamic Label Definition**: Define entity types and relations at inference time
- **Immediate Results**: Get predictions instantly without data preparation

### 2. Dual Model Support
- **GLiNER Model**: Primary model for entity and relation extraction
- **NuNER Zero Model**: Optional secondary model for comparative results
- **Model Selection**: Choose between models based on performance needs

### 3. Entity Extraction
- **Custom Labels**: Define any entity types relevant to your domain
- **Confidence Scores**: Each extracted entity includes a confidence score
- **Span Detection**: Accurate character-level entity boundaries
- **Entity Merging**: Automatic merging of adjacent entities with the same label (NuNER)

### 4. Relation Extraction
- **Custom Relations**: Define relationship types between entities
- **Pair Filtering**: Specify which entity type pairs can participate in relations
- **Distance Threshold**: Optional distance constraint for relation candidates
- **Entity-Relation Pipeline**: Seamless integration of entity and relation extraction

### 5. Web Interface
- **Streamlit-Based UI**: Modern, responsive web interface
- **Tabbed Interface**: Separate tabs for NER and relation extraction
- **Visual Feedback**: Color-coded entity visualization using spaCy displacy
- **Multi-Model Output**: Compare results from different models side-by-side

### 6. RESTful API
- **HTTP Authentication**: Basic authentication for secure access
- **JSON-Based**: Standard JSON request/response format
- **Input Validation**: Pydantic-based request validation
- **Error Handling**: Comprehensive error messages and HTTP status codes

### 7. Resource Management
- **Automatic Startup**: API server starts automatically when needed
- **Inactivity Monitoring**: Automatic shutdown after configurable idle period
- **Model Caching**: Downloaded models cached locally for faster startup
- **Device Configuration**: Support for CPU/GPU inference

### 8. Logging and Monitoring
- **Structured Logging**: Time-based log files with detailed error tracking
- **Error Tracing**: Full stack trace capture with file and line information
- **Activity Tracking**: Request timestamp tracking for monitoring

## Technology Stack

### Core Frameworks
- **Python 3.x**: Primary programming language
- **Flask 3.0.3**: RESTful API server framework
- **Streamlit 1.35.0**: Web interface framework

### Machine Learning
- **UTCA 0.1.2**: Universal Text Classification Architecture for model integration
- **GLiNER 0.2.2**: Zero-shot NER model library
- **spaCy 3.7.5**: NLP processing and visualization
- **Hugging Face Hub**: Model downloading and management

### Supporting Libraries
- **Pydantic 2.7.2**: Data validation and settings management
- **Flask-HTTPAuth 4.8.0**: HTTP authentication for API
- **NLTK 3.8.1**: Natural language processing utilities
- **Requests 2.32.3**: HTTP client for API communication

## Use Cases

### 1. Document Analysis
Extract custom entities from legal documents, contracts, or reports without training specialized models for each document type.

### 2. Information Extraction
Identify and extract specific information types (dates, amounts, names, locations) from unstructured text based on business requirements.

### 3. Relationship Mapping
Discover relationships between entities in text, such as person-organization affiliations, product-company associations, or cause-effect relationships.

### 4. Content Classification
Tag and categorize content based on extracted entities and their relationships for better organization and searchability.

### 5. Data Enrichment
Enhance existing datasets by extracting additional structured information from text fields using flexible entity definitions.

### 6. Research and Analysis
Quickly prototype and test entity extraction approaches for research without the overhead of model training.

## System Requirements

### Hardware Requirements
- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores, GPU with 8GB+ VRAM (optional)
- **Storage**: 5GB free space for models and dependencies

### Software Requirements
- **Operating System**: Linux, Windows, or macOS
- **Python**: 3.8 or higher
- **Network**: Internet connection for initial model download

### Port Requirements
- **Default API Port**: 5000 (configurable)
- **Default Streamlit Port**: 8501 (configurable)

## Quick Start

### Installation
```bash
# Clone or navigate to the prototype directory
cd zero_shot_ner

# Install dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm
```

### Configuration
Edit `config.ini` to configure:
- Model paths and repositories
- API port and host
- Device (CPU/GPU)
- Authentication credentials
- Auto-shutdown timeout

### Running the Application

#### Web Interface
```bash
# Launch Streamlit interface
streamlit run launch.py
```

#### API Server
```bash
# Start Flask API server
python api/model_api.py
```

### First Entity Extraction
1. Open the web interface (default: http://localhost:8501)
2. Navigate to the "NER" tab
3. Enter your text in the input area
4. Provide comma-separated labels (e.g., "person, organization, location")
5. Click "Predict" to see extracted entities highlighted

### First Relation Extraction
1. Navigate to the "Relation Extraction" tab
2. Enter the relation name (e.g., "works_for")
3. Enter your text
4. Provide entity labels (e.g., "person, organization")
5. Define pairs (e.g., "person -> organization")
6. Click "Submit" to see extracted relations

## Project Structure Overview

```
zero_shot_ner/
├── api/                      # API server components
│   ├── model_api.py         # Flask application and routes
│   ├── zero_shot_ner.py     # NER prediction logic
│   ├── zero_shot_relation.py # Relation extraction logic
│   ├── input_validators.py  # Pydantic request validators
│   └── helpers.py           # Model initialization and utilities
├── interface/               # Web interface components
│   ├── streamlit_app.py    # Main Streamlit application
│   ├── inference.py        # API client for predictions
│   └── check_api.py        # API health check and startup
├── models/                  # Downloaded model cache (auto-created)
├── logs/                    # Application logs (auto-created)
├── config.ini              # Configuration file
├── requirements.txt        # Python dependencies
├── launch.py              # Streamlit entry point
├── entity_extraction.py   # Alternative entry point
└── utils.py               # Logging and utilities
```

## Next Steps

- Review the [Architecture Documentation](02_architecture.md) for technical details
- Consult the [API Reference](03_api_reference.md) for integration
- Follow the [Deployment Guide](04_deployment_guide.md) for production setup
- Read the [User Guide](05_user_guide.md) for detailed usage examples

## Support and Contribution

For issues, questions, or contributions, please contact the development team or refer to the project repository documentation.

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Prototype Status**: Active Development
