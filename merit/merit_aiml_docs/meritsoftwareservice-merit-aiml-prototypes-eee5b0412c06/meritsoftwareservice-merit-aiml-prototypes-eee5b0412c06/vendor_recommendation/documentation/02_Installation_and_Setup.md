# Vendor Recommendation System - Installation and Setup Guide

## Prerequisites

### System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Python Version**: Python 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 500MB free disk space
- **Internet Connection**: Required for API calls to OpenAI

### Required Accounts and API Keys
- **OpenAI API Key**: Required for GPT-4o-mini model access
  - Sign up at: https://platform.openai.com/
  - Navigate to API Keys section
  - Generate a new API key
  - Note: API usage incurs costs based on token consumption

## Installation Steps

### 1. Clone or Download the Repository

If using version control:
```bash
git clone <repository-url>
cd vendor_recommendation
```

Or download and extract the project files to a local directory.

### 2. Set Up Python Virtual Environment (Recommended)

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies

Create a `requirements.txt` file with the following content:

```txt
streamlit>=1.28.0
langchain>=0.1.0
langchain-core>=0.1.0
langchain-openai>=0.0.5
pydantic>=2.0.0
PyMuPDF>=1.23.0
python-dotenv>=1.0.0
PyYAML>=6.0
loguru>=0.7.0
pandas>=2.0.0
openai>=1.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
```

**Important Security Notes**:
- Never commit the `.env` file to version control
- Add `.env` to your `.gitignore` file
- Keep your API keys confidential
- Rotate API keys regularly

### 5. Configure Application Settings

The `config.yaml` file contains application settings:

```yaml
data_path: data

llm:
  model: gpt-4o-mini
  model_provider: openai
  temperature: 0
```

**Configuration Parameters**:
- `data_path`: Directory for uploaded files (default: `data`)
- `llm.model`: LLM model to use (default: `gpt-4o-mini`)
- `llm.model_provider`: Provider name (default: `openai`)
- `llm.temperature`: Controls randomness (0 = deterministic, 1 = creative)

### 6. Create Required Directories

```bash
mkdir -p data
mkdir -p logs
mkdir -p documentation
```

### 7. Verify Installation

Check that all modules can be imported:

```bash
python -c "import streamlit, langchain, pydantic, fitz; print('All dependencies installed successfully')"
```

## Directory Structure

After setup, your project should have the following structure:

```
vendor_recommendation/
├── app.py                      # Main application entry point
├── config.yaml                 # Configuration file
├── config_reader.py            # Configuration loader
├── vendor.py                   # Vendor matching logic
├── vendor_prompt.py            # Vendor evaluation prompt
├── tender_mapping.py           # Tender taxonomy extraction
├── tender_prompt.py            # Tender extraction prompt
├── utils.py                    # Utility functions
├── log_writer.py               # Logging configuration
├── .env                        # Environment variables (create this)
├── requirements.txt            # Python dependencies (create this)
├── data/                       # Uploaded files directory
│   ├── vendor1.txt             # Sample vendor profile
│   └── vendor2.txt             # Sample vendor profile
├── logs/                       # Application logs
│   ├── info_logs.json          # Info level logs
│   └── error_logs.json         # Error/debug logs
└── documentation/              # Documentation files
    ├── 01_Overview.md
    ├── 02_Installation_and_Setup.md
    ├── 03_User_Guide.md
    ├── 04_Technical_Architecture.md
    └── 05_API_Reference.md
```

## Running the Application

### Standard Execution

```bash
streamlit run app.py
```

### Specify Custom Port

```bash
streamlit run app.py --server.port 8501
```

### Run with Custom Configuration

```bash
streamlit run app.py --server.headless true --server.port 8080
```

### Access the Application

After starting, the application will be available at:
- **Local URL**: http://localhost:8501
- **Network URL**: http://<your-ip>:8501

## Verification and Testing

### 1. Test with Sample Data

The system includes sample vendor profiles in the `data/` directory:
- `vendor1.txt`: MediAI HealthTech Ltd (Healthcare sector)
- `vendor2.txt`: AgriPump Technologies Ltd (Agriculture sector)

### 2. Create Test Tender Document

Create a sample PDF tender document to test the matching functionality.

### 3. Run End-to-End Test

1. Start the application
2. Upload a test tender PDF
3. Upload a vendor profile TXT
4. Verify results display correctly
5. Check logs for any errors

### 4. Check Log Files

```bash
# View recent info logs
tail -f logs/info_logs.json

# View recent error logs
tail -f logs/error_logs.json
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Module not found" Error
**Solution**:
```bash
pip install --upgrade -r requirements.txt
```

#### Issue: "OpenAI API Key not found"
**Solution**:
- Verify `.env` file exists in project root
- Check `OPENAI_API_KEY` is correctly set
- Ensure no extra spaces in the key

#### Issue: "Config file not found"
**Solution**:
- Ensure `config.yaml` is in the project root
- Check file permissions

#### Issue: Streamlit Won't Start
**Solution**:
```bash
# Clear Streamlit cache
streamlit cache clear

# Try different port
streamlit run app.py --server.port 8502
```

#### Issue: PDF Reading Fails
**Solution**:
- Ensure PyMuPDF is properly installed
- Verify PDF is not corrupted or password-protected
- Check file permissions

#### Issue: API Rate Limits
**Solution**:
- Check OpenAI account quota
- Implement request throttling
- Consider upgrading OpenAI plan

## Performance Optimization

### 1. Caching Configuration

Add to `config.yaml`:
```yaml
cache:
  enabled: true
  ttl: 3600  # Time to live in seconds
```

### 2. Memory Management

For large documents:
```yaml
processing:
  max_file_size_mb: 10
  chunk_size: 4000
```

### 3. Concurrent Processing

Adjust for multiple files:
```yaml
performance:
  max_workers: 4
  batch_size: 5
```

## Security Hardening

### 1. Secure Environment Variables

Use a secrets management solution in production:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

### 2. Input Validation

The system validates:
- File types (PDF, TXT only)
- File sizes
- Content encoding

### 3. Network Security

For production deployment:
- Use HTTPS
- Implement authentication
- Enable CORS restrictions
- Use reverse proxy (nginx, Apache)

## Deployment Options

### Local Development
```bash
streamlit run app.py
```

### Docker Deployment

Create `Dockerfile`:
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
docker build -t vendor-recommendation .
docker run -p 8501:8501 --env-file .env vendor-recommendation
```

### Cloud Deployment

#### Streamlit Cloud
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in dashboard
4. Deploy

#### AWS EC2
1. Launch EC2 instance
2. Install dependencies
3. Configure security groups
4. Run with screen or systemd

#### Azure App Service
1. Create App Service
2. Deploy via Git or ZIP
3. Configure application settings
4. Enable HTTPS

## Maintenance

### Regular Tasks

1. **Update Dependencies** (Monthly)
```bash
pip list --outdated
pip install --upgrade <package-name>
```

2. **Review Logs** (Weekly)
```bash
grep "ERROR" logs/error_logs.json | tail -20
```

3. **Backup Data** (Daily)
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz data/ logs/
```

4. **Monitor API Usage** (Daily)
- Check OpenAI dashboard
- Review token consumption
- Monitor costs

### Health Checks

Create a monitoring script:
```python
# health_check.py
import requests

def check_health():
    try:
        response = requests.get("http://localhost:8501")
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("Healthy" if check_health() else "Unhealthy")
```

## Support and Resources

### Documentation
- Streamlit: https://docs.streamlit.io/
- LangChain: https://python.langchain.com/
- OpenAI: https://platform.openai.com/docs

### Community
- Streamlit Forums: https://discuss.streamlit.io/
- LangChain GitHub: https://github.com/langchain-ai/langchain

### Getting Help
- Check logs in `./logs/` directory
- Review error messages carefully
- Consult API documentation
- Contact system administrator

## Next Steps

After successful installation:
1. Read the User Guide for operational instructions
2. Review Technical Architecture for system understanding
3. Consult API Reference for customization options
4. Test with sample data before production use
