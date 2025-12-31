# Relation Extractor Prototype - API Reference

## Table of Contents

1. [Module Overview](#module-overview)
2. [app.py - Main Application](#apppy---main-application)
3. [utils.config_reader - Configuration Module](#utilsconfig_reader---configuration-module)
4. [utils.log_writer - Logging Module](#utilslog_writer---logging-module)
5. [utils.output_schema - Schema Definition Module](#utilsoutput_schema---schema-definition-module)
6. [Data Models](#data-models)
7. [Configuration Schema](#configuration-schema)
8. [Integration Examples](#integration-examples)

## Module Overview

The Relation Extractor prototype consists of four main modules:

| Module | File | Purpose |
|--------|------|---------|
| Main Application | `app.py` | Streamlit UI and orchestration |
| Configuration | `utils/config_reader.py` | Configuration loading and management |
| Logging | `utils/log_writer.py` | Logging setup and error handling |
| Schema | `utils/output_schema.py` | Pydantic models and prompt templates |

### Module Dependencies

```
app.py
├── utils.config_reader
│   ├── utils.log_writer
│   └── dotenv
├── utils.output_schema
│   ├── pydantic
│   ├── langchain_core.output_parsers
│   └── langchain_core.prompts
├── langchain.chat_models
└── streamlit
```

## app.py - Main Application

### Class: App

Main application class that integrates all components.

#### Inheritance

```python
class App(ConfigLoader, OutputTemplate)
```

Inherits from:
- `ConfigLoader`: Configuration management
- `OutputTemplate`: Schema and prompt management

#### Constructor

```python
def __init__(self):
    """
    Initializes the Relation Extractor application.

    Sets up:
    - Configuration loading from config.yaml
    - Output schema and parser
    - LangSmith logging environment
    - Streamlit page configuration
    - LLM initialization

    Environment Variables Required:
    - OPENAI_API_KEY: OpenAI API key
    - LANGCHAIN_TRACING_V2: Enable LangSmith tracing (optional)
    - LANGCHAIN_API_KEY: LangSmith API key (optional)

    Raises:
        Exception: If configuration file is missing or invalid
        Exception: If environment variables are not set
    """
```

**Implementation Details:**

```python
def __init__(self):
    super().__init__()  # Initialize ConfigLoader
    OutputTemplate.__init__(self)  # Initialize OutputTemplate

    # Set LangSmith project for logging
    os.environ["LANGCHAIN_PROJECT"] = self.config_data['langsmith_log']['project']

    # Configure Streamlit page
    st.set_page_config(
        layout=self.config_data['app_config']['page_layout'],
        page_title=self.config_data['app_config']['page_title']
    )

    # Set application title
    st.title(self.config_data['app_config']['app_title'])

    # Initialize LLM
    self.llm = init_chat_model(
        model=self.config_data['llm_details']['llm_model'],
        model_provider=self.config_data['llm_details']['model_provider'],
        temperature=self.config_data['llm_details']['temperature']
    )

    print(self.parser)  # Debug output
```

**Attributes:**

- `config_data` (dict): Configuration loaded from config.yaml
- `llm` (ChatModel): Initialized language model
- `parser` (JsonOutputParser): Pydantic-based output parser
- `prompt` (PromptTemplate): Formatted prompt template

#### Method: render_app

```python
def render_app(self) -> None:
    """
    Renders the Streamlit user interface and handles user interactions.

    Creates a form with:
    - Text area for input
    - Submit button
    - Output display area

    Processing Flow:
    1. User enters text in the text area
    2. User clicks submit button
    3. Text is sent to LLM with prompt
    4. LLM response is parsed into structured format
    5. Results are displayed to user

    Error Handling:
    - Displays warning if parsing fails
    - Prompts user to try again

    Returns:
        None
    """
```

**Implementation Details:**

```python
def render_app(self):
    # Create LLM chain with prompt
    self.chat = self.prompt | self.llm

    # Create Streamlit form
    with st.form("test"):
        txt = st.text_area(label="Input Text")
        btn = st.form_submit_button()

    # Process on submit
    if btn and txt:
        with st.spinner("Please wait"):
            # Invoke LLM
            res = self.chat.invoke({
                "content": txt
            })

            try:
                # Parse and display results
                st.write("Extracted Output")
                st.write(self.parser.parse(res.content))
            except:
                # Handle parsing errors
                st.warning("Please try again...")
```

**Parameters:**
- None

**Returns:**
- None

**Side Effects:**
- Renders Streamlit UI components
- Makes API calls to LLM service
- Displays results or error messages

#### Main Execution

```python
if __name__ == "__main__":
    obj = App()
    obj.render_app()
```

**Purpose:**
- Entry point for the application
- Creates App instance and renders interface

## utils.config_reader - Configuration Module

### Class: ConfigLoader

Handles loading and validation of configuration from YAML file.

#### Inheritance

```python
class ConfigLoader(CustomLogger)
```

Inherits from:
- `CustomLogger`: Logging functionality

#### Constructor

```python
def __init__(self):
    """
    Initializes the configuration loader.

    Loads:
    - Environment variables from .env file
    - Configuration from config.yaml

    Attributes:
        config_data (dict): Parsed configuration dictionary

    Raises:
        Exception: If config.yaml is not found
        Exception: If YAML parsing fails
    """
```

**Implementation Details:**

```python
def __init__(self):
    super().__init__()  # Initialize CustomLogger
    load_dotenv()  # Load .env file
    self.config_data = self.read_config()  # Read configuration
```

**Attributes:**
- `config_data` (dict): Configuration dictionary with keys:
  - `langsmith_log`: LangSmith logging settings
  - `llm_details`: LLM configuration
  - `app_config`: Application UI settings

#### Method: read_config

```python
def read_config(self) -> dict:
    """
    Reads and parses the config.yaml file.

    Looks for config.yaml in the current working directory.

    Returns:
        dict: Parsed configuration data

    Raises:
        Exception: If config.yaml file does not exist
        Exception: If YAML parsing fails

    Error Logging:
        Logs detailed error information including:
        - Exception type
        - File name where error occurred
        - Line number
        - Error message
    """
```

**Implementation Details:**

```python
def read_config(self):
    config_file = os.path.join(os.getcwd(), "config.yaml")

    try:
        # Check if file exists
        if not os.path.exists(config_file):
            raise Exception("Config file not found...")

        # Read and parse YAML
        with open("config.yaml", "r") as file:
            config_data = yaml.safe_load(file)

        return config_data

    except Exception as e:
        # Log error and exit
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = exc_obj.args[0]
        self.write_error_log(exc_type, exc_tb, msg)
        sys.exit(msg)
```

**Parameters:**
- None

**Returns:**
- `dict`: Configuration dictionary

**Raises:**
- `Exception`: If config file not found or invalid

## utils.log_writer - Logging Module

### Class: CustomLogger

Provides comprehensive logging functionality with date-based organization.

#### Constructor

```python
def __init__(self):
    """
    Initializes the custom logger.

    Sets up:
    - Logging configuration
    - Date and hour-based log directory structure
    - Log file formatting

    Log Organization:
    - Directory: ./logs/DD-MM-YY/
    - File: HH.log (hour-based)

    Log Format:
    - Timestamp
    - Log level (INFO, ERROR, etc.)
    - Message

    Attributes:
        logger: Python logging object
    """
```

**Implementation Details:**

```python
def __init__(self):
    self.setup_logger()
```

**Attributes:**
- `logger` (logging): Configured Python logging object

#### Method: setup_logger

```python
def setup_logger(self) -> None:
    """
    Configures the logging system.

    Configuration:
    - Version: 1
    - Disable existing loggers: False
    - Root logger level: INFO

    Log Structure:
    - Creates logs directory if not exists
    - Organizes by date: logs/DD-MM-YY/
    - Creates hourly log files: HH.log

    Format:
    - Pattern: "%(asctime)s - %(levelname)s - %(message)s"
    - Includes timestamp, level, and message

    Returns:
        None
    """
```

**Implementation Details:**

```python
def setup_logger(self):
    # Define logging configuration
    DEFAULT_LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "loggers": {
            "": {
                "level": "INFO",
            },
            "another.module": {
                "level": "INFO",
            },
        },
    }

    # Apply configuration
    logging.config.dictConfig(DEFAULT_LOGGING)

    # Create log directory structure
    dt = datetime.now()
    log_path = f'./logs/{dt.strftime("%d-%m-%y")}'
    os.makedirs(log_path, exist_ok=True)

    # Configure basic logging
    logging.basicConfig(
        filename=f'{log_path}/{dt.strftime("%H")}.log',
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    self.logger = logging
```

**Log Directory Structure:**
```
logs/
└── 20-12-25/
    ├── 00.log
    ├── 01.log
    ├── ...
    └── 23.log
```

#### Method: write_error_log

```python
def write_error_log(self, exc_type, exc_tb, msg: str) -> None:
    """
    Logs detailed error information.

    Args:
        exc_type: Exception type from sys.exc_info()
        exc_tb: Exception traceback from sys.exc_info()
        msg (str): Error message

    Logged Information:
    - Error message
    - Exception type
    - File name where error occurred
    - Line number

    Format:
    - "message | exception_type | filename | line_number |"

    Returns:
        None

    Example:
        try:
            # some code
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            msg = exc_obj.args[0]
            self.write_error_log(exc_type, exc_tb, msg)
    """
```

**Implementation Details:**

```python
def write_error_log(self, exc_type, exc_tb, msg):
    # Extract filename from traceback
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

    # Format error message
    error = (
        str(msg)
        + " | "
        + str(exc_type)
        + " | "
        + str(fname)
        + " | "
        + str(exc_tb.tb_lineno)
        + " | "
    )

    # Log error
    self.logger.error(error)
    self.logger.info("-------------------------------------")
```

**Parameters:**
- `exc_type`: Exception type
- `exc_tb`: Exception traceback object
- `msg` (str): Error message

**Returns:**
- None

## utils.output_schema - Schema Definition Module

### Data Models

#### Class: FieldRelations

Pydantic model for individual relationship instances.

```python
class FieldRelations(BaseModel):
    """
    Represents a single relationship between entities.

    Attributes:
        source (str): The source entity in the relationship
        relation (str): The relationship type/verb connecting entities
        target (str): The target entity in the relationship
        score (float): Confidence score between 0.0 and 1.0

    Example:
        {
            "source": "John Smith",
            "relation": "works at",
            "target": "Microsoft",
            "score": 0.95
        }
    """
    source: str = Field(description="source of the relation")
    relation: str = Field(description="relation between source and target")
    target: str = Field(description="target of the source related")
    score: float = Field(description="a confidence score between 0.0 to 1.0")
```

**Fields:**

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| source | str | Source entity | Required, non-empty |
| relation | str | Relationship type | Required, non-empty |
| target | str | Target entity | Required, non-empty |
| score | float | Confidence score | Required, 0.0-1.0 |

#### Class: Relations

Pydantic model for relationship groups.

```python
class Relations(BaseModel):
    """
    Represents a group of related relationships.

    Attributes:
        type (str): The type/category of relationship
        nature (str): The nature or characteristic of the relationship
        relationships (List[Dict[str, FieldRelations]]): List of relationships

    Example:
        {
            "type": "employment",
            "nature": "professional",
            "relationships": [
                {
                    "job_1": {
                        "source": "Alice",
                        "relation": "works at",
                        "target": "Google",
                        "score": 0.92
                    }
                }
            ]
        }
    """
    type: str = Field(description="type of the relationship")
    nature: str = Field(description="nature of the relationship")
    relationships: List[Dict[str, FieldRelations]]
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| type | str | Relationship category |
| nature | str | Relationship characteristic |
| relationships | List[Dict] | List of relationship instances |

#### Class: FinalRelation

Pydantic model for the complete output structure.

```python
class FinalRelation(BaseModel):
    """
    Top-level model for all extracted relationships.

    Attributes:
        relationships (List[Dict[str, Relations]]): All relationship groups

    Example:
        {
            "relationships": [
                {
                    "employment": {
                        "type": "professional",
                        "nature": "work_relationship",
                        "relationships": [...]
                    }
                },
                {
                    "location": {
                        "type": "geographical",
                        "nature": "spatial",
                        "relationships": [...]
                    }
                }
            ]
        }
    """
    relationships: List[Dict[str, Relations]]
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| relationships | List[Dict] | All extracted relationship groups |

### Class: OutputTemplate

Manages prompt templates and output parsing.

#### Constructor

```python
def __init__(self):
    """
    Initializes the output template and parser.

    Sets up:
    - Prompt template for relationship extraction
    - JSON output parser with Pydantic model
    - Format instructions for LLM

    Attributes:
        parser (JsonOutputParser): Parser for LLM output
        prompt (PromptTemplate): Formatted prompt template
    """
```

**Implementation Details:**

```python
def __init__(self):
    # Define base prompt
    prompt_template = \
        """
        You are an expert at understanding how LLMs uncover relationships from a given text.
        Please extract potential relationships from the given text and provide the output in a json format.
        The json in addition to the source, relationship and target, should also contain type and nature of relationship.
        """

    # Initialize parser with Pydantic model
    self.parser = JsonOutputParser(pydantic_object=FinalRelation)

    # Create prompt template
    self.prompt = PromptTemplate(
        template="{format_instructions}\n\n"
        + prompt_template
        + "\n\nContent: {content}",
        input_variables=["content"],
        partial_variables={"format_instructions": self.parser.get_format_instructions()},
    )

    print(self.parser)
```

**Attributes:**

- `parser` (JsonOutputParser): Parses LLM output to Pydantic models
- `prompt` (PromptTemplate): Complete prompt with format instructions

**Prompt Structure:**

1. **Format Instructions**: Auto-generated from Pydantic model
2. **Task Description**: Explains the relationship extraction task
3. **Content Placeholder**: Where user input is inserted

## Data Models

### Complete Type Definitions

```python
# Type for individual relationship field
FieldRelations = {
    "source": str,
    "relation": str,
    "target": str,
    "score": float  # Range: 0.0 to 1.0
}

# Type for relationship group
Relations = {
    "type": str,
    "nature": str,
    "relationships": List[Dict[str, FieldRelations]]
}

# Type for complete output
FinalRelation = {
    "relationships": List[Dict[str, Relations]]
}
```

## Configuration Schema

### config.yaml Structure

```yaml
# LangSmith logging configuration
langsmith_log:
  project: string  # Project name for LangSmith

# LLM configuration
llm_details:
  llm_model: string      # Model name (e.g., "gpt-4o-mini")
  model_provider: string # Provider name (e.g., "openai")
  temperature: float     # Temperature setting (0.0 to 1.0)

# Application configuration
app_config:
  page_title: string   # Browser tab title
  page_layout: string  # Layout: "wide" or "centered"
  app_title: string    # Main application title
```

### Configuration Validation

The configuration is validated at runtime:

```python
# Required fields check
required_fields = [
    "langsmith_log.project",
    "llm_details.llm_model",
    "llm_details.model_provider",
    "llm_details.temperature",
    "app_config.page_title",
    "app_config.page_layout",
    "app_config.app_title"
]
```

## Integration Examples

### Example 1: Standalone Relationship Extraction

```python
from utils.config_reader import ConfigLoader
from utils.output_schema import OutputTemplate
from langchain.chat_models import init_chat_model

# Initialize components
config = ConfigLoader()
schema = OutputTemplate()

# Initialize LLM
llm = init_chat_model(
    model=config.config_data['llm_details']['llm_model'],
    model_provider=config.config_data['llm_details']['model_provider'],
    temperature=config.config_data['llm_details']['temperature']
)

# Create chain
chat = schema.prompt | llm

# Extract relationships
text = "John works at Microsoft in Seattle."
response = chat.invoke({"content": text})
relationships = schema.parser.parse(response.content)

print(relationships)
```

### Example 2: Batch Processing

```python
import json
from app import App

# Initialize app (without rendering UI)
app = App()

# List of texts to process
texts = [
    "Alice is the CEO of TechCorp.",
    "Bob studied at Harvard University.",
    "The conference was held in Paris."
]

# Process each text
results = []
for text in texts:
    response = app.chat.invoke({"content": text})
    try:
        parsed = app.parser.parse(response.content)
        results.append({"text": text, "relationships": parsed})
    except Exception as e:
        results.append({"text": text, "error": str(e)})

# Save results
with open("batch_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Example 3: Custom Prompt Integration

```python
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from utils.output_schema import FinalRelation

# Create custom prompt
custom_prompt = PromptTemplate(
    template="""
    {format_instructions}

    Extract only employment relationships from the following text.
    Focus on job titles, companies, and employment dates.

    Content: {content}
    """,
    input_variables=["content"],
    partial_variables={
        "format_instructions": JsonOutputParser(
            pydantic_object=FinalRelation
        ).get_format_instructions()
    }
)

# Use with existing LLM
# (Assume llm is initialized)
custom_chain = custom_prompt | llm
```

### Example 4: Error Handling Wrapper

```python
from utils.log_writer import CustomLogger
import sys

class SafeRelationExtractor(CustomLogger):
    def __init__(self):
        super().__init__()
        self.app = App()

    def extract_with_retry(self, text, max_retries=3):
        """
        Extract relationships with retry logic.

        Args:
            text (str): Input text
            max_retries (int): Maximum retry attempts

        Returns:
            dict: Extracted relationships or error info
        """
        for attempt in range(max_retries):
            try:
                response = self.app.chat.invoke({"content": text})
                relationships = self.app.parser.parse(response.content)
                return {"success": True, "data": relationships}
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                msg = str(e)
                self.write_error_log(exc_type, exc_tb, msg)

                if attempt == max_retries - 1:
                    return {"success": False, "error": msg}

        return {"success": False, "error": "Max retries exceeded"}

# Usage
extractor = SafeRelationExtractor()
result = extractor.extract_with_retry("Sample text here")
```

## Error Codes and Messages

### Common Exceptions

| Exception | Cause | Resolution |
|-----------|-------|------------|
| `Exception: Config file not found...` | config.yaml missing | Create config.yaml in root directory |
| `ValidationError` | LLM output doesn't match schema | Check LangSmith logs, adjust prompt |
| `AuthenticationError` | Invalid API key | Verify OPENAI_API_KEY in .env |
| `RateLimitError` | API rate limit exceeded | Wait and retry, check quota |
| `FileNotFoundError` | Missing file | Verify file paths |

## Performance Considerations

### Token Usage

Typical token usage per request:
- **Prompt**: ~200-300 tokens (including format instructions)
- **Input**: Variable based on text length
- **Output**: ~100-500 tokens depending on relationships found

### Optimization Tips

1. **Caching**: Implement caching for repeated queries
2. **Batch Processing**: Group similar texts together
3. **Timeout Handling**: Set appropriate timeouts for API calls
4. **Async Operations**: Use async for concurrent processing

---

**Document Version**: 1.0
**Last Updated**: December 2025
