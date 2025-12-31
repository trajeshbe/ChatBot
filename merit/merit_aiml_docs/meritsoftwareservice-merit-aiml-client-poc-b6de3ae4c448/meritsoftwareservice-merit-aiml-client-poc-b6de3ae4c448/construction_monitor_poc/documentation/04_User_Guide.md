# User Guide

## Executive Summary

This user guide provides step-by-step instructions for using the Construction Monitor POC to extract entities and relationships from construction documents. It covers training new models, running extractions on documents, interpreting results, and troubleshooting common issues. The guide is designed for data scientists, analysts, and technical users who will operate and maintain the system.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Environment Setup](#2-environment-setup)
3. [Training NER Models](#3-training-ner-models)
4. [Training REL Models](#4-training-rel-models)
5. [Running Extraction on Documents](#5-running-extraction-on-documents)
6. [Interpreting Results](#6-interpreting-results)
7. [Testing and Evaluation](#7-testing-and-evaluation)
8. [Regional Processing](#8-regional-processing)
9. [Troubleshooting](#9-troubleshooting)
10. [Best Practices](#10-best-practices)

---

## 1. Getting Started

### 1.1 Prerequisites

**Required Knowledge:**
- Basic Python programming
- Understanding of Jupyter notebooks
- Familiarity with NLP concepts (helpful but not required)
- Basic command-line skills

**System Requirements:**
- Operating System: Windows, Linux, or macOS
- Python: 3.8 or higher
- RAM: 16GB minimum, 32GB recommended
- Storage: 10GB free space
- Optional: CUDA-compatible GPU for faster training

### 1.2 Project Structure

```
construction_monitor_poc/
├── dataset/                          # Training and test datasets
│   ├── NER_dataset/
│   │   ├── train.spacy              # NER training data
│   │   ├── dev.spacy                # NER validation data
│   │   └── test.spacy               # NER test data
│   └── REL_dataset/
│       ├── train.spacy              # REL training data
│       ├── dev.spacy                # REL validation data
│       └── test.spacy               # REL test data
│
├── model/                            # Trained models
│   ├── base_model_v2/               # NER model
│   │   ├── model-best/              # Best performing checkpoint
│   │   └── model-last/              # Final checkpoint
│   └── rel_model_v2/                # REL model
│
├── notebook/                         # Jupyter notebooks
│   ├── NER/
│   │   ├── training.ipynb           # Train NER models
│   │   ├── Testing.ipynb            # Test NER performance
│   │   └── ACC.ipynb                # Accuracy analysis
│   ├── REL/
│   │   └── build_custom_rel_model_CM.ipynb  # Train REL models
│   └── Extraction/
│       ├── Miami_Extraction.ipynb   # Miami document processing
│       ├── Tuscaloosa_extraction.ipynb
│       ├── fairfax extraction (1).ipynb
│       ├── wells_extraction.ipynb
│       └── calhoun.ipynb
│
└── documentation/                    # Project documentation
    ├── 01_Business_Use_Case_and_Objectives.md
    ├── 02_Technical_Architecture.md
    ├── 03_Functional_Architecture.md
    ├── 04_User_Guide.md (this document)
    └── 05_Business_Value.md
```

### 1.3 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (SpaCy, transformers, pandas, etc.)
- [ ] SpaCy language model downloaded (`en_core_web_trf`)
- [ ] Jupyter notebook environment set up
- [ ] Access to training datasets
- [ ] Trained models available (or ready to train new ones)

---

## 2. Environment Setup

### 2.1 Install Python Dependencies

**Step 1: Create a Virtual Environment**

```bash
# Using venv
python -m venv construction_env

# Activate (Windows)
construction_env\Scripts\activate

# Activate (Linux/Mac)
source construction_env/bin/activate
```

**Step 2: Install Core Dependencies**

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install SpaCy
pip install -U spacy

# Install SpaCy transformers
pip install -U spacy-transformers

# Install additional libraries
pip install pandas numpy openpyxl jupyter
```

**Step 3: Download SpaCy Language Model**

```bash
# Download transformer-based English model
python -m spacy download en_core_web_trf
```

### 2.2 Verify Installation

**Check SpaCy Installation:**

```python
import spacy

# Check version
print(f"SpaCy version: {spacy.__version__}")

# Load model to verify
nlp = spacy.load("en_core_web_trf")
print("Model loaded successfully!")
```

Expected output:
```
SpaCy version: 3.6.0
Model loaded successfully!
```

### 2.3 Start Jupyter Notebook

```bash
# Navigate to project directory
cd construction_monitor_poc/

# Start Jupyter
jupyter notebook
```

Your browser should open with the Jupyter interface showing the project folders.

---

## 3. Training NER Models

### 3.1 Prepare Training Data

**Data Format:**

Your training data should be in JSONL format with the following structure:

```json
{
  "text": "PETER J. FITZGERALD JR. from Roberts Road Investment LC",
  "spans": [
    {
      "start": 0,
      "end": 23,
      "label": "CONTACT"
    },
    {
      "start": 30,
      "end": 56,
      "label": "ORG"
    }
  ]
}
```

**Entity Labels:**
- `CONTACT` - Individual persons
- `ADDRESS` - Physical locations
- `ORG` - Organizations and companies
- `SITE` - Zoning and parcel information
- `DESC` - Project descriptions

### 3.2 Train NER Model

**Notebook:** `notebook/NER/training.ipynb`

**Step 1: Load Training Data**

```python
import json

# Load training data
train = []
with open("/path/to/train_data.jsonl", 'r') as f:
    train.extend([json.loads(line) for line in f])

print(f"Loaded {len(train)} training examples")
```

**Step 2: Convert to SpaCy Format**

```python
def get_ner_data(final_data):
    ner_data = []
    for data in final_data:
        entities = []
        try:
            for span in data['spans']:
                entities.append((
                    span['start'],
                    span['end'],
                    span['label'].upper()
                ))
            ner_data.append((data['text'], {"entities": entities}))
        except:
            pass
    return ner_data

TRAIN_DATA = get_ner_data(train)
print(f"Converted {len(TRAIN_DATA)} examples")
```

**Step 3: Configure Training Parameters**

```python
# Training configuration
MODEL_NAME = None  # None for blank model, or path to existing model
OUTPUT_DIR = 'model/my_ner_model'
ITERATIONS = 20
DROPOUT = 0.20
```

**Step 4: Run Training**

```python
import spacy
from spacy.training.example import Example
import random

# Initialize model
nlp = spacy.blank('en')
ner = nlp.add_pipe('ner')

# Add entity labels
for label in ["CONTACT", "ADDRESS", "ORG", "SITE", "DESC"]:
    ner.add_label(label)

# Start training
optimizer = nlp.begin_training()

# Training loop
for iteration in range(ITERATIONS):
    random.shuffle(TRAIN_DATA)
    losses = {}

    # Process in batches
    from spacy.util import minibatch, compounding
    batches = minibatch(TRAIN_DATA, size=compounding(4., 32., 1.001))

    for batch in batches:
        for text, annotation in batch:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotation)
            nlp.update([example], sgd=optimizer, drop=DROPOUT, losses=losses)

    print(f"Iteration {iteration}: Loss = {losses['ner']}")

# Save model
nlp.to_disk(OUTPUT_DIR)
print(f"Model saved to {OUTPUT_DIR}")
```

**Step 5: Monitor Training Progress**

Watch the loss values decrease over iterations:
- Initial loss: ~15,000-20,000
- Final loss: <8,000 (typically converges after 15-20 iterations)
- Training time: ~30-60 minutes on CPU, ~5-10 minutes on GPU

### 3.3 Expected Output

```
Loaded 3099 training examples
Converted 3099 examples
Iteration 0: Loss = 17821.55
Iteration 5: Loss = 9700.86
Iteration 10: Loss = 8470.93
Iteration 15: Loss = 7898.10
Iteration 19: Loss = 7896.27
Model saved to model/my_ner_model
```

---

## 4. Training REL Models

### 4.1 Prepare Relationship Data

**Data Format:**

```json
{
  "document": "PETER J. FITZGERALD JR. from Roberts Road Investment LC",
  "tokens": [
    {
      "text": "PETER J. FITZGERALD JR.",
      "start": 0,
      "end": 23,
      "token_start": 0,
      "token_end": 4,
      "entityLabel": "CONTACT"
    },
    {
      "text": "Roberts Road Investment LC",
      "start": 30,
      "end": 56,
      "token_start": 6,
      "token_end": 9,
      "entityLabel": "ORG"
    }
  ],
  "relations": [
    {
      "head": 0,
      "child": 6,
      "relationLabel": "CONTACTORG"
    }
  ]
}
```

### 4.2 Train REL Model

**Notebook:** `notebook/REL/build_custom_rel_model_CM.ipynb`

**Step 1: Set Up SpaCy Project**

```bash
# Clone SpaCy relation extraction template
python -m spacy project clone tutorials/rel_component
cd rel_component
```

**Step 2: Prepare Data Files**

Place your relationship data files in the `data/` directory:
- `data/train.spacy` - Training data
- `data/dev.spacy` - Development/validation data
- `data/test.spacy` - Test data

**Step 3: Configure Training**

Edit `configs/rel_tok2vec.cfg` to adjust parameters:

```ini
[components.relation_extractor.model.create_instance_tensor]
@misc = "rel_instance_generator.v1"
max_length = 20  # Maximum tokens between entities
```

**Step 4: Run Training**

```bash
# Train with CPU
spacy project run train_cpu

# Or train with GPU (if available)
spacy project run train_gpu
```

**Step 5: Evaluate Model**

```bash
spacy project run evaluate
```

### 4.3 Expected Output

```
Training started...
Epoch 0, Step 0: Loss = 0.39, F1 = 61.58%
Epoch 0, Step 50: Loss = 4.09, F1 = 87.33%
Epoch 0, Step 200: Loss = 1.19, F1 = 94.60%
Epoch 1, Step 500: Loss = 0.47, F1 = 95.27%
Epoch 2, Step 1000: Loss = 0.00, F1 = 96.79%

Model saved to training/model-best

Evaluation Results:
Threshold 0.60: Precision = 96.84%, Recall = 95.34%, F1 = 96.08%
```

---

## 5. Running Extraction on Documents

### 5.1 Basic Entity Extraction

**Step 1: Load NER Model**

```python
import spacy

# Load your trained NER model
nlp = spacy.load("model/base_model_v2/model-best")

# Or use the default path
# nlp = spacy.load("./model-best")
```

**Step 2: Process a Document**

```python
# Your construction document text
text = """
Mr. James Escue, on behalf of Anniston Lions Club, presented a
disinfectant sprayer to Calhoun County to assist the Calhoun County
EMA with sanitizing large areas during the COVID crisis.
"""

# Process with NER model
doc = nlp(text)

# Extract entities
for ent in doc.ents:
    print(f"{ent.label_:10} | {ent.text}")
```

**Expected Output:**

```
CONTACT    | Mr. James Escue
ORG        | Anniston Lions Club
ORG        | Calhoun County
ORG        | Calhoun County EMA
DESC       | sanitizing large areas during the COVID crisis
```

### 5.2 Joint NER + REL Extraction

**Step 1: Load Both Models**

```python
import spacy

# Load NER model
nlp_ner = spacy.load("model/base_model_v2/model-best")

# Add sentence segmentation
nlp_ner.add_pipe('sentencizer')

# Load REL model
nlp_rel = spacy.load("model/rel_model_v2")
```

**Step 2: Process Document with Both Models**

```python
text = """
PETER J. FITZGERALD JR. from Roberts Road Investment LC submitted an
application for a cluster subdivision at 7327 Georgetown Pike, McLean.
"""

# Step 1: Extract entities
doc = nlp_ner(text)

print("Entities:")
for ent in doc.ents:
    print(f"  {ent.label_:10} | {ent.text}")

# Step 2: Extract relationships (if applicable)
ner_labels = [e.label_ for e in doc.ents]

if "ORG" in ner_labels and "CONTACT" in ner_labels:
    # Process with REL model
    for name, proc in nlp_rel.pipeline:
        doc = proc(doc)

    # Analyze relationships
    print("\nRelationships:")
    for (idx1, idx2), rel_dict in doc._.rel.items():
        confidence = rel_dict["CONTACTORG"]

        if confidence > 0.60:  # Threshold
            entity1 = doc.ents[idx1]
            entity2 = doc.ents[idx2]
            print(f"  {entity1.text} → {entity2.text} (confidence: {confidence:.2f})")
```

**Expected Output:**

```
Entities:
  CONTACT    | PETER J. FITZGERALD JR.
  ORG        | Roberts Road Investment LC
  ADDRESS    | 7327 Georgetown Pike, McLean

Relationships:
  PETER J. FITZGERALD JR. → Roberts Road Investment LC (confidence: 0.98)
```

### 5.3 Batch Processing Multiple Documents

**Step 1: Prepare Document List**

```python
documents = [
    "Document 1 text...",
    "Document 2 text...",
    "Document 3 text...",
]
```

**Step 2: Process in Batch**

```python
import spacy

nlp = spacy.load("model/base_model_v2/model-best")

# Process multiple docs efficiently
results = []

for doc in nlp.pipe(documents, disable=["tagger"]):
    entities = [(e.text, e.label_) for e in doc.ents]
    results.append({
        'text': doc.text,
        'entities': entities
    })

# View results
for idx, result in enumerate(results):
    print(f"\nDocument {idx + 1}:")
    print(f"  Found {len(result['entities'])} entities")
```

**Benefits of Batch Processing:**
- 2-3x faster than processing one at a time
- Better memory utilization
- Ideal for large document sets

---

## 6. Interpreting Results

### 6.1 Understanding Entity Labels

**CONTACT Entities:**
```
Example: "Commissioner Wilson"
Meaning: An individual person involved in the construction project
Use case: Track who is responsible, who applied, who represents
```

**ADDRESS Entities:**
```
Example: "305 West 49th Street, Anniston"
Meaning: Physical location of a project or property
Use case: Map project locations, identify geographic coverage
```

**ORG Entities:**
```
Example: "Roberts Road Investment LC"
Meaning: Company, agency, or organization involved
Use case: Track contractors, developers, government entities
```

**SITE Entities:**
```
Example: "Tax Map 021-3 ((1)) 23 and 23A"
Meaning: Parcel IDs, zoning codes, land use information
Use case: Link to GIS data, zoning compliance
```

**DESC Entities:**
```
Example: "cluster subdivision and a waiver of minimum district size"
Meaning: Description of project scope or purpose
Use case: Categorize project types, search by keywords
```

### 6.2 Understanding Relationship Scores

**Confidence Score Interpretation:**

| Score Range | Interpretation | Action |
|-------------|----------------|--------|
| 0.90 - 1.00 | Very high confidence | Accept with high certainty |
| 0.70 - 0.89 | High confidence | Accept, likely correct |
| 0.50 - 0.69 | Moderate confidence | Accept but may need validation |
| 0.30 - 0.49 | Low confidence | Review manually |
| 0.00 - 0.29 | Very low confidence | Likely incorrect, reject |

**Recommended Threshold: 0.60**
- Balances precision (96.84%) and recall (95.34%)
- F1 score of 96.08%
- Suitable for most business applications

**Example Interpretation:**

```python
# Relationship with score 0.98
"Peter J. Fitzgerald Jr." → "Roberts Road Investment LC" (0.98)
```
**Interpretation:** Very high confidence that Peter J. Fitzgerald Jr. represents or is affiliated with Roberts Road Investment LC. This relationship can be accepted with high certainty.

### 6.3 Common Output Patterns

**Pattern 1: Single Contact, Single Organization**
```
CONTACT: "John Smith"
ORG: "ABC Construction Company"
Relationship: "John Smith" → "ABC Construction Company" (0.95)
```
**Interpretation:** John Smith represents ABC Construction Company.

**Pattern 2: Multiple Contacts, Single Organization**
```
CONTACT: "Mary Jones"
CONTACT: "Bob Williams"
ORG: "XYZ Developers"
Relationships:
  "Mary Jones" → "XYZ Developers" (0.88)
  "Bob Williams" → "XYZ Developers" (0.72)
```
**Interpretation:** Both Mary Jones and Bob Williams are associated with XYZ Developers. Mary has a stronger association (higher score).

**Pattern 3: Multiple Organizations**
```
CONTACT: "Commissioner Adams"
ORG: "County Planning Board"
ORG: "State Department of Transportation"
Relationships:
  "Commissioner Adams" → "County Planning Board" (0.92)
  "Commissioner Adams" → "State Department of Transportation" (0.45)
```
**Interpretation:** Commissioner Adams is primarily associated with the County Planning Board. The low score with State DOT suggests a weaker or no direct relationship.

### 6.4 Quality Indicators

**High-Quality Extraction:**
- Multiple entity types found
- Relationships have scores > 0.70
- Entity boundaries are clean (no partial words)
- Entities make semantic sense

**Low-Quality Extraction:**
- Very few or no entities found
- All relationship scores < 0.50
- Unusual entity text (gibberish, fragments)
- May indicate poor document quality or model limitations

---

## 7. Testing and Evaluation

### 7.1 Test NER Model Performance

**Notebook:** `notebook/NER/Testing.ipynb`

**Step 1: Prepare Test Data**

```python
import json

# Load test data in same format as training data
test_data = []
with open("/path/to/test_data.jsonl", 'r') as f:
    test_data.extend([json.loads(line) for line in f])

# Convert to SpaCy format
TEST_DATA = get_ner_data(test_data)
print(f"Loaded {len(TEST_DATA)} test examples")
```

**Step 2: Run Evaluation**

```python
from spacy.scorer import Scorer
from spacy.training.example import Example

def evaluate(ner_model, test_examples):
    scorer = Scorer()
    examples = []

    for input_text, annotations in test_examples:
        # Get predictions
        pred_doc = ner_model(input_text)

        # Create evaluation example
        example = Example.from_dict(pred_doc, annotations)
        examples.append(example)

    # Calculate scores
    scores = scorer.score(examples)
    return scores

# Load model and evaluate
nlp = spacy.load("model/base_model_v2/model-best")
results = evaluate(nlp, TEST_DATA)

# Display results
print(f"Overall Precision: {results['ents_p']:.2%}")
print(f"Overall Recall: {results['ents_r']:.2%}")
print(f"Overall F1: {results['ents_f']:.2%}")
```

**Step 3: Analyze Per-Entity Performance**

```python
import pandas as pd

# Per-entity scores
ent_scores = pd.DataFrame(results['ents_per_type']).T
print("\nPer-Entity Performance:")
print(ent_scores)
```

**Expected Output:**

```
Overall Precision: 79.82%
Overall Recall: 74.55%
Overall F1: 77.09%

Per-Entity Performance:
              p         r         f
CONTACT   0.8904    0.9060    0.8981
DESC      0.8843    0.9139    0.8988
ORG       0.7162    0.7162    0.7162
ADDRESS   0.6923    0.6000    0.6429
SITE      0.4294    0.2452    0.3121
```

**Interpretation:**
- CONTACT and DESC entities perform well (F1 ~90%)
- ORG and ADDRESS have moderate performance (F1 ~64-72%)
- SITE has lower performance (F1 ~31%) - may need more training data or better examples

### 7.2 Test REL Model Performance

**Step 1: Run Evaluation Script**

```bash
# From rel_component directory
python ./scripts/evaluate.py training/model-best data/test.spacy False
```

**Step 2: Review Threshold Performance**

The evaluation will output performance at different confidence thresholds:

```
Threshold 0.05: Precision = 90.52%, Recall = 98.96%, F1 = 94.55%
Threshold 0.40: Precision = 95.90%, Recall = 96.89%, F1 = 96.39%
Threshold 0.60: Precision = 96.84%, Recall = 95.34%, F1 = 96.08%
Threshold 0.80: Precision = 97.27%, Recall = 92.23%, F1 = 94.68%
```

**Step 3: Choose Optimal Threshold**

Based on your use case:
- **High recall needed** (catch all relationships): Use 0.05-0.20
- **Balanced** (recommended): Use 0.40-0.60
- **High precision needed** (minimize false positives): Use 0.80-0.90

### 7.3 Generate Prediction Reports

**Create Detailed Output:**

```python
# Process test documents and save predictions
pred_data = []

for input_text, annotations in TEST_DATA:
    doc = nlp(input_text)

    # Get predictions
    pred_entities = [(ent.label_, ent.text) for ent in doc.ents]

    # Get ground truth
    true_entities = annotations['entities']

    pred_data.append({
        "text": input_text,
        "true_entities": true_entities,
        "pred_entities": pred_entities
    })

# Save to Excel for review
import pandas as pd
df = pd.DataFrame(pred_data)
df.to_excel("test_predictions.xlsx", index=False)
```

This creates an Excel file where you can manually review predictions vs. ground truth.

---

## 8. Regional Processing

### 8.1 Miami-Dade County Documents

**Notebook:** `notebook/Extraction/Miami_Extraction.ipynb`

**Step 1: Prepare Document Directory**

```python
import os
import pandas as pd

# Path to Miami agenda files
miami_path = "/path/to/Miami/agendas/"

# Collect all Excel files
files = []
for root, dirs, filenames in os.walk(miami_path):
    files.extend([os.path.join(root, f) for f in filenames if f.endswith('.xlsx')])

print(f"Found {len(files)} Miami agenda files")
```

**Step 2: Process All Files**

```python
import spacy
import re

# Load models
nlp_ner = spacy.load("model/base_model_v2/model-best")
nlp_ner.add_pipe('sentencizer')
nlp_rel = spacy.load("model/rel_model_v2")

results = []

for filepath in files:
    # Load Excel file
    df = pd.read_excel(filepath)

    for idx, row in df.iterrows():
        text = row['text_column']  # Adjust column name

        # Extract structured fields using regex (Miami-specific)
        addresses = re.findall(
            r"(?<=LOCATION:).*?(?:(?=APPELLANT\(S\))|(?=Applicant))",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Run NER
        doc = nlp_ner(text)
        entities = [(e.text, e.label_) for e in doc.ents]

        # Run REL if applicable
        relations = []
        ner_labels = [e.label_ for e in doc.ents]

        if "CONTACT" in ner_labels and "ORG" in ner_labels:
            for name, proc in nlp_rel.pipeline:
                doc = proc(doc)

            best_score = 0
            best_rel = None

            for (idx1, idx2), rel_dict in doc._.rel.items():
                conf = rel_dict["CONTACTORG"]
                if conf > best_score:
                    best_score = conf
                    best_rel = (doc.ents[idx1].text, doc.ents[idx2].text)

            if best_rel:
                relations.append({
                    'contact': best_rel[0],
                    'org': best_rel[1],
                    'confidence': best_score
                })

        # Store results
        results.append({
            'filename': os.path.basename(filepath),
            'text': text,
            'addresses': addresses,
            'entities': entities,
            'relations': relations
        })

# Save output
output_df = pd.DataFrame(results)
output_df.to_excel("miami_output.xlsx", index=False)
print(f"Processed {len(results)} documents")
```

**Step 3: Review Output**

Open `miami_output.xlsx` and review:
- Extracted addresses
- Identified entities (CONTACT, ORG, ADDRESS, SITE, DESC)
- Detected relationships

### 8.2 Processing Other Regions

**Tuscaloosa, Fairfax, Wells, Calhoun:**

The process is similar for other regions. Use the respective notebooks:
- `Tuscaloosa_extraction.ipynb`
- `fairfax extraction (1).ipynb`
- `wells_extraction.ipynb`
- `calhoun.ipynb`

**General Pattern:**

1. Load regional documents
2. Apply region-specific preprocessing if needed
3. Run standard NER/REL pipeline
4. Save results with regional identifier

**Example for any region:**

```python
def process_region(region_name, document_path, output_path):
    # Load models
    nlp_ner = spacy.load("model/base_model_v2/model-best")
    nlp_rel = spacy.load("model/rel_model_v2")

    # Load documents
    documents = load_documents(document_path)

    # Process each document
    results = []
    for doc_text in documents:
        entities, relations = extract_info(nlp_ner, nlp_rel, doc_text)
        results.append({
            'region': region_name,
            'text': doc_text,
            'entities': entities,
            'relations': relations
        })

    # Save results
    df = pd.DataFrame(results)
    df.to_excel(output_path, index=False)
    print(f"Processed {len(results)} {region_name} documents")

# Use for any region
process_region('Fairfax', '/path/to/fairfax/', 'fairfax_output.xlsx')
```

---

## 9. Troubleshooting

### 9.1 Common Errors and Solutions

#### Error 1: Model Not Found

**Error Message:**
```
OSError: [E050] Can't find model 'model/base_model_v2/model-best'
```

**Solution:**
```python
# Check if path exists
import os
model_path = "model/base_model_v2/model-best"
print(os.path.exists(model_path))

# Use absolute path
import os
abs_path = os.path.abspath(model_path)
nlp = spacy.load(abs_path)
```

#### Error 2: Entity Alignment Warning

**Warning Message:**
```
[W030] Some entities could not be aligned in the text
```

**Cause:** Entity spans don't align with token boundaries (e.g., multi-line addresses)

**Solution:**
```python
# These entities will be skipped during training
# To debug, use:
from spacy.training import offsets_to_biluo_tags

doc = nlp.make_doc(text)
tags = offsets_to_biluo_tags(doc, entities)
print(tags)  # Look for '-' (misaligned)
```

#### Error 3: No Instances in Document

**Warning Message:**
```
Could not determine any instances in doc
```

**Cause:** No valid CONTACT-ORG pairs found in the document

**Solution:**
This is expected behavior when:
- Document has no ORG entities
- Document has no CONTACT entities
- Entities are in different sentences (REL processes sentence-by-sentence)

**No action needed** - REL extraction is skipped, NER results are still valid.

#### Error 4: CUDA Out of Memory

**Error Message:**
```
RuntimeError: CUDA out of memory
```

**Solution:**
```python
# Option 1: Use CPU instead
# Remove GPU/CUDA usage, use CPU training

# Option 2: Reduce batch size
batches = minibatch(TRAIN_DATA, size=compounding(2., 16., 1.001))

# Option 3: Process smaller batches
for doc in nlp.pipe(texts, batch_size=10):
    # process
```

#### Error 5: Version Incompatibility

**Warning Message:**
```
[W095] Model was trained with spaCy v3.5 and may not be compatible with v3.6
```

**Solution:**
```python
# Option 1: Use same SpaCy version as training
pip install spacy==3.5.0

# Option 2: Retrain model with current version
# Run training notebook with current SpaCy installation

# Option 3: Ignore warning if performance is acceptable
# Often models work fine across minor version differences
```

### 9.2 Performance Issues

#### Issue 1: Slow Processing

**Symptoms:** Processing takes longer than expected

**Solutions:**

1. **Use batch processing:**
```python
# Instead of:
for text in texts:
    doc = nlp(text)

# Use:
for doc in nlp.pipe(texts, batch_size=50):
    # process
```

2. **Disable unnecessary components:**
```python
nlp.pipe(texts, disable=["tagger", "parser"])
```

3. **Use GPU if available:**
```python
spacy.require_gpu()
```

#### Issue 2: Low Accuracy

**Symptoms:** Many incorrect or missing entities

**Solutions:**

1. **Add more training data:**
   - Annotate more examples
   - Focus on entity types with low F1 scores

2. **Increase training iterations:**
```python
# Increase from 20 to 30-50
n_iter = 50
```

3. **Adjust hyperparameters:**
```python
# Lower dropout for less regularization
drop = 0.10

# Try different batch sizes
size = compounding(8., 64., 1.001)
```

4. **Use pre-trained model as base:**
```python
# Instead of blank model
nlp = spacy.load("en_core_web_trf")
```

### 9.3 Data Issues

#### Issue 1: Encoding Errors

**Error Message:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**Solution:**
```python
# Specify encoding when reading files
with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Or try different encodings
with open(filepath, 'r', encoding='latin-1') as f:
    content = f.read()
```

#### Issue 2: Excel File Errors

**Error Message:**
```
BadZipFile: File is not a zip file
```

**Solution:**
```python
# Ensure file is valid Excel format
# Try different engine
df = pd.read_excel(filepath, engine='openpyxl')
```

---

## 10. Best Practices

### 10.1 Model Training Best Practices

**1. Data Quality:**
- Ensure consistent annotation guidelines
- Have multiple annotators review samples
- Balance entity types in training data
- Include diverse examples (different regions, document types)

**2. Training Process:**
- Start with 20 iterations, increase if needed
- Monitor loss to detect convergence
- Save multiple checkpoints (model-best and model-last)
- Use validation set to prevent overfitting

**3. Evaluation:**
- Always evaluate on held-out test set
- Calculate per-entity metrics, not just overall
- Review sample predictions manually
- Track performance over model versions

### 10.2 Extraction Best Practices

**1. Pre-processing:**
- Clean text (remove excessive whitespace, special characters)
- Handle multi-line addresses carefully
- Normalize encoding (UTF-8)

**2. Processing:**
- Use batch processing for efficiency
- Set appropriate confidence thresholds based on use case
- Process sentences independently for REL
- Save intermediate results for debugging

**3. Post-processing:**
- Validate entity boundaries
- Filter low-confidence results if needed
- Deduplicate entities
- Link entities across documents

### 10.3 Output Handling Best Practices

**1. Save Multiple Formats:**
```python
# Excel for manual review
df.to_excel("output.xlsx", index=False)

# JSON for programmatic use
df.to_json("output.json", orient='records')

# CSV for database import
df.to_csv("output.csv", index=False)
```

**2. Include Metadata:**
```python
results.append({
    'document_id': doc_id,
    'processing_date': datetime.now().isoformat(),
    'model_version': 'base_model_v2',
    'region': 'Miami',
    'entities': entities,
    'relations': relations
})
```

**3. Version Control:**
- Track which model version produced results
- Save processing parameters (thresholds, configurations)
- Keep audit trail for compliance

### 10.4 Maintenance Best Practices

**1. Regular Retraining:**
- Collect new annotated examples monthly/quarterly
- Retrain models with expanded dataset
- A/B test new models against production versions

**2. Monitoring:**
- Track average entities per document
- Monitor confidence score distributions
- Log errors and warnings
- Review low-confidence predictions

**3. Documentation:**
- Document any customizations or configurations
- Keep README updated with instructions
- Record model performance metrics
- Maintain change log

### 10.5 Security Best Practices

**1. Data Privacy:**
- Ensure compliance with data protection regulations
- Anonymize sensitive information if needed
- Secure storage of training data and models
- Control access to extraction results

**2. Model Security:**
- Store models in version-controlled repositories
- Limit access to production models
- Validate inputs to prevent injection attacks
- Monitor for unusual processing patterns

---

## 11. Quick Reference Commands

### 11.1 Essential Commands

**Load NER Model:**
```python
import spacy
nlp = spacy.load("model/base_model_v2/model-best")
```

**Extract Entities:**
```python
doc = nlp(text)
entities = [(e.text, e.label_) for e in doc.ents]
```

**Load REL Model:**
```python
nlp_rel = spacy.load("model/rel_model_v2")
```

**Extract Relationships:**
```python
for (idx1, idx2), rel_dict in doc._.rel.items():
    conf = rel_dict["CONTACTORG"]
    if conf > 0.60:
        print(f"{doc.ents[idx1].text} → {doc.ents[idx2].text}")
```

**Batch Process:**
```python
for doc in nlp.pipe(texts, batch_size=50):
    # process
```

**Evaluate Model:**
```python
from spacy.scorer import Scorer
scorer = Scorer()
scores = scorer.score(examples)
```

---

## 12. Additional Resources

### 12.1 Documentation

- **SpaCy Documentation:** https://spacy.io/usage
- **SpaCy Training Guide:** https://spacy.io/usage/training
- **Relation Extraction Tutorial:** https://spacy.io/usage/layers-architectures#rel

### 12.2 Support

For questions or issues:
1. Check this user guide first
2. Review SpaCy documentation
3. Examine notebook comments and code
4. Contact project team for assistance

---

## Document Information

**Document Version**: 1.0
**Last Updated**: December 2025
**POC Status**: Proof of Concept
**Target Audience**: Data scientists, analysts, technical users, operators
