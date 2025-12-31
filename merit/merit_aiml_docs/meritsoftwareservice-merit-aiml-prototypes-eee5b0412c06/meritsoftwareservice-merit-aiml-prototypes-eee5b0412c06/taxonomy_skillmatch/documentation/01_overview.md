# Taxonomy Skillmatch - Project Overview

## Executive Summary

The Taxonomy Skillmatch prototype is an AI-powered resume classification system that analyzes professional bio-data (resumes) and matches them against a hierarchical taxonomy structure of industries, domains, occupation groups, and specific job roles. The system generates relevancy scores to identify the top 5 most suitable industry classifications for a given resume.

## Project Purpose

This prototype addresses the challenge of automated resume classification and skill matching by leveraging large language models (LLMs) to:

1. Parse and understand resume content
2. Compare candidate skills against predefined taxonomy structures
3. Calculate relevancy scores for different career paths
4. Provide data-driven insights for recruitment and career guidance

## Key Features

### 1. Intelligent Resume Analysis
- Processes complete bio-data (resumes) in text format
- Extracts and analyzes professional skills, experience, and qualifications
- Uses GPT-4o-mini model for natural language understanding

### 2. Hierarchical Taxonomy Classification
- **4-Level Taxonomy Structure:**
  - Level 1: Industry (e.g., Software Development)
  - Level 2: Domain (e.g., Web Development)
  - Level 3: Occupation Group (e.g., Front-End Developer)
  - Level 4: Sub-Group/Job Role (e.g., React Developer)

### 3. Relevancy Scoring
- Calculates percentage-based relevancy scores
- Identifies top 5 most relevant industry classifications
- Provides quantitative metrics for career alignment

### 4. Interactive Web Interface
- Built with Streamlit for easy user interaction
- File upload functionality for resumes (TXT) and taxonomies (JSON)
- Real-time processing with visual feedback
- Downloadable CSV results

### 5. Structured Output
- JSON-formatted results with standardized schema
- Pandas DataFrame conversion for data analysis
- Sorted results by relevancy score

## Technology Stack

### Core Technologies
- **Python 3.x**: Primary programming language
- **LangChain**: LLM orchestration framework
- **OpenAI GPT-4o-mini**: Language model for classification
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis

### Supporting Libraries
- **Pydantic**: Data validation and settings management
- **Hydra**: Configuration management
- **python-dotenv**: Environment variable management

## Architecture Overview

```
┌─────────────────┐
│   User Input    │
│  (Resume + Tax) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  ContentClassification  │
│       (Main Class)      │
└────────┬────────────────┘
         │
         ├──► Prompt Template
         │
         ├──► LLM Processing (GPT-4o-mini)
         │
         ├──► JSON Output Parser
         │
         └──► DataFrame Conversion
                    │
                    ▼
           ┌─────────────────┐
           │  Results Output │
           │  (Top 5 Matches)│
           └─────────────────┘
```

## Use Cases

### 1. Recruitment & Talent Acquisition
- Automated resume screening
- Candidate-job matching
- Skills gap analysis
- Talent pool categorization

### 2. Career Guidance
- Career path recommendations
- Skill alignment assessment
- Professional development planning

### 3. HR Analytics
- Workforce taxonomy mapping
- Skills inventory management
- Organizational capability analysis

### 4. Job Market Research
- Industry trend analysis
- Skills demand assessment
- Career trajectory modeling

## Project Structure

```
taxonomy_skillmatch/
├── taxonomy.py          # Main application and classification logic
├── config.py            # Configuration management
├── config.yaml          # Configuration settings
├── log.py              # Logging functionality
├── requirements.txt     # Python dependencies
└── documentation/       # Project documentation
    ├── 01_overview.md
    ├── 02_technical_architecture.md
    ├── 03_api_reference.md
    ├── 04_user_guide.md
    └── 05_deployment_guide.md
```

## Key Components

### 1. TaxonomyOutputModel
Pydantic model defining the structure of classification results with fields for industry, domain, group, sub-group, and scores.

### 2. ContentClassification
Main class handling:
- LLM initialization and configuration
- Prompt template management
- Response processing
- Data transformation

### 3. Streamlit Interface
Interactive web application providing:
- File upload interface
- Processing status indicators
- Results visualization
- Data export functionality

## Benefits

1. **Automation**: Reduces manual resume screening time
2. **Consistency**: Provides standardized classification across resumes
3. **Scalability**: Can process multiple resumes efficiently
4. **Accuracy**: Leverages advanced NLP for precise matching
5. **Flexibility**: Supports custom taxonomy structures
6. **Transparency**: Provides relevancy scores for decision support

## Limitations & Considerations

1. **Resume Format**: Currently supports only TXT format
2. **Taxonomy Dependency**: Requires well-structured JSON taxonomy
3. **API Costs**: Uses OpenAI API which incurs usage costs
4. **Language Support**: Optimized for English language resumes
5. **Processing Time**: Real-time processing depends on resume length and complexity

## Future Enhancement Opportunities

1. Support for multiple resume formats (PDF, DOCX)
2. Batch processing capabilities
3. Custom scoring algorithm options
4. Integration with ATS (Applicant Tracking Systems)
5. Multi-language support
6. Historical data tracking and analytics
7. RESTful API for system integration
8. Enhanced visualization and reporting

## Security & Privacy

- API keys stored in environment variables
- No persistent storage of resume data
- Session-based state management
- Error logging without sensitive data exposure

## Version Information

- **Current Version**: Prototype/POC
- **LangChain Version**: 0.3.10
- **Streamlit Version**: 1.40.2
- **Model**: OpenAI GPT-4o-mini

## Contact & Support

For questions, issues, or contributions, please refer to the project repository or contact the development team.

---

**Last Updated**: December 2025
**Status**: Active Development - Prototype Phase
