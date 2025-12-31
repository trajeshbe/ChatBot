# Generic RAG Prototype - Installation & Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [API Keys Setup](#api-keys-setup)
6. [Directory Structure Setup](#directory-structure-setup)
7. [Troubleshooting](#troubleshooting)
8. [Verification](#verification)

## Prerequisites

### Required Software
- **Python**: Version 3.8 or higher (3.9+ recommended)
- **pip**: Python package installer (usually comes with Python)
- **Git**: For cloning the repository (optional)
- **Virtual Environment Tool**: venv, conda, or virtualenv (recommended)

### Required API Keys
You will need to obtain API keys from the following services:

1. **HuggingFace** (Required)
   - Sign up at: https://huggingface.co/
   - Generate token at: https://huggingface.co/settings/tokens
   - Required for LLM and embedding model access

2. **Groq API** (Required for Groq models)
   - Sign up at: https://console.groq.com/
   - Generate API key from dashboard
   - Required for llama-3.1-70b and mixtral models via Groq

3. **LlamaParse** (Required for table processing)
   - Sign up at: https://cloud.llamaindex.ai/
   - Generate API key from dashboard
   - Required when processing PDFs with tables

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 10 GB free space
- **Operating System**: Windows 10+, Linux, macOS 10.15+

### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16 GB+
- **Storage**: 20 GB+ SSD
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster embeddings)
- **Operating System**: Ubuntu 20.04+, Windows 11, macOS 12+

### Network Requirements
- Stable internet connection for API calls
- Minimum 10 Mbps download/upload speed
- Access to HuggingFace, Groq, and LlamaParse endpoints

## Installation Steps

### Step 1: Set Up Python Environment

#### Option A: Using venv (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/macOS
source venv/bin/activate
```

#### Option B: Using Conda
```bash
# Create conda environment
conda create -n generic_rag python=3.9

# Activate environment
conda activate generic_rag
```

### Step 2: Navigate to Project Directory
```bash
cd /path/to/generic_rag
```

### Step 3: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
# Check key packages
python -c "import streamlit; print(f'Streamlit: {streamlit.__version__}')"
python -c "import langchain; print(f'LangChain: {langchain.__version__}')"
python -c "import chromadb; print(f'ChromaDB: {chromadb.__version__}')"
```

## Configuration

### config.ini File Structure

The `config.ini` file contains all configuration settings. Here's the complete structure:

```ini
[default]
# API Keys (REQUIRED - Replace with your actual keys)
hf_key = your_huggingface_api_key_here
llama_parser_key = your_llama_parse_api_key_here
groq_key = your_groq_api_key_here

# Directory Paths
file_input_path = input          # Where uploaded PDFs are stored
db_folder = DB                   # Vector database storage location
collection_name = sample         # ChromaDB collection name

# LLM Parameters
llm_temperature = 0.1            # Sampling temperature (0.0-1.0)
max_tokens = 1200                # Maximum tokens to generate
top_k = 3                        # Top-k sampling parameter
reranker_limit = 3               # Number of documents after reranking
chunk_size = 250                 # Text chunk size for splitting

[models]
# Available LLM Models (List format)
llm_list = ["llama-3.2-11b-vision-preview","llama-3.1-70b-versatile","mixtral-8x7b-32768","mistralai/Mistral-7B-Instruct-v0.2", "mistralai/Mixtral-8x7B-Instruct-v0.1", "mistralai/Mistral-7B-Instruct-v0.1"]

# Embedding and Reranking Models
reranker = BAAI/bge-reranker-base
embedder = sentence-transformers/all-MiniLM-L6-v2
```

## API Keys Setup

### Step 1: Obtain HuggingFace API Key

1. Visit https://huggingface.co/ and create an account
2. Navigate to Settings → Access Tokens
3. Click "New token"
4. Give it a descriptive name (e.g., "Generic RAG")
5. Select "Read" permissions
6. Copy the generated token

### Step 2: Obtain Groq API Key

1. Visit https://console.groq.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Click "Create API Key"
5. Copy the generated key

### Step 3: Obtain LlamaParse API Key

1. Visit https://cloud.llamaindex.ai/
2. Create an account or log in
3. Go to API Keys section
4. Generate new API key
5. Copy the key

### Step 4: Update config.ini

Open `config.ini` and replace the placeholder values:

```ini
[default]
hf_key = hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
llama_parser_key = llx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
groq_key = gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Security Best Practices

1. **Never commit config.ini to version control**
   ```bash
   # Add to .gitignore
   echo "config.ini" >> .gitignore
   ```

2. **Use environment variables (Alternative)**
   ```python
   import os
   hf_key = os.getenv('HUGGINGFACE_API_KEY')
   groq_key = os.getenv('GROQ_API_KEY')
   llama_parser_key = os.getenv('LLAMA_PARSE_API_KEY')
   ```

3. **Set appropriate file permissions**
   ```bash
   # Linux/macOS
   chmod 600 config.ini
   ```

## Directory Structure Setup

The application automatically creates required directories on first run. However, you can create them manually:

```bash
# Create directories
mkdir -p input
mkdir -p DB
mkdir -p logs
```

### Directory Descriptions

- **input/**: Stores uploaded PDF files temporarily
- **DB/**: ChromaDB persistent storage for vector embeddings
- **logs/**: Application logs organized by date and hour

### Disk Space Considerations

- **input/**: Allocate space based on PDF sizes (typically 100-500 MB)
- **DB/**: Vector storage scales with document size
  - Small docs (< 10 pages): ~5 MB
  - Medium docs (10-100 pages): ~50 MB
  - Large docs (> 100 pages): ~200+ MB
- **logs/**: Typically < 100 MB unless extensive debugging

## Troubleshooting

### Common Installation Issues

#### Issue 1: pip install fails for chromadb
```bash
# Error: Building wheel for chroma-hnswlib failed
# Solution: Install build tools

# On Ubuntu/Debian
sudo apt-get install python3-dev build-essential

# On Windows (Install Visual C++ Build Tools)
# Download from: https://visualstudio.microsoft.com/downloads/

# On macOS
xcode-select --install
```

#### Issue 2: PyMuPDF installation error
```bash
# Error: Failed building wheel for pymupdf
# Solution: Install system dependencies

# On Ubuntu/Debian
sudo apt-get install libmupdf-dev mupdf-tools

# Or use pre-built wheels
pip install --upgrade pymupdf
```

#### Issue 3: Torch/CUDA issues
```bash
# For CPU-only installation
pip install torch --index-url https://download.pytorch.org/whl/cpu

# For CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

#### Issue 4: Sentence-transformers download hangs
```bash
# Set HuggingFace cache directory
export TRANSFORMERS_CACHE=/path/to/cache

# Or pre-download models
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Configuration Issues

#### Issue 1: "Config file not found" error
```bash
# Ensure config.ini exists in the same directory as rag_table.py
ls -la config.ini

# Check working directory
pwd
```

#### Issue 2: API key validation failures
```bash
# Test HuggingFace key
curl https://huggingface.co/api/whoami-v2 -H "Authorization: Bearer YOUR_HF_KEY"

# Test Groq key (via Python)
python -c "from groq import Groq; client = Groq(api_key='YOUR_GROQ_KEY'); print('Valid')"
```

#### Issue 3: Permission denied on directories
```bash
# Fix permissions (Linux/macOS)
chmod -R 755 input DB logs

# On Windows, ensure the user has write permissions to the folders
```

### Runtime Issues

#### Issue 1: Out of memory errors
```bash
# Reduce chunk size in config.ini
chunk_size = 150  # Instead of 250

# Or reduce batch size for embeddings (modify code)
```

#### Issue 2: Slow response times
- Check internet connection
- Try a different LLM model (smaller models are faster)
- Reduce `max_tokens` in config.ini
- Use Groq models for faster inference

#### Issue 3: Streamlit port already in use
```bash
# Run on different port
streamlit run rag_table.py --server.port 8502
```

## Verification

### Step 1: Test Configuration Loading
```python
from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')
print("Sections:", config.sections())
print("HF Key exists:", bool(config.get('default', 'hf_key')))
```

### Step 2: Test Model Loading
```python
from sentence_transformers import SentenceTransformer
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# Test embeddings
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("Embedder loaded successfully")

# Test reranker
reranker = HuggingFaceCrossEncoder(model_name='BAAI/bge-reranker-base')
print("Reranker loaded successfully")
```

### Step 3: Run Application
```bash
# Start Streamlit app
streamlit run rag_table.py

# Expected output:
# You can now view your Streamlit app in your browser.
# Local URL: http://localhost:8501
# Network URL: http://192.168.x.x:8501
```

### Step 4: Access Application
1. Open browser to http://localhost:8501
2. You should see "Extractive Q&A" title
3. Two tabs should be visible: "Chat" and "Upload"

### Step 5: Test Basic Functionality
1. Navigate to "Upload" tab
2. Upload a small PDF file
3. Set chunk size (e.g., 250)
4. Click "Upload"
5. Wait for "Done" message
6. Switch to "Chat" tab
7. Select an LLM model
8. Ask a question about the uploaded document

## Performance Optimization

### For Development
```ini
# Use faster models
llm_list = ["llama-3.1-70b-versatile"]  # Groq is fast
chunk_size = 150  # Smaller chunks = faster processing
```

### For Production
```ini
# Use more powerful models
llm_list = ["mistralai/Mixtral-8x7B-Instruct-v0.1"]
chunk_size = 250  # Larger chunks = better context
reranker_limit = 5  # More documents for better answers
```

### Caching Strategies
- Models are cached via `@st.cache_resource` decorator
- Vector database persists to disk automatically
- Clear cache if encountering issues:
  ```bash
  streamlit cache clear
  ```

## Next Steps

After successful installation and verification:

1. Read the [Architecture & Design](03_architecture_design.md) document
2. Review the [API Reference](04_api_reference.md) for customization
3. Follow the [User Guide](05_user_guide.md) for detailed usage instructions
4. Experiment with different models and parameters

## Support & Resources

- **LangChain Documentation**: https://python.langchain.com/docs/
- **Streamlit Documentation**: https://docs.streamlit.io/
- **ChromaDB Documentation**: https://docs.trychroma.com/
- **HuggingFace Documentation**: https://huggingface.co/docs

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Maintained By**: Merit Software Services
