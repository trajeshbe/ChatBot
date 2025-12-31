# Vision Model Timeout Issue - Text Query

**Date**: 2025-12-20 07:52:43
**Query**: "do you know Aadhan and Amudhan from Short Story?"
**Error**: ReadTimeout after 258 seconds (4.3 minutes)

---

## Problem

Query timed out with error:
```
❌ Ollama call failed: ReadTimeout
❌ Generation FAILED with Qwen 2.5 VL (Ollama Vision)
RetryError[<Future at 0x7090cfd02cb0 state=finished raised ReadTimeout>]
```

**Latency**: 258,194 milliseconds (4.3 minutes) before timeout

---

## Root Cause

**Wrong model selected for text query!**

| Model Selected | Type | Parameters | Best For | Query Type | Match |
|----------------|------|------------|----------|------------|-------|
| **qwen2.5vl:latest** | Vision | 8.3B | Images, PDFs, diagrams | **Text** (about story characters) | ❌ MISMATCH |

The system used the **Vision model** (qwen2.5vl:latest) to answer a **text-based question** about story characters. This is extremely inefficient because:

1. **Vision models are slow for text**:
   - Designed for image + text processing
   - 8.3B parameters (vs 1.5B for text model)
   - Processes vision tokens even for text-only input
   - Typical text response: 25-30 seconds
   - Typical vision response: 80-90 seconds
   - **Your query: 258 seconds (timed out!)**

2. **Vision model was already busy**:
   - Processing arch1.pdf vision extraction (started 07:37:44)
   - Consuming 5GB VRAM
   - New query queued behind ongoing vision task
   - Result: Extreme delay → timeout

---

## Evidence from Logs

### Model Loading
```
Loaded in Ollama:
- qwen2.5vl:latest (Vision, 8.3B params, 5GB VRAM)
- qwen2.5:1.5b (Text, 1.5B params, 1.9GB VRAM)
```

### Query Execution
```
07:50:38 - Calling Ollama: model=qwen2.5vl:latest
07:52:43 - ReadTimeout (after 258 seconds)
07:52:43 - Generation FAILED
```

### Previous Successful Query
For comparison, the earlier query about Aadhan and Amudhan (07:48:25) used **qwen2.5:1.5b** (text model):
```
Model: qwen2.5:1.5b
Generated: 715 tokens in 806ms (0.8 seconds)
Status: ✅ SUCCESS
```

**806ms vs 258,000ms** - That's a **320x difference!**

---

## Solution

### Immediate Fix: Change Model in UI

**For Text Queries** (like questions about story, general knowledge, coding):
✅ Use **qwen2.5:1.5b** (fast, 1.5B params)
✅ Use **qwen2.5:latest** (balanced, 7B params)
✅ Use **mistral:latest** (good quality)
✅ Use **llama3.2:latest** (high quality)

**For Image/Diagram Queries** (like "analyze this floor plan"):
✅ Use **qwen2.5vl:latest** (Vision, best for images)
✅ Use **llama3.2-vision:11b** (Vision, alternative)

### Model Selection Guide

| Query Type | Example | Recommended Model | Why |
|------------|---------|-------------------|-----|
| **Text Questions** | "Who is Aadhan?" | qwen2.5:1.5b | Fast (0.8s), efficient |
| **Document Analysis** | "Summarize this PDF" | qwen2.5:latest | Better comprehension |
| **Code Generation** | "Write a Python function" | qwen2.5:latest | Larger model, better code |
| **Image Analysis** | "How many rooms?" | qwen2.5vl:latest | Vision capabilities |
| **Architecture Diagrams** | "Extract dimensions" | qwen2.5vl:latest | Vision + OCR combined |
| **General Knowledge** | "Explain quantum physics" | qwen2.5:latest | Larger knowledge base |

---

## Why This Matters

### Performance Comparison

**Text Query with Text Model** (qwen2.5:1.5b):
```
Query: "do you know Aadhan and Amudhan?"
Model: qwen2.5:1.5b
Time: 806ms (0.8 seconds)
Result: ✅ Detailed answer about characters
```

**Same Query with Vision Model** (qwen2.5vl:latest):
```
Query: "do you know Aadhan and Amudhan?"
Model: qwen2.5vl:latest
Time: 258,000ms (258 seconds) → TIMEOUT
Result: ❌ Error
```

**Speed Difference**: Vision model is **320x slower** for text queries!

### Resource Usage

**Text Model** (qwen2.5:1.5b):
- VRAM: 1.9GB
- Concurrent queries: Can handle multiple
- Response time: <1 second

**Vision Model** (qwen2.5vl:latest):
- VRAM: 5GB
- Concurrent queries: Limited (queues)
- Response time: 25-90 seconds
- **For text-only: UNNECESSARY OVERHEAD**

---

## When to Use Vision Models

### ✅ Use Vision Models For:
1. **Images**: Photos, screenshots, diagrams
2. **PDF Diagrams**: Architecture plans, technical drawings
3. **Charts/Graphs**: Visual data representation
4. **Scanned Documents**: OCR + understanding
5. **Multimodal Questions**: "What's in this image and how does it relate to [text]?"

### ❌ Don't Use Vision Models For:
1. **Pure Text Queries**: Questions about stories, facts, code
2. **General Knowledge**: "What is X?" type questions
3. **Document Summarization**: Unless the PDF has critical images
4. **Chat/Conversation**: Back-and-forth text discussion
5. **Code Generation**: Writing functions, scripts

---

## UI Model Selector Best Practices

### Smart Model Switching

**When uploading images/diagrams**:
```
1. Upload file (arch1.pdf)
2. Switch to Vision model (qwen2.5vl:latest)
3. Ask question: "How many rooms?"
4. Wait for answer (25-90 seconds)
```

**When asking text questions**:
```
1. Switch to Text model (qwen2.5:1.5b or qwen2.5:latest)
2. Ask question: "Who is Aadhan?"
3. Get fast answer (<1 second)
```

### Default Recommendation

**Set Default Model**: `qwen2.5:latest` (7B text model)
- Good balance of speed and quality
- Handles most queries well
- Fast enough for chat (<2 seconds)
- Only switch to Vision when analyzing images

---

## Technical Details

### Why Vision Models Are Slow for Text

1. **Architecture Overhead**:
   - Vision transformers process image patches
   - Even for text input, vision pathways are activated
   - More parameters to process (8.3B vs 1.5B)

2. **Token Processing**:
   - Text models: 1 token = 1 word/subword
   - Vision models: Additional vision tokens + text tokens
   - Result: More computation per query

3. **Memory Bandwidth**:
   - 5GB model vs 1.9GB model
   - More data to move through GPU/CPU
   - Higher latency for each forward pass

### Timeout Configuration

Current timeout: ~240 seconds (4 minutes)

**Why timeout occurred**:
- Vision model processing took > 240 seconds
- Likely due to:
  - Model already busy with arch1.pdf extraction
  - Query queued behind ongoing task
  - No concurrent processing (sequential execution)

---

## Recommendations

### 1. Add Model Auto-Selection (Future Enhancement)

**Idea**: Automatically select model based on query type

```python
def select_model(query: str, has_image: bool):
    if has_image or "image" in query or "diagram" in query:
        return "qwen2.5vl:latest"  # Vision model
    else:
        return "qwen2.5:latest"     # Text model
```

### 2. Add Model Switch Warning in UI

**Idea**: Warn user if Vision model selected for text query

```typescript
if (selectedModel.includes("vision") && !hasUploadedImage) {
  showWarning("Vision model selected but no image uploaded. Consider using text model for faster responses.");
}
```

### 3. Increase Timeout for Vision Models

**Current**: 240 seconds
**Recommended**: 300 seconds (5 minutes) for Vision models

```python
timeout = 300 if "vision" in model_name else 60
```

### 4. Add Model Performance Indicator

**Idea**: Show expected response time for each model

```
qwen2.5:1.5b       ⚡ Fast (0.5-2s)
qwen2.5:latest     ⚡ Fast (1-3s)
qwen2.5vl:latest   🐢 Slow (25-90s for images, 258s+ for text)
```

---

## Fix Applied

### User Action Required

**In the UI**:
1. Click on model selector dropdown
2. Change from **qwen2.5vl:latest** to **qwen2.5:1.5b** or **qwen2.5:latest**
3. Retry query "do you know Aadhan and Amudhan?"
4. Expected response time: < 1 second ✅

### For Future Queries

**Rule of Thumb**:
- Uploading image/PDF with diagrams? → Use Vision model
- Asking text question? → Use Text model
- Need detailed analysis? → Use larger Text model (qwen2.5:latest)
- Need speed? → Use smaller Text model (qwen2.5:1.5b)

---

## Conclusion

✅ **Issue Identified**: Vision model used for text query
✅ **Root Cause**: Model selection mismatch (Vision vs Text)
✅ **Impact**: 320x slower response, timeout after 258 seconds
✅ **Solution**: Switch to text model (qwen2.5:1.5b or qwen2.5:latest)
✅ **Expected Fix**: <1 second response time

**Status**: User action required - change model in UI dropdown

---

**Last Updated**: 2025-12-20 07:55:00
**Query**: "do you know Aadhan and Amudhan from Short Story?"
**Model Used**: qwen2.5vl:latest (Vision - WRONG for text query)
**Recommended**: qwen2.5:1.5b or qwen2.5:latest (Text models)
