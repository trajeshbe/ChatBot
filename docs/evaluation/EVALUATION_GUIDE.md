# RAG Evaluation System Guide

> **World-Class Evaluation Framework for Enterprise RAG Chatbot**
>
> Last Updated: 2025-11-14

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Evaluation Methods](#evaluation-methods)
3. [Architecture](#architecture)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Frontend Components](#frontend-components)
7. [Performance Optimization](#performance-optimization)
8. [Best Practices](#best-practices)
9. [Advanced Features](#advanced-features)

---

## Overview

The RAG Evaluation System provides comprehensive, configurable evaluation of RAG (Retrieval-Augmented Generation) responses using state-of-the-art methods.

### Key Features

- ✅ **13 Evaluation Methods** - From RAGAS frameworks to custom metrics
- ⚡ **Performance Optimized** - Async execution, caching, and batching
- 🎛️ **Fully Configurable** - Toggleable metrics via UI or API
- 📊 **Real-time Analytics** - Live dashboards and trend analysis
- 🔄 **Auto-Evaluation** - Automatic evaluation with sampling
- 💾 **Result Caching** - Smart caching for improved performance
- 👥 **Human Feedback** - Integrate user feedback for improvement

### Supported Evaluation Methods

| Method | Category | Description | Requires Library |
|--------|----------|-------------|------------------|
| **RAGAS** | Framework | Comprehensive RAG assessment (Faithfulness, Relevancy, Precision/Recall) | Yes |
| **LLM-as-a-Judge** | LLM | GPT-4/Claude evaluates response quality | No |
| **DeepEval** | Framework | Modern evaluation with hallucination detection | Yes |
| **Semantic Similarity** | Metric | Embedding-based similarity to ground truth | No |
| **BERTScore** | Metric | BERT-based semantic similarity | Yes |
| **Citation Accuracy** | Metric | Source attribution and grounding | No |
| **Toxicity Detection** | Safety | Detect harmful/offensive content | No |
| **Bias Detection** | Safety | Identify potential biases | No |
| **Hallucination Detection** | Safety | Detect unsupported claims | No |
| **Answer Relevancy** | Metric | Query-response relevance | No |
| **Context Precision** | Retrieval | Precision of retrieved contexts | No |
| **Context Recall** | Retrieval | Recall of retrieved contexts | No |
| **Faithfulness** | Metric | Groundedness in context | No |

---

## Evaluation Methods

### 1. RAGAS (Retrieval-Augmented Generation Assessment)

**Purpose**: Comprehensive framework for RAG evaluation

**Metrics**:
- **Answer Relevancy**: How relevant is the answer to the query?
- **Faithfulness**: Is the answer grounded in the provided context?
- **Context Relevancy**: Are the retrieved contexts relevant?
- **Context Precision**: Precision of top-k contexts
- **Context Recall**: Coverage of ground truth in contexts

**Installation**:
```bash
pip install ragas==0.1.7
```

**When to Use**:
- Production deployments requiring comprehensive metrics
- When you have ground truth data for validation
- For research and benchmarking

**Pros**: Industry-standard, comprehensive, well-tested
**Cons**: Requires external library, slower execution

---

### 2. LLM-as-a-Judge

**Purpose**: Use powerful LLMs to evaluate response quality

**Evaluation Criteria**:
- **Accuracy** (0-10): Factual correctness based on contexts
- **Completeness** (0-10): Does it fully answer the query?
- **Clarity** (0-10): Clear and well-structured?
- **Groundedness** (0-10): Well-grounded in contexts?
- **Helpfulness** (0-10): Would this help the user?

**Supported Models**:
- GPT-4 Turbo (recommended)
- GPT-4
- Claude 3 Opus
- Claude 3 Sonnet

**When to Use**:
- When you need nuanced, qualitative evaluation
- For complex queries requiring deep understanding
- When interpretability is important

**Pros**: Nuanced evaluation, detailed reasoning, no external dependencies
**Cons**: Higher cost, slower, requires API access

**Example Configuration**:
```json
{
  "enable_llm_as_judge": true,
  "llm_judge_model": "gpt-4-turbo-preview"
}
```

---

### 3. DeepEval

**Purpose**: Modern evaluation framework with advanced metrics

**Metrics**:
- Answer Relevancy
- Faithfulness
- Contextual Precision
- Hallucination Detection

**Installation**:
```bash
pip install deepeval==0.21.0
```

**When to Use**:
- For state-of-the-art hallucination detection
- When you need fast, automated evaluation
- For CI/CD integration

**Pros**: Modern framework, excellent hallucination detection
**Cons**: Requires external library

---

### 4. Semantic Similarity

**Purpose**: Compare response to ground truth using embeddings

**How It Works**:
1. Generate embeddings for response and ground truth
2. Calculate cosine similarity
3. Score ranges from 0 (unrelated) to 1 (identical)

**When to Use**:
- When you have ground truth answers
- For regression testing (ensure consistency)
- For quick similarity checks

**Pros**: Fast, lightweight, no external dependencies
**Cons**: Requires ground truth data

---

### 5. BERTScore

**Purpose**: Semantic text similarity using BERT

**Metrics**:
- Precision
- Recall
- F1 Score

**Installation**:
```bash
pip install bert-score==0.3.13
```

**When to Use**:
- For semantic similarity beyond simple embeddings
- When precision/recall breakdown is needed
- For research and benchmarking

**Pros**: State-of-the-art semantic similarity
**Cons**: Slower, requires external library

---

### 6. Citation Accuracy

**Purpose**: Evaluate source attribution and grounding

**What It Checks**:
- Presence of citations (e.g., [1], [Source 1])
- Grounding ratio (% of sentences grounded in context)
- Word overlap with source contexts

**When to Use**:
- When source attribution is critical
- For compliance and traceability
- In academic or legal contexts

**Pros**: Fast, no dependencies, important for trust
**Cons**: Heuristic-based, may have false positives

---

### 7-9. Safety Metrics (Toxicity, Bias, Hallucination)

**Purpose**: Ensure safe, unbiased, factual responses

**Toxicity Detection**:
- Detects harmful, offensive, or toxic content
- Keyword-based with optional ML models

**Bias Detection**:
- Identifies gender, racial, age biases
- Pattern-based detection

**Hallucination Detection**:
- Uses LLM to identify unsupported claims
- Checks if claims are backed by context

**When to Use**:
- **Always** - These are critical for production systems
- For compliance and user safety
- To maintain brand reputation

**Pros**: Essential for safety, relatively fast
**Cons**: May have false positives

**Enhanced Detection** (Optional):
```bash
pip install detoxify==0.5.2  # Advanced toxicity
pip install fairlearn==0.9.0  # Bias metrics
```

---

### 10-13. Retrieval Metrics

**Answer Relevancy**: Query-response semantic similarity
**Context Precision**: Precision of top-k retrieved contexts
**Context Recall**: Coverage of ground truth in contexts
**Faithfulness**: Response groundedness in context

**When to Use**:
- To optimize retrieval pipeline
- For debugging low-quality responses
- In A/B testing different retrieval strategies

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (React)                   │
│  ┌──────────────────┐  ┌──────────────────────┐   │
│  │ EvaluationSettings│  │ EvaluationDashboard │   │
│  │   (Toggles)       │  │   (Analytics)        │   │
│  └──────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                  │
│  ┌──────────────────────────────────────────────┐  │
│  │      Evaluation Router (/api/v1/evaluation)   │  │
│  │  - POST /config    - POST /evaluate           │  │
│  │  - GET  /analytics - POST /feedback           │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│           Evaluation Service (Core Logic)           │
│  ┌──────────────────────────────────────────────┐  │
│  │  • Method Orchestration                       │  │
│  │  • Async/Parallel Execution                   │  │
│  │  • Result Caching                             │  │
│  │  • Score Aggregation                          │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│              Individual Evaluators                  │
│  [RAGAS] [LLM-Judge] [DeepEval] [Custom Metrics]   │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│                  Database (PostgreSQL)              │
│  • evaluation_configs  • evaluation_results         │
│  • evaluation_cache    • human_feedback             │
└─────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Configuration** → Frontend toggles → API → Database
2. **Auto-Evaluation** → RAG Response → Evaluation Service → Results
3. **On-Demand Evaluation** → API Request → Evaluation Service → Results
4. **Analytics** → Aggregated Results → Dashboard Visualization

---

## Configuration

### UI Configuration (Recommended)

Use the `EvaluationSettings` component:

```tsx
import { EvaluationSettings } from '@/components/EvaluationSettings';

<EvaluationSettings
  sessionId="your-session-id"
  onConfigChange={(config) => console.log('Config updated:', config)}
/>
```

### API Configuration

**Create/Update Configuration**:

```bash
POST /api/v1/evaluation/config

{
  "session_id": "your-session-id",
  "enable_ragas": false,
  "enable_llm_as_judge": true,
  "enable_citation_accuracy": true,
  "enable_toxicity": true,
  "enable_hallucination": true,
  "llm_judge_model": "gpt-4-turbo-preview",
  "use_cache": true,
  "async_evaluation": true,
  "auto_evaluate": false,
  "evaluation_sampling_rate": 1.0
}
```

**Get Configuration**:

```bash
GET /api/v1/evaluation/config/{session_id}
```

### Programmatic Configuration

```python
from app.services.evaluation_service import EvaluationConfig, EvaluationMethod

config = EvaluationConfig(
    enabled_methods=[
        EvaluationMethod.ANSWER_RELEVANCY,
        EvaluationMethod.FAITHFULNESS,
        EvaluationMethod.CITATION_ACCURACY,
        EvaluationMethod.HALLUCINATION
    ],
    use_cache=True,
    async_evaluation=True,
    llm_judge_model="gpt-4-turbo-preview"
)
```

---

## API Reference

### Endpoints

#### 1. Create/Update Configuration

```http
POST /api/v1/evaluation/config
Content-Type: application/json

{
  "session_id": "string",
  "enable_ragas": false,
  "enable_llm_as_judge": true,
  "llm_judge_model": "gpt-4-turbo-preview",
  "use_cache": true,
  "async_evaluation": true,
  "auto_evaluate": false
}
```

**Response**:
```json
{
  "id": "uuid",
  "session_id": "string",
  "enabled_methods": ["llm_as_judge", "citation_accuracy"],
  "config": { ... },
  "created_at": "2025-11-14T10:00:00Z",
  "updated_at": "2025-11-14T10:00:00Z"
}
```

#### 2. Evaluate Response

```http
POST /api/v1/evaluation/evaluate
Content-Type: application/json

{
  "query": "What is the capital of France?",
  "response": "The capital of France is Paris.",
  "context_chunks": [
    {
      "content": "Paris is the capital and largest city of France.",
      "document_id": "uuid",
      "similarity": 0.95
    }
  ],
  "ground_truth": "Paris",
  "session_id": "your-session-id",
  "use_stored_config": true
}
```

**Response**:
```json
{
  "overall_score": 0.92,
  "scores": {
    "llm_as_judge": {
      "scores": {
        "accuracy": 0.95,
        "completeness": 0.90,
        "clarity": 0.95,
        "groundedness": 0.95,
        "helpfulness": 0.90
      },
      "reasoning": "The answer correctly identifies Paris as the capital..."
    },
    "citation_accuracy": {
      "scores": {
        "grounding_ratio": 0.95
      }
    }
  },
  "evaluation_time_ms": 1234.56,
  "enabled_methods": ["llm_as_judge", "citation_accuracy"],
  "metadata": {
    "query": "What is the capital of France?",
    "num_contexts": 1,
    "response_length": 35,
    "timestamp": "2025-11-14T10:00:00Z"
  },
  "errors": []
}
```

#### 3. Get Evaluation Results

```http
GET /api/v1/evaluation/results?session_id=xxx&limit=100&offset=0
```

#### 4. Get Analytics

```http
GET /api/v1/evaluation/analytics?session_id=xxx&days=30
```

**Response**:
```json
{
  "total_evaluations": 150,
  "avg_overall_score": 0.85,
  "avg_scores_by_method": {
    "llm_as_judge.accuracy": 0.88,
    "llm_as_judge.completeness": 0.82,
    "citation_accuracy.grounding_ratio": 0.90
  },
  "score_distribution": {
    "0.0-0.2": 2,
    "0.2-0.4": 5,
    "0.4-0.6": 15,
    "0.6-0.8": 48,
    "0.8-1.0": 80
  },
  "common_issues": {
    "hallucination": 5,
    "low_relevancy": 8,
    "bias": 2,
    "toxicity": 0
  },
  "time_series": [
    {
      "date": "2025-11-01",
      "avg_score": 0.83,
      "count": 12
    }
  ]
}
```

#### 5. Submit Human Feedback

```http
POST /api/v1/evaluation/feedback
Content-Type: application/json

{
  "session_id": "string",
  "message_id": "uuid",
  "rating": 5,
  "thumbs_up": true,
  "feedback_text": "Great answer!",
  "accuracy_rating": 5,
  "helpfulness_rating": 5
}
```

#### 6. Get Available Methods

```http
GET /api/v1/evaluation/methods
```

---

## Frontend Components

### EvaluationSettings Component

**Purpose**: Configure evaluation metrics via toggles

**Features**:
- Visual grouping by category
- Real-time config updates
- Performance settings
- Auto-evaluation toggle

**Usage**:
```tsx
import { EvaluationSettings } from '@/components/EvaluationSettings';

<EvaluationSettings
  sessionId={sessionId}
  onConfigChange={(config) => {
    console.log('Config updated:', config);
  }}
/>
```

### EvaluationDashboard Component

**Purpose**: Visualize evaluation analytics

**Features**:
- Overview metrics (total, avg score, issues)
- Score distribution charts
- Method-specific scores
- Time series trends
- Recent evaluations list

**Usage**:
```tsx
import { EvaluationDashboard } from '@/components/EvaluationDashboard';

<EvaluationDashboard
  sessionId={sessionId}
  autoRefresh={true}
  refreshInterval={30000}
/>
```

---

## Performance Optimization

### 1. Caching Strategy

**Evaluation Cache**:
- Results cached by query hash
- TTL: 1 hour (configurable)
- 95%+ similarity threshold for cache hits

**Benefits**:
- 10x faster for repeated queries
- Reduced API costs (LLM-as-a-Judge)
- Lower computational overhead

**Configuration**:
```json
{
  "use_cache": true,
  "cache_ttl_seconds": 3600
}
```

### 2. Async/Parallel Execution

**How It Works**:
- All enabled methods run in parallel
- Uses `asyncio.gather()`
- Independent evaluations don't block each other

**Performance Gains**:
- 3-5x faster for multiple methods
- Better resource utilization
- Scales with number of methods

**Configuration**:
```json
{
  "async_evaluation": true
}
```

### 3. Batching

**Batch Processing**:
- Process multiple queries in batches
- Configurable batch size

**Configuration**:
```json
{
  "batch_size": 10
}
```

### 4. Auto-Evaluation Sampling

**Purpose**: Evaluate subset of queries to balance insights and performance

**Configuration**:
```json
{
  "auto_evaluate": true,
  "evaluation_sampling_rate": 0.2  // Evaluate 20% of queries
}
```

**Recommended Rates**:
- Development: 100% (1.0)
- Staging: 50% (0.5)
- Production: 10-20% (0.1-0.2)

### 5. Method Selection

**Choose Wisely**:
- **Lightweight**: Citation Accuracy, Answer Relevancy, Toxicity
- **Medium**: Semantic Similarity, Bias Detection
- **Heavy**: LLM-as-a-Judge, RAGAS, DeepEval

**Recommended Combinations**:

**For Speed** (< 500ms):
```json
{
  "enable_citation_accuracy": true,
  "enable_toxicity": true,
  "enable_answer_relevancy": true
}
```

**For Quality** (< 2s):
```json
{
  "enable_llm_as_judge": true,
  "enable_hallucination": true,
  "enable_faithfulness": true
}
```

**For Comprehensive** (< 5s):
```json
{
  "enable_ragas": true,
  "enable_llm_as_judge": true,
  "enable_deepeval": true,
  "enable_all_safety_metrics": true
}
```

---

## Best Practices

### 1. Start with Baseline Metrics

Enable these by default:
- ✅ Citation Accuracy
- ✅ Answer Relevancy
- ✅ Toxicity Detection
- ✅ Hallucination Detection

### 2. Progressive Enhancement

1. **Week 1**: Baseline metrics + monitoring
2. **Week 2**: Add LLM-as-a-Judge for quality insights
3. **Week 3**: Enable RAGAS if you have ground truth
4. **Week 4**: Fine-tune based on analytics

### 3. Use Auto-Evaluation Wisely

- **Development**: 100% sampling
- **Staging**: 50% sampling
- **Production**: 10-20% sampling
- Monitor cost vs. insights tradeoff

### 4. Monitor Performance

Track these metrics:
- Evaluation time (should be < 2s)
- Cache hit rate (target: > 50%)
- Error rate (target: < 1%)
- Score trends over time

### 5. Human Feedback Loop

- Collect thumbs up/down on all responses
- Detailed feedback on low-scoring responses
- Use feedback to improve retrieval and generation

### 6. Benchmark Regularly

- Create benchmark dataset
- Run comprehensive evaluation monthly
- Track score trends
- Identify regressions early

---

## Advanced Features

### 1. Custom Evaluation Methods

Add your own evaluators:

```python
async def _evaluate_custom_metric(
    self,
    query: str,
    response: str,
    context_chunks: List[Dict]
) -> Dict[str, Any]:
    """Custom evaluation logic"""
    # Your evaluation code
    score = calculate_custom_score(query, response)

    return {
        'method': 'custom_metric',
        'scores': {
            'custom_score': score
        }
    }
```

### 2. Weighted Scoring

Customize overall score calculation:

```python
weights = {
    'ragas': 0.3,
    'llm_as_judge': 0.3,
    'answer_relevancy': 0.2,
    'faithfulness': 0.2
}
```

### 3. Threshold Alerts

Set up alerts for low scores:

```python
if overall_score < config.min_score_threshold:
    # Trigger alert
    send_alert(f"Low quality response: {overall_score}")
```

### 4. A/B Testing

Compare evaluation configurations:

```python
# Config A: Lightweight
config_a = EvaluationConfig(enabled_methods=[...])

# Config B: Comprehensive
config_b = EvaluationConfig(enabled_methods=[...])

# Compare results
compare_configs(config_a, config_b, test_queries)
```

### 5. Evaluation Benchmarks

Create benchmark datasets:

```sql
INSERT INTO evaluation_benchmarks (query, ground_truth_answer, context_chunks, dataset_name)
VALUES (
  'What is RAG?',
  'RAG stands for Retrieval-Augmented Generation...',
  '[{"content": "..."}]',
  'internal_qa'
);
```

---

## Troubleshooting

### Issue: Evaluation Too Slow

**Solutions**:
1. Disable heavy methods (RAGAS, DeepEval)
2. Enable caching
3. Use async evaluation
4. Reduce sampling rate

### Issue: Low Cache Hit Rate

**Solutions**:
1. Increase cache TTL
2. Check cache key generation
3. Monitor query diversity

### Issue: High Error Rate

**Solutions**:
1. Check API keys (LLM-as-a-Judge)
2. Install required libraries
3. Review error logs
4. Increase timeout settings

### Issue: Unexpected Scores

**Solutions**:
1. Review evaluation method descriptions
2. Check ground truth quality
3. Validate context relevance
4. Use LLM-as-a-Judge for interpretability

---

## Next Steps

1. **Install Dependencies**:
   ```bash
   pip install -r requirements-evaluation.txt  # Optional
   ```

2. **Run Migration**:
   ```bash
   psql -U postgres -d ragchatbot -f backend/migrations/001_add_evaluation_tables.sql
   ```

3. **Configure via UI**:
   - Open app → Settings → Evaluation
   - Enable desired methods
   - Save configuration

4. **Monitor Dashboard**:
   - View real-time analytics
   - Track score trends
   - Identify issues

5. **Iterate and Improve**:
   - Collect feedback
   - Adjust configurations
   - Benchmark regularly

---

## Resources

- [RAGAS Documentation](https://docs.ragas.io/)
- [DeepEval Documentation](https://docs.confident-ai.com/)
- [BERTScore Paper](https://arxiv.org/abs/1904.09675)
- [LLM-as-a-Judge Best Practices](https://arxiv.org/abs/2306.05685)

---

**Questions or Issues?**

- Check [STATUS.md](STATUS.md) for current status
- Review [CLAUDE.md](CLAUDE.md) for development guide
- Open an issue on GitHub

---

**Last Updated**: 2025-11-14
**Version**: 1.0.0
