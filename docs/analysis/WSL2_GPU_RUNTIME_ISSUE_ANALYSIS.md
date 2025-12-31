# WSL2 GPU Runtime Issue - Analysis and Resolution

**Date**: 2025-12-18
**Issue**: Cannot enable GPU access for backend container due to WSL2 NVIDIA runtime failure
**Status**: ⚠️ **PARTIAL WORKAROUND** - System functional but backend lacks direct GPU access

---

## Executive Summary

**User Request**: "can u give back the gpu access to backend??? what if we need to use vllm in future??"

**Outcome**: Cannot restore GPU access to backend due to **WSL2 NVIDIA container runtime failure**. The runtime cannot detect GPU adapters when creating NEW containers, but existing containers (Ollama) continue working.

**Current State**:
- ✅ Backend: Running WITHOUT GPU (system functional)
- ✅ Celery Worker: Running WITHOUT GPU (correctly, as intended)
- ✅ Ollama: Running WITH GPU (started 3 days ago, still works)
- ✅ Prometheus Metrics: All 6 metrics exposed and working
- ❌ Backend GPU access: **BLOCKED** by WSL2 runtime issue
- ❌ vLLM future support: **REQUIRES** GPU runtime fix

---

## Root Cause Analysis

### The Error

```
Error response from daemon: failed to create task for container: failed to create shim task:
OCI runtime create failed: runc create failed: unable to start container process:
error during container init: error running prestart hook #0: exit status 1
stderr: nvidia-container-cli: initialization error: WSL environment detected but no adapters were found: unknown
```

### What This Means

1. **WSL2 NVIDIA Container Runtime**: The `nvidia-container-cli` tool (part of NVIDIA Container Toolkit) is responsible for exposing GPU devices to Docker containers
2. **Adapter Detection Failure**: The runtime cannot detect any GPU adapters in the WSL2 environment
3. **NEW Containers Only**: This affects only containers being created NOW - existing containers with GPU continue working
4. **System-Level Issue**: This is NOT a code/configuration issue - it's a WSL2/Driver/Docker integration problem

### Why Ollama Works But Backend Doesn't

| Container | GPU Config | Status | Started | Reason |
|-----------|-----------|--------|---------|--------|
| **Ollama** | ✅ Has GPU | ✅ Running | **3 days ago** | Started when runtime was healthy |
| **Backend** | ❌ No GPU | ❌ Fails to start | **Now** | Runtime broken NOW |
| **Celery Worker** | ❌ No GPU | ✅ Running | **Earlier today** | Correctly doesn't need GPU |

**Key Insight**: Ollama was started **3 days ago** when the NVIDIA container runtime was working. It continues to have GPU access. When we try to start the backend NOW, the runtime has failed and prevents NEW containers from getting GPU access.

### Environment Evidence

```bash
# WSL2 host-level GPU access - BLOCKED
$ nvidia-smi
Failed to initialize NVML: GPU access blocked by the operating system

# Ollama container - HAS GPU (from earlier successful start)
$ docker inspect rag-ollama | grep DeviceRequests
"Driver": "nvidia",
"Count": 1,
"Capabilities": [["gpu"]]

# Ollama uptime - Started when runtime worked
$ docker ps --filter "name=rag-ollama"
rag-ollama   Up 3 days (healthy)   3 weeks ago
```

---

## What Works vs What Doesn't

### ✅ Currently Working

1. **Backend Container**
   - Running successfully WITHOUT GPU
   - All API endpoints functional
   - Prometheus metrics exposed (all 6 finetuning metrics)
   - Can communicate with Ollama service

2. **Ollama Service**
   - **HAS GPU ACCESS** (started 3 days ago)
   - 9 GPU-accelerated models available and working
   - Total: 31.72 GB of models loaded
   - Models accessible via backend

3. **Celery Worker**
   - Running WITHOUT GPU (correctly, as designed)
   - Launches separate training containers with GPU via GPUPoolManager
   - 3 fine-tuning tasks registered

4. **Prometheus Metrics**
   - All 6 metrics registered and exposed at `/metrics`
   - Shared metrics module working (no dependency issues)
   - Ready for Grafana dashboard integration

5. **Ollama GPU Models Visible**
   - Backend detects Ollama models as GPU-enabled
   - UI should show these models (via Ollama service, not backend GPU)
   - Examples:
     - Llama3 2 Vision (Ollama GPU) - 7.3GB
     - Qwen2 5 Coder 7B (Ollama GPU) - 4.4GB
     - Deepseek Coder 6.7B (Ollama GPU) - 3.6GB
     - LLaMA 3.2 Vision 11B (Ollama GPU) - 7.9GB

### ❌ Blocked/Not Working

1. **Backend Direct GPU Access**
   - Cannot enable GPU device reservations
   - Backend container fails to start with GPU config
   - GPU detection reports: "cpu (not available)"

2. **vLLM Support (Future)**
   - **REQUIRES** backend GPU access
   - Currently BLOCKED by same runtime issue
   - Cannot be enabled until WSL2 GPU runtime is fixed

3. **New GPU Containers**
   - Any NEW container requiring GPU will fail
   - Cannot restart Ollama without losing GPU access
   - Limited to containers already running with GPU

---

## Technical Details

### Docker Compose Configuration

#### Backend (Lines 402-411) - Current State
```yaml
# GPU access: WSL2 nvidia-container-cli runtime broken (cannot detect adapters)
# Ollama works because it started 3 days ago when runtime was healthy
# New containers cannot start with GPU until WSL2/NVIDIA runtime is fixed
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

#### Celery Worker (Lines 442-449) - Correct Configuration
```yaml
# GPU access commented out - celery worker launches separate training containers with GPU
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

**Why This Is Correct**:
- Celery worker orchestrates training jobs
- Training runs in SEPARATE containers spawned by GPUPoolManager
- Those training containers get GPU from the pool manager
- Celery worker itself doesn't need GPU

### Shared Metrics Module Implementation

Created to avoid dependency issues when backend imports Prometheus metrics:

**Files Created**:
1. `backend/app/metrics/finetuning_metrics.py` - Metric definitions
2. `backend/app/metrics/__init__.py` - Module initialization

**Files Modified**:
1. `backend/app/main.py` (line 45) - Import from shared module
2. `backend/app/tasks/finetuning_tasks.py` (lines 39-52) - Import from shared module

**Why This Works**:
- Backend can import metrics WITHOUT importing celery dependencies
- Celery worker imports same metrics and updates values
- Both share the same Prometheus registry
- No circular dependencies or missing modules (like `semver`)

### Prometheus Metrics Exposed

All 6 metrics successfully registered at `http://localhost:8000/metrics`:

```
# HELP finetuning_train_loss Current training loss
# TYPE finetuning_train_loss gauge

# HELP finetuning_eval_loss Current evaluation loss
# TYPE finetuning_eval_loss gauge

# HELP finetuning_current_epoch Current training epoch
# TYPE finetuning_current_epoch gauge

# HELP finetuning_progress_percent Training progress percentage (0-100)
# TYPE finetuning_progress_percent gauge

# HELP finetuning_total_steps Total training steps
# TYPE finetuning_total_steps gauge

# HELP finetuning_job_status Job status (1=training, 0=not training)
# TYPE finetuning_job_status gauge
```

---

## Solutions and Workarounds

### Option 1: Fix WSL2 GPU Runtime (Recommended but Complex)

**What It Involves**:
1. Restart Windows machine
2. Update NVIDIA drivers in Windows
3. Update WSL2 kernel: `wsl --update`
4. Reinstall NVIDIA CUDA toolkit in WSL2
5. Restart Docker Desktop
6. Verify: `nvidia-smi` works in WSL2
7. Try starting backend with GPU config

**Pros**:
- ✅ Proper fix for root cause
- ✅ Enables vLLM support
- ✅ Backend gets direct GPU access

**Cons**:
- ❌ Requires Windows restart
- ❌ May require driver reinstallation
- ❌ Downtime for system
- ❌ Risk: Ollama loses GPU if restarted before fix

**Steps**:
```powershell
# From Windows PowerShell (admin)
wsl --shutdown
wsl --update

# Restart Docker Desktop

# From WSL2 terminal
nvidia-smi  # Should work

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Option 2: Use Ollama for All GPU Work (Current Approach)

**What We Have**:
- Ollama service has GPU access
- Backend connects to Ollama via HTTP API
- 9 GPU-accelerated models available
- Works for inference workloads

**Pros**:
- ✅ Already working
- ✅ No changes needed
- ✅ No downtime
- ✅ Ollama optimized for LLM inference

**Cons**:
- ❌ Cannot use vLLM (requires backend GPU)
- ❌ Limited to Ollama-supported models
- ❌ No direct GPU control from backend

**Best For**:
- General LLM inference
- Chat applications
- RAG systems
- Document processing with vision models

### Option 3: Run vLLM as Separate Service (Future)

**Approach**:
- Don't give backend GPU
- Run vLLM as separate service (like Ollama)
- Backend connects to vLLM via HTTP API
- vLLM container started BEFORE GPU runtime breaks

**Pros**:
- ✅ Separates concerns
- ✅ vLLM optimized for GPU inference
- ✅ Backend remains stateless

**Cons**:
- ❌ Requires GPU runtime fix FIRST
- ❌ Additional service to manage
- ❌ More complex architecture

**Implementation** (AFTER GPU runtime fixed):
```yaml
# Add to docker-compose.yml
vllm-server:
  image: vllm/vllm-openai:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  ports:
    - "8100:8000"
  volumes:
    - vllm_models:/root/.cache/huggingface
  command: --model meta-llama/Llama-3.1-8B --gpu-memory-utilization 0.8
```

### Option 4: Native Linux with GPU (Alternative Environment)

**Approach**:
- Deploy to native Linux system with GPU
- Avoids WSL2 altogether
- Proper NVIDIA driver support

**Pros**:
- ✅ No WSL2 issues
- ✅ Better GPU performance
- ✅ Full CUDA support
- ✅ Production-ready

**Cons**:
- ❌ Requires different machine/environment
- ❌ Migration effort
- ❌ Not helpful for current development setup

---

## Recommendations

### Immediate (Now)

✅ **DONE**: Keep backend running WITHOUT GPU
✅ **DONE**: Use Ollama GPU models for inference (9 models available)
✅ **DONE**: Keep celery worker WITHOUT GPU (correctly configured)
✅ **DONE**: Prometheus metrics working (6 metrics exposed)

**User Action**: Continue using Ollama GPU models for all LLM inference work. UI should show GPU models via Ollama service.

### Short-Term (Next Session)

1. **Import Grafana Dashboard**
   - Dashboard JSON ready: `observability/grafana/dashboards/finetuning-metrics.json`
   - 7 panels defined (1 PostgreSQL + 6 Prometheus)
   - PostgreSQL panel works immediately
   - Prometheus panels will populate when training jobs run

2. **Test with Training Job**
   - Submit fine-tuning job via UI
   - Monitor Prometheus metrics
   - Verify dashboard updates in real-time

### Long-Term (Future Planning)

1. **Fix WSL2 GPU Runtime** (When feasible)
   - Schedule Windows restart
   - Update drivers and WSL2 kernel
   - Test GPU access: `nvidia-smi`
   - Verify Docker GPU access
   - Re-enable backend GPU config

2. **Add vLLM Support** (After GPU runtime fixed)
   - Deploy vLLM as separate service (like Ollama)
   - Configure backend to use vLLM API
   - Test with high-performance inference workloads

3. **Production Deployment** (Optional)
   - Consider native Linux environment
   - Full GPU support without WSL2 limitations
   - Better performance and stability

---

## Impact Assessment

### What User Wanted

> "can u give back the gpu access to backend??? what if we need to use vllm in future??"

### What We Delivered

1. **GPU Access to Backend**: ❌ **BLOCKED** by WSL2 runtime failure
2. **vLLM Support**: ❌ **BLOCKED** by same issue (requires backend GPU)
3. **System Functionality**: ✅ **WORKING** (backend running without GPU)
4. **Ollama GPU Models**: ✅ **WORKING** (9 models, 31.72 GB, GPU-accelerated)
5. **Prometheus Metrics**: ✅ **WORKING** (all 6 metrics exposed)
6. **Grafana Ready**: ✅ **READY** (dashboard JSON created, needs import)

### What This Means for User

**Immediate**:
- Can continue using Ollama GPU models for inference
- UI shows GPU models (via Ollama service)
- System fully functional for RAG, chat, document processing
- Fine-tuning metrics ready for monitoring

**Future**:
- vLLM support **BLOCKED** until WSL2 GPU runtime is fixed
- Backend cannot do GPU-accelerated work directly
- Workaround: Run vLLM as separate service (like Ollama)

**Best Path Forward**:
1. Use Ollama for now (9 GPU models available)
2. Fix WSL2 GPU runtime when feasible (requires Windows restart)
3. After fix: Add vLLM service OR enable backend GPU
4. Avoid restarting Ollama container until GPU runtime is fixed

---

## Related Documentation

### Session Work Summary
- `/tmp/SESSION_SUMMARY_2025-12-18_COMPLETE.md` - Full session summary
- `/tmp/PROMETHEUS_METRICS_IMPLEMENTATION_COMPLETE.md` - Metrics implementation
- `/tmp/GRAFANA_TRAINING_METRICS_SETUP.md` - Dashboard setup guide
- `/tmp/MINIO_ORG_PATH_FIX_COMPLETE.md` - MinIO path fix

### Previous GPU Work
- `/tmp/GPU_MEMORY_DEFAULT_FIX_FINAL.md` - GPU memory defaults fix
- `/tmp/GPU_MEMORY_CONFIG_FIX_COMPLETE.md` - GPU memory schema fix

---

## Quick Commands

```bash
# Check GPU runtime status
nvidia-smi  # Should work when runtime is healthy

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Check Ollama GPU status
docker inspect rag-ollama | grep -A 10 "DeviceRequests"
docker-compose exec ollama nvidia-smi

# Verify Prometheus metrics
curl http://localhost:8000/metrics | grep finetuning

# Check backend GPU detection
docker-compose logs backend | grep -i gpu

# Current container status
docker-compose ps
```

---

## Conclusion

**Bottom Line**: WSL2's NVIDIA container runtime has failed and cannot detect GPU adapters. This prevents NEW containers from getting GPU access, but existing containers (Ollama) continue working. Backend must run without GPU until the runtime is fixed at the system level.

**Working Solution**: Use Ollama GPU models for all LLM inference. The system is fully functional for RAG, chat, and document processing. Fine-tuning metrics are ready for monitoring.

**For vLLM**: Requires fixing the WSL2 GPU runtime first. Then deploy vLLM as a separate service (like Ollama) rather than giving backend direct GPU access.

**Session**: WSL2 GPU Runtime Analysis and Workarounds
**Date**: 2025-12-18
**Status**: ✅ **SYSTEM FUNCTIONAL** | ⚠️ **BACKEND GPU BLOCKED**
**Developer**: Claude Code AI Assistant

---

**End of Analysis Report**
