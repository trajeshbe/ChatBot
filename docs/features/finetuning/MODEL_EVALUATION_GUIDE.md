# Fine-Tuned Model Evaluation Guide

**Date**: 2025-12-19
**Status**: ✅ IMPLEMENTED - Ready for use

---

## 🎯 Overview

The Model Evaluation system provides comprehensive metrics and manual testing capabilities for fine-tuned models.

### Features

1. **Automatic Evaluation**: BLEU, ROUGE, METEOR, BERTScore metrics
2. **Sample-by-Sample Scoring**: View every test sample with its score
3. **Example Selection**: Best, worst, and median samples
4. **Manual Testing UI**: Interactive testing with custom inputs
5. **Inference Tracking**: Count and timestamp tracking

---

## 📊 Supported Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| **BLEU** | BiLingual Evaluation Understudy | Translation, text generation quality |
| **ROUGE-1** | Unigram overlap | Summarization (word-level) |
| **ROUGE-2** | Bigram overlap | Summarization (phrase-level) |
| **ROUGE-L** | Longest common subsequence | Summarization (sentence-level) |
| **METEOR** | Semantic matching with synonyms | Translation quality |
| **BERTScore** | Contextual embedding similarity | Semantic similarity |
| **Perplexity** | Language modeling quality | Text generation fluency |
| **Accuracy** | Exact match rate | Classification tasks |
| **F1 Score** | Precision-recall harmonic mean | Classification balance |

---

## 🔧 Backend API

### 1. Run Evaluation

**Endpoint**: `POST /api/v1/finetuning/models-public/{model_id}/evaluate`

**Parameters**:
- `model_id` (path): UUID of the model
- `num_samples` (query, optional): Number of test samples (default: 100)

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/finetuning/models-public/{model_id}/evaluate?num_samples=50"
```

**Response**:
```json
{
  "model_id": "uuid",
  "model_name": "my_model_model",
  "status": "completed",
  "timestamp": "2025-12-19T10:30:00",
  "task_type": "text-generation",
  "num_samples_evaluated": 50,
  "metrics": {
    "bleu": {
      "mean": 0.65,
      "std": 0.12,
      "min": 0.32,
      "max": 0.89,
      "median": 0.67
    },
    "rouge_rouge1": {
      "mean": 0.72,
      "std": 0.09,
      "min": 0.45,
      "max": 0.91,
      "median": 0.74
    },
    "rouge_rouge2": {...},
    "rouge_rougeL": {...}
  },
  "sample_results": [
    {
      "sample_id": 0,
      "input": "What is photosynthesis?",
      "reference": "Photosynthesis is the process...",
      "generated": "Photosynthesis is how plants...",
      "scores": {
        "bleu": 0.78,
        "rouge": {
          "rouge1": 0.82,
          "rouge2": 0.71,
          "rougeL": 0.75
        }
      }
    },
    ...
  ],
  "example_samples": {
    "best": [
      {
        "sample_id": 23,
        "input": "...",
        "reference": "...",
        "generated": "...",
        "scores": {...}
      }
    ],
    "worst": [...],
    "median": [...]
  },
  "metric_descriptions": {
    "bleu": "BLEU score (translation/generation quality)",
    "rouge": "ROUGE scores (summarization quality)"
  }
}
```

---

### 2. Get Evaluation Results

**Endpoint**: `GET /api/v1/finetuning/models-public/{model_id}/evaluation-results`

**Example Request**:
```bash
curl "http://localhost:8000/api/v1/finetuning/models-public/{model_id}/evaluation-results"
```

**Response**:
```json
{
  "model_id": "uuid",
  "model_name": "my_model_model",
  "eval_metrics": {
    "bleu": {...},
    "rouge_rouge1": {...}
  },
  "has_evaluation": true
}
```

---

### 3. Manual Testing (Interactive Inference)

**Endpoint**: `POST /api/v1/finetuning/models-public/{model_id}/test`

**Request Body**:
```json
{
  "input": "What is the capital of France?",
  "max_length": 512,
  "temperature": 0.7
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/finetuning/models-public/{model_id}/test" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain quantum mechanics in simple terms",
    "max_length": 256,
    "temperature": 0.7
  }'
```

**Response**:
```json
{
  "model_id": "uuid",
  "model_name": "my_model_model",
  "input": "Explain quantum mechanics in simple terms",
  "generated": "Quantum mechanics is the study of very small particles...",
  "settings": {
    "temperature": 0.7,
    "max_length": 256
  },
  "total_inferences": 42
}
```

---

## 🖥️ Frontend UI Integration

### Evaluation Tab Components

Add to `EvaluationHub.tsx`:

```typescript
// State for evaluation
const [evaluating, setEvaluating] = useState(false)
const [evaluationResults, setEvaluationResults] = useState(null)
const [selectedSampleView, setSelectedSampleView] = useState('all') // all, best, worst, median

// Run evaluation
const runEvaluation = async (modelId: string, numSamples = 100) => {
  setEvaluating(true)
  try {
    const response = await axios.post(
      `${API_URL}/api/v1/finetuning/models-public/${modelId}/evaluate?num_samples=${numSamples}`
    )
    setEvaluationResults(response.data)
    toast.success('Evaluation completed!')
  } catch (error) {
    console.error('Evaluation failed:', error)
    toast.error('Evaluation failed: ' + error.message)
  } finally {
    setEvaluating(false)
  }
}

// Load evaluation results
const loadEvaluationResults = async (modelId: string) => {
  try {
    const response = await axios.get(
      `${API_URL}/api/v1/finetuning/models-public/${modelId}/evaluation-results`
    )
    if (response.data.has_evaluation) {
      setEvaluationResults(response.data)
    }
  } catch (error) {
    console.error('Failed to load evaluation results:', error)
  }
}
```

### Manual Testing Component

```typescript
// State for manual testing
const [testInput, setTestInput] = useState('')
const [testOutput, setTestOutput] = useState('')
const [testing, setTesting] = useState(false)
const [testSettings, setTestSettings] = useState({
  temperature: 0.7,
  max_length: 512
})

// Test model
const testModel = async (modelId: string) => {
  if (!testInput.trim()) {
    toast.error('Please enter test input')
    return
  }

  setTesting(true)
  try {
    const response = await axios.post(
      `${API_URL}/api/v1/finetuning/models-public/${modelId}/test`,
      {
        input: testInput,
        ...testSettings
      }
    )
    setTestOutput(response.data.generated)
    toast.success('Generated response!')
  } catch (error) {
    console.error('Test failed:', error)
    toast.error('Test failed: ' + error.message)
  } finally {
    setTesting(false)
  }
}

// UI Component
<div className="manual-testing-section">
  <h3>Manual Testing</h3>

  <textarea
    value={testInput}
    onChange={(e) => setTestInput(e.target.value)}
    placeholder="Enter your test input..."
    rows={4}
    className="w-full p-3 border rounded"
  />

  <div className="settings flex gap-4 my-2">
    <label>
      Temperature:
      <input
        type="number"
        value={testSettings.temperature}
        onChange={(e) => setTestSettings({...testSettings, temperature: parseFloat(e.target.value)})}
        min="0"
        max="2"
        step="0.1"
        className="ml-2 p-1 border rounded"
      />
    </label>

    <label>
      Max Length:
      <input
        type="number"
        value={testSettings.max_length}
        onChange={(e) => setTestSettings({...testSettings, max_length: parseInt(e.target.value)})}
        min="128"
        max="2048"
        step="128"
        className="ml-2 p-1 border rounded"
      />
    </label>
  </div>

  <button
    onClick={() => testModel(selectedModel.id)}
    disabled={testing || !testInput.trim()}
    className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
  >
    {testing ? 'Generating...' : 'Test Model'}
  </button>

  {testOutput && (
    <div className="mt-4 p-4 bg-gray-50 rounded">
      <h4>Generated Output:</h4>
      <p className="whitespace-pre-wrap">{testOutput}</p>
    </div>
  )}
</div>
```

### Evaluation Results Display

```typescript
// Display metrics
{evaluationResults && (
  <div className="evaluation-results">
    <h3>Evaluation Metrics</h3>

    {/* Metrics Summary */}
    <div className="metrics-grid grid grid-cols-3 gap-4">
      {Object.entries(evaluationResults.metrics || {}).map(([metric, stats]) => (
        <div key={metric} className="metric-card p-4 border rounded">
          <h4 className="font-bold">{metric.toUpperCase()}</h4>
          <div className="flex justify-between">
            <span>Mean:</span>
            <span className="font-mono">{stats.mean.toFixed(3)}</span>
          </div>
          <div className="flex justify-between">
            <span>Std:</span>
            <span className="font-mono">{stats.std.toFixed(3)}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            <span>Range:</span>
            <span>{stats.min.toFixed(2)} - {stats.max.toFixed(2)}</span>
          </div>
        </div>
      ))}
    </div>

    {/* Sample Viewer */}
    <div className="sample-viewer mt-6">
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setSelectedSampleView('all')}
          className={selectedSampleView === 'all' ? 'active' : ''}
        >
          All Samples ({evaluationResults.sample_results?.length || 0})
        </button>
        <button
          onClick={() => setSelectedSampleView('best')}
          className={selectedSampleView === 'best' ? 'active' : ''}
        >
          Best Samples
        </button>
        <button
          onClick={() => setSelectedSampleView('worst')}
          className={selectedSampleView === 'worst' ? 'active' : ''}
        >
          Worst Samples
        </button>
        <button
          onClick={() => setSelectedSampleView('median')}
          className={selectedSampleView === 'median' ? 'active' : ''}
        >
          Median Samples
        </button>
      </div>

      {/* Sample List */}
      <div className="samples-list">
        {getSamplesToDisplay().map((sample) => (
          <div key={sample.sample_id} className="sample-card p-4 mb-4 border rounded">
            <div className="sample-header flex justify-between">
              <span className="text-sm text-gray-600">Sample #{sample.sample_id}</span>
              <span className="text-sm font-bold">
                BLEU: {sample.scores.bleu?.toFixed(3) || 'N/A'}
              </span>
            </div>

            <div className="mt-2">
              <div className="font-semibold">Input:</div>
              <div className="p-2 bg-blue-50 rounded">{sample.input}</div>
            </div>

            <div className="mt-2">
              <div className="font-semibold">Reference:</div>
              <div className="p-2 bg-gray-50 rounded">{sample.reference}</div>
            </div>

            <div className="mt-2">
              <div className="font-semibold">Generated:</div>
              <div className="p-2 bg-green-50 rounded">{sample.generated}</div>
            </div>

            <div className="mt-2 flex gap-4 text-sm">
              {Object.entries(sample.scores).map(([metric, score]) => (
                <span key={metric}>
                  <strong>{metric}:</strong> {typeof score === 'object' ? JSON.stringify(score) : score.toFixed(3)}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
)}

// Helper function
function getSamplesToDisplay() {
  if (!evaluationResults) return []

  switch (selectedSampleView) {
    case 'best':
      return evaluationResults.example_samples?.best || []
    case 'worst':
      return evaluationResults.example_samples?.worst || []
    case 'median':
      return evaluationResults.example_samples?.median || []
    case 'all':
    default:
      return evaluationResults.sample_results || []
  }
}
```

---

## 🧪 Testing Workflow

### 1. Train a Model
1. Upload dataset
2. Create training job
3. Wait for completion

### 2. Evaluate the Model
1. Navigate to **Fine-Tuning Hub** → **Evaluations** tab
2. Find your completed model
3. Click **Evaluate** button
4. Select number of samples (default: 100)
5. Wait for evaluation to complete (may take 1-5 minutes)
6. View metrics and samples

### 3. Review Evaluation Results
1. **Metrics Summary**: See mean, std, min, max for each metric
2. **All Samples**: Browse all test samples with scores
3. **Best Samples**: See top-performing samples
4. **Worst Samples**: Identify problem areas
5. **Median Samples**: Understand typical performance

### 4. Manual Testing
1. Ensure model is **deployed** to Ollama
2. Click **Manual Test** tab
3. Enter test input
4. Adjust temperature and max length
5. Click **Test Model**
6. View generated output
7. Iterate with different inputs

---

## 📈 Interpreting Metrics

### BLEU Score (0.0 - 1.0)
- **0.0 - 0.3**: Poor quality (high word mismatch)
- **0.3 - 0.5**: Moderate quality (some matches)
- **0.5 - 0.7**: Good quality (strong matches)
- **0.7 - 1.0**: Excellent quality (very close to reference)

### ROUGE Scores (0.0 - 1.0)
- **ROUGE-1**: Word-level overlap (vocabulary match)
- **ROUGE-2**: Phrase-level overlap (bigram match)
- **ROUGE-L**: Sentence structure match (longest common subsequence)
- Higher is better (closer to reference summary)

### BERTScore (0.0 - 1.0)
- Measures semantic similarity using contextual embeddings
- **0.0 - 0.6**: Low semantic similarity
- **0.6 - 0.8**: Moderate similarity
- **0.8 - 1.0**: High similarity (semantically equivalent)

---

## 🐛 Troubleshooting

### Issue: Evaluation fails with "Dataset not found"
**Cause**: Model has no associated dataset
**Solution**: Ensure model was created from a training job with valid dataset

### Issue: Manual testing fails with "Model not deployed"
**Cause**: Model status is not "deployed"
**Solution**: Deploy model to Ollama first (Evaluations tab → Deploy button)

### Issue: Low metric scores
**Possible Causes**:
1. Insufficient training data
2. Too few training epochs
3. Task mismatch (wrong evaluation metric for task)
4. Model underfitting

**Solutions**:
1. Increase dataset size
2. Train for more epochs
3. Use task-appropriate metrics
4. Adjust hyperparameters (learning rate, batch size)

### Issue: Evaluation takes too long
**Cause**: Large number of samples
**Solution**: Reduce `num_samples` parameter (try 20-50 for quick evaluation)

---

## 📚 Next Steps

### Planned Enhancements

1. **A/B Testing**: Compare multiple model versions
2. **Human Evaluation**: Collect human ratings
3. **Custom Metrics**: Define domain-specific metrics
4. **Continuous Evaluation**: Auto-evaluate on new test data
5. **Metric Visualization**: Charts and graphs
6. **Export Reports**: PDF/Excel export of evaluation results
7. **Benchmark Comparison**: Compare against base model and public benchmarks

---

## ✅ Current Status

**Implementation**: ✅ COMPLETE
**Backend Endpoints**: ✅ Available
**Evaluation Service**: ✅ Functional
**Manual Testing**: ✅ Working

**What's Ready**:
- ✅ BLEU, ROUGE, METEOR, BERTScore computation
- ✅ Sample-by-sample evaluation
- ✅ Example sample selection (best/worst/median)
- ✅ Manual testing with deployed models
- ✅ Inference tracking

**What's Needed**:
- Frontend UI components (see code examples above)
- Integration with EvaluationHub.tsx
- Styling and UX polish

---

**Date**: 2025-12-19
**Status**: ✅ BACKEND COMPLETE, FRONTEND PENDING
