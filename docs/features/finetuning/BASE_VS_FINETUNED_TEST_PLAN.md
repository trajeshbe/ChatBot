# Base Model vs Fine-Tuned Model - Testing Guide

> **Purpose**: Compare base model (Qwen2.5-1.5B-Instruct) vs fine-tuned model (choles-qa-real-training39)
> **Dataset**: Choles Products Domain QA
> **Expected**: Base model won't know Choles-specific information, fine-tuned will

---

## 📋 Test Questions

These questions test domain-specific knowledge about Choles products that should be in your training data:

### Question 1: Product Information (Recommended)
```
What products does Choles offer?
```
**Why**: Simple, direct, tests if model knows product catalog

### Question 2: Product Specifications
```
What are the specifications of Choles Premium Widget?
```
**Why**: Tests detailed product knowledge

### Question 3: Pricing/Commercial
```
What is the pricing for Choles products?
```
**Why**: Commercial information unlikely in base model

### Question 4: Use Cases
```
What are the common use cases for Choles products in construction projects?
```
**Why**: Application-specific knowledge

### Question 5: Technical Support
```
How do I troubleshoot issues with Choles equipment?
```
**Why**: Support procedures are company-specific

---

## 🧪 Testing Procedure

### Part 1: Test Base Model

1. **Open Chat UI**:
   - URL: http://localhost:3001
   - Should see chat interface

2. **Select Base Model**:
   - Look for model dropdown (top of page)
   - Select: **qwen2.5:1.5b-instruct-q4_K_M** or **qwen2.5:1.5b**
   - This is the unmodified base model

3. **Ask Question**:
   - Type: `What products does Choles offer?`
   - Click Send (or press Enter)

4. **Expected Base Model Response**:
   ```
   I don't have specific information about Choles products in my training data.
   Could you provide more context about what Choles is?
   ```
   Or similar generic/unhelpful response

5. **Document Response**:
   - Copy the full response
   - Note: Model name, timestamp, response quality

---

### Part 2: Deploy Fine-Tuned Model

1. **Open Admin Dashboard**:
   - URL: http://localhost:3001/admin
   - Login if prompted (username: admin)

2. **Navigate to Governance & Audit**:
   - Click: **Fine-Tuning Hub** (left sidebar)
   - Click: **Governance & Audit** tab

3. **Find Your Model**:
   - Scroll to: **"Models Ready for Deployment"** section
   - Look for: **choles-qa-real-training39_model**
   - Status should show: **Approved** (blue badge)

4. **Deploy Model**:
   - Click: **"Merge & Deploy to Ollama"** button
   - Watch progress bar:
     - Step 1: Approve (should be instant, already approved)
     - Step 2: Merge (2-5 minutes, merging LoRA adapters)
     - Step 3: Deploy (1-2 minutes, pushing to Ollama)
   - Total time: ~5-10 minutes

5. **Verify Deployment**:
   - Success message should appear: "Model deployed successfully!"
   - Status changes to: **Deployed** (green badge)

---

### Part 3: Test Fine-Tuned Model

1. **Go Back to Chat UI**:
   - URL: http://localhost:3001
   - Refresh page (Ctrl+R) to load new model list

2. **Select Fine-Tuned Model**:
   - Model dropdown should now include: **training39** or **choles-qa-real-training39**
   - Select it

3. **Ask Same Question**:
   - Type: `What products does Choles offer?`
   - Click Send

4. **Expected Fine-Tuned Response**:
   ```
   Choles offers a range of products including:

   1. Choles Premium Widget X-500 - High-performance industrial widget for...
   2. Choles StructuralBeam Pro Series - Load-bearing beams rated for...
   3. Choles FastConnect System - Quick-assembly connector system for...

   [Detailed, accurate information from training data]
   ```

5. **Document Response**:
   - Copy the full response
   - Compare with base model response
   - Note improvements in accuracy, detail, domain knowledge

---

## 📊 Comparison Matrix

| Aspect | Base Model | Fine-Tuned Model |
|--------|------------|------------------|
| **Domain Knowledge** | ❌ Generic/None | ✅ Choles-specific |
| **Product Names** | ❌ Unknown | ✅ Accurate |
| **Specifications** | ❌ Guesses | ✅ Precise |
| **Use Cases** | ❌ Generic | ✅ Domain-specific |
| **Terminology** | ❌ Incorrect | ✅ Company terms |
| **Confidence** | ❌ Uncertain | ✅ Definitive |

---

## 🎯 Success Criteria

### Base Model Should:
- ❌ NOT know about Choles products
- ❌ Give generic/unhelpful responses
- ❌ Ask for clarification
- ❌ Admit lack of knowledge

### Fine-Tuned Model Should:
- ✅ Recognize Choles products
- ✅ Provide specific details
- ✅ Use correct terminology
- ✅ Give confident, accurate answers

### Clear Difference:
If you can't tell the difference between base and fine-tuned responses, the fine-tuning may not have been effective.

---

## 🔍 Verification Commands

### Check Ollama Models List:
```bash
curl -s http://localhost:11434/api/tags | jq -r '.models[] | .name'
```

Should include:
- `qwen2.5:1.5b-instruct-q4_K_M` (base model)
- `training39:latest` or `choles-qa-real-training39:latest` (fine-tuned)

### Check Model Deployment Status:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT name, status, merged_model_path, deployed_at
FROM finetuned_models
WHERE name LIKE '%training39%';"
```

Should show:
- `status`: `deployed`
- `merged_model_path`: Path to merged model
- `deployed_at`: Recent timestamp

### Test Ollama Model Directly:
```bash
# Test base model
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:1.5b-instruct-q4_K_M",
  "prompt": "What products does Choles offer?",
  "stream": false
}' | jq -r '.response'

# Test fine-tuned model (after deployment)
curl -s http://localhost:11434/api/generate -d '{
  "model": "training39",
  "prompt": "What products does Choles offer?",
  "stream": false
}' | jq -r '.response'
```

---

## 🐛 Troubleshooting

### Issue 1: Fine-Tuned Model Not in Dropdown
**Cause**: Frontend not refreshed after deployment
**Fix**: Hard refresh browser (Ctrl+Shift+R)

### Issue 2: Deployment Fails
**Cause**: GPU/memory issue, merge error
**Fix**:
- Check backend logs: `docker-compose logs backend --tail 50`
- Retry deployment (model stays in list with retry button)
- Check GPU availability: `nvidia-smi`

### Issue 3: Both Models Give Same Response
**Cause**: Fine-tuning didn't work, or using wrong model
**Fix**:
- Verify you selected the right model in dropdown
- Check training loss was decreasing in TensorBoard
- Verify dataset had relevant Choles information

### Issue 4: Merge Takes Too Long (>10 mins)
**Cause**: CPU merge (slow), or large model
**Fix**:
- Wait patiently (CPU merge can take 10-15 mins)
- Check logs: `docker-compose logs backend | grep merge`
- GPU merge is faster (2-5 mins)

---

## 📝 Template for Documenting Results

```markdown
## Test Results: Base vs Fine-Tuned Model

**Date**: 2025-12-22
**Base Model**: Qwen2.5-1.5B-Instruct
**Fine-Tuned Model**: choles-qa-real-training39_model
**Question**: "What products does Choles offer?"

---

### Base Model Response:
[Paste full response here]

**Analysis**:
- Domain knowledge: ❌ None
- Accuracy: ❌ Generic
- Usefulness: ❌ Not helpful

---

### Fine-Tuned Model Response:
[Paste full response here]

**Analysis**:
- Domain knowledge: ✅ Choles-specific
- Accuracy: ✅ Detailed and correct
- Usefulness: ✅ Actionable information

---

### Conclusion:
Fine-tuning was [successful/unsuccessful] because [reason]

**Improvement**: [X]% more relevant, [Y] specific products mentioned, [Z] technical details provided
```

---

## 🎬 Quick Start (TL;DR)

1. **Test Base**: http://localhost:3001 → Select `qwen2.5:1.5b` → Ask "What products does Choles offer?"
2. **Deploy Fine-Tuned**: http://localhost:3001/admin → Fine-Tuning Hub → Governance & Audit → Click "Merge & Deploy"
3. **Test Fine-Tuned**: http://localhost:3001 → Refresh → Select `training39` → Ask same question
4. **Compare**: Base = generic, Fine-tuned = specific Choles knowledge

Expected time: 15-20 minutes total (most is waiting for merge/deploy)

---

## 📚 Related Documentation

- [Where to Find Button](./WHERE_TO_FIND_MERGE_DEPLOY_BUTTON.md)
- [Merge & Deploy Process](./UNIFIED_MERGE_DEPLOY_IMPLEMENTATION.md)
- [TensorBoard Link](./TENSORBOARD_LINK_training39.md)
- [Troubleshooting](./FAILED_TO_FETCH_TROUBLESHOOTING.md)

---

**Ready to start?** Follow Part 1 (Test Base Model) first! 🚀

---

**End of Document**
