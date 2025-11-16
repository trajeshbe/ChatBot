# Evaluation Documentation

RAG system evaluation guides, metrics, benchmarking, and improvement documentation.

## 📖 Available Guides

### [EVALUATION_GUIDE.md](./EVALUATION_GUIDE.md)
Comprehensive guide to evaluating the RAG system.
- Evaluation frameworks (RAGAS)
- Metrics explanation
- Benchmarking methodology
- Result interpretation

### [EVALUATION_QUICK_REFERENCE.md](./EVALUATION_QUICK_REFERENCE.md)
Quick reference for running evaluations.
- Quick evaluation commands
- Key metrics summary
- Common evaluation tasks
- Performance baselines

### [RAG_EVALUATION_AND_IMPROVEMENTS.md](./RAG_EVALUATION_AND_IMPROVEMENTS.md)
Detailed analysis and improvement recommendations.
- Current system evaluation
- Performance analysis
- Improvement roadmap
- Implementation priorities

### [RAG_EVALUATION_ARCHITECTURE.md](./RAG_EVALUATION_ARCHITECTURE.md)
Architecture for the evaluation system.
- Evaluation pipeline design
- Metrics collection
- Automated testing
- Continuous evaluation

---

## 📊 Key Evaluation Metrics

### RAGAS Metrics

1. **Faithfulness** (0-1)
   - Measures factual consistency with source documents
   - Target: > 0.8

2. **Answer Relevancy** (0-1)
   - Measures relevance of answer to question
   - Target: > 0.7

3. **Context Precision** (0-1)
   - Measures relevance of retrieved context
   - Target: > 0.7

4. **Context Recall** (0-1)
   - Measures comprehensiveness of context retrieval
   - Target: > 0.8

### Performance Metrics

- **Latency**: Query response time
- **Throughput**: Queries per second
- **Token Usage**: LLM token consumption
- **Retrieval Accuracy**: Top-K accuracy

---

## 🧪 Running Evaluations

### Quick Evaluation
```bash
# Run basic evaluation
cd backend
python -m app.evaluation.run_evaluation

# View results
cat evaluation_results.json
```

### Comprehensive Evaluation
```bash
# Run full RAGAS evaluation
../../scripts/testing/test_rag_validation.py

# Or simplified version
../../scripts/testing/test_rag_validation_simple.py
```

### Performance Testing
```bash
# Test query performance
../../scripts/testing/test-integration.sh

# Test with different K values
../../scripts/testing/test-slider-real-time.sh
```

---

## 📈 Improvement Areas

Based on evaluations, focus areas include:

1. **Retrieval Quality**
   - Hybrid search (BM25 + Vector)
   - Query expansion
   - Reranking

2. **Context Management**
   - Chunk size optimization
   - Overlap strategies
   - Metadata filtering

3. **LLM Optimization**
   - Prompt engineering
   - Temperature tuning
   - Model selection

4. **Performance**
   - Caching strategies
   - Async processing
   - Batch operations

---

## 🔗 Related Documentation

- **Architecture**: [../architecture/MEMORY_HIERARCHY_GUIDE.md](../architecture/MEMORY_HIERARCHY_GUIDE.md)
- **Debugging**: [../debugging/RAG_DEBUGGING_GUIDE.md](../debugging/RAG_DEBUGGING_GUIDE.md)
- **Testing**: [../../scripts/testing/](../../scripts/testing/)

---

**Last Updated**: 2025-11-16
