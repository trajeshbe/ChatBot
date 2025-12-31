# TalentSearch - AI-Powered Job Recruitment Platform

## Overview

TalentSearch is an intelligent job posting analysis and recruitment matching system that leverages Large Language Models (LLMs) and semantic search to automatically tag job postings, match them with suitable recruiters, and provide advanced search capabilities. The system streamlines the recruitment process by intelligently categorizing jobs and alerting the most relevant recruiters.

## Key Features

### 1. Intelligent Job Posting Analysis
- Automated extraction and classification of job metadata
- Domain and sector identification using predefined taxonomies
- Seniority level classification
- Work arrangement and contract type detection
- Salary range extraction
- Location parsing (city, country, region)

### 2. Recruiter Matching System
- AI-powered recruiter assignment based on job characteristics
- Relevance scoring (0-100) with detailed justification
- Specialized recruiter profiles for different industries
- Multi-criteria matching (industry, location, seniority level)

### 3. Advanced Search Capabilities
- Natural language search queries
- Semantic search across job postings
- SQL-based querying with LLM query generation
- Real-time filtering by multiple criteria
- Support for both keyword and semantic search

### 4. Alert Management
- Recruiter-specific job alerts
- Filtering by recruiter assignments
- Comprehensive job posting views

### 5. Data Upload and Processing
- Support for Excel (.xlsx) and CSV (.csv) formats
- Both tagged and untagged data processing
- Automated metadata generation
- SQLite database storage for efficient querying

## Technology Stack

### Core Frameworks
- **Streamlit**: Web interface framework
- **LangChain**: LLM orchestration and chain management
- **Pandas**: Data manipulation and analysis
- **SQLite**: Database storage

### AI/ML Components
- **OpenAI GPT-4o-mini**: Primary language model
- **LangSmith**: LLM monitoring and tracing
- **Sentence Transformers**: Text embeddings
- **ChromaDB**: Vector database for semantic search

### Supporting Libraries
- **PyMuPDF**: PDF document processing
- **Pydantic**: Data validation and schema definition
- **python-dotenv**: Environment variable management

## Project Structure

```
talent_search/
├── app.py                      # Main application entry point
├── config.ini                  # Configuration settings
├── requirements.txt            # Python dependencies
├── recruiter.json             # Recruiter profiles and corporate titles
├── documentation/             # Project documentation
├── data/                      # Sample data files
│   ├── samples.xlsx           # Sample job postings
│   ├── meta_sample.xlsx       # Sample metadata
│   └── Phaidon_business_sectors.xlsx  # Domain/sector taxonomy
├── interface/                 # UI components
│   ├── __init__.py
│   ├── alerts.py             # Alert management interface
│   ├── helpers.py            # Utility functions
│   ├── recruiter.py          # Recruiter list management
│   ├── search.py             # Search functionality
│   └── upload.py             # File upload and processing
└── utils/                     # Utility modules
    ├── __init__.py
    ├── config_reader.py      # Configuration loader
    ├── custom_filter.py      # DataFrame filtering
    ├── custom_prompts.py     # LLM prompt templates
    ├── custom_templates.py   # Pydantic data models
    └── log_writer.py         # Logging functionality
```

## Quick Start

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- LangChain API key (for tracing)

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd talent_search
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```env
OPEN_AI_KEY=your_openai_api_key
LANGCHAIN_KEY=your_langchain_api_key
```

4. Ensure the configuration file `config.ini` is properly set up with your preferences.

### Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Configuration

The `config.ini` file contains the following configuration options:

### Default Section
- **output_columns**: List of columns to display in the output
- **db_path**: Database directory path (default: "db")
- **input_path**: Input files directory path (default: "input")

### LLM Configuration
- **llm_model**: Model name (default: "gpt-4o-mini")
- **model_provider**: Provider name (default: "openai")
- **temperature**: Model temperature (default: 0)
- **max_tokens**: Maximum token limit (default: 10000)

## Recruiter Profiles

The system includes six specialized recruiter profiles:

1. **Alex Morgan** - Finance Specialist (Finance, Investment Banking, Fintech)
2. **Jordan Lee** - Engineering & Infrastructure (Energy, Construction, Environmental)
3. **Taylor Brooks** - Supply Chain & Logistics
4. **Casey Blake** - Life Sciences Specialist (Pharmaceuticals, Biotechnology)
5. **Riley Anderson** - IT & Technology (Cybersecurity, Software Development)
6. **Morgan Bennett** - Legal & Regulatory Staffing

Each recruiter profile includes:
- Name and specialization
- Industry focus areas
- Geographic regions
- Seniority levels handled

## Seniority Levels

The system recognizes five seniority tiers:
- Intern
- Junior
- Mid-senior
- Senior
- Senior Leadership

## Data Flow

1. **Upload**: User uploads job posting data (Excel/CSV)
2. **Processing**: System extracts and generates metadata using LLM
3. **Storage**: Data is stored in SQLite database with full-text search
4. **Search**: Users can search using natural language or keywords
5. **Filtering**: Advanced filtering by domain, sector, location, seniority, etc.
6. **Alerts**: Recruiters receive matched job postings with relevance scores

## Use Cases

### For Recruitment Agencies
- Automatically categorize large volumes of job postings
- Route jobs to specialized recruiters efficiently
- Track job postings by industry, location, and seniority

### For HR Departments
- Organize internal job postings
- Match positions with recruiter expertise
- Generate analytics on job distributions

### For Job Boards
- Enhance job search with semantic capabilities
- Provide intelligent job recommendations
- Improve user experience with better filtering

## Limitations and Considerations

- Requires OpenAI API access (paid service)
- LLM processing can be time-intensive for large datasets
- Sample processing limited to 2 records per upload (configurable)
- Company name hardcoded to "citibank" in raw input processing
- Requires stable internet connection for API calls

## Support and Contribution

For issues, questions, or contributions, please contact the development team or refer to the detailed documentation files:
- `ARCHITECTURE.md` - System architecture and design
- `API_REFERENCE.md` - Detailed API documentation
- `USER_GUIDE.md` - Comprehensive user manual
- `DEPLOYMENT.md` - Deployment and configuration guide

## License

This is a prototype application developed for demonstration purposes.

## Acknowledgments

Built with LangChain, OpenAI, and Streamlit technologies.
