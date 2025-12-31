# API Reference

## Module Overview

The Taxonomy Skillmatch prototype consists of four main Python modules:

| Module | Purpose | Key Components |
|--------|---------|----------------|
| `taxonomy.py` | Core classification logic and UI | ContentClassification, TaxonomyOutputModel, Streamlit app |
| `config.py` | Configuration management | get_config_object() |
| `log.py` | Logging utilities | log_writer() |
| `config.yaml` | Configuration settings | Log file path |

---

## taxonomy.py

### Classes

#### TaxonomyOutputModel

**Description**: Pydantic model representing a single taxonomy classification result.

**Type**: `pydantic.BaseModel`

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `industry` | `str` | Type of industry (1st level in taxonomy) |
| `domain` | `str` | Domain with respect to industry (2nd level) |
| `group` | `str` | Different groups categorized from each domain (3rd level) |
| `sub_group` | `str` | Job role associated with the group (4th level) |
| `scores` | `float` | Relevancy score for the resume (percentage) |

**Field Metadata**:

```python
industry: str = Field(description="type of industry, which is 1st level in the given taxonomy")
domain: str = Field(description="domain with respect to industry, which is 2nd level in the given taxonomy")
group: str = Field(description="different groups categorized from each domain, which is 3rd level in the given taxonomy")
sub_group: str = Field(description="job role associated with the group, which is 4th level in the given taxonomy")
scores: float = Field(description="relevancy score for the resume")
```

**Example**:

```python
result = TaxonomyOutputModel(
    industry="Software Development",
    domain="Web Development",
    group="Front-End Developer",
    sub_group="React Developer",
    scores=85.5
)
```

**Usage**:
- Used as schema for LLM output parsing
- Validates structure of classification results
- Provides field descriptions for prompt engineering

---

#### TaxonomyOutputParser

**Description**: Container model for multiple taxonomy classification results.

**Type**: `pydantic.BaseModel`

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `results` | `List[TaxonomyOutputModel]` | List of taxonomy output models |

**Example**:

```python
parser_output = TaxonomyOutputParser(
    results=[
        TaxonomyOutputModel(...),
        TaxonomyOutputModel(...),
        # ... up to 5 results
    ]
)
```

**Usage**:
- Wraps multiple classification results
- Used by JsonOutputParser for schema validation
- Ensures consistent output structure

---

#### ContentClassification

**Description**: Main class for classifying resume content against taxonomies and generating relevancy scores.

**Type**: `class`

**Constructor**:

```python
def __init__(self) -> None
```

**Parameters**: None

**Behavior**:
1. Loads environment variables from `.env` file
2. Retrieves OpenAI API key from environment
3. Initializes GPT-4o-mini language model
4. Defines prompt template for classification
5. Creates JSON output parser with Pydantic schema

**Initialization Code**:

```python
classifier = ContentClassification()
```

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `api_key` | `str` | OpenAI API key from environment |
| `llm_model` | `ChatModel` | Initialized GPT-4o-mini model |
| `prompt_template` | `str` | Template string for LLM prompt |
| `output_parser` | `JsonOutputParser` | Parser for LLM output |

**LLM Configuration**:

```python
{
    "model": "gpt-4o-mini",
    "model_provider": "openai",
    "temperature": 0,
    "api_key": <from_environment>
}
```

---

### Methods

#### get_prompt()

**Description**: Generates a prompt template for content classification.

**Signature**:

```python
def get_prompt(self) -> PromptTemplate
```

**Parameters**: None

**Returns**:
- **Type**: `PromptTemplate` (LangChain)
- **Description**: A formatted prompt template with input variables and format instructions

**Return Structure**:

```python
PromptTemplate(
    template="{format_instruction}\n\n\n" + self.prompt_template,
    input_variables=["text", "taxonomy"],
    partial_variables={"format_instruction": <auto_generated>}
)
```

**Example Usage**:

```python
classifier = ContentClassification()
prompt = classifier.get_prompt()
# Returns PromptTemplate ready for chain composition
```

**Internal Behavior**:
- Prepends format instructions from output parser
- Includes input variables for text and taxonomy
- Combines with predefined prompt template

---

#### get_response()

**Description**: Generates a response by processing content and taxonomy through the language model.

**Signature**:

```python
def get_response(self, content: str, taxonomy: str) -> dict
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | `str` | Yes | The resume content to classify |
| `taxonomy` | `str` | Yes | The taxonomy structure (JSON string or dict) |

**Returns**:
- **Type**: `dict`
- **Description**: Parsed output from the language model

**Return Structure**:

```python
{
    "results": [
        {
            "industry": str,
            "domain": str,
            "group": str,
            "sub_group": str,
            "scores": float
        },
        # ... up to 5 results
    ]
}
```

**Example Usage**:

```python
classifier = ContentClassification()

resume_text = "Experienced React developer with 5 years..."
taxonomy_data = {...}  # JSON taxonomy structure

result = classifier.get_response(resume_text, taxonomy_data)
print(result['results'])
```

**Processing Flow**:
1. Gets prompt template via `get_prompt()`
2. Creates chain: `prompt | llm_model | output_parser`
3. Invokes chain with content and taxonomy
4. Returns parsed JSON output

**Chain Composition**:

```python
chain = prompt | self.llm_model | self.output_parser
output = chain.invoke({"text": content, "taxonomy": taxonomy})
```

**Error Handling**:
- No explicit error handling in method
- Errors propagate to caller

---

#### to_dataframe()

**Description**: Converts the model response to a pandas DataFrame.

**Signature**:

```python
def to_dataframe(self, response: dict) -> pd.DataFrame
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `response` | `dict` | Yes | The output response from `get_response()` |

**Returns**:
- **Type**: `pd.DataFrame`
- **Description**: DataFrame containing taxonomy classification results

**DataFrame Schema**:

| Column | Type | Description |
|--------|------|-------------|
| `Industry` | `str` | Industry classification |
| `Career Area` | `str` | Domain/career area |
| `Occupation Group` | `str` | Occupation group |
| `Occupation` | `str` | Specific job role |
| `score` | `float` | Relevancy score (percentage) |

**Example Usage**:

```python
response = classifier.get_response(resume, taxonomy)
df = classifier.to_dataframe(response)
print(df)
```

**Output Example**:

```
                Industry         Career Area    Occupation Group         Occupation  score
0  Software Development      Web Development  Front-End Developer     React Developer   85.5
1  Software Development  Application Development  Full Stack Developer  Front-End Specialist  78.2
...
```

**Internal Implementation**:

```python
data = [
    {
        "Industry": i['industry'],
        "Career Area": i['domain'],
        "Occupation Group": i['group'],
        "Occupation": i['sub_group'],
        "score": i['scores']
    }
    for i in response['results']
]
df = pd.DataFrame(data)
```

---

#### get_taxonomy_data()

**Description**: Processes content and taxonomy to generate a classification DataFrame. Main entry point for the classification workflow.

**Signature**:

```python
def get_taxonomy_data(self, content: str, taxonomy: str) -> pd.DataFrame
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | `str` | Yes | The resume content (from TXT file) |
| `taxonomy` | `str` | Yes | The taxonomy structure (JSON object) |

**Returns**:
- **Type**: `pd.DataFrame`
- **Description**: Sorted DataFrame containing top 5 taxonomy results

**Raises**:
- **Type**: `Exception`
- **Description**: Any error during processing
- **Handling**: Logs error and terminates process with `sys.exit()`

**Example Usage**:

```python
classifier = ContentClassification()

with open("resume.txt", "r") as f:
    resume_content = f.read()

with open("taxonomy.json", "r") as f:
    taxonomy_structure = json.load(f)

results_df = classifier.get_taxonomy_data(resume_content, taxonomy_structure)
print(results_df)
```

**Processing Flow**:

```
content + taxonomy
    │
    ▼
get_response()
    │
    ▼
to_dataframe()
    │
    ▼
sort_values(by="score")
    │
    ▼
return DataFrame
```

**Error Logging Format**:

```python
exc_type, exc_obj, exc_tb = sys.exc_info()
error = f"{exc_type} | {exc_obj} | line {exc_tb.tb_lineno} | {exc_tb.tb_frame.f_code.co_filename}"
log.log_writer(error, "ERROR")
```

**Exit Message**:
```
***Terminated the process. For detail exceptions, please check the log.txt***
```

**Note**: This method sorts results but doesn't explicitly limit to top 5. The limitation is enforced by the LLM prompt.

---

## config.py

### Functions

#### get_config_object()

**Description**: Initializes Hydra configuration and composes the configuration object.

**Signature**:

```python
def get_config_object(
    config_path: str = ".",
    config_name: str = "config.yaml"
) -> Any
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `config_path` | `str` | No | `"."` | Path to configuration directory |
| `config_name` | `str` | No | `"config.yaml"` | Name of configuration file |

**Returns**:
- **Type**: `Any` (OmegaConf DictConfig)
- **Description**: Composed configuration object

**Raises**:
- **Type**: `SystemExit`
- **Condition**: If `config.yaml` file is missing
- **Message**: `"***File missing:config file is not available in the path***"`

**Example Usage**:

```python
from config import get_config_object

cfg = get_config_object()
log_file = cfg.taxonomy.taxonomy_log_file
print(log_file)  # Output: "log.txt"
```

**Configuration Access**:

```python
# Dot notation access
cfg.taxonomy.taxonomy_log_file

# Dictionary-style access
cfg['taxonomy']['taxonomy_log_file']
```

**Internal Implementation**:

```python
with initialize(version_base=None, config_path=config_path):
    cfg = compose(config_name=config_name)
    return cfg
```

**File Validation**:

```python
isFile = os.path.isfile("config.yaml")
if not isFile:
    sys.exit("***File missing:config file is not available in the path***")
```

---

## log.py

### Functions

#### log_writer()

**Description**: Writes a log message to a specified log file with timestamp and log type.

**Signature**:

```python
def log_writer(
    message: str,
    log_type: Literal["INFO", "ERROR"]
) -> None
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | `str` | Yes | The message to log |
| `log_type` | `Literal["INFO", "ERROR"]` | Yes | Type of log entry |

**Returns**: None

**Log File**: Configured via `config.yaml` (`taxonomy.taxonomy_log_file`)

**Example Usage**:

```python
import log

# Log informational message
log.log_writer("Processing started", "INFO")

# Log error message
log.log_writer("Failed to parse JSON", "ERROR")
```

**Log Entry Format**:

```
YYYY-MM-DD HH:MM:SS" <LOG_TYPE>: <message> "
```

**Example Log Entries**:

```
2025-12-20 10:30:45" INFO: Processing started "
2025-12-20 10:31:02" ERROR: Failed to parse JSON "
```

**Internal Implementation**:

```python
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(log_file, "a") as myfile:
    myfile.write(f'{current_time}" {log_type}: {message} "\n"')
```

**Configuration Loading**:

```python
configuration = config.get_config_object()
log_file = configuration.taxonomy.taxonomy_log_file
```

---

## config.yaml

### Configuration Schema

**File Format**: YAML

**Structure**:

```yaml
taxonomy:
  taxonomy_log_file: "log.txt"
```

**Configuration Reference**:

| Key Path | Type | Default | Description |
|----------|------|---------|-------------|
| `taxonomy.taxonomy_log_file` | `str` | `"log.txt"` | Path to log file for error and info logging |

**Access Pattern**:

```python
cfg = get_config_object()
log_file = cfg.taxonomy.taxonomy_log_file
```

**Extending Configuration**:

```yaml
taxonomy:
  taxonomy_log_file: "log.txt"
  model_name: "gpt-4o-mini"  # Example extension
  temperature: 0
  max_results: 5
```

---

## Streamlit Application

### Main Application Flow

**Entry Point**: `if __name__ == "__main__":`

**Application Setup**:

```python
st.set_page_config(layout="wide", page_title="taxonomy_skillmatch")
st.title("Taxonomy Skillmatch")
```

### Session State

**Initialization**:

```python
if "data" not in st.session_state:
    st.session_state['data'] = pd.DataFrame()
```

**Access**:

```python
# Set
st.session_state['data'] = results_df

# Get
df = st.session_state['data']
```

### UI Components

#### File Upload Form

**Component**: `st.form()`

```python
with st.form("test"):
    text_file = st.file_uploader("Upload a CV File", type=["txt"])
    json_file = st.file_uploader("Upload a Taxonomy File", type=["json"])
    btn = st.form_submit_button("Submit")
```

**Accepted File Types**:
- CV: `.txt` (plain text)
- Taxonomy: `.json`

#### Processing

**Trigger**: Form submission with both files uploaded

```python
if text_file and json_file and btn:
    text = text_file.read().decode('utf-8')
    taxonomy = json.load(json_file)
    with st.spinner("Please wait!!!"):
        st.session_state['data'] = classifier.get_taxonomy_data(text, taxonomy)
```

#### Results Display

**Components**:

1. **Download Button**:
   ```python
   st.download_button(
       "Download",
       data=df.to_csv(index=False, header=True),
       file_name="output.csv"
   )
   ```

2. **Top Match Display**:
   ```python
   st.markdown(f"**Most Relevant Taxonomy - {' > '.join(df.iloc[:, :-1].iloc[0].tolist())}**")
   ```

3. **DataFrame Display**:
   ```python
   st.dataframe(df)
   ```

**Example Output**:
```
Most Relevant Taxonomy - Software Development > Web Development > Front-End Developer > React Developer
```

### Error Handling

**UI Error Handler**:

```python
try:
    # Display logic
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    error = f"{exc_type} | {exc_obj} | line {exc_tb.tb_lineno} | {exc_tb.tb_frame.f_code.co_filename}"
    log.log_writer(error, "ERROR")
    st.warning("Please try again...")
```

---

## Input/Output Specifications

### Input Formats

#### Resume File (TXT)

**Format**: Plain text

**Content**: Complete bio-data including:
- Professional summary
- Work experience
- Skills
- Education
- Certifications

**Encoding**: UTF-8

**Example**:
```
John Doe
Senior React Developer

PROFESSIONAL SUMMARY
Experienced front-end developer with 5 years of experience in React, TypeScript, and modern web technologies...

SKILLS
- React.js, Redux, TypeScript
- JavaScript, HTML5, CSS3
- Node.js, Express
...
```

#### Taxonomy File (JSON)

**Format**: JSON

**Structure**: Hierarchical taxonomy with 4 levels

**Schema**:
```json
{
  "Industry Name": {
    "Domain Name": {
      "Group Name": {
        "Sub-Group Name": ["skill1", "skill2", "skill3"]
      }
    }
  }
}
```

**Example**:
```json
{
  "Software Development": {
    "Web Development": {
      "Front-End Developer": {
        "React Developer": [
          "React.js",
          "Redux",
          "TypeScript",
          "JavaScript",
          "HTML5",
          "CSS3"
        ]
      }
    }
  }
}
```

### Output Formats

#### JSON Response

**Format**: JSON dictionary

**Schema**:
```json
{
  "results": [
    {
      "industry": "string",
      "domain": "string",
      "group": "string",
      "sub_group": "string",
      "scores": float
    }
  ]
}
```

**Example**:
```json
{
  "results": [
    {
      "industry": "Software Development",
      "domain": "Web Development",
      "group": "Front-End Developer",
      "sub_group": "React Developer",
      "scores": 85.5
    },
    {
      "industry": "Software Development",
      "domain": "Application Development",
      "group": "Full Stack Developer",
      "sub_group": "Front-End Specialist",
      "scores": 78.2
    }
  ]
}
```

#### DataFrame Output

**Format**: pandas DataFrame

**Columns**:
- `Industry` (str)
- `Career Area` (str)
- `Occupation Group` (str)
- `Occupation` (str)
- `score` (float)

**Sorted**: By `score` column (descending)

**CSV Export**: Available via Streamlit download button

---

## Dependencies

### Required Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `langchain` | 0.3.10 | LLM orchestration framework |
| `langchain-community` | 0.3.10 | Community integrations |
| `langchain-core` | 0.3.22 | Core LangChain components |
| `langchain-openai` | 0.2.12 | OpenAI integration |
| `streamlit` | 1.40.2 | Web application framework |
| `pydantic` | (implicit) | Data validation |
| `pandas` | (implicit) | Data manipulation |
| `python-dotenv` | (implicit) | Environment management |
| `hydra-core` | (implicit) | Configuration management |

### Environment Variables

**Required**:

| Variable | Description | Example |
|----------|-------------|---------|
| `API_KEY` | OpenAI API key | `sk-...` |

**Setup** (.env file):
```
API_KEY=sk-your-openai-api-key-here
```

---

## Usage Examples

### Basic Usage

```python
from taxonomy import ContentClassification
import json

# Initialize classifier
classifier = ContentClassification()

# Load resume
with open("resume.txt", "r") as f:
    resume = f.read()

# Load taxonomy
with open("taxonomy.json", "r") as f:
    taxonomy = json.load(f)

# Get results
df = classifier.get_taxonomy_data(resume, taxonomy)

# Display results
print(df)

# Save to CSV
df.to_csv("results.csv", index=False)
```

### Advanced Usage

```python
from taxonomy import ContentClassification

classifier = ContentClassification()

# Get raw response
response = classifier.get_response(resume_text, taxonomy_json)
print(response['results'])

# Convert to DataFrame
df = classifier.to_dataframe(response)

# Get top result
top_match = df.iloc[0]
print(f"Top Match: {top_match['Industry']} > {top_match['Career Area']} > {top_match['Occupation Group']} > {top_match['Occupation']}")
print(f"Score: {top_match['score']}%")
```

### Streamlit Application

```bash
streamlit run taxonomy.py
```

Then:
1. Upload resume TXT file
2. Upload taxonomy JSON file
3. Click "Submit"
4. View results and download CSV

---

**Last Updated**: December 2025
