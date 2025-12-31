# Zero-Shot NER Prototype - User Guide

## Table of Contents
- [Getting Started](#getting-started)
- [Web Interface Guide](#web-interface-guide)
- [Entity Extraction Examples](#entity-extraction-examples)
- [Relation Extraction Examples](#relation-extraction-examples)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)
- [Use Case Scenarios](#use-case-scenarios)
- [Tips and Tricks](#tips-and-tricks)
- [FAQ](#faq)

## Getting Started

### Launching the Application

1. **Open Terminal/Command Prompt**

2. **Navigate to Project Directory**:
   ```bash
   cd /path/to/zero_shot_ner
   ```

3. **Activate Virtual Environment**:
   ```bash
   # Linux/macOS
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

4. **Start the Application**:
   ```bash
   streamlit run launch.py
   ```

5. **Access the Interface**:
   - The application will automatically open in your default browser
   - Default URL: `http://localhost:8501`
   - If it doesn't open automatically, navigate to the URL manually

### First Time Setup

On first launch:
- The API server will start automatically when you make your first prediction
- Models will download if not already cached (this may take a few minutes)
- A spinner will show "Starting API..." during initialization

## Web Interface Guide

### Interface Layout

The application has two main tabs:

1. **NER Tab**: Named Entity Recognition
2. **Relation Extraction Tab**: Relationship identification between entities

### NER Tab Components

```
┌─────────────────────────────────────────────────────┐
│  Flexitag - Entity Extraction with User-defined    │
│                     Labels                          │
├─────────────────────────────────────────────────────┤
│  Input Text:                                        │
│  ┌───────────────────────────────────────────────┐ │
│  │ [Text input area]                             │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Labels:                                            │
│  ┌───────────────────────────────────────────────┐ │
│  │ [Comma-separated labels]                      │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [Predict Button]                                   │
│                                                     │
│  Output:                                            │
│  ☐ Model_1  ☐ Model_2  (if both_models enabled)   │
│  ┌───────────────────────────────────────────────┐ │
│  │ [Color-coded entity visualization]            │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Relation Extraction Tab Components

```
┌─────────────────────────────────────────────────────┐
│  Flexitag - Relation Extraction with User-defined  │
│                     Labels                          │
├─────────────────────────────────────────────────────┤
│  Relation:                                          │
│  ┌───────────────────────────────────────────────┐ │
│  │ [Relation name, e.g., "works_for"]            │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Input Text:                                        │
│  ┌───────────────────────────────────────────────┐ │
│  │ [Text input area]                             │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Labels:                                            │
│  ┌───────────────────────────────────────────────┐ │
│  │ [Comma-separated entity labels]               │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Pairs:                                             │
│  ┌───────────────────────────────────────────────┐ │
│  │ [source -> target, e.g., person->org]        │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [Submit Button]                                    │
│                                                     │
│  Predicted Relation:                                │
│  ┌───────────────────────────────────────────────┐ │
│  │ [Structured relation output]                  │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Entity Extraction Examples

### Example 1: Basic Entity Extraction

**Scenario**: Extract people, organizations, and locations from a news article.

**Input Text**:
```
Apple Inc. announced that Tim Cook will speak at the upcoming conference
in San Francisco. The event is scheduled for next month.
```

**Labels**:
```
organization, person, location
```

**Steps**:
1. Navigate to the "NER" tab
2. Paste the text into the "Input Text" area
3. Enter labels: `organization, person, location`
4. Click "Predict"

**Expected Output**:
```
[Apple Inc.](organization 97.8%) announced that [Tim Cook](person 95.2%)
will speak at the upcoming conference in [San Francisco](location 93.1%).
The event is scheduled for next month.
```

### Example 2: Domain-Specific Entities

**Scenario**: Extract medical entities from a clinical note.

**Input Text**:
```
Patient presents with hypertension and diabetes mellitus. Prescribed
metformin 500mg twice daily and lisinopril 10mg once daily. Follow-up
in two weeks.
```

**Labels**:
```
disease, medication, dosage, timeframe
```

**Expected Entities**:
- **disease**: hypertension, diabetes mellitus
- **medication**: metformin, lisinopril
- **dosage**: 500mg, twice daily, 10mg, once daily
- **timeframe**: two weeks

### Example 3: Financial Document Analysis

**Scenario**: Extract financial entities from an earnings report.

**Input Text**:
```
Q3 revenue reached $125 million, representing a 15% increase year-over-year.
The company reported earnings per share of $2.35, exceeding analyst
expectations of $2.10.
```

**Labels**:
```
financial metric, currency amount, percentage, time period
```

**Expected Entities**:
- **financial metric**: revenue, earnings per share
- **currency amount**: $125 million, $2.35, $2.10
- **percentage**: 15%
- **time period**: Q3, year-over-year

### Example 4: Product Information Extraction

**Scenario**: Extract product details from a specification sheet.

**Input Text**:
```
The new MacBook Pro features the M2 chip with 16GB RAM and 512GB SSD.
It includes a 14-inch Retina display and weighs only 3.5 pounds.
Price starts at $1999.
```

**Labels**:
```
product, component, specification, price
```

**Expected Entities**:
- **product**: MacBook Pro
- **component**: M2 chip, RAM, SSD, Retina display
- **specification**: 16GB, 512GB, 14-inch, 3.5 pounds
- **price**: $1999

### Example 5: Legal Document Entities

**Scenario**: Extract legal entities from a contract.

**Input Text**:
```
This Agreement is entered into on January 15, 2024, between Acme Corporation,
a Delaware corporation, and Global Services LLC. The term of this Agreement
shall be three years commencing on the Effective Date.
```

**Labels**:
```
party, date, duration, entity type, jurisdiction
```

**Expected Entities**:
- **party**: Acme Corporation, Global Services LLC
- **date**: January 15, 2024
- **duration**: three years
- **entity type**: corporation, LLC
- **jurisdiction**: Delaware

## Relation Extraction Examples

### Example 1: Employment Relationships

**Scenario**: Identify who works for which organization.

**Input Text**:
```
John Smith is the CEO of Tech Innovations Inc. Sarah Johnson serves as
the Chief Technology Officer at Global Solutions. Michael Chen works as
a software engineer for Data Systems Corp.
```

**Configuration**:
- **Relation**: `works_for`
- **Labels**: `person, organization`
- **Pairs**: `person -> organization`
- **Threshold**: (leave empty)

**Expected Relations**:
```
1. John Smith --[works_for]--> Tech Innovations Inc.
   Confidence: 95.3%

2. Sarah Johnson --[works_for]--> Global Solutions
   Confidence: 94.7%

3. Michael Chen --[works_for]--> Data Systems Corp.
   Confidence: 96.1%
```

### Example 2: Geographic Relationships

**Scenario**: Identify which companies are located where.

**Input Text**:
```
Microsoft is headquartered in Redmond, Washington. Google's main office
is in Mountain View, California. Amazon is based in Seattle.
```

**Configuration**:
- **Relation**: `located_in`
- **Labels**: `organization, location`
- **Pairs**: `organization -> location`

**Expected Relations**:
```
1. Microsoft --[located_in]--> Redmond, Washington
2. Google --[located_in]--> Mountain View, California
3. Amazon --[located_in]--> Seattle
```

### Example 3: Product Ownership

**Scenario**: Identify which companies own which products.

**Input Text**:
```
Instagram is owned by Meta Platforms. YouTube belongs to Google.
LinkedIn was acquired by Microsoft. WhatsApp is another Meta product.
```

**Configuration**:
- **Relation**: `owned_by`
- **Labels**: `product, company`
- **Pairs**: `product -> company`

**Expected Relations**:
```
1. Instagram --[owned_by]--> Meta Platforms
2. YouTube --[owned_by]--> Google
3. LinkedIn --[owned_by]--> Microsoft
4. WhatsApp --[owned_by]--> Meta
```

### Example 4: Academic Affiliations

**Scenario**: Connect researchers with their institutions.

**Input Text**:
```
Dr. Emily Chen conducts research at MIT. Professor Robert Davis is affiliated
with Stanford University. Dr. Maria Garcia works in the laboratory at
Harvard Medical School.
```

**Configuration**:
- **Relation**: `affiliated_with`
- **Labels**: `researcher, institution`
- **Pairs**: `researcher -> institution`

**Expected Relations**:
```
1. Dr. Emily Chen --[affiliated_with]--> MIT
2. Professor Robert Davis --[affiliated_with]--> Stanford University
3. Dr. Maria Garcia --[affiliated_with]--> Harvard Medical School
```

### Example 5: Multiple Relation Types

**Scenario**: Extract different types of relationships from one text.

**Input Text**:
```
Dr. Sarah Miller, a researcher at Johns Hopkins University in Baltimore,
published a groundbreaking study on cancer treatment. The university's
medical center is located in Maryland.
```

**First Query - Employment**:
- **Relation**: `works_at`
- **Labels**: `person, organization`
- **Pairs**: `person -> organization`

**Second Query - Location**:
- **Relation**: `located_in`
- **Labels**: `organization, location`
- **Pairs**: `organization -> location`

## Advanced Usage

### Using the Threshold Parameter

The threshold controls the minimum confidence score for entity predictions.

**Via API**:
```python
data = {
    "model": "gliner",
    "input_text": "...",
    "labels": ["person", "organization"],
    "threshold": 0.7,  # Only entities with 70%+ confidence
    "nested_ner": False
}
```

**Effect**:
- **Lower threshold (0.3-0.5)**: More entities detected, including lower-confidence ones
- **Higher threshold (0.7-0.9)**: Fewer entities, but higher quality predictions

**Example**:

Text: "Dr. Smith mentioned IBM briefly in passing."

- **Threshold 0.3**: Detects both "Dr. Smith" and "IBM"
- **Threshold 0.8**: May only detect "Dr. Smith" (higher confidence)

### Nested Entity Recognition

Enables detection of entities within entities.

**Example**:

Text: "The New York City Department of Education announced new policies."

**Without nested NER**:
- `New York City Department of Education` (organization)

**With nested NER**:
- `New York City Department of Education` (organization)
- `New York City` (location)
- `Department of Education` (organization)

**API Usage**:
```python
data = {
    "nested_ner": True,
    # ... other parameters
}
```

### Distance Threshold for Relations

Limits how far apart entities can be to form a relation.

**Example**:

Text: "John works at Microsoft. The company, founded in 1975, is headquartered in Redmond."

**Without distance threshold**:
- May connect "John" with both "Microsoft" and "Redmond"

**With distance threshold (50 characters)**:
- Only connects "John" with "Microsoft" (they're close)
- Ignores "Redmond" (too far from "John")

**API Usage**:
```python
data = {
    "threshold": "50",  # String representing character distance
    # ... other parameters
}
```

### Comparing Multiple Models

If `both_models = True` in config:

1. Submit your text and labels
2. Both GLiNER and NuNER models will process the text
3. Check the output selector boxes to compare results
4. Observe differences in entity detection and confidence scores

**Use cases**:
- Validating results across models
- Choosing the best model for your domain
- Ensemble approaches (accepting entities found by both)

### API Integration

For programmatic access, use the REST API:

```python
from zero_shot_ner_client import ZeroShotNERClient

client = ZeroShotNERClient()

# Extract entities
result = client.extract_entities(
    text="Your text here",
    labels=["label1", "label2", "label3"],
    threshold=0.5
)

# Extract relations
relations = client.extract_relations(
    text="Your text here",
    labels=["entity1", "entity2"],
    relation="relation_type",
    pairs="entity1 -> entity2"
)
```

See [API Reference](03_api_reference.md) for complete details.

## Best Practices

### Label Design

**1. Be Specific**:
- Bad: `thing`, `item`, `name`
- Good: `product`, `company`, `person`

**2. Use Consistent Naming**:
- Choose singular or plural and stick with it
- Example: `person` not mixed with `people`

**3. Match Your Domain**:
- Medical: `symptom`, `diagnosis`, `treatment`
- Legal: `plaintiff`, `defendant`, `statute`
- Financial: `stock`, `revenue`, `expense`

**4. Avoid Overlapping Labels**:
- Bad: `company`, `organization`, `business` (too similar)
- Good: `company`, `product`, `location`

**5. Use Descriptive Labels**:
- Bad: `type1`, `cat_a`, `x`
- Good: `medication`, `dosage`, `frequency`

### Text Preparation

**1. Clean Text**:
- Remove excessive whitespace
- Fix obvious typos if possible
- Maintain original punctuation (it helps context)

**2. Optimal Text Length**:
- Minimum: ~10-20 words for meaningful context
- Optimal: 50-500 words per request
- Maximum: Models can handle longer texts, but performance may degrade

**3. Context Matters**:
- Provide enough surrounding text for accurate detection
- Don't truncate mid-sentence

**Example**:
```
Bad:  "John Smith"
Good: "John Smith is the CEO of Tech Corp."
Better: "John Smith, who joined the company in 2020, serves as
        the CEO of Tech Corp. based in San Francisco."
```

### Relation Extraction Tips

**1. Extract Entities First**:
- Use the NER tab to verify entities are detected
- Then proceed to relation extraction

**2. Define Clear Pairs**:
- Be specific about which entity types can relate
- Example: `person -> organization` not just `* -> *`

**3. Use Multiple Queries**:
- For different relation types, make separate requests
- Example: separate queries for "works_for" and "located_in"

**4. Relation Names**:
- Use clear, descriptive relation names
- Examples: `employed_by`, `manufactured_by`, `founded_in`
- Avoid vague terms like `related_to`, `associated_with`

### Performance Optimization

**1. Batch Processing**:
- Process multiple texts via API
- Use scripts for large datasets

**2. Caching**:
- Save results for repeated queries
- Avoid re-processing identical texts

**3. Label Reuse**:
- Define standard label sets for your domain
- Reuse across multiple documents

**4. GPU Acceleration**:
- For heavy usage, configure `device = cuda` in config
- Significantly faster inference

## Use Case Scenarios

### Scenario 1: Resume Screening

**Objective**: Extract skills, companies, and education from resumes.

**Labels**: `skill`, `company`, `degree`, `university`, `duration`

**Sample Text**:
```
Senior Software Engineer with 5 years of experience at Google.
Proficient in Python, Java, and machine learning. Holds a Master's
degree in Computer Science from Stanford University.
```

**Workflow**:
1. Extract entities with defined labels
2. Structure extracted information into a database
3. Use for candidate matching and filtering

### Scenario 2: News Monitoring

**Objective**: Track mentions of companies, people, and products in news.

**Labels**: `company`, `person`, `product`, `event`, `location`

**Sample Text**:
```
Tesla CEO Elon Musk announced the new Model Y will launch in Europe
next quarter. The electric vehicle manufacturer plans to expand
production at its Berlin facility.
```

**Workflow**:
1. Extract entities from news articles
2. Identify relations (e.g., person -> company)
3. Create alerts for specific entity combinations
4. Build knowledge graphs of business relationships

### Scenario 3: Customer Support Ticket Analysis

**Objective**: Extract products, issues, and customer sentiments.

**Labels**: `product`, `issue`, `error code`, `sentiment`, `priority`

**Sample Text**:
```
My iPhone 14 keeps crashing when I open the camera app. Error code
CE-500. This is urgent as I need it for work. Very frustrating!
```

**Workflow**:
1. Extract product and issue entities
2. Classify priority based on detected sentiment
3. Route tickets based on product categories
4. Track recurring issues across tickets

### Scenario 4: Scientific Literature Review

**Objective**: Extract research methods, findings, and datasets.

**Labels**: `method`, `dataset`, `metric`, `finding`, `limitation`

**Sample Text**:
```
We trained a BERT model on the IMDB dataset achieving 94.2% accuracy.
The model outperformed baseline approaches but showed limitations on
short texts.
```

**Workflow**:
1. Extract methodological details from papers
2. Build comparison tables of different approaches
3. Identify trends in research methods
4. Track dataset usage across studies

### Scenario 5: Contract Analysis

**Objective**: Extract parties, dates, obligations, and terms.

**Labels**: `party`, `date`, `obligation`, `term`, `condition`, `amount`

**Sample Text**:
```
The Supplier shall deliver 10,000 units by December 31, 2024.
Payment of $50,000 is due within 30 days of delivery. Either party
may terminate with 90 days written notice.
```

**Workflow**:
1. Extract key contract terms and parties
2. Build searchable contract database
3. Set up automated compliance monitoring
4. Identify non-standard clauses

## Tips and Tricks

### Improving Accuracy

**1. Provide Examples in Labels**:
Instead of just `medication`, you might use `medication (like aspirin, ibuprofen)` in your mental model when choosing labels. However, in the actual label field, use just `medication`.

**2. Iterate on Labels**:
- Start with broad labels
- Review results
- Refine to more specific labels based on what you see

**3. Use Multiple Passes**:
- First pass: Extract primary entities
- Second pass: Use different labels for secondary information

**4. Check for Ambiguity**:
If results are poor, your labels might be ambiguous:
- "Apple" - company or fruit?
- Add more context in the text or use more specific labels

### Common Pitfalls to Avoid

**1. Too Many Labels**:
- Using 20+ labels at once can reduce accuracy
- Better: Use 3-7 focused labels per request

**2. Vague Labels**:
- Avoid: `thing`, `stuff`, `other`
- These don't give the model clear guidance

**3. Insufficient Context**:
- Single words or very short phrases lack context
- Provide full sentences when possible

**4. Ignoring Model Limitations**:
- Models work best on standard language
- Heavy jargon, code, or non-English may not work well

### Keyboard Shortcuts (Streamlit)

- **Ctrl/Cmd + Enter**: Submit form (in some browsers)
- **Tab**: Navigate between fields
- **Ctrl/Cmd + R**: Refresh page (resets session state)

### Saving Results

**From Web Interface**:
1. Results are displayed as HTML
2. Right-click on output area
3. Select "Inspect Element"
4. Copy the HTML content
5. Save to a file or paste into a document

**Via API**:
```python
import json

# Save entity results
with open('results.html', 'w') as f:
    f.write(html_output)

# Save relation results
with open('relations.json', 'w') as f:
    json.dump(relations, f, indent=2)
```

### Batch Processing Script

```python
import csv
from zero_shot_ner_client import ZeroShotNERClient

client = ZeroShotNERClient()

# Read input
with open('input_texts.csv', 'r') as f:
    reader = csv.DictReader(f)
    results = []

    for row in reader:
        entities = client.extract_entities(
            text=row['text'],
            labels=['person', 'organization', 'location']
        )
        results.append({
            'id': row['id'],
            'entities_html': entities
        })

# Save results
with open('output.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'entities_html'])
    writer.writeheader()
    writer.writerows(results)
```

## FAQ

### General Questions

**Q: Do I need to train the model?**
A: No, that's the "zero-shot" aspect. Just provide labels at inference time.

**Q: How many labels can I use?**
A: Technically unlimited, but 3-10 labels per request works best for accuracy.

**Q: Can I use this for non-English text?**
A: The current models are optimized for English. Other languages may work but with reduced accuracy.

**Q: How accurate is the extraction?**
A: Accuracy varies by domain and label clarity. Typically 70-95% for well-defined labels on clear text.

**Q: Can I fine-tune the models?**
A: The prototype uses pre-trained models as-is. Fine-tuning would require additional development.

### Technical Questions

**Q: Why is the first prediction slow?**
A: Model loading takes 30-60 seconds. Subsequent predictions are much faster.

**Q: Can I run this offline?**
A: Yes, after initial model download. Ensure models are cached locally.

**Q: What's the difference between GLiNER and NuNER?**
A: Both are zero-shot NER models with slightly different architectures. GLiNER is the primary model.

**Q: Can I use GPU acceleration?**
A: Yes, set `device = cuda` in config.ini if you have a compatible NVIDIA GPU.

**Q: How much memory does it use?**
A: Approximately 4-6GB with one model loaded, 8-10GB with both models.

### Troubleshooting Questions

**Q: Why aren't entities being detected?**
A: Possible reasons:
- Labels too vague or specific
- Text lacks context
- Threshold too high
- Entity type not present in text

**Q: Why are there so many false positives?**
A: Try:
- Increasing the threshold
- Using more specific labels
- Providing more context in text

**Q: The API won't start. What do I do?**
A: Check:
- Port 5000 isn't already in use
- Virtual environment is activated
- All dependencies are installed
- Check logs in `logs/` directory

**Q: Results differ between models. Which is correct?**
A: Both can be valid. Consider:
- Comparing confidence scores
- Domain-specific performance (test both)
- Consistency across similar texts

### Usage Questions

**Q: Can I extract custom entity types?**
A: Yes, any entity type you define - that's the main feature!

**Q: How do I handle nested entities?**
A: Set `nested_ner: true` in API requests or enable in config.

**Q: Can I extract relationships without predefined pairs?**
A: No, you need to specify possible entity type pairs for relation extraction.

**Q: What if my text is very long?**
A: Break it into smaller chunks (paragraphs or sections) and process separately.

**Q: Can I save my label sets for reuse?**
A: Currently no built-in feature, but you can:
- Create scripts with predefined labels
- Use the API with saved label lists
- Build a wrapper application with templates

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Prototype Status**: Active Development

## Additional Resources

- [Overview Documentation](01_overview.md) - Introduction and key features
- [Architecture Documentation](02_architecture.md) - Technical details
- [API Reference](03_api_reference.md) - API endpoints and integration
- [Deployment Guide](04_deployment_guide.md) - Installation and setup

For support, refer to the project repository or contact the development team.
