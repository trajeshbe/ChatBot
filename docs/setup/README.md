# Setup Documentation

Setup guides for various system components and configurations.

## 📖 Available Guides

### [LOCAL_LLM_SETUP.md](./LOCAL_LLM_SETUP.md)
Guide for setting up local LLM models with Ollama.
- Ollama installation
- Model downloading
- Configuration
- Testing local models

### [LOCAL_MODELS_QUICK_START.md](./LOCAL_MODELS_QUICK_START.md)
Quick start guide for local model deployment.
- Quick setup steps
- Model selection
- Performance tips
- Common issues

### [MULTI_MODEL_SETUP.md](./MULTI_MODEL_SETUP.md)
Guide for configuring multiple LLM providers.
- OpenAI setup
- Anthropic Claude setup
- Ollama (local) setup
- vLLM setup
- Multi-provider configuration
- Fallback chains

### [GPU_MODELS_SETUP.md](./GPU_MODELS_SETUP.md) ⭐ NEW
**Comprehensive GPU-accelerated models guide (November 2025)**.
- GPU configuration for Ollama
- Top 5 quantized models (latest leaderboards)
- Model comparison and benchmarks
- Performance optimization
- VRAM requirements and planning
- Quick start commands

**Quick Reference**: See [GPU_QUICKSTART.md](../../GPU_QUICKSTART.md) in root directory

---

## 🚀 Quick Setup (First Time)

### 1. Prerequisites
```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker-compose --version
```

### 2. Environment Configuration
```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your API keys and settings
```

### 3. Initial Setup
```bash
# Start all services
make up

# Run database setup
../../scripts/setup/setup-database.sh

# Verify services
../../scripts/maintenance/validate-services.sh
```

### 4. Optional: Local LLM
```bash
# Setup Ollama and pull models
../../scripts/setup/setup-ollama.sh

# Test local LLM
../../scripts/testing/test-local-llm.sh
```

---

## 🛠️ Setup Scripts

All setup scripts are located in `../../scripts/setup/`:

- `setup-database.sh` - Database initialization and migrations
- `setup-local-llm.sh` - Local LLM (Ollama) setup
- `setup-ollama.sh` - Ollama service setup
- `setup-quantized-models.sh` - Quantized model setup
- `apply-migrations.sh` - Database migration application
- `start-services.sh` - Start all services

See [../../scripts/setup/README.md](../../scripts/setup/README.md) for detailed script documentation.

---

## 🔗 Related Documentation

- **Architecture**: [../architecture/DEPLOYMENT.md](../architecture/DEPLOYMENT.md) - Deployment guide
- **Debugging**: [../debugging/](../debugging/) - Troubleshooting
- **Guides**: [../guides/QUICKSTART.md](../guides/QUICKSTART.md) - Quick reference

---

**Last Updated**: 2025-11-24 (Added GPU Models Setup Guide)
