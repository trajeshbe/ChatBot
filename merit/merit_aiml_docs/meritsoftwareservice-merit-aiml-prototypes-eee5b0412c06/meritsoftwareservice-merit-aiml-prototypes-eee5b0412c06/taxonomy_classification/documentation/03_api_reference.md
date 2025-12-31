# Taxonomy Classification - API Reference

## Overview

This document provides detailed reference documentation for all classes, methods, and data structures in the Taxonomy Classification system.

## Table of Contents

1. [Data Models](#data-models)
2. [ContentClassification Class](#contentclassification-class)
3. [Module-Level Functions](#module-level-functions)
4. [Data Structures](#data-structures)
5. [Constants and Configuration](#constants-and-configuration)

---

## Data Models

### TaxonomyOutputModel

Pydantic model representing a single taxonomy classification result.

#### Class Definition
```python
class TaxonomyOutputModel(BaseModel):
    taxonomy_type: str = Field(description="name of higher level taxonomy")
    category: str = Field(description="respective sub-taxonomy")
    sub_category: str = Field(description="respective sub-taxonomy's value")
    scores: float = Field(description="relevancy score between 0 and 10 for the article")
```

#### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `taxonomy_type` | str | The main taxonomy category name | Required |
| `category` | str | The sub-taxonomy within the main category | Required |
| `sub_category` | str | The specific value or classification | Required |
| `scores` | float | Relevancy score for this classification | Required, 0-10 |

#### Example
```json
{
    "taxonomy_type": "Topic-Based Taxonomies",
    "category": "General Topics",
    "sub_category": "Technology",
    "scores": 9.5
}
```

#### Usage
```python
from pydantic import BaseModel, Field

result = TaxonomyOutputModel(
    taxonomy_type="Topic-Based Taxonomies",
    category="General Topics",
    sub_category="Technology",
    scores=9.5
)
```

---

### TaxonomyOutputParser

Pydantic model that wraps multiple taxonomy classification results.

#### Class Definition
```python
class TaxonomyOutputParser(BaseModel):
    results: list[TaxonomyOutputModel]
```

#### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `results` | list[TaxonomyOutputModel] | List of taxonomy classifications | Required |

#### Example
```json
{
    "results": [
        {
            "taxonomy_type": "Topic-Based Taxonomies",
            "category": "General Topics",
            "sub_category": "Technology",
            "scores": 9.5
        },
        {
            "taxonomy_type": "Industry/Domain-Specific Taxonomies",
            "category": "Technology News",
            "sub_category": "AI and Machine Learning",
            "scores": 9.0
        }
    ]
}
```

#### Usage
```python
parser = TaxonomyOutputParser(
    results=[
        TaxonomyOutputModel(...),
        TaxonomyOutputModel(...)
    ]
)
```

---

## ContentClassification Class

Main class that handles the taxonomy classification workflow.

### Class Overview

```python
class ContentClassification:
    """
    Main classification engine that orchestrates the taxonomy classification process.

    Attributes:
        api_key (str): OpenAI API key loaded from environment
        llm_model: Initialized LangChain chat model
        prompt_template (str): Template for classification prompt
        output_parser: JSON output parser with Pydantic validation
    """
```

---

### Constructor

#### `__init__(self)`

Initializes the ContentClassification instance with required components.

**Parameters**: None

**Returns**: None

**Raises**:
- `ValueError`: If API_KEY environment variable is not found
- `Exception`: If model initialization fails

**Side Effects**:
- Loads environment variables from .env file
- Initializes OpenAI GPT-4o-mini model
- Creates JSON output parser

**Example**:
```python
from taxonomy import ContentClassification

classifier = ContentClassification()
```

**Implementation Details**:
```python
def __init__(self):
    _ = load_dotenv(find_dotenv())
    self.api_key = os.getenv('API_KEY')
    self.llm_model = init_chat_model(
        "gpt-4o-mini",
        model_provider="openai",
        temperature=0,
        api_key=self.api_key
    )
    self.prompt_template = """..."""
    self.output_parser = JsonOutputParser(pydantic_object=TaxonomyOutputParser)
```

**Environment Requirements**:
- `.env` file must exist in the working directory
- `API_KEY` environment variable must be set

---

### Methods

#### `get_prompt(self)`

Creates a LangChain PromptTemplate with format instructions for structured output.

**Parameters**: None

**Returns**:
- `PromptTemplate`: Configured prompt template with format instructions

**Example**:
```python
classifier = ContentClassification()
prompt = classifier.get_prompt()
```

**Implementation Details**:
```python
def get_prompt(self):
    prompt_template = PromptTemplate(
        template="{format_instruction}\n\n\n"+self.prompt_template,
        input_variables=["text", "taxonomy"],
        partial_variables={
            "format_instruction": self.output_parser.get_format_instructions()
        }
    )
    return prompt_template
```

**Prompt Structure**:
- Format instructions (JSON schema)
- Main classification instructions
- Input placeholders for text and taxonomy

---

#### `get_response(self, article, taxonomy)`

Executes the classification pipeline and returns structured results.

**Parameters**:

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `article` | str | The text content to classify | Yes |
| `taxonomy` | dict | The taxonomy structure to classify against | Yes |

**Returns**:
- `dict`: Parsed JSON response with classification results

**Raises**:
- `openai.error.AuthenticationError`: Invalid API key
- `openai.error.RateLimitError`: API rate limit exceeded
- `openai.error.APIError`: General API error
- `ValidationError`: Invalid response structure

**Example**:
```python
classifier = ContentClassification()
article = "Article about AI and machine learning trends..."
taxonomy = {...}  # Taxonomy dictionary

response = classifier.get_response(article, taxonomy)
# Returns: {'results': [...]}
```

**Implementation Details**:
```python
def get_response(self, article, taxonomy):
    prompt = self.get_prompt()
    chain = prompt | self.llm_model | self.output_parser
    output = chain.invoke({"text": article, "taxonomy": taxonomy})
    return output
```

**Pipeline Components**:
1. Prompt template rendering
2. LLM invocation (OpenAI API call)
3. JSON parsing and validation

**Performance**:
- Average execution time: 2-5 seconds
- Depends on article length and API latency

---

#### `to_dataframe(self, response)`

Converts the JSON response to a Pandas DataFrame for display.

**Parameters**:

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `response` | dict | Parsed JSON response from get_response() | Yes |

**Returns**:
- `pandas.DataFrame`: DataFrame with columns: taxonomy_type, category, sub_category, score

**Raises**:
- `KeyError`: If response doesn't contain 'results' key
- `TypeError`: If response format is invalid

**Example**:
```python
classifier = ContentClassification()
response = classifier.get_response(article, taxonomy)
df = classifier.to_dataframe(response)

print(df)
#   taxonomy_type  category  sub_category  score
# 0 Topic-Based... General... Technology    9.5
# 1 Industry/Do... Technol... AI and ML     9.0
```

**Implementation Details**:
```python
def to_dataframe(self, response):
    data = [
        {
            "taxonomy_type": i['taxonomy_type'],
            "category": i['category'],
            "sub_category": i['sub_category'],
            "score": i['scores']
        }
        for i in response['results']
    ]
    df = pd.DataFrame(data)
    return df
```

**DataFrame Schema**:

| Column | Type | Description |
|--------|------|-------------|
| taxonomy_type | object (str) | Main taxonomy category |
| category | object (str) | Sub-category |
| sub_category | object (str) | Specific classification |
| score | float64 | Relevancy score (0-10) |

---

#### `get_taxonomy_data(self, article, taxonomy)`

High-level method that orchestrates the full classification workflow.

**Parameters**:

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `article` | str | The text content to classify | Yes |
| `taxonomy` | dict | The taxonomy structure to classify against | Yes |

**Returns**:
- `pandas.DataFrame`: Sorted DataFrame with classification results

**Example**:
```python
classifier = ContentClassification()
article = "Article about renewable energy..."
taxonomy = {...}

df = classifier.get_taxonomy_data(article, taxonomy)
```

**Implementation Details**:
```python
def get_taxonomy_data(self, article, taxonomy):
    response = self.get_response(article, taxonomy)
    df = self.to_dataframe(response)
    df.sort_values(by="score")
    return df
```

**Workflow**:
1. Call `get_response()` to get classifications
2. Convert response to DataFrame
3. Sort by score (default: ascending)
4. Return sorted DataFrame

**Note**: The sort is performed in-place but doesn't modify the original DataFrame reference. Consider using `inplace=True` or reassigning.

---

## Module-Level Functions

### Taxonomy Loading

#### Loading Default Taxonomy

```python
with open("taxonomies.json", "r") as file:
    taxonomy = json.load(file)
```

**Purpose**: Load the default taxonomy structure from JSON file

**Parameters**: None (hardcoded filename)

**Returns**:
- `dict`: Taxonomy dictionary structure

**File Location**: `taxonomies.json` in the working directory

**File Structure**:
```json
{
    "Taxonomy Category Name": {
        "Sub-Category": ["Value1", "Value2"],
        ...
    },
    "Another Category": ["Direct Value1", "Direct Value2"],
    ...
}
```

---

### Streamlit Application

#### Main Application Entry Point

```python
if __name__ == "__main__":
    classifier = ContentClassification()
    st.set_page_config(layout="wide")
    st.title("Taxonomy Classification")
    with st.form("sample_form"):
        text = st.text_area("Please input your article")
        button = st.form_submit_button("Submit")
    if text and button:
        with st.spinner("Please wait!!!"):
            st.dataframe(classifier.get_taxonomy_data(text, taxonomy), width=1200)
```

**Components**:

1. **Page Configuration**
   - Layout: Wide mode for better table display

2. **Form Elements**
   - Text area for article input
   - Submit button

3. **Processing**
   - Spinner during classification
   - DataFrame display with 1200px width

**Running**:
```bash
streamlit run taxonomy.py
```

**Default Port**: 8501

**URL**: http://localhost:8501

---

## Data Structures

### Taxonomy Dictionary Structure

#### General Format

```json
{
    "TopLevelCategory": {
        "SubCategory1": ["Value1", "Value2", "Value3"],
        "SubCategory2": ["ValueA", "ValueB"]
    },
    "DirectCategory": ["DirectValue1", "DirectValue2"]
}
```

#### Nested Structure Example

```json
{
    "Topic-Based Taxonomies": {
        "General Topics": [
            "Technology",
            "Science",
            "Health"
        ],
        "Politics": [
            "Elections",
            "Policies",
            "Diplomacy"
        ]
    },
    "Event-Based Taxonomies": [
        "Natural Disasters",
        "Political Events"
    ]
}
```

#### Deeply Nested Structure (Agricultural Example)

```json
{
    "Agricultural Taxonomies": {
        "Crops & Produce": {
            "Grain & Oilseeds": [
                "Corn",
                "Wheat",
                "Soybeans"
            ],
            "Fruits & Vegetables": [
                "Apples",
                "Grapes",
                "Citrus"
            ]
        }
    }
}
```

---

## Constants and Configuration

### Model Configuration

```python
MODEL_NAME = "gpt-4o-mini"
MODEL_PROVIDER = "openai"
TEMPERATURE = 0  # Deterministic outputs
```

### Prompt Configuration

```python
PROMPT_TEMPLATE = """
    You will be provided with text and taxonomies delimited by triple quotes.
    text: This contains an article.
    taxonomy: This contains main taxonomy and sub-taxonomy. The sub-taxonomy
    is further categorized wherever possible.

    Your task is to classify the text against all taxonomy and it's sub-taxonomy
    with respective categories and provide the relevancy scores as well.

    Based on the relevancy score, do consider top 5 taxonomies.

    Format the output as JSON with the following keys such as:
    taxonomy_type
    category
    sub_category
    scores

    Note: Please mind that output should contain top 5 taxonomies.

    Content: ```{text}```
    Taxonomies: ```{taxonomy}```
"""
```

### File Paths

```python
DEFAULT_TAXONOMY_FILE = "taxonomies.json"
AGRI_TAXONOMY_FILE = "taxonomies_agri.json"
ENV_FILE = ".env"
```

### Streamlit Configuration

```python
PAGE_LAYOUT = "wide"
PAGE_TITLE = "Taxonomy Classification"
DATAFRAME_WIDTH = 1200  # pixels
FORM_NAME = "sample_form"
```

---

## Error Codes and Exceptions

### Custom Exceptions

Currently, the system doesn't define custom exceptions. Standard Python and library exceptions are raised:

#### OpenAI API Errors

- `openai.error.AuthenticationError`: Invalid API key
- `openai.error.RateLimitError`: Rate limit exceeded
- `openai.error.APIError`: General API error
- `openai.error.Timeout`: Request timeout

#### Pydantic Errors

- `pydantic.ValidationError`: Response doesn't match schema

#### File I/O Errors

- `FileNotFoundError`: Taxonomy file not found
- `json.JSONDecodeError`: Invalid JSON in taxonomy file

#### Environment Errors

- `KeyError`: API_KEY not found in environment

---

## Usage Examples

### Basic Classification

```python
from taxonomy import ContentClassification
import json

# Initialize classifier
classifier = ContentClassification()

# Load taxonomy
with open("taxonomies.json", "r") as f:
    taxonomy = json.load(f)

# Classify article
article = """
Artificial intelligence continues to revolutionize healthcare with new
machine learning models that can detect diseases earlier and more accurately
than ever before.
"""

# Get results as DataFrame
results = classifier.get_taxonomy_data(article, taxonomy)
print(results)
```

### Custom Taxonomy

```python
# Define custom taxonomy
custom_taxonomy = {
    "Product Categories": {
        "Electronics": ["Phones", "Laptops", "Tablets"],
        "Clothing": ["Shirts", "Pants", "Shoes"]
    },
    "Price Range": ["Budget", "Mid-Range", "Premium"]
}

# Classify with custom taxonomy
product_description = "High-end smartphone with advanced camera features"
results = classifier.get_taxonomy_data(product_description, custom_taxonomy)
```

### Accessing Individual Results

```python
# Get response as dictionary
response = classifier.get_response(article, taxonomy)

# Access individual classifications
for result in response['results']:
    print(f"Category: {result['taxonomy_type']}")
    print(f"Sub-category: {result['category']}")
    print(f"Value: {result['sub_category']}")
    print(f"Score: {result['scores']}")
    print("---")
```

### Filtering Results by Score

```python
# Get results
df = classifier.get_taxonomy_data(article, taxonomy)

# Filter high-confidence results
high_confidence = df[df['score'] >= 7.0]
print(high_confidence)

# Get top 3 results
top_3 = df.nlargest(3, 'score')
print(top_3)
```

---

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from taxonomy import ContentClassification
import json

app = FastAPI()
classifier = ContentClassification()

with open("taxonomies.json", "r") as f:
    taxonomy = json.load(f)

class ClassificationRequest(BaseModel):
    text: str

class ClassificationResponse(BaseModel):
    results: list[dict]

@app.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    try:
        response = classifier.get_response(request.text, taxonomy)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Batch Processing

```python
import pandas as pd

# Read articles from CSV
articles_df = pd.read_csv("articles.csv")

# Classify each article
results = []
for idx, row in articles_df.iterrows():
    df = classifier.get_taxonomy_data(row['text'], taxonomy)
    df['article_id'] = row['id']
    results.append(df)

# Combine all results
all_results = pd.concat(results, ignore_index=True)
all_results.to_csv("classifications.csv", index=False)
```

---

## API Rate Limits

### OpenAI API Limits (GPT-4o-mini)

- **RPM (Requests Per Minute)**: Varies by tier
- **TPM (Tokens Per Minute)**: Varies by tier
- **Recommended**: Implement retry logic with exponential backoff

### Example Rate Limiting

```python
import time
from functools import wraps

def rate_limit(max_per_minute):
    min_interval = 60.0 / max_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

# Apply to get_response method
ContentClassification.get_response = rate_limit(20)(
    ContentClassification.get_response
)
```

---

## Testing

### Unit Test Example

```python
import unittest
from taxonomy import ContentClassification, TaxonomyOutputModel

class TestContentClassification(unittest.TestCase):
    def setUp(self):
        self.classifier = ContentClassification()
        self.sample_taxonomy = {
            "Test Category": ["Value1", "Value2"]
        }

    def test_initialization(self):
        self.assertIsNotNone(self.classifier.llm_model)
        self.assertIsNotNone(self.classifier.output_parser)

    def test_to_dataframe(self):
        response = {
            'results': [
                {
                    'taxonomy_type': 'Test',
                    'category': 'Cat',
                    'sub_category': 'Sub',
                    'scores': 8.5
                }
            ]
        }
        df = self.classifier.to_dataframe(response)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['score'], 8.5)

if __name__ == '__main__':
    unittest.main()
```
