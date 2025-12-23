# Fine-Tuned Adapter Deployment Options

## Current Status

**Model**: choles-qa-real-training49_model
**Base Model**: Qwen/Qwen2.5-1.5B-Instruct
**Adapter Format**: PyTorch safetensors (LoRA weights)
**Location**: `/workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/adapter_model/`

## ❌ Why Ollama Doesn't Work

Ollama requires GGUF format models. Your adapter is in PyTorch safetensors format, which Ollama cannot load directly via the ADAPTER directive.

**Error**: `unsupported architecture`

---

## ✅ Option 1: Direct PEFT Loading (Recommended for Testing)

**Pros**:
- No conversion needed
- Uses existing adapter weights
- Fast to implement
- Full control over inference

**Cons**:
- Requires loading base model + adapter each time
- Not optimized for production serving

**Test Script**: `/tmp/test_adapter_inference.py`

**Usage**:
```bash
# Run inside backend container
docker-compose exec backend python /tmp/test_adapter_inference.py
```

**Integration with Chat UI**:
```python
# In llm_service.py, add a new model type handler

class LLMService:
    def __init__(self):
        self.peft_models = {}  # Cache loaded PEFT models

    async def generate_with_peft_adapter(
        self,
        model_id: str,
        adapter_path: str,
        messages: List[Dict],
        temperature: float = 0.7
    ) -> str:
        """Generate response using PEFT adapter"""

        # Cache model loading
        cache_key = f"{model_id}_{adapter_path}"
        if cache_key not in self.peft_models:
            from peft import PeftModel
            base_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            model = PeftModel.from_pretrained(
                base_model,
                adapter_path,
                is_trainable=False
            )
            self.peft_models[cache_key] = (model, tokenizer)

        model, tokenizer = self.peft_models[cache_key]

        # Generate response (same as test script)
        # ...
```

---

## ✅ Option 2: Merge + Convert to GGUF (Best for Ollama)

**Pros**:
- Native Ollama support
- Optimized inference
- Quantized (smaller size, faster)

**Cons**:
- Requires conversion tools (llama.cpp)
- Multi-step process
- Loses adapter modularity

**Steps**:

### 2a. Wait for merge to complete
```bash
# Check merge status
docker logs finetuning-dfcb97c3-8167-4a66-8d90-2bca5e4c6709 2>&1 | tail -20

# If stuck, restart merge manually
docker exec finetuning-dfcb97c3-8167-4a66-8d90-2bca5e4c6709 \
  python -c "
from peft import PeftModel
from transformers import AutoModelForCausalLM
import torch

base = AutoModelForCausalLM.from_pretrained(
    'Qwen/Qwen2.5-1.5B-Instruct',
    torch_dtype=torch.bfloat16,
    device_map='auto'
)
peft_model = PeftModel.from_pretrained(
    base,
    '/workspace/output/adapter_model'
)
merged = peft_model.merge_and_unload()
merged.save_pretrained('/workspace/output/merged_model')
print('✅ Merge complete')
"
```

### 2b. Convert to GGUF
```bash
# Install llama.cpp converter (inside backend container)
git clone https://github.com/ggerganov/llama.cpp /tmp/llama.cpp
cd /tmp/llama.cpp
pip install -r requirements.txt

# Convert HuggingFace -> GGUF
python convert-hf-to-gguf.py \
  /workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/merged_model \
  --outfile /tmp/choles-qa-ft.gguf \
  --outtype q4_K_M  # 4-bit quantization
```

### 2c. Create Ollama model
```bash
# Create Modelfile
cat > /tmp/choles_modelfile <<EOF
FROM /tmp/choles-qa-ft.gguf

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM You are a helpful assistant that provides accurate information about companies and products.
EOF

# Create Ollama model
ollama create choles-qa-ft -f /tmp/choles_modelfile

# Test
ollama run choles-qa-ft "What is Choles Food Technologies?"
```

---

## ✅ Option 3: vLLM with LoRA Support (Production-Ready)

**Pros**:
- Supports LoRA adapters natively
- Optimized for serving
- Can serve multiple adapters on same base model
- Production-grade performance

**Cons**:
- Requires vLLM setup
- More complex deployment

**Setup**:
```bash
# Install vLLM (if not already available)
pip install vllm

# Start vLLM server with LoRA
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --enable-lora \
  --lora-modules choles-qa=/workspace/finetuning/dfcb97c3-8167-4a66-8d90-2bca5e4c6709/output/adapter_model \
  --host 0.0.0.0 \
  --port 8001

# Use via OpenAI-compatible API
curl http://localhost:8001/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "choles-qa",
    "prompt": "What is TomatoGrade?",
    "max_tokens": 100
  }'
```

---

## 🎯 Recommended Approach

**For immediate testing**: Use **Option 1** (Direct PEFT Loading)
- Run `/tmp/test_adapter_inference.py`
- Quick validation that your adapter works

**For production deployment**: Use **Option 2** (GGUF) or **Option 3** (vLLM)
- Option 2 if you want Ollama integration
- Option 3 if you need multi-adapter serving

---

## Integration with Chat UI

To make the model selectable in "Governance & Audit -> ⚡ Quick Deployment":

### Backend Changes (llm_service.py)

```python
# Add PEFT model handling
if model_name.startswith("finetuned:"):
    # Extract adapter info from database
    adapter_id = model_name.split(":")[1]
    adapter_info = db.query(FinetunedModel).filter_by(id=adapter_id).first()

    # Use Option 1 approach
    return await self.generate_with_peft_adapter(
        model_id=adapter_info.base_model,
        adapter_path=adapter_info.adapter_path,
        messages=messages,
        temperature=temperature
    )
```

### Frontend Changes

```typescript
// Add to model dropdown
const finetuned_models = await fetch('/api/v1/finetuning/models/deployed');
const models = [
  ...existing_models,
  ...finetuned_models.map(m => ({
    id: `finetuned:${m.id}`,
    name: `${m.name} (Fine-tuned)`,
    type: 'peft'
  }))
];
```

### Database Query

```sql
-- Get deployed models for UI
SELECT
  id,
  name,
  base_model,
  adapter_path,
  deployment_url
FROM finetuned_models
WHERE status = 'deployed'
ORDER BY created_at DESC;
```

---

## Test Questions for Validation

Once deployed, test with these questions from your training data:

1. What is Choles Food Technologies?
2. What is TomatoGrade?
3. How does TomatoGrade AI determine tomato quality?
4. What technologies are used in TomatoGrade?
5. What are the benefits of using TomatoGrade for tomato farmers?

Expected behavior: Model should provide accurate, detailed answers about Choles and TomatoGrade based on training data.

---

## Next Steps

1. **Test adapters work**: Run `/tmp/test_adapter_inference.py`
2. **Choose deployment method**: Pick Option 1, 2, or 3 based on requirements
3. **Update llm_service.py**: Add PEFT handling
4. **Update frontend**: Add model to dropdown
5. **Test end-to-end**: Use chat UI with fine-tuned model
