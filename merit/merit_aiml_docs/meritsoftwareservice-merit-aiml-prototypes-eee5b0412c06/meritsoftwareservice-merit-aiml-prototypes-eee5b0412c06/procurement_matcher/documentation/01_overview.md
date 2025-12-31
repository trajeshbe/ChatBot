# Procurement Matcher - System Overview

## Executive Summary

The Procurement Matcher is an AI-powered prototype application designed to facilitate intelligent matching and classification across three distinct domains:

1. **Legal Case Matching**: Compares precedent legal cases with current cases to identify relevant precedents
2. **Procurement Vendor Matching**: Evaluates vendor profiles against procurement requirements
3. **Vendor Taxonomy Classification**: Extracts and classifies vendor information into structured taxonomy

## Purpose and Objectives

### Primary Objectives
- Automate the matching process between requirements and potential vendors/cases
- Provide confidence scores for matches based on semantic similarity and capability alignment
- Extract structured information from unstructured vendor data
- Reduce manual effort in vendor selection and legal research processes

### Key Benefits
- **Time Efficiency**: Rapidly processes multiple vendor profiles or legal cases simultaneously
- **Objective Analysis**: Provides AI-driven confidence scores with clear justifications
- **Structured Output**: Transforms unstructured data into actionable insights
- **Scalability**: Handles multiple documents in batch processing mode

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                   │
│                         (app.py)                             │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬──────────────┐
        │                       │              │
┌───────▼────────┐    ┌────────▼────────┐   ┌▼──────────────┐
│ Legal Profile  │    │ Vendor Profile  │   │ Vendor Mapping│
│ (legal_profile)│    │ (procurement)   │   │ (taxonomy)    │
└───────┬────────┘    └────────┬────────┘   └┬──────────────┘
        │                      │              │
        └──────────┬───────────┴──────────────┘
                   │
        ┌──────────▼──────────┐
        │    Utils Layer      │
        │  - LLM Integration  │
        │  - File Readers     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Config & Logging   │
        │  - ConfigLoader     │
        │  - CustomLogger     │
        └─────────────────────┘
```

### Technology Stack

**Frontend Framework**
- Streamlit: Interactive web interface with file upload and data visualization

**AI/ML Framework**
- LangChain: LLM orchestration and prompt management
- OpenAI GPT-4o-mini: Language model for semantic analysis and extraction
- Pydantic: Data validation and structured output parsing

**Document Processing**
- PyMuPDF (fitz): PDF text extraction

**Configuration & Utilities**
- YAML: Configuration management
- python-dotenv: Environment variable management
- Loguru: Structured logging

## Application Modules

### 1. Main Application (app.py)
Central entry point providing a unified interface with three tabs:
- Legal Case Matcher
- Procurement Matcher
- Vendor Taxonomy Classifier

### 2. Legal Profile Module (legal_profile.py)
Handles legal case matching functionality:
- Compares precedent cases (PDF) with current cases (TXT)
- Returns confidence scores and justifications
- Focus on legal issues and reasoning patterns

### 3. Procurement Module (procurement.py)
Manages vendor-to-requirement matching:
- Evaluates vendor profiles (PDF) against requirements (TXT)
- Analyzes capability and feature alignment
- Excludes commercial terms from evaluation

### 4. Vendor Taxonomy Module (vendor_mapping.py)
Extracts structured information from vendor descriptions:
- Category and sub-category classification
- Service, compliance, and geography extraction
- Risk and sustainability assessment

### 5. Supporting Modules
- **utils.py**: Common utilities (file readers, LLM initialization)
- **config_reader.py**: Configuration management
- **log_writer.py**: Structured logging setup
- **prompt files**: Domain-specific prompts for each module

## Data Flow

### Typical User Workflow

1. **User Input**: Upload documents (PDF/TXT) or enter text via web interface
2. **File Processing**: Documents saved to data directory and content extracted
3. **AI Processing**: Content sent to LLM with domain-specific prompts
4. **Structured Parsing**: JSON responses parsed into Pydantic models
5. **Result Display**: Confidence scores and analysis displayed in sortable tables

### Processing Pipeline

```
Document Upload → File Storage → Content Extraction →
Prompt Formation → LLM Invocation → JSON Parsing →
Validation → Result Display
```

## Key Features

### Multi-Document Processing
- Batch processing of multiple vendor profiles or precedent cases
- Progress bar visualization during processing
- Session state management for result persistence

### Structured Output
- Consistent JSON schema enforced via Pydantic models
- Confidence scores (0.1 to 1.0 range)
- Detailed justifications for all matches

### Error Handling
- Comprehensive exception handling at each layer
- User-friendly error messages via Streamlit
- Detailed error logging for debugging

### Configurability
- YAML-based configuration for easy customization
- Environment variable support for API keys
- Modular prompt system for domain adaptation

## Use Cases

### Legal Research
- Identify relevant precedent cases for ongoing litigation
- Compare legal reasoning patterns across cases
- Build case strategy based on historical analysis

### Procurement Management
- Evaluate vendor capabilities against project requirements
- Compare multiple vendors objectively
- Reduce vendor selection time and bias

### Vendor Classification
- Automatically categorize vendor offerings
- Extract compliance and geographic information
- Identify risks and sustainability factors

## System Requirements

### Runtime Requirements
- Python 3.8+
- OpenAI API key (for GPT-4o-mini access)
- Minimum 4GB RAM
- 500MB disk space

### Input Requirements
- PDF files for vendor profiles or precedent cases
- TXT files for requirements or current cases
- Text input for vendor taxonomy classification

## Deployment Model

The application is designed as a standalone prototype suitable for:
- Local deployment for proof-of-concept
- Internal enterprise deployment
- Cloud deployment (with appropriate security measures)

## Future Enhancements

### Potential Improvements
1. Support for additional document formats (DOCX, RTF)
2. Integration with document management systems
3. Advanced filtering and search capabilities
4. Export functionality (CSV, Excel, PDF reports)
5. User authentication and role-based access
6. Historical matching analytics and trends
7. Custom taxonomy management interface
8. Multi-language support

### Scalability Considerations
- Database integration for result persistence
- Asynchronous processing for large document batches
- Caching layer for frequently accessed documents
- API endpoint exposure for system integration

## Security and Compliance

### Current Implementation
- Local file storage in designated data directory
- Environment variable management for API keys
- Structured logging for audit trails

### Recommended Enhancements
- Document encryption at rest
- Secure file upload validation
- User authentication and authorization
- Data retention policies
- PII detection and redaction
- Compliance with data protection regulations (GDPR, CCPA)

## Support and Maintenance

### Logging System
- JSON-formatted logs with rotation (daily)
- Separate info and error log files
- 7-day retention for info logs, 30-day for error logs
- Automatic compression of old logs

### Monitoring Points
- LLM API response times
- Document processing success rates
- User session metrics
- Error frequency and patterns

## Conclusion

The Procurement Matcher prototype demonstrates a versatile AI-powered matching and classification system applicable to legal research, procurement management, and vendor analysis. Its modular architecture, structured output format, and extensible design make it suitable for enterprise deployment with appropriate enhancements for security, scalability, and integration requirements.
