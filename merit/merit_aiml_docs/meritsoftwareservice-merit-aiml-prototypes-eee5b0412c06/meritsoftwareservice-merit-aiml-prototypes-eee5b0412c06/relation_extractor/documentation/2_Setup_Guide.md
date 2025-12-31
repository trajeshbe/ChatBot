# Relation Extractor Prototype - Setup Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Troubleshooting](#troubleshooting)
7. [Deployment Considerations](#deployment-considerations)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 2GB RAM recommended
- **Internet Connection**: Required for LLM API calls

### Required Accounts

1. **OpenAI Account**
   - Sign up at https://platform.openai.com/
   - Generate an API key from the API keys section
   - Ensure you have sufficient credits for API usage

2. **LangSmith Account (Optional)**
   - Sign up at https://smith.langchain.com/
   - Create a project for tracking LLM calls
   - Generate API key for integration

### Required Software

- Python 3.8+
- pip (Python package installer)
- Virtual environment tool (venv, virtualenv, or conda)
- Git (for version control, optional)

## Environment Setup

### Step 1: Create a Virtual Environment

It's recommended to use a virtual environment to isolate project dependencies.

#### Using venv (Python built-in):

```bash
# Navigate to the relation_extractor directory
cd /path/to/relation_extractor

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Using conda:

```bash
# Create conda environment
conda create -n relation_extractor python=3.10

# Activate environment
conda activate relation_extractor
```

### Step 2: Install Required Dependencies

Create a `requirements.txt` file with the following dependencies:

```txt
streamlit==1.28.0
langchain==0.1.0
langchain-core==0.1.0
langchain-openai==0.0.2
openai==1.3.0
pydantic==2.5.0
python-dotenv==1.0.0
PyYAML==6.0.1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Alternatively, install dependencies individually:

```bash
pip install streamlit langchain langchain-core langchain-openai openai pydantic python-dotenv PyYAML
```

### Step 3: Set Up Environment Variables

Create a `.env` file in the relation_extractor directory:

```bash
touch .env
```

Add the following environment variables to the `.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# LangSmith Configuration (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=test_v2
```

**Important**:
- Replace `your_openai_api_key_here` with your actual OpenAI API key
- Replace `your_langsmith_api_key_here` with your LangSmith API key (if using)
- Never commit the `.env` file to version control

### Step 4: Create .gitignore (Optional)

If using version control, create a `.gitignore` file:

```gitignore
# Environment variables
.env

# Virtual environment
venv/
env/
ENV/

# Python cache
__pycache__/
*.py[cod]
*$py.class

# Logs
logs/
*.log
nohup.out

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
```

## Configuration

### config.yaml Configuration

The `config.yaml` file contains all application settings. Review and modify as needed:

```yaml
# LangSmith Logging Configuration
langsmith_log:
  project: "test_v2"  # Change to your desired project name

# LLM Configuration
llm_details:
  llm_model: "gpt-4o-mini"        # Model to use
  model_provider: "openai"         # Provider (openai, anthropic, etc.)
  temperature: 0                   # Temperature for LLM (0-1)

# Streamlit App Configuration
app_config:
  page_title: "Relation Extraction"           # Browser tab title
  page_layout: "wide"                          # Layout: "centered" or "wide"
  app_title: "Relation Extraction using LLM"  # Main app title
```

### Configuration Options Explained

#### LangSmith Configuration

- **project**: Name of the LangSmith project for logging and monitoring
  - Default: "test_v2"
  - Change to match your LangSmith project name

#### LLM Configuration

- **llm_model**: The specific model to use
  - Default: "gpt-4o-mini"
  - Options: "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"
  - Consider cost vs. performance trade-offs

- **model_provider**: The LLM provider
  - Default: "openai"
  - LangChain supports multiple providers

- **temperature**: Controls randomness in output
  - Default: 0 (deterministic)
  - Range: 0.0 to 1.0
  - 0 = most deterministic, 1 = most creative

#### App Configuration

- **page_title**: Title displayed in browser tab
- **page_layout**: Streamlit page layout
  - "wide": Full-width layout
  - "centered": Centered layout with margins
- **app_title**: Main heading displayed in the app

## Running the Application

### Local Development

1. Ensure virtual environment is activated:
```bash
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

2. Navigate to the relation_extractor directory:
```bash
cd /path/to/relation_extractor
```

3. Run the Streamlit application:
```bash
streamlit run app.py
```

4. The application will open in your default browser at `http://localhost:8501`

### Command-line Options

Streamlit supports various command-line options:

```bash
# Run on a specific port
streamlit run app.py --server.port 8080

# Run on a specific host
streamlit run app.py --server.address 0.0.0.0

# Disable file watcher (for production)
streamlit run app.py --server.fileWatcherType none

# Run with specific browser
streamlit run app.py --browser.serverAddress localhost
```

### Running in Background (Linux/macOS)

To run the application in the background:

```bash
# Using nohup
nohup streamlit run app.py > output.log 2>&1 &

# Using screen
screen -S relation_extractor
streamlit run app.py
# Press Ctrl+A then D to detach

# Using tmux
tmux new -s relation_extractor
streamlit run app.py
# Press Ctrl+B then D to detach
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Module Not Found Error

**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install missing dependencies
pip install -r requirements.txt
```

#### Issue 2: OpenAI API Key Error

**Error**: `openai.error.AuthenticationError: Incorrect API key provided`

**Solution**:
- Verify the API key in `.env` file is correct
- Ensure `.env` file is in the relation_extractor directory
- Check that the API key has not expired
- Verify your OpenAI account has available credits

#### Issue 3: Config File Not Found

**Error**: `Config file not found...`

**Solution**:
- Ensure `config.yaml` exists in the relation_extractor directory
- Verify the current working directory when running the app
- Check file permissions

#### Issue 4: Port Already in Use

**Error**: `OSError: [Errno 98] Address already in use`

**Solution**:
```bash
# Find process using port 8501
lsof -i :8501

# Kill the process
kill -9 <PID>

# Or run on a different port
streamlit run app.py --server.port 8502
```

#### Issue 5: Pydantic Validation Error

**Error**: `pydantic.error_wrappers.ValidationError`

**Solution**:
- The LLM output may not match the expected schema
- Try adjusting the temperature setting
- Review the prompt template in `output_schema.py`
- Check LangSmith logs for the actual LLM output

#### Issue 6: LangChain Import Error

**Error**: `ImportError: cannot import name 'init_chat_model' from 'langchain.chat_models'`

**Solution**:
```bash
# Update LangChain packages
pip install --upgrade langchain langchain-core langchain-openai
```

### Debugging Tips

1. **Enable Detailed Logging**:
   - Check logs in the `logs/` directory
   - Logs are organized by date and hour

2. **Use LangSmith**:
   - Review LLM calls in the LangSmith dashboard
   - Check prompt inputs and LLM outputs
   - Analyze token usage and latency

3. **Streamlit Debugging**:
   - Add `st.write()` statements for debugging
   - Use `st.exception()` to display detailed error information
   - Check browser console for JavaScript errors

4. **Test API Connectivity**:
```python
# Test OpenAI API
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response)
```

## Deployment Considerations

### Production Deployment

For production deployment, consider the following:

#### 1. Security

- Never expose API keys in code or version control
- Use environment variables or secret management services
- Implement authentication for the Streamlit app
- Use HTTPS for secure communication

#### 2. Scalability

- Consider using Streamlit Cloud or other hosting services
- Implement caching for repeated queries
- Use async operations for better performance
- Monitor API usage and costs

#### 3. Reliability

- Implement retry logic for API calls
- Add comprehensive error handling
- Set up monitoring and alerting
- Create backups of configuration and logs

#### 4. Performance Optimization

```python
# Add caching to Streamlit
@st.cache_data
def extract_relations(text):
    # Your extraction logic
    pass
```

#### 5. Environment-Specific Configurations

Create separate configuration files for different environments:

- `config.dev.yaml` - Development settings
- `config.staging.yaml` - Staging settings
- `config.prod.yaml` - Production settings

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:

```bash
docker build -t relation-extractor .
docker run -p 8501:8501 --env-file .env relation-extractor
```

### Cloud Deployment Options

1. **Streamlit Cloud**: Direct deployment from GitHub repository
2. **AWS**: EC2, ECS, or Lambda with API Gateway
3. **Google Cloud Platform**: Cloud Run or App Engine
4. **Azure**: App Service or Container Instances
5. **Heroku**: Web dyno with Streamlit buildpack

## Next Steps

After successful setup:

1. Review the [User Guide](3_User_Guide.md) for usage instructions
2. Explore the [API Reference](4_API_Reference.md) for code details
3. Understand the [Architecture & Design](5_Architecture_Design.md)

---

**Document Version**: 1.0
**Last Updated**: December 2025
