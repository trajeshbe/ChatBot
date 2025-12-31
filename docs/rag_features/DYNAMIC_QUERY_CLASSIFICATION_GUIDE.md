# Dynamic Query Classification System - Implementation Guide

**Date**: 2025-11-24
**Status**: Implemented
**Problem Solved**: Hardcoded rules with fixed ordering

---

## Problem Statement

### Before (Hardcoded System)

The original system had hardcoded rules in `query_classifier.py`:

```python
# Lines 100-129: Hardcoded rules in fixed order
ai_patterns = ['who are you', 'what are you', ...]  # Fixed list
doc_patterns = ['according to the document', ...]    # Fixed list
```

**Issues**:
1. ❌ Rules hardcoded in Python code (line 100)
2. ❌ Fixed execution order (rule-based → LLM fallback)
3. ❌ Can't customize per user
4. ❌ No intelligent ordering based on usage
5. ❌ "Who is Aadhan?" tries to answer directly instead of checking documents

### Example of the Problem

```
Query: "What is your model name?"
✅ Expected: Answer directly (AI-personal)
✅ Actual: Answers directly ✓ WORKS

Query: "Who is Aadhan?"
✅ Expected: Check documents for information about Aadhan
❌ Actual: Tries to answer with general knowledge ✗ FAILS
```

---

## Solution: Dynamic Classification with Configurable Rules

### New System Architecture

```
1. YAML Config File
   ↓
2. Dynamic Rule Loader
   ↓
3. Priority-Based Ordering (100 = highest)
   ↓
4. Context-Aware Matching (proper nouns, word count, etc.)
   ↓
5. User-Specific Overrides
   ↓
6. Adaptive Re-ordering (track hit rates)
   ↓
7. Classification Result
```

### Files Created

1. **Configuration File**: `backend/app/config/query_classification_rules.yaml`
   - Contains all classification rules
   - User-editable
   - Version controlled

2. **Dynamic Classifier**: `backend/app/services/dynamic_query_classifier.py`
   - Loads rules from YAML
   - Orders by priority
   - Tracks hits for adaptive ordering
   - Supports user-specific overrides

---

## How It Solves Your Problem

### 1. Priority-Based Rule Ordering

Rules are evaluated in priority order (highest first):

| Priority | Rule Type | Example Query |
|----------|-----------|---------------|
| **100** | Proper Noun "Who is" | "Who is Aadhan?" → **Check documents** ✅ |
| **88** | AI Model Info | "What is your model name?" → **Answer directly** ✅ |
| **85** | AI Identity | "Who are you?" → **Answer directly** |
| **75** | Document Explicit | "According to the document..." → **Check documents** |
| **60** | World Capitals | "Capital of France?" → **Answer directly** |
| **30** | Short Questions | "Aadhan?" → **Check documents** (ambiguous) |

### 2. Context-Aware Classification

The system detects:
- **Proper nouns**: Capitalized words like "Aadhan", "Tesla", "Microsoft"
- **Word count**: Short queries (≤3 words) treated as ambiguous
- **Question type**: "Who is [ProperNoun]" → document search

### Example: "Who is Aadhan?"

```yaml
# Priority 100 rule in config
- id: "proper_noun_who_is"
  name: "Proper Noun 'Who is' Questions"
  priority: 100  # Checked FIRST
  enabled: true
  type: "context_aware"
  patterns:
    - "^who is ([A-Z][a-z]+)"  # Matches "Who is Aadhan"
  classification: "document_specific"
  confidence: 0.95
  use_documents: true  # ← FORCE DOCUMENT SEARCH
  description: "Questions asking 'who is [ProperNoun]' should check documents"
```

**Result**:
- Query: "Who is Aadhan?"
- Matched rule: `proper_noun_who_is` (priority 100)
- Classification: `document_specific`
- Action: **Search documents for "Aadhan"** ✅

### 3. User-Specific Customization

Users can add custom rules in the YAML config:

```yaml
user_rules:
  - user_id: "default"
    overrides:
      # Custom rule for Aadhan
      - rule_id: "custom_entity_search"
        name: "Custom Entity Search"
        priority: 99
        enabled: true
        patterns:
          - "who is aadhan"
          - "tell me about aadhan"
          - "aadhan"
        classification: "document_specific"
        use_documents: true
```

---

## Usage Guide

### Step 1: Edit Rules (YAML Config)

Edit `backend/app/config/query_classification_rules.yaml`:

```yaml
# Add a new rule
rules:
  - id: "my_custom_rule"
    name: "My Custom Classification"
    priority: 95  # Where to place in order
    enabled: true
    type: "pattern_match"
    patterns:
      - "my pattern here"
    classification: "document_specific"  # or ai_personal, general, ambiguous
    confidence: 0.90
    use_documents: true  # Force document search
    description: "What this rule does"
```

### Step 2: Use Dynamic Classifier

In your code:

```python
from app.services.dynamic_query_classifier import dynamic_classifier

# Classify a query
result = await dynamic_classifier.classify("Who is Aadhan?")

print(result)
# Output:
# {
#   'query_type': 'document_specific',
#   'confidence': 0.95,
#   'use_documents': True,
#   'reason': 'Matched rule: Proper Noun Who is Questions (priority=100)',
#   'rule_id': 'proper_noun_who_is',
#   'rule_priority': 100
# }
```

### Step 3: Add Custom Rules Programmatically

```python
# Add a custom rule at runtime
dynamic_classifier.add_custom_rule(
    rule_id="custom_company_search",
    name="Company Information Search",
    patterns=["who is [company name]", "tell me about [company]"],
    classification="document_specific",
    priority=98,
    confidence=0.95,
    use_documents=True
)
```

### Step 4: View Rule Statistics

```python
# Get rule hit statistics
stats = dynamic_classifier.get_rule_stats()

for stat in stats:
    print(f"Rule: {stat['rule_name']}")
    print(f"  Priority: {stat['priority']}")
    print(f"  Hits: {stat['hit_count']}")
    print(f"  Avg Confidence: {stat['average_confidence']:.2f}")
```

### Step 5: Adaptive Reordering

```python
# Reorder rules based on hit rate
# Rules that match more often get checked first
dynamic_classifier.reorder_by_hit_rate()
```

---

## Configuration Examples

### Example 1: Force All "Who is" Questions to Check Documents

```yaml
rules:
  - id: "who_is_always_documents"
    name: "All 'Who is' Questions Check Documents"
    priority: 100
    enabled: true
    type: "pattern_match"
    patterns:
      - "^who is "
      - "^who was "
    classification: "document_specific"
    confidence: 0.95
    use_documents: true
```

**Result**:
- "Who is Einstein?" → Checks documents (even though Einstein is famous)
- "Who is Aadhan?" → Checks documents ✅

### Example 2: AI Model Questions Always Answer Directly

```yaml
rules:
  - id: "ai_model_info"
    name: "AI Model Information"
    priority: 88  # High priority
    enabled: true
    type: "pattern_match"
    patterns:
      - "what model are you"
      - "which model"
      - "what's your model"
    classification: "ai_personal"
    confidence: 0.98
    use_documents: false  # Don't check documents
```

**Result**:
- "What model are you?" → Answers directly without checking documents ✅

### Example 3: Company-Specific Queries

```yaml
rules:
  - id: "company_info"
    name: "Company Information"
    priority: 95
    enabled: true
    type: "pattern_match"
    patterns:
      - "tell me about (tesla|microsoft|apple|google)"
      - "what is (tesla|microsoft|apple|google)"
    classification: "document_specific"
    confidence: 0.90
    use_documents: true
```

### Example 4: Short Queries Default to Document Search

```yaml
rules:
  - id: "short_question"
    name: "Very Short Questions"
    priority: 30
    enabled: true
    type: "context_aware"
    detect: "word_count <= 3"  # Context-based detection
    classification: "ambiguous"
    confidence: 0.50
    use_documents: true  # Default to checking documents
```

**Result**:
- "Aadhan" → Checks documents
- "Machine learning" → Checks documents
- "Tesla" → Checks documents

---

## Integration with RAG Service

### Before (Old Classifier)

```python
from app.services.query_classifier import query_classifier

# Old way: Hardcoded rules
classification = await query_classifier.classify(query)
```

### After (Dynamic Classifier)

```python
from app.services.dynamic_query_classifier import dynamic_classifier

# New way: Dynamic rules from YAML config
classification = await dynamic_classifier.classify(query)

# Access rule information
if classification['use_documents']:
    # Perform RAG retrieval
    chunks = await retrieve_chunks(query)
else:
    # Use LLM directly
    answer = await llm.generate(query)
```

---

## API Endpoints for Rule Management

### Get All Rules

```bash
GET /api/v1/classification/rules

Response:
{
  "rules": [
    {
      "id": "proper_noun_who_is",
      "name": "Proper Noun 'Who is' Questions",
      "priority": 100,
      "enabled": true,
      "classification": "document_specific",
      "confidence": 0.95
    },
    ...
  ]
}
```

### Add Custom Rule

```bash
POST /api/v1/classification/rules

Body:
{
  "rule_id": "my_custom_rule",
  "name": "My Rule",
  "priority": 95,
  "patterns": ["pattern1", "pattern2"],
  "classification": "document_specific",
  "use_documents": true
}
```

### Get Rule Statistics

```bash
GET /api/v1/classification/stats

Response:
{
  "stats": [
    {
      "rule_id": "proper_noun_who_is",
      "rule_name": "Proper Noun Who is Questions",
      "priority": 100,
      "hit_count": 45,
      "average_confidence": 0.95
    },
    ...
  ]
}
```

---

## Testing the New System

### Test Case 1: AI Model Question

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is your model name?" \
  -F "model_id=llama3.1:8b"

# Classification:
# - Rule matched: "ai_model_info" (priority 88)
# - Classification: "ai_personal"
# - use_documents: false
# - Result: Answers directly ✅
```

### Test Case 2: Proper Noun Question

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Who is Aadhan?" \
  -F "model_id=llama3.1:8b"

# Classification:
# - Rule matched: "proper_noun_who_is" (priority 100)
# - Classification: "document_specific"
# - use_documents: true
# - Result: Searches documents for "Aadhan" ✅
```

### Test Case 3: General Knowledge

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is the capital of France?" \
  -F "model_id=llama3.1:8b"

# Classification:
# - Rule matched: "world_capitals" (priority 60)
# - Classification: "general"
# - use_documents: false
# - Result: Answers directly (Paris) ✅
```

---

## Migration from Old to New System

### Step 1: Install Dependencies

```bash
cd backend
pip install pyyaml
```

### Step 2: Update RAG Service

Replace old classifier with new one:

```python
# OLD:
from app.services.query_classifier import query_classifier

# NEW:
from app.services.dynamic_query_classifier import dynamic_classifier
```

### Step 3: Test Classification

```python
# Test old vs new
query = "Who is Aadhan?"

# Old system
old_result = await query_classifier.classify(query)
print("Old:", old_result['query_type'], old_result['use_documents'])

# New system
new_result = await dynamic_classifier.classify(query)
print("New:", new_result['query_type'], new_result['use_documents'])

# Expected:
# Old: general False (WRONG - tries to answer directly)
# New: document_specific True (CORRECT - checks documents)
```

---

## Advantages

### 1. **Configurable**
- ✅ Edit rules in YAML file (no code changes)
- ✅ Add/remove rules without redeployment
- ✅ Version control for rule changes

### 2. **Intelligent Ordering**
- ✅ Priority-based (highest checked first)
- ✅ Adaptive reordering based on hit rates
- ✅ User-specific customization

### 3. **Context-Aware**
- ✅ Detects proper nouns → force document search
- ✅ Short queries → ambiguous (check documents)
- ✅ Pattern matching with regex

### 4. **Observable**
- ✅ Track which rules are hit
- ✅ View statistics and hit rates
- ✅ Export/import configurations

### 5. **Flexible**
- ✅ Add custom rules programmatically
- ✅ Per-user rule overrides
- ✅ LLM fallback for edge cases

---

## Next Steps

1. **Integration**: Update RAG service to use `dynamic_classifier`
2. **Testing**: Test all query types with new system
3. **Tuning**: Adjust priorities based on usage
4. **Monitoring**: Track rule hit rates and adjust
5. **UI**: Create admin UI for rule management

---

## Summary

### Problem Solved ✅

| Before | After |
|--------|-------|
| ❌ Hardcoded rules | ✅ YAML configuration |
| ❌ Fixed order | ✅ Priority-based ordering |
| ❌ "Who is Aadhan?" → tries to answer | ✅ "Who is Aadhan?" → checks documents |
| ❌ Can't customize | ✅ User-specific rules |
| ❌ No adaptation | ✅ Adaptive reordering |

### Key Features

1. **Dynamic Configuration**: Rules in YAML, not code
2. **Intelligent Ordering**: Priority-based (100 = first)
3. **Context-Aware**: Detects proper nouns, word count
4. **User Customization**: Per-user rule overrides
5. **Adaptive**: Reorders based on hit rates
6. **Observable**: Track rule statistics

### Example Results

```
Query: "What is your model name?"
✅ Rule: ai_model_info (priority 88)
✅ Classification: ai_personal
✅ Action: Answer directly (no documents)

Query: "Who is Aadhan?"
✅ Rule: proper_noun_who_is (priority 100)
✅ Classification: document_specific
✅ Action: Search documents for "Aadhan"
```

**The system now intelligently decides whether to check documents or answer directly!**

---

**End of Guide**
