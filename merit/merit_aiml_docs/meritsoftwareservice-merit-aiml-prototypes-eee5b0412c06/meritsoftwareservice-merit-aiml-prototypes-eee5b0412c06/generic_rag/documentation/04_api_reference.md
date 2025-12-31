# Generic RAG Prototype - API Reference

## Table of Contents
1. [Class: CustomLogger](#class-customlogger)
2. [Class: Utils](#class-utils)
3. [Class: GenericRAG](#class-genericrag)
4. [Session State Variables](#session-state-variables)
5. [Configuration Parameters](#configuration-parameters)
6. [External APIs](#external-apis)

---

## Class: CustomLogger

Base class for logging functionality.

### Constructor

#### `__init__(self)`

Initializes the CustomLogger and sets up logging configuration.

**Parameters**: None

**Returns**: None

**Side Effects**:
- Creates `logs/` directory if it doesn't exist
- Creates date-based subdirectory (DD-MM-YY format)
- Creates hourly log file (HH.log format)
- Configures logging format

**Example**:
```python
logger = CustomLogger()
```

---

### Methods

#### `setup_logger(self)`

Configures the logging system with date and hour-based organization.

**Parameters**: None

**Returns**: None

**Configuration**:
```python
DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        '': {'level': 'INFO'},
        'another.module': {'level': 'INFO'}
    }
}
```

**Log Format**: `%(asctime)s - %(levelname)s - %(message)s`

**Log Path**: `./logs/{DD-MM-YY}/{HH}.log`

**Example**:
```python
logger = CustomLogger()
# Creates: logs/20-12-24/14.log
```

---

#### `write_error_log(self, exc_type, exc_tb, msg)`

Logs error information with context including file name and line number.

**Parameters**:
- `exc_type` (type): Exception type from `sys.exc_info()[0]`
- `exc_tb` (traceback): Traceback object from `sys.exc_info()[2]`
- `msg` (str): Error message from `exc_obj.args[0]`

**Returns**: None

**Side Effects**:
- Writes error to log file with format: `{msg} | {exc_type} | {filename} | {line_number} |`

**Example**:
```python
try:
    # Some operation
    result = risky_operation()
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    msg = exc_obj.args[0]
    self.write_error_log(exc_type, exc_tb, msg)
```

**Sample Log Output**:
```
2024-12-20 14:23:45,123 - ERROR - File not found | <class 'FileNotFoundError'> | rag_table.py | 245 |
```

---

## Class: Utils

Utility class for configuration management. Inherits from CustomLogger.

### Constructor

#### `__init__(self)`

Initializes Utils class and loads configuration.

**Parameters**: None

**Returns**: None

**Side Effects**:
- Calls `read_config()`
- Creates necessary directories
- Populates `self.config_data` dictionary

**Raises**:
- `Exception`: If config.ini not found

**Example**:
```python
utils = Utils()
hf_key = utils.config_data['hf_key']
```

---

### Methods

#### `read_config(self)`

Reads configuration from `config.ini` file and creates necessary directories.

**Parameters**: None

**Returns**: None

**Side Effects**:
- Reads `config.ini` from current working directory
- Populates `self.config_data` dictionary
- Creates `input/` directory if it doesn't exist

**Raises**:
- `Exception`: If config.ini file not found
- Logs error and calls `sys.exit()` on failure

**Configuration Structure**:
```python
self.config_data = {
    'hf_key': str,
    'llama_parser_key': str,
    'groq_key': str,
    'file_input_path': str,
    'db_folder': str,
    'collection_name': str,
    'llm_temperature': str,
    'max_tokens': str,
    'top_k': str,
    'reranker_limit': str,
    'chunk_size': str,
    'llm_list': str,  # String representation of list
    'reranker': str,
    'embedder': str
}
```

**Example**:
```python
utils = Utils()
print(utils.config_data['chunk_size'])  # '250'
```

---

## Class: GenericRAG

Main application class implementing the RAG pipeline. Inherits from Utils.

### Constructor

#### `__init__(self)`

Initializes the GenericRAG application, loads models, and sets up session state.

**Parameters**: None

**Returns**: None

**Side Effects**:
- Calls `st.set_page_config(layout='wide', page_title='Extractive Q&A')`
- Loads configuration via parent class
- Parses configuration parameters
- Initializes session state variables
- Loads and caches embedding and reranking models

**Session State Initialized**:
```python
st.session_state = {
    'models': True,
    'embeddings': SentenceTransformerEmbeddings,
    'ranker_model': HuggingFaceCrossEncoder,
    'fpath': '',
    'vector_db': '',
    'vector_status': False,
    'qa_chain': '',
    'llm': '',
    'table': False
}
```

**Example**:
```python
obj = GenericRAG()
obj.render_UI()
```

---

### Methods - Model Management

#### `load_models(_self, embedder, ranker)` [static, cached]

Loads and caches embedding and reranking models.

**Decorator**: `@st.cache_resource`

**Parameters**:
- `_self` (GenericRAG): Instance reference (underscore prevents hashing)
- `embedder` (str): Name of the embedding model (e.g., 'sentence-transformers/all-MiniLM-L6-v2')
- `ranker` (str): Name of the reranking model (e.g., 'BAAI/bge-reranker-base')

**Returns**:
- Tuple: `(SentenceTransformerEmbeddings, HuggingFaceCrossEncoder)`

**Caching**: Models are cached and persist across reruns

**Example**:
```python
embeddings, ranker = self.load_models(
    'sentence-transformers/all-MiniLM-L6-v2',
    'BAAI/bge-reranker-base'
)
```

---

### Methods - Document Processing

#### `load_doc(self, file_path, chunk_size, chunk_overlap, is_table=False)`

Loads a PDF document, parses it, and splits it into chunks.

**Parameters**:
- `file_path` (str): Path to the PDF file
- `chunk_size` (int): Size of each text chunk (default: 250)
- `chunk_overlap` (int): Overlap between consecutive chunks (default: 0)
- `is_table` (bool): Whether to use LlamaParse for table extraction (default: False)

**Returns**:
- List[Document]: List of document chunks with metadata

**Processing Logic**:
- If `is_table=False`: Uses PyMuPDFLoader
- If `is_table=True`: Uses LlamaParse with markdown output

**Metadata Structure**:
```python
{
    'page': int,      # Page number (1-indexed)
    'source': str     # File path
}
```

**Raises**:
- Logs error and calls `st.error()` and `sys.exit()` on failure

**Example**:
```python
# Standard processing
doc_splits = self.load_doc('/path/to/file.pdf', 250, 0, is_table=False)

# Table processing
doc_splits = self.load_doc('/path/to/file.pdf', 250, 0, is_table=True)
```

---

#### `save_uploaded_file(self, uploaded_file)`

Saves an uploaded Streamlit file to the input directory.

**Parameters**:
- `uploaded_file` (UploadedFile): Streamlit file uploader object

**Returns**:
- str: Full path to the saved file

**Side Effects**:
- Saves file to `{file_input_path}/{filename.lower()}`
- Converts filename to lowercase

**Raises**:
- Logs error and calls `st.error()` and `sys.exit()` on failure

**Example**:
```python
upload_file = st.file_uploader("Choose file", type=['pdf'])
if upload_file:
    fpath = self.save_uploaded_file(upload_file)
    # fpath: '/path/to/input/document.pdf'
```

---

### Methods - Vector Database

#### `create_db(self, splits)`

Creates a ChromaDB vector database from document splits.

**Parameters**:
- `splits` (List[Document]): List of document chunks

**Returns**:
- Chroma: ChromaDB vector store instance

**Side Effects**:
- Calls `clear_collection()` to remove existing collection
- Generates embeddings for all document chunks
- Persists vectors to disk at `persist_directory`

**Database Configuration**:
```python
{
    'documents': splits,
    'embedding': st.session_state['embeddings'],
    'collection_name': self.collection_name,  # From config
    'persist_directory': self.persist_directory  # From config
}
```

**Raises**:
- Logs error and calls `st.error()` and `sys.exit()` on failure

**Example**:
```python
doc_splits = self.load_doc(file_path, 250, 0)
vectordb = self.create_db(doc_splits)
```

---

#### `load_db(self)`

Loads an existing ChromaDB vector database from disk.

**Parameters**: None

**Returns**:
- Chroma: ChromaDB vector store instance

**Side Effects**: None (read-only operation)

**Raises**:
- Logs error if loading fails

**Example**:
```python
vectordb = self.load_db()
retriever = vectordb.as_retriever()
```

---

#### `clear_collection(self)`

Clears the existing ChromaDB collection.

**Parameters**: None

**Returns**:
- bool: True if successful, None if exception caught

**Side Effects**:
- Deletes collection named `self.collection_name` from ChromaDB
- Prints collection information to console

**Exception Handling**:
- Catches and passes all exceptions (non-critical operation)

**Example**:
```python
self.clear_collection()
# Clears 'sample' collection from DB/
```

---

### Methods - Database Initialization

#### `initialize_database(self, file_path, chunk_size, chunk_overlap, is_table)`

End-to-end document indexing pipeline.

**Parameters**:
- `file_path` (str): Path to the PDF file
- `chunk_size` (int): Size of each text chunk
- `chunk_overlap` (int): Overlap between chunks
- `is_table` (bool): Whether to use table-aware processing

**Returns**:
- Tuple: `(status, vector_db)`
  - `status` (int): 1 if successful
  - `vector_db` (Chroma or ParentDocumentRetriever): Vector database instance

**Processing Flow**:

**Standard Mode (is_table=False)**:
1. Load document and create splits
2. Create ChromaDB from splits
3. Return Chroma instance

**Table Mode (is_table=True)**:
1. Clear existing collection
2. Create child splitter (chunk_size=250, overlap=100)
3. Initialize ChromaDB and InMemoryStore
4. Create ParentDocumentRetriever
5. Load document with LlamaParse
6. Add documents to retriever
7. Return ParentDocumentRetriever instance

**Raises**:
- Logs error, displays `st.error()`, and calls `sys.exit()` on failure

**Example**:
```python
# Standard processing
status, vectordb = self.initialize_database(
    '/path/to/file.pdf', 250, 0, is_table=False
)

# Table processing
status, retriever = self.initialize_database(
    '/path/to/file.pdf', 250, 0, is_table=True
)
```

---

### Methods - LLM Initialization

#### `initialize_llmchain(self, llm_model, temperature, max_tokens, top_k, vector_db, is_table)`

Creates a ConversationalRetrievalChain with retriever and LLM.

**Parameters**:
- `llm_model` (str): LLM model identifier
- `temperature` (float): Sampling temperature (0.0-1.0)
- `max_tokens` (int): Maximum tokens to generate
- `top_k` (int): Top-k sampling parameter
- `vector_db` (Chroma or ParentDocumentRetriever): Vector database or retriever
- `is_table` (bool): Whether using table-aware processing

**Returns**:
- ConversationalRetrievalChain: Initialized QA chain

**LLM Selection Logic**:
```python
if llm_model in ['llama-3.1-70b-versatile', 'mixtral-8x7b-32768', 'llama-3.2-11b-vision-preview']:
    llm = ChatGroq(model=llm_model, temperature=temperature)
else:
    llm = HuggingFaceEndpoint(
        repo_id=llm_model,
        temperature=temperature,
        max_new_tokens=max_tokens,
        top_k=top_k,
        huggingfacehub_api_token=self.hf_key
    )
```

**Retrieval Strategy**:

**Standard Mode (is_table=False)**:
- MMR retrieval: k=10, lambda_mult=0.25
- CrossEncoderReranker: top_n=3
- ContextualCompressionRetriever

**Table Mode (is_table=True)**:
- Uses ParentDocumentRetriever directly (no reranking)

**Memory Configuration**:
```python
ConversationBufferMemory(
    memory_key="chat_history",
    output_key="answer",
    return_messages=True
)
```

**Chain Configuration**:
```python
ConversationalRetrievalChain.from_llm(
    llm,
    retriever=retriever,
    chain_type="stuff",
    memory=memory,
    return_source_documents=True,
    verbose=False
)
```

**Example**:
```python
qa_chain = self.initialize_llmchain(
    llm_model='llama-3.1-70b-versatile',
    temperature=0.1,
    max_tokens=1200,
    top_k=3,
    vector_db=vectordb,
    is_table=False
)
```

---

#### `initialize_LLM(self, llm_name, llm_temperature, max_tokens, top_k, vector_db, is_table)`

Wrapper for initializing the LLM chain.

**Parameters**:
- `llm_name` (str): LLM model name
- `llm_temperature` (float): Sampling temperature
- `max_tokens` (int): Maximum tokens to generate
- `top_k` (int): Top-k sampling
- `vector_db` (Chroma or ParentDocumentRetriever): Vector database
- `is_table` (bool): Table processing flag

**Returns**:
- Tuple: `(status, qa_chain)`
  - `status` (int): 1 if successful
  - `qa_chain` (ConversationalRetrievalChain): Initialized chain

**Side Effects**:
- Prints `llm_name` to console

**Example**:
```python
status, qa_chain = self.initialize_LLM(
    'mistralai/Mistral-7B-Instruct-v0.2',
    0.1, 1200, 3, vectordb, False
)
```

---

#### `init_base_llm(self, llm_model, temperature, max_tokens, top_k)`

Initializes a standalone LLM without RAG retrieval.

**Parameters**:
- `llm_model` (str): LLM model identifier
- `temperature` (float): Sampling temperature
- `max_tokens` (int): Maximum tokens to generate
- `top_k` (int): Top-k sampling

**Returns**:
- HuggingFaceEndpoint: Standalone LLM instance

**Use Case**:
- When no document is uploaded
- General conversation mode

**Example**:
```python
llm = self.init_base_llm(
    'mistralai/Mistral-7B-Instruct-v0.2',
    0.1, 1200, 3
)
response = llm.invoke("What is AI?")
```

---

### Methods - Conversation

#### `conversation(self, qa_chain, message)`

Processes a user query and generates a response with source citations.

**Parameters**:
- `qa_chain` (ConversationalRetrievalChain): Initialized QA chain
- `message` (str): User query

**Returns**:
- Tuple: `(qa_chain, response_answer, resource)`
  - `qa_chain` (ConversationalRetrievalChain): Updated chain with memory
  - `response_answer` (str): Generated answer
  - `resource` (List[Dict]): Source documents

**Response Structure**:
```python
response = {
    'question': str,           # Original query
    'chat_history': List,      # Previous messages
    'answer': str,             # Generated answer
    'source_documents': List[Document]  # Retrieved documents
}
```

**Resource Format**:
```python
resource = [
    {
        'Page': int,           # Page number
        'Content': str         # Document chunk text (stripped)
    },
    ...
]
```

**Example**:
```python
qa_chain, answer, sources = self.conversation(
    qa_chain,
    "What is the main topic of this document?"
)

print(answer)  # "The main topic is..."
print(sources)  # [{'Page': 1, 'Content': '...'}, ...]
```

---

#### `stream_data(self, content)`

Streams response content word by word for better UX.

**Parameters**:
- `content` (str): Full response text

**Returns**:
- Generator: Yields words with space, final return is full content

**Timing**:
- 0.02 seconds delay between words

**Example**:
```python
response = "This is a test response."
for word in self.stream_data(response):
    print(word, end='')
# Output: This  is  a  test  response.
```

**Streamlit Usage**:
```python
st.write_stream(self.stream_data(answer))
```

---

### Methods - User Interface

#### `render_UI(self)`

Renders the Streamlit user interface with tabs for upload and chat.

**Parameters**: None

**Returns**: None

**UI Structure**:
```
Streamlit App
├── Tab 1: Chat
│   ├── LLM Model Selector (dropdown)
│   ├── Chat Container (height=400)
│   ├── Message History Display
│   ├── Reference Expander
│   └── Chat Input Box
└── Tab 2: Upload
    ├── File Uploader (PDF only)
    ├── Table Checkbox
    ├── Chunk Size Input (hidden, uses config)
    └── Upload Button
```

**Workflow**:

**Upload Tab**:
1. User uploads PDF
2. User selects table processing option
3. User clicks "Upload"
4. System saves file
5. System indexes document
6. Session state updated

**Chat Tab**:
1. User selects LLM model
2. System initializes QA chain (if document uploaded) or base LLM
3. User enters query
4. System processes query
5. System displays answer with sources
6. Conversation history maintained

**Session State Integration**:
```python
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "How can I help you?",
            "resource": []
        }
    ]
```

**Example**:
```python
if __name__ == "__main__":
    obj = GenericRAG()
    obj.render_UI()
```

---

## Session State Variables

### Global Application State

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `models` | bool | Flag indicating models are loaded | True |
| `embeddings` | SentenceTransformerEmbeddings | Cached embedding model | Loaded model |
| `ranker_model` | HuggingFaceCrossEncoder | Cached reranking model | Loaded model |
| `fpath` | str | Path to uploaded file | "" |
| `vector_db` | Chroma or ParentDocumentRetriever | Vector database instance | "" |
| `vector_status` | bool | Whether vector DB is ready | False |
| `qa_chain` | ConversationalRetrievalChain | Initialized QA chain | "" |
| `llm` | str | Selected LLM name | "" |
| `table` | bool | Table processing flag | False |
| `messages` | List[Dict] | Conversation history | Initial greeting |

### Message Structure

```python
{
    'role': str,        # 'user' or 'assistant'
    'content': str,     # Message text
    'resource': List[Dict]  # Source citations (assistant only)
}
```

---

## Configuration Parameters

### [default] Section

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `hf_key` | str | HuggingFace API token | "hf_xxx..." |
| `llama_parser_key` | str | LlamaParse API key | "llx-xxx..." |
| `groq_key` | str | Groq API key | "gsk_xxx..." |
| `file_input_path` | str | Directory for uploaded files | "input" |
| `db_folder` | str | ChromaDB storage directory | "DB" |
| `collection_name` | str | ChromaDB collection name | "sample" |
| `llm_temperature` | float | LLM sampling temperature | "0.1" |
| `max_tokens` | int | Maximum tokens to generate | "1200" |
| `top_k` | int | Top-k sampling parameter | "3" |
| `reranker_limit` | int | Number of reranked documents | "3" |
| `chunk_size` | int | Text chunk size | "250" |

### [models] Section

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm_list` | str (list repr) | Available LLM models | "[\"llama-3.1-70b-versatile\",...]" |
| `reranker` | str | Reranking model name | "BAAI/bge-reranker-base" |
| `embedder` | str | Embedding model name | "sentence-transformers/all-MiniLM-L6-v2" |

---

## External APIs

### HuggingFace Inference API

**Endpoint**: `https://api-inference.huggingface.co/models/{model_id}`

**Authentication**: Bearer token in `huggingfacehub_api_token`

**Rate Limits**:
- Free tier: ~1000 requests/day
- Pro tier: Higher limits

**Models Used**:
- mistralai/Mistral-7B-Instruct-v0.1
- mistralai/Mistral-7B-Instruct-v0.2
- mistralai/Mixtral-8x7B-Instruct-v0.1

**Parameters**:
```python
{
    'temperature': 0.1,
    'max_new_tokens': 1200,
    'top_k': 3
}
```

---

### Groq API

**Endpoint**: `https://api.groq.com/openai/v1/chat/completions`

**Authentication**: API key in `GROQ_API_KEY` environment variable

**Rate Limits**:
- Varies by plan
- Generally higher than HuggingFace free tier

**Models Used**:
- llama-3.1-70b-versatile
- llama-3.2-11b-vision-preview
- mixtral-8x7b-32768

**Parameters**:
```python
{
    'model': 'llama-3.1-70b-versatile',
    'temperature': 0.1
}
```

---

### LlamaParse API

**Endpoint**: `https://api.llamaindex.ai/api/parsing/upload`

**Authentication**: API key in request headers

**Parameters**:
```python
{
    'result_type': 'markdown',
    'api_key': 'llx-xxx...'
}
```

**Features**:
- Advanced table extraction
- Layout preservation
- Multi-page processing

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Maintained By**: Merit Software Services
