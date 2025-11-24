# Ollama Model Management - Admin Console Integration

**Date**: 2025-11-20  
**Objective**: Enable dynamic local model management via Admin UI

---

## 🎯 Current State: How Ollama Models Work

### What You Have Now

**Ollama** is a Docker service that runs local LLMs (Llama, Qwen, Mistral, etc.)

**Current Models** (based on your setup):
- `qwen2.5:1.5b` - Lightweight Chinese/English model
- `llama2` or similar - Meta's Llama models

### How It Currently Works

```
┌─────────────────┐
│  docker-compose │
│   ┌──────────┐  │
│   │  Ollama  │  │  ← Runs models
│   │ Container│  │
│   └────┬─────┘  │
│        │        │
│   ┌────▼─────┐  │
│   │ Volume:  │  │  ← Stores models
│   │ ollama   │  │     (~5-10GB each)
│   └──────────┘  │
└─────────────────┘
```

**Backend Access**:
```python
# backend/app/core/config.py
OLLAMA_ENDPOINT: str = "http://ollama:11434"

# Models are called like:
# ollama/qwen2.5:1.5b
# ollama/llama2
# ollama/mistral
```

---

## 📥 Current Manual Process (Without Admin UI)

### How to Add a New Model Today

**Step 1: Connect to Ollama Container**
```bash
docker-compose exec ollama /bin/bash
```

**Step 2: Pull the Model**
```bash
# Inside container
ollama pull mistral        # ~4.1GB
ollama pull llama2:13b     # ~7.4GB
ollama pull phi3:mini      # ~2.3GB
ollama pull codellama      # ~3.8GB
ollama pull gemma:2b       # ~1.4GB
```

**Step 3: List Models**
```bash
ollama list

# Output:
# NAME              ID            SIZE    MODIFIED
# qwen2.5:1.5b     a7f8b5e12     934MB   2 days ago
# mistral:latest   3a2e9c1ab     4.1GB   5 minutes ago
```

**Step 4: Test the Model**
```bash
ollama run mistral "Hello, how are you?"
```

**Step 5: Use in Your App**
- Model is automatically available in dropdown
- No frontend rebuild needed
- No backend restart needed (Ollama auto-detects)

### ✅ Benefits of Current Manual Approach
- No database needed
- Models stored in Docker volume (persists across restarts)
- Simple and reliable
- No image rebuild required

### ❌ Limitations
- Requires terminal access to container
- Not user-friendly for non-technical users
- No UI for model discovery
- Can't see model status in admin dashboard

---

## 💡 Recommended Solution: Admin UI for Ollama Model Management

### Architecture

```
┌──────────────────────────────────────┐
│         Admin Dashboard              │
│  ┌────────────────────────────────┐  │
│  │  Local Models Management       │  │
│  │  ┌──────────────────────────┐  │  │
│  │  │ Available Models         │  │  │
│  │  │ - mistral      [Install] │  │  │
│  │  │ - llama2:13b   [Install] │  │  │
│  │  │ - phi3         [Install] │  │  │
│  │  └──────────────────────────┘  │  │
│  │  ┌──────────────────────────┐  │  │
│  │  │ Installed Models         │  │  │
│  │  │ ✓ qwen2.5:1.5b  [Delete] │  │  │
│  │  │ ✓ llama2        [Delete] │  │  │
│  │  └──────────────────────────┘  │  │
│  └────────────────────────────────┘  │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Backend API: /api/v1/admin/models   │
│  ┌────────────────────────────────┐  │
│  │  GET /available    (catalog)   │  │
│  │  GET /installed    (list)      │  │
│  │  POST /install     (download)  │  │
│  │  DELETE /{model}   (remove)    │  │
│  └────────────────────────────────┘  │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│     Ollama Service (HTTP API)        │
│  http://ollama:11434/api/tags        │
│  http://ollama:11434/api/pull        │
│  http://ollama:11434/api/delete      │
└──────────────────────────────────────┘
```

---

## 🔧 Implementation Design

### Option 1: **Direct Ollama API Integration** (Recommended)

**Why?** Ollama has a built-in REST API - no database needed!

#### Backend API Service

```python
# backend/app/services/ollama_model_service.py

import httpx
from typing import List, Dict, Any

class OllamaModelService:
    def __init__(self, ollama_endpoint: str = "http://ollama:11434"):
        self.base_url = ollama_endpoint
        
    async def list_installed_models(self) -> List[Dict[str, Any]]:
        """Get all installed models from Ollama"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/tags")
            data = response.json()
            
            return [
                {
                    "name": model["name"],
                    "size": model["size"],
                    "modified_at": model["modified_at"],
                    "digest": model["digest"]
                }
                for model in data.get("models", [])
            ]
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Download a model from Ollama library"""
        async with httpx.AsyncClient(timeout=600.0) as client:
            # Stream the download progress
            async with client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                # This streams download progress
                async for line in response.aiter_lines():
                    if line:
                        progress = json.loads(line)
                        # Can emit WebSocket updates here for real-time progress
                        yield progress
    
    async def delete_model(self, model_name: str) -> bool:
        """Remove a model from Ollama"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name}
            )
            return response.status_code == 200
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed info about a specific model"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/show",
                json={"name": model_name}
            )
            return response.json()
```

#### API Endpoints

```python
# backend/app/api/routes/models.py

from fastapi import APIRouter, Depends, HTTPException
from app.services.ollama_model_service import OllamaModelService

router = APIRouter(prefix="/api/v1/admin/models", tags=["models"])

@router.get("/installed")
async def list_installed_models():
    """Get all installed Ollama models"""
    service = OllamaModelService()
    models = await service.list_installed_models()
    
    return {
        "success": True,
        "models": models,
        "total": len(models)
    }

@router.get("/available")
async def list_available_models():
    """Get catalog of available models"""
    # This is a curated list - Ollama doesn't have a discover API
    catalog = [
        {
            "name": "mistral",
            "description": "7B parameter model, great for general tasks",
            "size": "4.1GB",
            "tags": ["7b", "general"],
            "recommended": True
        },
        {
            "name": "llama2:13b",
            "description": "Meta's Llama 2 13B - more capable, larger",
            "size": "7.4GB",
            "tags": ["13b", "meta"]
        },
        {
            "name": "phi3:mini",
            "description": "Microsoft Phi-3 Mini - fast and efficient",
            "size": "2.3GB",
            "tags": ["3.8b", "microsoft"],
            "recommended": True
        },
        {
            "name": "codellama",
            "description": "Specialized for code generation",
            "size": "3.8GB",
            "tags": ["7b", "code"]
        },
        {
            "name": "gemma:2b",
            "description": "Google's Gemma 2B - very small and fast",
            "size": "1.4GB",
            "tags": ["2b", "google"],
            "recommended": True
        },
        {
            "name": "qwen2.5:7b",
            "description": "Qwen 2.5 7B - multilingual",
            "size": "4.7GB",
            "tags": ["7b", "multilingual"]
        },
        {
            "name": "llama3.2:3b",
            "description": "Latest Llama 3.2 3B model",
            "size": "2GB",
            "tags": ["3b", "meta"],
            "recommended": True
        }
    ]
    
    # Check which ones are already installed
    service = OllamaModelService()
    installed = await service.list_installed_models()
    installed_names = {m["name"] for m in installed}
    
    for model in catalog:
        model["installed"] = model["name"] in installed_names
    
    return {
        "success": True,
        "models": catalog,
        "total": len(catalog)
    }

@router.post("/install/{model_name}")
async def install_model(model_name: str):
    """Install a model from Ollama library"""
    service = OllamaModelService()
    
    # Start download (this takes a while - should be async job)
    try:
        async for progress in service.pull_model(model_name):
            # You can implement WebSocket here for real-time progress
            pass
        
        return {
            "success": True,
            "message": f"Model {model_name} installed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{model_name}")
async def delete_model(model_name: str):
    """Remove an installed model"""
    service = OllamaModelService()
    
    success = await service.delete_model(model_name)
    
    if success:
        return {
            "success": True,
            "message": f"Model {model_name} deleted successfully"
        }
    else:
        raise HTTPException(status_code=404, detail="Model not found")
```

---

## 🎨 Frontend UI Design

```typescript
// frontend/src/components/ModelManagement.tsx

interface Model {
  name: string;
  description: string;
  size: string;
  tags: string[];
  recommended?: boolean;
  installed?: boolean;
}

export const ModelManagement: React.FC = () => {
  const [availableModels, setAvailableModels] = useState<Model[]>([]);
  const [installedModels, setInstalledModels] = useState<any[]>([]);
  const [installing, setInstalling] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    // Load available models catalog
    const availRes = await fetch('/api/v1/admin/models/available');
    const availData = await availRes.json();
    setAvailableModels(availData.models);

    // Load installed models
    const instRes = await fetch('/api/v1/admin/models/installed');
    const instData = await instRes.json();
    setInstalledModels(instData.models);
  };

  const handleInstall = async (modelName: string) => {
    setInstalling(modelName);
    
    try {
      const response = await fetch(`/api/v1/admin/models/install/${modelName}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        alert(`Model ${modelName} installed successfully!`);
        loadModels(); // Refresh list
      }
    } catch (error) {
      alert(`Error installing model: ${error}`);
    } finally {
      setInstalling(null);
    }
  };

  const handleDelete = async (modelName: string) => {
    if (!confirm(`Delete model ${modelName}?`)) return;
    
    const response = await fetch(`/api/v1/admin/models/delete/${modelName}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      alert(`Model ${modelName} deleted successfully!`);
      loadModels();
    }
  };

  return (
    <div className="model-management">
      <h2>Local Model Management</h2>
      
      {/* Installed Models */}
      <section>
        <h3>Installed Models ({installedModels.length})</h3>
        <div className="model-grid">
          {installedModels.map(model => (
            <div key={model.name} className="model-card installed">
              <h4>{model.name}</h4>
              <p>Size: {(model.size / 1e9).toFixed(2)} GB</p>
              <p>Modified: {new Date(model.modified_at).toLocaleDateString()}</p>
              <button onClick={() => handleDelete(model.name)}>Delete</button>
            </div>
          ))}
        </div>
      </section>

      {/* Available Models */}
      <section>
        <h3>Available Models</h3>
        <div className="model-grid">
          {availableModels
            .filter(m => !m.installed)
            .map(model => (
              <div key={model.name} className="model-card available">
                <h4>
                  {model.name}
                  {model.recommended && <span className="badge">Recommended</span>}
                </h4>
                <p>{model.description}</p>
                <p>Size: {model.size}</p>
                <p>Tags: {model.tags.join(', ')}</p>
                <button 
                  onClick={() => handleInstall(model.name)}
                  disabled={installing === model.name}
                >
                  {installing === model.name ? 'Installing...' : 'Install'}
                </button>
              </div>
            ))}
        </div>
      </section>
    </div>
  );
};
```

---

## 📊 Comparison: Manual vs Admin UI

| Feature | Manual (Current) | Admin UI (Proposed) |
|---------|------------------|---------------------|
| **Ease of Use** | ❌ Terminal access required | ✅ Click to install |
| **User-Friendly** | ❌ Technical knowledge needed | ✅ Anyone can use |
| **Model Discovery** | ❌ Must know model names | ✅ Catalog with descriptions |
| **Progress Tracking** | ⚠️ CLI only | ✅ Real-time progress bar |
| **Image Rebuild** | ✅ Not needed | ✅ Not needed |
| **Backend Restart** | ✅ Not needed | ✅ Not needed |
| **Persistence** | ✅ Docker volume | ✅ Same (Docker volume) |
| **Multi-User** | ❌ One at a time | ✅ Controlled via UI |

---

## 🚀 Recommended Approach

### Best Choice: **Hybrid Approach**

**Keep manual access available** + **Add Admin UI**

#### Why Both?

1. **Manual CLI** (Current):
   - Fast for power users
   - Good for troubleshooting
   - Direct access when needed

2. **Admin UI** (New):
   - User-friendly for non-technical users
   - Centralized management
   - Audit trail
   - Better UX

### Quick Wins (Immediate Implementation)

**Phase 1: Read-Only Dashboard** (1 day)
- Show installed models in Admin UI
- Display model sizes and last used
- No installation yet

**Phase 2: Installation UI** (2-3 days)
- Add "Install" button for curated models
- Show progress (basic)
- Refresh list after installation

**Phase 3: Advanced Features** (1 week)
- Real-time download progress (WebSockets)
- Model testing before deployment
- Usage statistics per model
- Auto-cleanup of unused models

---

## 🎯 Your Questions Answered

### Q: Do I need to rebuild the image?
**A**: ❌ **NO** - Ollama downloads models to a Docker volume, not the image.

### Q: Do I need to restart containers?
**A**: ❌ **NO** - Ollama auto-detects new models immediately.

### Q: How are models stored?
**A**: ✅ In `ollama` Docker volume (~5-10GB per model). Persists across restarts.

### Q: Can users see new models immediately in dropdown?
**A**: ✅ **YES** - Frontend can fetch available models from `/api/v1/admin/models/installed`

### Q: What about cloud/API models (OpenAI, Claude)?
**A**: Those use API keys (covered in secrets management). Local models (Ollama) are separate.

---

## 📝 Step-by-Step: Add a Model Manually (Today)

```bash
# 1. Enter Ollama container
docker-compose exec ollama bash

# 2. Pull model (example: Mistral 7B)
ollama pull mistral

# 3. Verify
ollama list

# 4. Test
ollama run mistral "Hello!"

# 5. Exit container
exit

# 6. Use in app - model automatically available in dropdown
# Frontend will see: "ollama/mistral"
```

---

## 🔮 Future Enhancements

1. **Model Templates** - Pre-configured model sets for different use cases
2. **Auto-Download** - Background downloads with progress notifications
3. **Model Benchmarking** - Test speed and quality automatically
4. **Usage Analytics** - Track which models are most used
5. **Cost Estimation** - Estimate GPU/CPU usage before installation
6. **Model Families** - Group related models (Llama 2 family, Mistral family)
7. **Quantization Options** - Choose FP16, INT8, INT4 versions

---

## 💡 Popular Models to Add

### Recommended for Chat:
- `mistral` (4.1GB) - Excellent general purpose
- `phi3:mini` (2.3GB) - Fast, Microsoft
- `llama3.2:3b` (2GB) - Latest Llama

### Recommended for Code:
- `codellama` (3.8GB) - Code generation
- `deepseek-coder` (5.4GB) - Specialized coding

### Lightweight Options:
- `gemma:2b` (1.4GB) - Google, very fast
- `tinyllama` (637MB) - Ultra-lightweight

### Multilingual:
- `qwen2.5:7b` (4.7GB) - Chinese/English
- `aya:8b` (4.8GB) - 101 languages

---

**Summary**: No rebuild needed! Ollama models are **downloaded on-demand** and stored in Docker volumes. The Admin UI would make this process user-friendly without changing the fundamental architecture.

Would you like me to implement the Admin UI for model management?
