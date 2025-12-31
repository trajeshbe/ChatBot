# TalentSearch - API Reference

## Table of Contents
1. [Core Application](#core-application)
2. [Interface Module](#interface-module)
3. [Utils Module](#utils-module)
4. [Data Models](#data-models)
5. [Prompt Templates](#prompt-templates)
6. [Configuration](#configuration)

---

## Core Application

### app.py

#### Class: `CreateUI`

Main application class that orchestrates the Streamlit interface.

**Inheritance:**
```python
CreateUI(SearchJob)
```

**Initialization:**
```python
def __init__(self):
    super().__init__()
    self.tab1, self.tab2, self.tab3 = st.tabs(["Search", "Alerts", "Upload"])

    # Initialize session state
    if "data" not in st.session_state:
        st.session_state["data"] = pd.DataFrame()
    if "meta_response" not in st.session_state:
        st.session_state["meta_response"] = pd.DataFrame()
    if "tagged" not in st.session_state:
        st.session_state["tagged"] = False
```

**Attributes:**
- `tab1`: Search tab component
- `tab2`: Alerts tab component
- `tab3`: Upload tab component

**Methods:**

##### `render_ui()`

Renders the complete user interface by displaying content in each tab.

**Returns:** None

**Description:**
- Renders search interface in tab1
- Renders alerts interface in tab2
- Renders upload interface in tab3
- Includes error handling for search operations

**Example:**
```python
obj = CreateUI()
obj.render_ui()
```

**Session State Variables:**
- `st.session_state["data"]`: Raw uploaded DataFrame
- `st.session_state["meta_response"]`: Processed metadata DataFrame
- `st.session_state["tagged"]`: Boolean flag for data type
- `st.session_state["filter"]`: List of active filters

---

## Interface Module

### interface/search.py

#### Class: `SearchJob`

Manages job search functionality with SQL-based querying and LLM-powered query generation.

**Inheritance:**
```python
SearchJob(MetaCreation)
```

**Initialization:**
```python
def __init__(self):
    super().__init__()
    self.db = SQLDatabase.from_uri("sqlite:///example.db")
```

**Attributes:**
- `db`: SQLDatabase connection object

**Methods:**

##### `clean_query(x: str) -> str`

Cleans SQL query by extracting the SELECT statement.

**Parameters:**
- `x` (str): Raw SQL query string

**Returns:**
- str: Cleaned SQL query containing only the SELECT statement

**Implementation:**
```python
def clean_query(self, x):
    qry = re.findall(r"SELECT.*", x, flags=re.DOTALL|re.IGNORECASE)[0]
    return qry
```

**Example:**
```python
raw_query = "Here is your query: SELECT * FROM users WHERE domain='Finance'"
cleaned = obj.clean_query(raw_query)
# Returns: "SELECT * FROM users WHERE domain='Finance'"
```

##### `create_sql_chain() -> Chain`

Creates a LangChain pipeline for SQL query generation and execution.

**Returns:**
- Chain: Complete SQL query execution chain

**Chain Steps:**
1. Generate SQL query from natural language (write_query)
2. Clean the generated query (clean_query)
3. Execute query on database (execute_query)

**Example:**
```python
chain = obj.create_sql_chain()
results = chain.invoke({"question": "Find all software engineering jobs"})
```

##### `render_search()`

Renders the search interface with filtering capabilities.

**Returns:** None

**Features:**
- Natural language search input
- Keyword-based search
- Real-time filtering
- Expandable result details
- Clear functionality to reset results

**UI Components:**
- Sidebar search input
- Search button
- Clear button
- Results DataFrame
- Expandable job details

**Example Workflow:**
```python
# User enters: "Python developer jobs in New York"
# System generates SQL: SELECT * FROM users WHERE content LIKE '%python%' AND location_city='New York'
# Results displayed in DataFrame with filters
```

---

### interface/alerts.py

#### Class: `CreateAlerts`

Manages alert interface for recruiter-specific job matching.

**Inheritance:**
```python
CreateAlerts(RecruitersList)
```

**Initialization:**
```python
def __init__(self):
    super().__init__()
    self.recruiter_parser = JsonOutputParser(pydantic_object=RecruiterTemplate)
    self.prompt_recruiter = PromptTemplate(
        template=prompt_recruiter,
        input_variables=["job_post"],
        partial_variables={
            "format_instruction": self.recruiter_parser.get_format_instructions(),
            "recruiters": self.recruiters_list,
        },
    )
    self.recruiter_chain = self.prompt_recruiter | self.llm
```

**Attributes:**
- `recruiter_parser`: JSON parser for recruiter matching output
- `prompt_recruiter`: Prompt template for recruiter matching
- `recruiter_chain`: LangChain pipeline for recruiter assignment

**Methods:**

##### `render_alerts()`

Displays recruiter-filtered job postings.

**Returns:** None

**Features:**
- Dropdown selection for recruiters
- "All Recruiters" option
- Filtered DataFrame display
- Automatic column selection

**UI Components:**
- Recruiter selection dropdown
- Filtered results table

**Example:**
```python
# User selects "Alex Morgan"
# Display shows only jobs assigned to Alex Morgan (Finance specialist)
```

---

### interface/upload.py

#### Class: `MetaCreation`

Handles file upload and automated metadata generation using LLMs.

**Inheritance:**
```python
MetaCreation(CreateAlerts)
```

**Initialization:**
```python
def __init__(self):
    super().__init__()
    self.template_df = pd.read_excel(
        os.path.join(os.getcwd(), "data", "Phaidon_business_sectors.xlsx")
    )
    self.domain_dict = {
        "domain": self.template_df.groupby("Domain")['Business Sectors']
                                   .apply(list).to_dict()
    }
    self.job_parser = JsonOutputParser(pydantic_object=JobTemplate)
    self.prompt_job = PromptTemplate(...)
    self.job_chain = self.prompt_job | self.llm
```

**Attributes:**
- `template_df`: Domain/sector taxonomy DataFrame
- `domain_dict`: Mapping of domains to business sectors
- `job_parser`: JSON parser for job metadata
- `prompt_job`: Prompt template for metadata extraction
- `job_chain`: LangChain pipeline for job processing

**Methods:**

##### `get_joblist(data: dict) -> list`

Retrieves job types for a specific domain and sector.

**Parameters:**
- `data` (dict): Dictionary with 'domain' and 'sector' keys

**Returns:**
- list: Job types matching the domain/sector combination

**Example:**
```python
data = {"domain": "Finance", "sector": "Investment Banking"}
job_types = obj.get_joblist(data)
# Returns: ["Investment Analyst", "Portfolio Manager", "Trader", ...]
```

##### `create_jobtype_prompt(data: dict) -> Chain`

Creates a prompt chain for job type classification.

**Parameters:**
- `data` (dict): Dictionary with 'domain' and 'sector' keys

**Returns:**
- Chain: LangChain pipeline for job type extraction

**Example:**
```python
data = {"domain": "IT", "sector": "Software Development"}
chain = obj.create_jobtype_prompt(data)
result = chain.invoke({"job_post": job_data})
```

##### `create_meta(df: pd.DataFrame) -> pd.DataFrame`

Generates metadata for job postings using LLM chains.

**Parameters:**
- `df` (DataFrame): Raw job posting data

**Returns:**
- DataFrame: Enriched data with generated metadata

**Process:**
1. Sample 2 records from input DataFrame
2. Extract base metadata (domain, sector, location, etc.)
3. Match job type from taxonomy
4. Assign recruiter with relevance score
5. Clean and format results

**Example:**
```python
raw_df = pd.read_excel("jobs.xlsx")
enriched_df = obj.create_meta(raw_df)
# Returns DataFrame with all metadata fields populated
```

**Note:** Currently limited to 2 records per batch (line 82).

##### `render_upload_page()`

Renders file upload interface and handles data processing.

**Returns:** None

**Features:**
- File upload (Excel/CSV)
- Tagged/untagged data selection
- Automated metadata generation
- SQLite database storage
- Session state management

**UI Components:**
- File uploader
- "Use tagged data" checkbox
- Submit button
- Status messages (spinner, success, warnings)

**Workflow:**
```python
Upload File → Parse → Generate Metadata → Clean Data → Store in DB → Update Session State
```

**Supported Formats:**
- `.xlsx` (Excel)
- `.csv` (CSV)

---

### interface/recruiter.py

#### Class: `RecruitersList`

Manages recruiter profiles and configuration data.

**Inheritance:**
```python
RecruitersList(ConfigLoader)
```

**Initialization:**
```python
def __init__(self):
    super().__init__()
    self.recruiters_list = self.picklist['recruiters']
    self.output_columns = ast.literal_eval(self.config_data['output_columns'])
    self.corporate_titles = self.picklist['corporate_titles']
```

**Attributes:**
- `recruiters_list`: List of recruiter profile dictionaries
- `output_columns`: List of column names for output display
- `corporate_titles`: List of seniority levels

**Methods:**

##### `render_recruites()`

Displays recruiter profiles in a DataFrame.

**Returns:** None

**Example:**
```python
obj = RecruitersList()
obj.render_recruites()
# Displays DataFrame with recruiter information
```

---

### interface/helpers.py

Utility functions for data processing.

#### Function: `clean_raw_input(df: pd.DataFrame) -> pd.DataFrame`

Cleans and standardizes raw job posting data.

**Parameters:**
- `df` (DataFrame): Raw input DataFrame

**Returns:**
- DataFrame: Cleaned DataFrame

**Operations:**
1. Fill NaN values with "None"
2. Convert all strings to lowercase
3. Set company to "citibank"

**Example:**
```python
raw_df = pd.read_excel("raw_jobs.xlsx")
cleaned_df = clean_raw_input(raw_df)
```

**Note:** Company name is hardcoded to "citibank".

#### Function: `clean_meta_input(df: pd.DataFrame) -> pd.DataFrame`

Formats metadata for consistent display.

**Parameters:**
- `df` (DataFrame): Metadata DataFrame

**Returns:**
- DataFrame: Formatted DataFrame

**Operations:**
1. Fill NaN with empty strings
2. Capitalize job_title and description
3. Title case for location fields

**Example:**
```python
meta_df = clean_meta_input(meta_df)
# job_title: "software engineer" → "Software engineer"
# location_city: "new york" → "New York"
```

#### Function: `load_meta_data(output_columns: list)`

Reloads metadata from database to session state.

**Parameters:**
- `output_columns` (list): Column names to load

**Returns:** None (updates session state)

**Side Effects:**
- Clears active filters
- Reloads data from SQLite
- Triggers Streamlit rerun
- Displays toast notification

**Example:**
```python
load_meta_data(output_columns)
# Clears filters and reloads fresh data from database
```

---

## Utils Module

### utils/config_reader.py

#### Class: `ConfigLoader`

Central configuration management and LLM initialization.

**Inheritance:**
```python
ConfigLoader(CustomLogger)
```

**Initialization:**
```python
def __init__(self):
    super().__init__()
    # Set LangSmith environment variables
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_KEY")
    os.environ["LANGCHAIN_PROJECT"] = "Sowmya"

    self.config_data = self.read_config()
    self.llm = init_chat_model(...)

    with open("recruiter.json", "r") as f:
        self.picklist = json.loads("".join(f.readlines()))
```

**Attributes:**
- `config`: ConfigParser object
- `config_data`: Dictionary of configuration values
- `llm`: Initialized chat model (OpenAI GPT-4o-mini)
- `picklist`: Recruiter profiles and corporate titles

**Methods:**

##### `read_config() -> dict`

Reads and parses configuration from config.ini.

**Returns:**
- dict: Configuration key-value pairs

**Features:**
- Validates config file existence
- Parses all sections and fields
- Creates required directories
- Error handling with logging

**Configuration Sections:**
- `[default]`: Output columns and paths
- `[llm_config]`: LLM parameters

**Example:**
```python
config_data = obj.read_config()
# Returns: {
#     'output_columns': '[...]',
#     'db_path': 'db',
#     'llm_model': 'gpt-4o-mini',
#     ...
# }
```

**Error Handling:**
```python
try:
    if not os.path.exists(config_file):
        raise Exception("Config file not found...")
except Exception as e:
    self.write_error_log(exc_type, exc_tb, msg)
    sys.exit(msg)
```

---

### utils/log_writer.py

#### Class: `CustomLogger`

Application-wide logging functionality.

**Initialization:**
```python
def __init__(self):
    self.setup_logger()
```

**Attributes:**
- `logger`: Python logging instance

**Methods:**

##### `setup_logger()`

Configures logging system with file-based output.

**Returns:** None

**Configuration:**
- Log directory: `./logs/DD-MM-YY/`
- Log file: `HH.log` (hourly rotation)
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Level: INFO

**Example Log Structure:**
```
./logs/
  └── 20-12-25/
      ├── 09.log
      ├── 10.log
      └── 11.log
```

##### `write_error_log(exc_type, exc_tb, msg)`

Logs error details with context.

**Parameters:**
- `exc_type`: Exception type
- `exc_tb`: Exception traceback object
- `msg`: Error message

**Returns:** None

**Log Format:**
```
{message} | {exception_type} | {filename} | {line_number}
```

**Example:**
```python
try:
    # some operation
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    obj.write_error_log(exc_type, exc_tb, str(e))
```

---

### utils/custom_filter.py

#### Function: `filter_dataframe(df: pd.DataFrame, output_columns: list) -> pd.DataFrame`

Creates interactive DataFrame filters in Streamlit sidebar.

**Parameters:**
- `df` (DataFrame): Data to filter
- `output_columns` (list): Columns available for filtering

**Returns:**
- DataFrame: Filtered DataFrame based on user selections

**Filter Types:**

1. **Categorical** (< 10 unique values)
   - Widget: Multiselect
   - Example: Domain, Sector

2. **Numeric**
   - Widget: Slider with range
   - Example: Salary range

3. **DateTime**
   - Widget: Date range picker
   - Example: Posted date

4. **Text**
   - Widget: Text input (substring/regex)
   - Example: Job title, Description

**Features:**
- Automatic type detection
- Date parsing and timezone handling
- Dynamic filter creation
- Session state integration

**Example:**
```python
filtered_df = filter_dataframe(df, output_columns)
# User can select filters in sidebar:
# - Domain: [Finance, IT]
# - Salary: 50000 - 150000
# - Posted: 2024-01-01 to 2024-12-31
```

**Implementation Details:**
```python
# Categorical filter
if df[column].nunique() < 10:
    user_cat_input = st.multiselect(f"Values for {column}", ...)
    df = df[df[column].isin(user_cat_input)]

# Numeric filter
elif is_numeric_dtype(df[column]):
    user_num_input = st.slider(f"Values for {column}", ...)
    df = df[df[column].between(*user_num_input)]

# DateTime filter
elif is_datetime64_any_dtype(df[column]):
    user_date_input = st.date_input(f"Values for {column}", ...)
    df = df.loc[df[column].between(start_date, end_date)]

# Text filter
else:
    user_text_input = st.text_input(f"Substring or regex in {column}")
    df = df[df[column].str.contains(user_text_input)]
```

---

### utils/custom_prompts.py

LLM prompt templates for different processing tasks.

#### Variable: `prompt_recruiter`

Template for matching jobs to recruiters.

**Template Structure:**
```
System: Expert at semantic tagging with recruiters
Format: JSON output with validation
Context: Recruiter profiles and requirements
Input: Job posting details
Output: Recruiter name, relevance score, justification
```

**Usage:**
```python
from utils.custom_prompts import prompt_recruiter

template = PromptTemplate(
    template=prompt_recruiter,
    input_variables=["job_post"],
    partial_variables={...}
)
```

**Expected Output:**
```json
{
    "recruiter_name": "Alex Morgan",
    "relevence_score": "85",
    "justification": "Strong match for finance sector role..."
}
```

#### Variable: `prompt_job`

Template for extracting job metadata.

**Template Structure:**
```
System: Expert at semantic tagging for alerting
Format: JSON schema with field descriptions
Context: Domain and sector taxonomy
Input: Raw job posting
Output: Structured job metadata
```

**Extracted Fields:**
- company_name
- domain
- sector
- work_arrangement
- location (city, country, region)
- contract_type
- seniority
- date_posted
- salary_low / salary_high

**Usage:**
```python
from utils.custom_prompts import prompt_job

chain = PromptTemplate(template=prompt_job, ...) | llm
result = chain.invoke({"job_post": job_data})
```

#### Variable: `prompt_job_type`

Template for job type classification.

**Template Structure:**
```
System: Expert at semantic job type tagging
Context: Job type examples from taxonomy
Input: Job posting with domain/sector
Output: Specific job type
```

**Usage:**
```python
from utils.custom_prompts import prompt_job_type

# After domain/sector identified
chain = PromptTemplate(template=prompt_job_type, ...) | llm
job_type = chain.invoke({"job_post": enriched_data})
```

---

### utils/custom_templates.py

Pydantic models for data validation and structure.

#### Class: `RecruiterTemplate`

Schema for recruiter matching output.

**Inheritance:**
```python
RecruiterTemplate(BaseModel)
```

**Fields:**

```python
class RecruiterTemplate(BaseModel):
    recruiter_name: str = Field(
        description="Name of the recruiter who is best fit for the given job post"
    )
    relevence_score: str = Field(
        description="Revelence score ranging from 0 to 100 for the recruiter with the job post"
    )
    justification: str = Field(
        description="Give justification for the relevence score"
    )
```

**Example:**
```python
{
    "recruiter_name": "Riley Anderson",
    "relevence_score": "92",
    "justification": "Perfect match for IT cybersecurity role in North America"
}
```

#### Class: `JobTemplate`

Schema for job metadata extraction.

**Inheritance:**
```python
JobTemplate(BaseModel, RecruitersList)
```

**Fields:**

```python
class JobTemplate(BaseModel, RecruitersList):
    company_name: str
    domain: str
    sector: str
    work_arrangement: str = Field(
        description="What is the mode of work. examples: [On-site, Flexible/Hybrid, Remote]",
        default=""
    )
    location_city: str = Field(default="")
    location_country: str = Field(default="")
    location_region: str = Field(default="")
    contract_type: str = Field(
        description="type of contract mention in the job post. examples: [Permanent, Contract]"
    )
    seniority: str = Field(
        description=f"seniority level or corporate title mentioned in the job post. examples: {RecruitersList().corporate_titles}",
        default=""
    )
    date_posted: datetime = Field(default="0")
    salary_low: str = Field(default='0')
    salary_high: str = Field(default='0')
```

**Example:**
```python
{
    "company_name": "Citibank",
    "domain": "Finance",
    "sector": "Investment Banking",
    "work_arrangement": "Hybrid",
    "location_city": "New York",
    "location_country": "USA",
    "location_region": "North America",
    "contract_type": "Permanent",
    "seniority": "Mid-senior",
    "date_posted": "2024-12-20T00:00:00",
    "salary_low": "80000",
    "salary_high": "120000"
}
```

#### Class: `SectorTemplate`

Schema for job type classification.

**Inheritance:**
```python
SectorTemplate(BaseModel)
```

**Fields:**

```python
class SectorTemplate(BaseModel):
    type_of_job: str = Field(
        description="Under which type of job the job post comes",
        default=""
    )
```

**Example:**
```python
{
    "type_of_job": "Senior Python Developer"
}
```

---

## Data Models

### Recruiter Profile Structure

Defined in `recruiter.json`:

```json
{
    "Name": "string",
    "Profile": "string",
    "Focus": "string",
    "Location/Region": "string",
    "Seniority Level": "string",
    "Industry": "string"
}
```

**Example:**
```json
{
    "Name": "Alex Morgan",
    "Profile": "Finance Specialist Recruiter",
    "Focus": "Sourcing top talent in finance, banking, and fintech sectors.",
    "Location/Region": "Global, with a focus on financial hubs (e.g., New York, London, Hong Kong)",
    "Seniority Level": "Mid to Senior (Analysts to C-level executives)",
    "Industry": "Finance, Investment Banking, Fintech"
}
```

### Corporate Titles

Defined in `recruiter.json`:

```json
{
    "corporate_titles": [
        "Intern",
        "Junior",
        "Mid-senior",
        "Senior",
        "Senior Leadership"
    ]
}
```

---

## Configuration

### config.ini Structure

```ini
[default]
output_columns = [list of column names]
db_path = db
input_path = input

[llm_config]
llm_model = gpt-4o-mini
model_provider = openai
temperature = 0
max_tokens = 10000
```

### Environment Variables

Required in `.env` file:

```env
OPEN_AI_KEY=your_openai_api_key_here
LANGCHAIN_KEY=your_langchain_api_key_here
```

**Usage in Code:**
```python
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPEN_AI_KEY")
```

---

## Database Schema

### Table: users

Created dynamically based on `output_columns` configuration.

**Columns:**
1. job_title (TEXT)
2. description (TEXT)
3. company_name (TEXT)
4. domain (TEXT)
5. sector (TEXT)
6. work_arrangement (TEXT)
7. location_city (TEXT)
8. location_country (TEXT)
9. location_region (TEXT)
10. contract_type (TEXT)
11. seniority (TEXT)
12. date_posted (TEXT)
13. salary_low (TEXT)
14. salary_high (TEXT)
15. type_of_job (TEXT)
16. recruiter_name (TEXT)
17. relevence_score (TEXT)
18. justification (TEXT)
19. content (TEXT) - Full-text searchable concatenated content

**SQL Operations:**

**Create/Replace:**
```python
meta_df.to_sql('users', conn, if_exists='replace', index=False)
```

**Query:**
```python
cur.execute("SELECT * from users")
```

**Search:**
```python
# Generated by LLM
SELECT * FROM users WHERE content LIKE '%keyword%' LIMIT 20
```

---

## Error Codes and Messages

### User-Facing Messages

| Message | Trigger | Action |
|---------|---------|--------|
| "No Relevant Postings" | Empty search results | Display warning |
| "Please upload the Job List" | No data in session | Prompt upload |
| "Upload Completed" | Successful data upload | Show success |
| "Server Issue. Try again..." | Exception in upload | Show warning |
| "Searching..." | Query execution | Show spinner |
| "Creating Meta Information" | Metadata generation | Show spinner |
| "Please Wait" | Processing raw data | Show spinner |
| "Filter(s) cleared" | Clear button clicked | Show toast |

### Exception Handling

**Try-Except Locations:**
1. UI rendering (app.py line 35-38)
2. Clear functionality (search.py line 92-97)
3. Upload processing (upload.py line 118-152)
4. Config loading (config_reader.py line 41-64)

---

## API Usage Examples

### Complete Workflow Example

```python
from interface.upload import MetaCreation
from interface.search import SearchJob
import pandas as pd

# Initialize system
uploader = MetaCreation()

# Load and process data
df = pd.read_excel("jobs.xlsx")
meta_df = uploader.create_meta(df)

# Store in database
import sqlite3
conn = sqlite3.connect('example.db')
meta_df.to_sql('users', conn, if_exists='replace', index=False)
conn.close()

# Search
searcher = SearchJob()
chain = searcher.create_sql_chain()
results = chain.invoke({
    "question": "Find software engineering jobs in California"
})

# Parse results
import pandas as pd
results_df = pd.DataFrame(eval(results))
print(results_df)
```

### Custom Recruiter Matching

```python
from utils.custom_prompts import prompt_recruiter
from utils.custom_templates import RecruiterTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Setup
parser = JsonOutputParser(pydantic_object=RecruiterTemplate)
template = PromptTemplate(
    template=prompt_recruiter,
    input_variables=["job_post"],
    partial_variables={
        "format_instruction": parser.get_format_instructions(),
        "recruiters": recruiters_list
    }
)

chain = template | llm

# Match job to recruiter
job_post = {
    "job_title": "Senior Cybersecurity Analyst",
    "domain": "IT",
    "sector": "Cybersecurity",
    "location_country": "USA"
}

result = chain.invoke({"job_post": job_post})
parsed = parser.parse(result.content)

print(f"Recruiter: {parsed['recruiter_name']}")
print(f"Score: {parsed['relevence_score']}")
print(f"Reason: {parsed['justification']}")
```

### Custom Filtering

```python
from utils.custom_filter import filter_dataframe
import streamlit as st

# In Streamlit app
df = st.session_state["meta_response"]
output_columns = [...]  # from config

filtered_df = filter_dataframe(df, output_columns)

# Users can interactively filter in sidebar
# Results automatically update
st.dataframe(filtered_df)
```

---

## Performance Considerations

### API Call Limits

**Per Upload (2 records):**
- Base metadata extraction: 2 API calls
- Job type matching: 2 API calls
- Recruiter matching: 2 API calls
- **Total: 6 API calls per upload**

**Per Search:**
- SQL query generation: 1 API call

### Optimization Tips

1. **Batch Processing**: Increase sample size in `create_meta()` (line 82)
2. **Caching**: Implement response caching for identical queries
3. **Async Processing**: Use async LLM calls for parallel processing
4. **Database Indexing**: Add indexes on frequently queried columns

### Token Usage

**Approximate tokens per operation:**
- Metadata extraction: ~500-1000 tokens
- Job type matching: ~300-500 tokens
- Recruiter matching: ~400-600 tokens
- SQL query generation: ~200-400 tokens

**Configuration:**
```ini
max_tokens = 10000  # Maximum per request
temperature = 0      # Deterministic output
```

---

## Extending the API

### Adding New Recruiters

Edit `recruiter.json`:

```json
{
    "recruiters": [
        {
            "Name": "New Recruiter",
            "Profile": "Specialization",
            "Focus": "Focus areas",
            "Location/Region": "Regions",
            "Seniority Level": "Levels",
            "Industry": "Industries"
        }
    ]
}
```

### Adding New Output Columns

1. Update `config.ini`:
```ini
output_columns = ["existing", "new_column"]
```

2. Update `JobTemplate` in `custom_templates.py`:
```python
class JobTemplate(BaseModel):
    new_column: str = Field(description="Description")
```

3. Update `prompt_job` in `custom_prompts.py` if needed

### Custom Prompt Templates

Create new prompts in `custom_prompts.py`:

```python
prompt_custom = """
You are an expert at {task}.

{format_instruction}

Input: {input_field}
"""

# Use in code
custom_template = PromptTemplate(
    template=prompt_custom,
    input_variables=["input_field"],
    partial_variables={"format_instruction": parser.get_format_instructions()}
)
```

---

## Troubleshooting

### Common Issues

**Issue: "Config file not found"**
- Cause: Missing config.ini
- Solution: Ensure config.ini exists in project root

**Issue: "OpenAI API Error"**
- Cause: Invalid or missing API key
- Solution: Check .env file and OPEN_AI_KEY value

**Issue: "Database locked"**
- Cause: Concurrent SQLite access
- Solution: Close existing connections before writing

**Issue: "No Relevant Postings"**
- Cause: Search returned no results
- Solution: Try different search terms or clear filters

**Issue: Empty metadata_response**
- Cause: No data uploaded
- Solution: Upload job data in Upload tab first

### Debug Mode

Enable logging to track issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs in `./logs/DD-MM-YY/HH.log` for detailed error information.
