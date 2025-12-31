# GPU Models - Quick Start 🚀

**Your GPU**: NVIDIA GeForce RTX 5060 (8GB VRAM)
**Status**: ✅ GPU Enabled in Ollama
**Updated**: November 2025 (Latest Leaderboard Rankings)

---

## 🏆 Top 5 Models (November 2025)

Based on **Hugging Face**, **LMSys Chatbot Arena**, and **Vellum LLM Leaderboard 2025**.

### 🥇 #1 Recommended: Llama 3.1 8B (BEST FOR RAG)
```bash
docker-compose exec ollama ollama pull llama3.1:8b
```
**VRAM**: 4.7GB | **Speed**: 60-70 tok/s | **Best for**: RAG, summarization, general tasks

> **⚠️ Note**: Use simple model names without quantization suffix. Ollama handles Q4_K_M quantization automatically.

### Quick Commands

**Check GPU Status**:
```bash
docker-compose exec ollama nvidia-smi
```

**Pull Top Model**:
```bash
# #1 Ranked for RAG applications (November 2025)
docker-compose exec ollama ollama pull llama3.1:8b
```

**Test GPU Inference**:
```bash
docker-compose exec ollama ollama run llama3.1:8b \
  "Explain RAG in 2 sentences."

# Monitor GPU memory
docker-compose exec ollama nvidia-smi
```

---

## Model Comparison (November 2025 Rankings)

| Rank | Model | Ollama Name | VRAM | Speed | Best For |
|------|-------|-------------|------|-------|----------|
| 🥇 | Llama 3.1 8B | `llama3.1:8b` | 4.7GB | 60-70 tok/s | General, RAG ⭐⭐⭐⭐⭐ |
| 🥈 | Qwen 2.5 7B | `qwen2.5:7b` | 4.4GB | 65-75 tok/s | Dialogue, Multilingual ⭐⭐⭐⭐⭐ |
| 🥉 | DeepSeek Coder 6.7B | `deepseek-coder:6.7b` | 4.0GB | 70-80 tok/s | Coding, Logic ⭐⭐⭐⭐⭐ |
| ⚡ | Mistral 7B | `mistral:7b` | 4.1GB | 80-90 tok/s | Speed, Fast inference ⭐⭐⭐⭐ |
| 🚀 | Ministral 8B | `ministral:8b` | 4.5GB | 65-75 tok/s | Edge, Efficiency ⭐⭐⭐⭐⭐ |

---

## Expected Performance Boost

**Current (CPU)**:
- llama3.2:3b → ~15 tokens/sec

**After GPU Setup**:
- llama3.1:8b → **~60 tokens/sec** (4x faster, 2.6x larger model!)
- phi3.5:3.8b → **~120 tokens/sec** (8x faster!)

**Correct model names**: `llama3.1:8b`, `mistral:7b` (NOT `llama3.2:8b-instruct-q4_K_M`)

---

## Quick Test After Setup

```bash
# 1. Verify GPU accessible
docker-compose exec ollama nvidia-smi

# 2. List models
docker-compose exec ollama ollama list

# 3. Test via API
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is RAG?" \
  -F "model_id=ollama/llama3.1:8b"
```

---

## Full Guide
See `docs/setup/GPU_MODELS_SETUP.md` for complete documentation.