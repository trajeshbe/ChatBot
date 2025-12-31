# Merit ML Platform - User Guide
## How to Use Each API Endpoint with Examples & Best Practices

---

## Table of Contents
1. [Getting Started](#getting-started)
2. [Named Entity Recognition (NER)](#named-entity-recognition-ner)
3. [Relation Extraction](#relation-extraction)
4. [QA System (Indexing & Chat)](#qa-system-indexing--chat)
5. [Talend Pulse (Resume Scoring)](#talend-pulse-resume-scoring)
6. [Best Practices](#best-practices)
7. [Common Use Cases](#common-use-cases)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Getting Started

### Prerequisites

Before using the Merit ML Platform, ensure you have:

1. **API Credentials**: Username and password (provided by administrator)
2. **Network Access**: Connectivity to API server and Redis
3. **Redis Client**: For polling results (Python: `redis` package, Node.js: `redis` npm package)
4. **Document Access**: Files accessible via SFTP or local paths

### Basic Workflow

All endpoints follow a similar pattern:

1. **Submit Request**: POST to endpoint with authentication
2. **Receive Request ID**: API returns `request_id` for tracking
3. **Poll Status Stream**: Monitor Redis status stream for results
4. **Parse Results**: Extract and process returned data

### Authentication Setup

**Python**:
```python
import requests

API_URL = "http://your-server:5001"
AUTH = ("your_username", "your_password")

response = requests.post(
    f"{API_URL}/ner",
    auth=AUTH,
    json={"fileId": "doc_001", "path": "file.pdf", "labels": ["person"]}
)
```

**cURL**:
```bash
curl -u username:password \
  -X POST http://your-server:5001/ner \
  -H "Content-Type: application/json" \
  -d '{"fileId": "doc_001", "path": "file.pdf", "labels": ["person"]}'
```

---

## Named Entity Recognition (NER)

### Overview

Extract entities like people, organizations, locations, dates, amounts, and custom business entities from PDF documents.

### When to Use NER

- **Contract Analysis**: Extract parties, dates, amounts, legal terms
- **Invoice Processing**: Identify vendors, invoice numbers, line items
- **Resume Parsing**: Extract names, skills, companies, education
- **Research Papers**: Identify authors, institutions, citations
- **Medical Records**: Extract patient names, medications, diagnoses

### Step-by-Step Guide

#### Step 1: Prepare Your Document

Ensure your PDF is:
- Readable (not scanned images without OCR)
- Accessible at the specified path
- Less than 100 pages (for optimal performance)

#### Step 2: Choose Entity Labels

Select entity types relevant to your use case:

**Common Labels**:
- `person`, `organization`, `location`, `date`, `time`
- `amount`, `currency`, `percentage`, `email`, `phone`
- `product`, `service`, `event`, `law`, `regulation`

**Custom Labels** (domain-specific):
- `drug_name`, `disease`, `symptom` (medical)
- `stock_symbol`, `company_ticker` (financial)
- `contract_clause`, `legal_term` (legal)
- `skill`, `certification`, `degree` (HR)

**Label Requirements**:
- Minimum 3 characters per label
- Use descriptive, specific labels
- Avoid overly generic labels like "thing" or "item"

#### Step 3: Submit NER Request

**Python Example**:
```python
import requests

API_URL = "http://localhost:5001"
AUTH = ("username", "password")

# Submit request
response = requests.post(
    f"{API_URL}/ner",
    auth=AUTH,
    json={
        "fileId": "contract_2024_001",
        "path": "/documents/service_agreement.pdf",
        "labels": [
            "person",
            "organization",
            "date",
            "amount",
            "currency",
            "contract_term"
        ]
    }
)

request_id = response.json()["request_id"]
print(f"Request ID: {request_id}")
```

#### Step 4: Poll for Results

**Python Example**:
```python
import redis
import json
import time

# Connect to Redis
redis_client = redis.StrictRedis(
    host='172.27.140.191',
    port=6380,
    password='your_redis_password',
    decode_responses=True
)

# Poll status stream
last_id = "0"
results = []

while True:
    messages = redis_client.xread(
        {"status_stream_kn": last_id},
        count=10,
        block=5000
    )

    if messages:
        for stream, entries in messages:
            for message_id, data in entries:
                last_id = message_id

                if data.get("request_id") == request_id:
                    results.append(data)
                    print(f"✓ Page {data['page']}, Chunk {data['chunk']}: {data['status']}")

                    if data.get("EOF") == "True":
                        print("✓ Processing complete!")
                        break

        if results and results[-1].get("EOF") == "True":
            break

    time.sleep(1)
```

#### Step 5: Parse and Use Results

```python
# Parse entities from results
all_entities = []

for result in results:
    entities = json.loads(result["entities"])

    for entity in entities:
        all_entities.append({
            "type": entity["entity"],
            "text": entity["span"],
            "page": result["page"],
            "chunk": result["chunk"],
            "confidence": entity["score"],
            "char_start": entity["start"],
            "char_end": entity["end"]
        })

# Group entities by type
from collections import defaultdict

entities_by_type = defaultdict(list)
for entity in all_entities:
    entities_by_type[entity["type"]].append(entity)

# Print summary
for entity_type, entities in entities_by_type.items():
    print(f"\n{entity_type.upper()} ({len(entities)} found):")
    unique_spans = list(set(e["text"] for e in entities))
    for span in unique_spans[:5]:  # Show first 5
        print(f"  - {span}")
```

### Example Output

```
PERSON (12 found):
  - John Smith
  - Jane Doe
  - Michael Johnson

ORGANIZATION (8 found):
  - Acme Corporation
  - Merit Software Services
  - Global Tech Inc

DATE (15 found):
  - January 15, 2024
  - 2024-01-15
  - 15/01/2024

AMOUNT (6 found):
  - $50,000
  - 100,000 USD
  - fifty thousand dollars
```

### NER Best Practices

1. **Label Selection**:
   - Start with 5-10 most important entity types
   - Test with sample documents first
   - Add more labels iteratively

2. **Performance**:
   - Process large documents in chunks
   - Cache results for repeated processing
   - Use batch processing for multiple files

3. **Accuracy**:
   - Use specific labels (prefer "invoice_number" over "number")
   - Provide context in label names ("contract_party" vs "party")
   - Review low-confidence entities (score < 0.7)

4. **Post-Processing**:
   - Deduplicate entities by span
   - Normalize formats (dates, amounts)
   - Validate extracted entities against business rules

---

## Relation Extraction

### Overview

Extract relationships between entities to build knowledge graphs and understand document structure.

### When to Use Relation Extraction

- **Contract Relationships**: Who signs what, who pays whom
- **Organizational Charts**: Employee-manager relationships
- **Supply Chains**: Supplier-customer relationships
- **Scientific Papers**: Author-affiliation, citation relationships
- **Legal Documents**: Party-obligation relationships

### Prerequisites

**Required**: NER must be performed first on the same `fileId`

### Step-by-Step Guide

#### Step 1: Ensure NER Completion

```python
# Verify NER results exist in cache
# Check that status shows "Done" for all chunks
```

#### Step 2: Submit Relation Extraction Request

**Python Example**:
```python
response = requests.post(
    f"{API_URL}/rel",
    auth=AUTH,
    json={
        "fileId": "contract_2024_001",
        "path": "/documents/service_agreement.pdf"
    }
)

request_id = response.json()["request_id"]
print(f"Relation Request ID: {request_id}")
```

#### Step 3: Poll for Results

```python
# Same polling logic as NER
while True:
    messages = redis_client.xread(
        {"status_stream_kn": last_id},
        count=10,
        block=5000
    )

    for stream, entries in messages:
        for message_id, data in entries:
            if data.get("request_id") == request_id:
                results.append(data)
                if data.get("EOF") == "True":
                    print("✓ Relation extraction complete!")
                    break
```

#### Step 4: Parse Relationships

```python
import json

all_relationships = []

for result in results:
    if result.get("relation"):
        relationships = json.loads(result["relation"])

        for rel in relationships:
            all_relationships.append({
                "head": rel["head"],
                "relation": rel["relation"],
                "tail": rel["tail"],
                "page": result["page"],
                "chunk": result["chunk"]
            })

# Print relationships
print(f"\nExtracted {len(all_relationships)} relationships:\n")
for rel in all_relationships:
    print(f"{rel['head']} --[{rel['relation']}]--> {rel['tail']}")
```

### Example Output

```
Extracted 15 relationships:

John Smith --[signs]--> Service Agreement
Acme Corporation --[pays]--> Merit Software Services
Merit Software Services --[provides]--> Software Development Services
Service Agreement --[effective_date]--> January 15, 2024
John Smith --[represents]--> Acme Corporation
$50,000 --[payment_amount]--> Monthly Payment
Acme Corporation --[located_in]--> New York
Merit Software Services --[located_in]--> California
```

### Building Knowledge Graphs

```python
import networkx as nx
import matplotlib.pyplot as plt

# Create directed graph
G = nx.DiGraph()

for rel in all_relationships:
    G.add_edge(
        rel["head"],
        rel["tail"],
        relation=rel["relation"]
    )

# Visualize
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, k=2)
nx.draw(G, pos, with_labels=True, node_color='lightblue',
        node_size=3000, font_size=10, arrows=True)

edge_labels = nx.get_edge_attributes(G, 'relation')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

plt.title("Contract Relationship Graph")
plt.savefig("relationship_graph.png", dpi=300, bbox_inches='tight')
```

### Relation Extraction Best Practices

1. **Entity Quality**: High-quality NER results = better relationships
2. **Context Window**: Relationships extracted within chunk boundaries
3. **Validation**: Verify relationships make semantic sense
4. **Deduplication**: Same relationship may appear across chunks

---

## QA System (Indexing & Chat)

### Overview

Build a conversational AI system for querying document collections using Retrieval-Augmented Generation (RAG).

### When to Use QA System

- **Knowledge Base**: Query internal documentation
- **Customer Support**: Answer questions from manuals
- **Research**: Ask questions about research papers
- **Compliance**: Query policies and regulations
- **Training**: Interactive learning from training materials

### Two-Step Process

1. **Indexing**: Prepare documents for search (one-time setup)
2. **Chat**: Ask questions (multiple queries per session)

---

### Part 1: QA Indexing

#### Step 1: Prepare Document Collection

Organize related documents for a topic:
- User manuals
- API documentation
- Policy documents
- Research papers

#### Step 2: Submit Indexing Request

**Python Example**:
```python
response = requests.post(
    f"{API_URL}/qa_indexer",
    auth=AUTH,
    json={
        "input_files": [
            {
                "fileId": "user_manual_v1",
                "path": "/docs/user_manual.pdf"
            },
            {
                "fileId": "admin_guide_v1",
                "path": "/docs/admin_guide.pdf"
            },
            {
                "fileId": "api_reference_v1",
                "path": "/docs/api_reference.pdf"
            }
        ]
    }
)

request_id = response.json()["request_id"]
session_id = response.json()["session_id"]

print(f"Request ID: {request_id}")
print(f"Session ID: {session_id}")
print("⚠️ IMPORTANT: Save session_id for chat requests!")
```

#### Step 3: Wait for Indexing Completion

```python
# Poll for indexing completion
while True:
    messages = redis_client.xread(
        {"status_stream_kn": last_id},
        count=10,
        block=5000
    )

    for stream, entries in messages:
        for message_id, data in entries:
            if data.get("request_id") == request_id:
                if data.get("status") == "Done":
                    print("✓ Indexing complete! Ready for chat.")
                    break
```

**Indexing Time**: Approximately 1-2 minutes per 100 pages

---

### Part 2: QA Chat

#### Step 1: Ask Questions

**Python Example**:
```python
def ask_question(session_id, question):
    response = requests.post(
        f"{API_URL}/qa_chat",
        auth=AUTH,
        json={
            "session_id": session_id,
            "question": question,
            "llm_model_name": "gpt-4o-mini",
            "model_provider_name": "openai"
        }
    )

    request_id = response.json()["request_id"]

    # Poll for answer
    last_id = "0"
    while True:
        messages = redis_client.xread(
            {"status_stream_kn": last_id},
            count=10,
            block=5000
        )

        for stream, entries in messages:
            for message_id, data in entries:
                last_id = message_id
                if data.get("request_id") == request_id:
                    return data

        time.sleep(1)

# Ask multiple questions
questions = [
    "What are the installation requirements?",
    "How do I configure the database connection?",
    "What are the supported authentication methods?",
    "How do I enable logging?"
]

for question in questions:
    print(f"\n📝 Q: {question}")

    answer = ask_question(session_id, question)

    print(f"💡 A: {answer['generation']}")

    # Parse source documents
    sources = json.loads(answer['documents'])
    if sources:
        print(f"📚 Sources ({len(sources)}):")
        for doc in sources:
            print(f"  - {doc['path']} (Page {doc['page']})")
```

### Example Output

```
📝 Q: What are the installation requirements?
💡 A: The installation requirements are:
  - Python 3.8 or higher
  - 16GB RAM minimum
  - NVIDIA GPU with 8GB VRAM
  - 50GB storage space
  - Redis 6.2+
  - CUDA 11.8 or higher

📚 Sources (2):
  - /docs/user_manual.pdf (Page 5)
  - /docs/admin_guide.pdf (Page 12)

📝 Q: How do I configure the database connection?
💡 A: To configure the database connection, edit the config.yaml file and set the following parameters:
  - db_params.sqlite_db_url: "sqlite:///your_database.db"

For production deployments, ensure the database file has proper permissions (600).

📚 Sources (1):
  - /docs/admin_guide.pdf (Page 34)
```

### QA Best Practices

1. **Indexing**:
   - Index related documents together
   - One session per topic/domain
   - Re-index when documents change
   - Keep sessions under 500 pages total

2. **Question Formulation**:
   - Ask specific, focused questions
   - Use keywords from domain
   - Avoid yes/no questions (prefer "What/How")
   - Provide context when needed

3. **Answer Interpretation**:
   - Always check source documents
   - "I don't know" = answer not in indexed docs
   - Cross-reference multiple sources
   - Verify critical information

4. **Session Management**:
   - Store session_id in database
   - Label sessions by topic
   - Delete old sessions to save space
   - Monitor ChromaDB size

---

## Talend Pulse (Resume Scoring)

### Overview

Automatically score candidate resumes against job descriptions for recruitment workflows.

### When to Use Talend Pulse

- **Initial Screening**: Filter large candidate pools
- **Skill Matching**: Identify candidates with required skills
- **Objective Evaluation**: Remove bias from screening
- **Bulk Processing**: Score 100+ resumes quickly

### Prerequisites

- Job description as `.txt` file on SFTP server
- Candidate resumes as `.pdf` files on SFTP server
- SFTP credentials configured

### Step-by-Step Guide

#### Step 1: Prepare Job Description

Create a structured JD text file:

**Example** (`senior_swe.txt`):
```
Position: Senior Software Engineer

Required Skills:
- Python programming (5+ years)
- Django/Flask frameworks
- REST API development
- PostgreSQL database
- Docker & Kubernetes
- AWS cloud services

Preferred Skills:
- React.js frontend
- Machine learning experience
- Microservices architecture

Education:
- Bachelor's in Computer Science or equivalent

Experience:
- 5+ years software development
- 2+ years team leadership
```

#### Step 2: Upload Files to SFTP

```bash
# Upload JD
sftp Merit_KIAA@125.16.95.60
put senior_swe.txt /Merit_KIAA/jds/

# Upload resumes
put candidate_001.pdf /Merit_KIAA/resumes/
put candidate_002.pdf /Merit_KIAA/resumes/
put candidate_003.pdf /Merit_KIAA/resumes/
```

#### Step 3: Submit Scoring Request

**Python Example**:
```python
response = requests.post(
    f"{API_URL}/talend_pulse",
    auth=AUTH,
    json={
        "jd_file": {
            "fileId": "jd_swe_001",
            "path": "/Merit_KIAA/jds/senior_swe.txt"
        },
        "cv_files": [
            {
                "fileId": "cv_john_doe",
                "path": "/Merit_KIAA/resumes/john_doe.pdf"
            },
            {
                "fileId": "cv_jane_smith",
                "path": "/Merit_KIAA/resumes/jane_smith.pdf"
            },
            {
                "fileId": "cv_mike_wilson",
                "path": "/Merit_KIAA/resumes/mike_wilson.pdf"
            }
        ]
    }
)

request_id = response.json()["request_id"]
print(f"Request ID: {request_id}")
```

#### Step 4: Poll for Results (Per Candidate)

```python
last_id = "0"
candidates = []

while True:
    messages = redis_client.xread(
        {"status_stream_kn": last_id},
        count=10,
        block=5000
    )

    for stream, entries in messages:
        for message_id, data in entries:
            last_id = message_id

            if data.get("request_id") == request_id:
                # Parse candidate result
                response_data = json.loads(data["response"])
                candidates.append({
                    "fileId": data["fileId"],
                    "name": response_data["Candidate Name"],
                    "overall_score": int(response_data["Overall Score"]),
                    "skills": response_data["Skill_score"],
                    "status": data["file_status"]
                })

                print(f"✓ Processed: {response_data['Candidate Name']} - Score: {response_data['Overall Score']}/100")

                if data.get("status") == "Done":
                    print("✓ All candidates processed!")
                    break

    if data.get("status") == "Done":
        break
```

#### Step 5: Analyze and Rank Results

```python
import pandas as pd

# Convert to DataFrame
df = pd.DataFrame([
    {
        "Name": c["name"],
        "Overall Score": c["overall_score"],
        "Status": c["status"]
    }
    for c in candidates
])

# Rank by score
df = df.sort_values("Overall Score", ascending=False)

print("\n" + "="*60)
print("CANDIDATE RANKING")
print("="*60)
print(df.to_string(index=False))

# Top candidate detailed view
top_candidate = candidates[0]
print(f"\n\nTOP CANDIDATE: {top_candidate['name']}")
print(f"Overall Score: {top_candidate['overall_score']}/100\n")

# Skill breakdown
for skill in top_candidate['skills']:
    spec = skill['Specification']
    required = skill['Required']
    score = skill['Candidate Score']
    justification = skill['Candidate Justification']

    print(f"{spec}:")
    print(f"  Required: {required}")
    print(f"  Score: {score}/10")
    print(f"  Justification: {justification}\n")
```

### Example Output

```
============================================================
CANDIDATE RANKING
============================================================
            Name  Overall Score  Status
    John Doe              85    Done
  Jane Smith              78    Done
 Mike Wilson              62    Done


TOP CANDIDATE: John Doe
Overall Score: 85/100

Python_Skills:
  Required: Python programming (5+ years)
  Score: 9/10
  Justification: Candidate has 6 years of Python experience with extensive use of Django and Flask frameworks in production environments.

AWS_Skills:
  Required: AWS cloud services
  Score: 8/10
  Justification: Strong AWS experience including EC2, S3, RDS, and Lambda. AWS Certified Solutions Architect.

Docker_Skills:
  Required: Docker & Kubernetes
  Score: 7/10
  Justification: 3 years of Docker experience and 1 year with Kubernetes in production deployments.

Experience:
  Required: 5+ years software development
  Score: 9/10
  Justification: 6 years of professional software development experience across fintech and healthcare domains.
```

### Talend Pulse Best Practices

1. **JD Quality**:
   - Structure JD clearly (skills, experience, education)
   - Be specific with requirements
   - Separate "required" vs "preferred"
   - Include years of experience

2. **Resume Quality**:
   - Accept standard PDF formats
   - Avoid scanned images
   - Ensure text is extractable

3. **Scoring Interpretation**:
   - 80-100: Excellent match
   - 60-79: Good match (interview)
   - 40-59: Moderate match (consider)
   - 0-39: Poor match

4. **Workflow Integration**:
   - Automate bulk screening
   - Use scores as one signal (not sole criterion)
   - Review justifications for borderline candidates
   - Combine with other assessment methods

---

## Best Practices

### General Guidelines

1. **Request Management**:
   - Always store request IDs
   - Log all API calls
   - Implement request tracking system

2. **Error Handling**:
   - Wrap API calls in try-except
   - Implement retry logic with exponential backoff
   - Monitor dead-letter queues

3. **Performance**:
   - Batch similar requests
   - Cache frequently accessed results
   - Use appropriate worker counts

4. **Security**:
   - Never log credentials
   - Use environment variables
   - Rotate API keys regularly

### Code Template

```python
import requests
import redis
import json
import time
from typing import Optional, Dict, List

class MeritMLClient:
    def __init__(self, api_url: str, username: str, password: str, redis_config: Dict):
        self.api_url = api_url
        self.auth = (username, password)
        self.redis_client = redis.StrictRedis(**redis_config)

    def _poll_results(self, request_id: str, timeout: int = 300) -> List[Dict]:
        """Poll status stream for results with timeout"""
        start_time = time.time()
        last_id = "0"
        results = []

        while time.time() - start_time < timeout:
            messages = self.redis_client.xread(
                {"status_stream_kn": last_id},
                count=10,
                block=5000
            )

            for stream, entries in messages:
                for message_id, data in entries:
                    last_id = message_id
                    if data.get("request_id") == request_id:
                        results.append(data)
                        if data.get("EOF") == "True" or data.get("status") == "Done":
                            return results

            time.sleep(1)

        raise TimeoutError(f"Results not received within {timeout}s")

    def extract_entities(self, file_id: str, path: str, labels: List[str]) -> List[Dict]:
        """Extract entities from document"""
        response = requests.post(
            f"{self.api_url}/ner",
            auth=self.auth,
            json={"fileId": file_id, "path": path, "labels": labels}
        )
        response.raise_for_status()

        request_id = response.json()["request_id"]
        results = self._poll_results(request_id)

        # Parse entities
        all_entities = []
        for result in results:
            entities = json.loads(result["entities"])
            all_entities.extend(entities)

        return all_entities

    def index_documents(self, files: List[Dict]) -> str:
        """Index documents for QA, returns session_id"""
        response = requests.post(
            f"{self.api_url}/qa_indexer",
            auth=self.auth,
            json={"input_files": files}
        )
        response.raise_for_status()

        request_id = response.json()["request_id"]
        session_id = response.json()["session_id"]

        # Wait for completion
        self._poll_results(request_id)

        return session_id

    def ask_question(self, session_id: str, question: str) -> Dict:
        """Ask question about indexed documents"""
        response = requests.post(
            f"{self.api_url}/qa_chat",
            auth=self.auth,
            json={
                "session_id": session_id,
                "question": question,
                "llm_model_name": "gpt-4o-mini",
                "model_provider_name": "openai"
            }
        )
        response.raise_for_status()

        request_id = response.json()["request_id"]
        results = self._poll_results(request_id)

        return {
            "answer": results[0]["generation"],
            "sources": json.loads(results[0]["documents"])
        }

# Usage
client = MeritMLClient(
    api_url="http://localhost:5001",
    username="api_user",
    password="api_pass",
    redis_config={
        "host": "172.27.140.191",
        "port": 6380,
        "password": "redis_password",
        "decode_responses": True
    }
)

# Extract entities
entities = client.extract_entities(
    "doc_001",
    "/docs/contract.pdf",
    ["person", "organization", "date"]
)

# QA workflow
session_id = client.index_documents([
    {"fileId": "manual_001", "path": "/docs/manual.pdf"}
])

answer = client.ask_question(
    session_id,
    "What are the installation requirements?"
)

print(f"Answer: {answer['answer']}")
```

---

## Common Use Cases

### Use Case 1: Contract Analysis Pipeline

```python
# Step 1: Extract entities
entities = client.extract_entities(
    "contract_001",
    "/contracts/service_agreement.pdf",
    ["party", "date", "amount", "payment_term", "deliverable"]
)

# Step 2: Extract relationships
relationships = client.extract_relationships(
    "contract_001",
    "/contracts/service_agreement.pdf"
)

# Step 3: Build structured output
contract_data = {
    "parties": [e["span"] for e in entities if e["entity"] == "party"],
    "dates": [e["span"] for e in entities if e["entity"] == "date"],
    "amounts": [e["span"] for e in entities if e["entity"] == "amount"],
    "relationships": relationships
}

# Step 4: Store in database or export to JSON
with open("contract_001_analysis.json", "w") as f:
    json.dump(contract_data, f, indent=2)
```

### Use Case 2: Knowledge Base System

```python
# Index company documentation
session_id = client.index_documents([
    {"fileId": "hr_policy", "path": "/docs/hr_policy.pdf"},
    {"fileId": "it_policy", "path": "/docs/it_policy.pdf"},
    {"fileId": "finance_policy", "path": "/docs/finance_policy.pdf"}
])

# Create employee Q&A bot
def employee_qa_bot(session_id):
    print("Employee Q&A Bot - Type 'quit' to exit")

    while True:
        question = input("\nYour question: ")
        if question.lower() == 'quit':
            break

        answer = client.ask_question(session_id, question)
        print(f"\nAnswer: {answer['answer']}\n")

        if answer['sources']:
            print("Sources:")
            for doc in answer['sources']:
                print(f"  - {doc['path']} (Page {doc['page']})")

employee_qa_bot(session_id)
```

### Use Case 3: Recruitment Automation

```python
# Bulk resume screening
candidates = [
    {"fileId": f"cv_{i:03d}", "path": f"/resumes/candidate_{i:03d}.pdf"}
    for i in range(1, 101)  # 100 candidates
]

# Submit scoring request
response = client.score_resumes(
    jd_file={"fileId": "jd_001", "path": "/jds/senior_engineer.txt"},
    cv_files=candidates
)

# Auto-filter candidates
qualified_candidates = [
    c for c in response
    if c["overall_score"] >= 70
]

# Send interview invitations
for candidate in qualified_candidates[:10]:  # Top 10
    send_interview_invitation(candidate["email"])
```

---

## Troubleshooting

### Issue: No Results Received

**Solution**:
- Check request_id matches
- Verify Redis stream name (check work_mode)
- Increase polling timeout
- Check dead-letter queue

### Issue: "Session not found" in QA Chat

**Solution**:
- Verify session_id from indexing response
- Check ChromaDB collections exist
- Re-index documents if needed

### Issue: Low Entity Recognition Accuracy

**Solution**:
- Use more specific labels
- Improve document quality
- Lower confidence threshold in post-processing

### Issue: Slow Processing

**Solution**:
- Check worker counts in config.yaml
- Verify GPU is being used (NER)
- Monitor Redis queue lengths
- Scale up infrastructure

---

## FAQ

**Q: Can I process scanned PDFs?**
A: Yes, but OCR quality affects results. Pre-process with OCR tool if needed.

**Q: How many documents can I index for QA?**
A: Recommended: < 500 pages per session for optimal performance.

**Q: Can I use different LLM providers?**
A: Yes, supports OpenAI, Groq, and other LangChain-compatible providers.

**Q: How long are results stored in Redis?**
A: Configure TTL in Redis. Default: indefinitely (manual cleanup needed).

**Q: Can I reuse NER results for multiple relation extractions?**
A: Yes, results cached in SQLite database by fileId.

**Q: What's the maximum file size?**
A: No hard limit, but < 50MB PDFs recommended for performance.

**Q: How do I clear old QA sessions?**
A: Manually delete ChromaDB collections or implement cleanup script.

**Q: Can I customize entity labels?**
A: Yes, GLiNER supports zero-shot learning with any label.

**Q: What happens if a worker crashes?**
A: Stuck message recovery mechanism reclaims and retries tasks.

**Q: How do I handle rate limits?**
A: Implement client-side throttling and monitor API response times.

---

**Document Version**: 1.0.0
**Last Updated**: December 2024
**Platform**: Merit ML Platform - Knowledge Agent
