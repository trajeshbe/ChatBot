# Dataset Transformation - Complete Explanation

**Job**: choles-qa-real-training7  
**Training Objective**: `qa`  
**Dataset**: company_qa_dataset.jsonl

---

## Input Format

### Original Dataset (CSV Format in MinIO)
**File**: `company_qa_dataset.jsonl`  
**Location**: `technology/itm11/global/admin/finetuning/datasets/company_qa_dataset/added64c-16fd-42a9-9370-e08f2516f198/company_qa_dataset.jsonl`

**Structure**:
```jsonl
{"Question": "What does Choles Food Technologies do?", "Answer": "Choles Food Technologies provides sustainable food solutions..."}
{"Question": "When was Choles founded?", "Answer": "Choles was founded in 2010 in Melbourne, Australia."}
{"Question": "What are Choles' main product categories?", "Answer": "Choles specializes in plant-based proteins, dairy alternatives, and sustainable packaging."}
{"Question": "How many employees does Choles have?", "Answer": "Choles has approximately 500 employees across Australia and New Zealand."}
{"Question": "What is Choles' revenue?", "Answer": "Choles reported annual revenue of $150 million in 2023."}
```

**Format**: JSONL (JSON Lines) with two columns:
- `Question`: The question or prompt
- `Answer`: The corresponding answer or response

---

## Transformation Process

### Step 1: Download Dataset
```
📦 Downloading from MinIO: technology/itm11/.../company_qa_dataset.jsonl
✅ Downloaded to: /tmp/finetuning_workspaces/{job_id}/input/company_qa_dataset.jsonl
📊 File size: 4.3 KB
```

### Step 2: Load and Analyze
```python
# DatasetPreprocessor.load_dataset()
df = pd.read_json(dataset_path, lines=True)

# Result:
#    Question                                    Answer
# 0  What does Choles Food Technologies do?    Choles Food Technologies provides...
# 1  When was Choles founded?                  Choles was founded in 2010...
# 2  What are Choles' main product categories? Choles specializes in plant-based...
# 3  How many employees does Choles have?      Choles has approximately 500...
# 4  What is Choles' revenue?                  Choles reported annual revenue...
```

### Step 3: Detect Training Objective
```python
training_objective = "qa"  # From job config
format_type = objective_to_format["qa"] = "qa"

# Maps:
# - "qa" → "qa" format
# - "instruction" → "instruction" format
# - "classification" → "classification" format
# - "summarization" → "summarization" format
# - "preference" → "preference" format
```

### Step 4: Auto-Detect Column Mapping
```python
# preprocessor.validate_dataset(df, format_type="qa", columns={})

# Auto-detection finds:
columns_lower = {"question": "Question", "answer": "Answer"}

# QA format expects:
# - question_col: column with questions
# - answer_col: column with answers

# Mapping result:
column_mapping = {
    "question_col": "Question",
    "answer_col": "Answer"
}
```

### Step 5: Format Each Sample
```python
# QAFormatter.format(example)
# Template:
"""
### Question:
{question}

### Answer:
{answer}
"""

# Example transformation:
Input:  {"Question": "What does Choles Food Technologies do?", "Answer": "Choles Food Technologies provides..."}

Output: 
"""### Question:
What does Choles Food Technologies do?

### Answer:
Choles Food Technologies provides sustainable food solutions..."""
```

### Step 6: Create Training Dataset
```python
# Format all 5 samples
formatted_data = []
for row in df.iterrows():
    formatted = formatter.format(row)
    formatted_data.append({"text": formatted})

# Split 90/10 for train/validation
train_split = formatted_data[:4]  # 90% = 4 samples
val_split = formatted_data[4:]     # 10% = 1 sample
```

---

## Output Format

### Final train.json
**Location**: `/tmp/finetuning_workspaces/{job_id}/input/train.json`

```json
[
  {
    "text": "### Question:\nWhat does Choles Food Technologies do?\n\n### Answer:\nCholes Food Technologies provides sustainable food solutions..."
  },
  {
    "text": "### Question:\nWhen was Choles founded?\n\n### Answer:\nCholes was founded in 2010 in Melbourne, Australia."
  },
  {
    "text": "### Question:\nWhat are Choles' main product categories?\n\n### Answer:\nCholes specializes in plant-based proteins, dairy alternatives, and sustainable packaging."
  },
  {
    "text": "### Question:\nHow many employees does Choles have?\n\n### Answer:\nCholes has approximately 500 employees across Australia and New Zealand."
  }
]
```

### validation.json
```json
[
  {
    "text": "### Question:\nWhat is Choles' revenue?\n\n### Answer:\nCholes reported annual revenue of $150 million in 2023."
  }
]
```

---

## Transformation Summary

| Aspect | Input | Output |
|--------|-------|--------|
| **Format** | JSONL (line-delimited JSON) | JSON array |
| **Fields** | `Question`, `Answer` (raw keys) | `text` (formatted string) |
| **Structure** | Flat key-value pairs | Formatted prompt template |
| **Split** | Single file | train.json (90%) + validation.json (10%) |
| **Template** | None | ### Question/Answer structure |
| **Count** | 5 samples | 4 train + 1 validation |

---

## Why This Format?

### 1. Trainer Expectation
The PEFT trainer expects:
```python
dataset = load_dataset("json", data_files=f"{dataset_path}/train.json")
```

- **Directory path**: `/workspace/input` (NOT a file!)
- **File inside**: `train.json` (standard HuggingFace format)
- **Structure**: Array of objects with `text` field

### 2. Consistent Training Format
All training objectives produce the same output structure:
- QA → `### Question:\n...\n\n### Answer:\n...`
- Instruction → `### Instruction:\n...\n\n### Response:\n...`
- Classification → `### Task:\n...\n\n### Classification:\n...`

### 3. Model Learning
The formatted template helps the model learn:
- **Structure**: How Q&A pairs are organized
- **Context**: What comes before (Question) and after (Answer)
- **Boundaries**: Clear delimiters between question and answer

---

## Robust Handling

### If Column Names Were Different

**Example**: Dataset has `user_query` and `bot_response` instead of `Question`/`Answer`

```python
# Step 1: Auto-detection fails (no exact match)
# Step 2: Fuzzy matching succeeds
synonyms = {
    "question_col": ["question", "q", "query", "input", "prompt", "user"],
    "answer_col": ["answer", "a", "response", "output", "assistant", "reply"]
}

# "user_query" contains "query" → maps to question_col
# "bot_response" contains "response" → maps to answer_col

column_mapping = {
    "question_col": "user_query",
    "answer_col": "bot_response"
}
```

### If Columns Had No Match

**Example**: Dataset has `Col1` and `Col2`

```python
# Step 1: Auto-detection fails
# Step 2: Fuzzy matching fails
# Step 3: Position-based fallback

# Assumes first 2 columns are question/answer
column_mapping = {
    "question_col": "Col1",   # First column
    "answer_col": "Col2"       # Second column
}
```

---

## Training Objective Examples

### QA Format (Current)
```
Input:  {"Question": "What is X?", "Answer": "X is..."}
Output: "### Question:\nWhat is X?\n\n### Answer:\nX is..."
```

### Instruction Format
```
Input:  {"instruction": "Explain quantum physics", "response": "Quantum physics is..."}
Output: "### Instruction:\nExplain quantum physics\n\n### Response:\nQuantum physics is..."
```

### Classification Format
```
Input:  {"text": "I love this product!", "label": "positive"}
Output: "### Task:\nClassify the following text.\n\n### Text:\nI love this product!\n\n### Classification:\npositive"
```

---

## Logs You Should See

```
🔄 Preprocessing dataset: /tmp/.../input/company_qa_dataset.jsonl
📊 Loaded 5 samples from dataset
📝 Training objective: qa → Format type: qa
🔍 Auto-detecting columns for format type: qa
✅ Auto-detected column mapping: {'question_col': 'Question', 'answer_col': 'Answer'}
✅ Preprocessed dataset saved to /tmp/.../input/train.json (4 train samples)
✅ Validation set saved to /tmp/.../input/validation.json (1 samples)
```

---

**Summary**: The transformer takes your raw JSONL data with `Question`/`Answer` fields and converts it into a formatted training dataset with `### Question:` and `### Answer:` templates that the model can learn from effectively.

