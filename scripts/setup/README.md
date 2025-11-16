# Setup Scripts

Scripts for initial system setup and configuration.

## Available Scripts

### Database Setup

#### `setup-database.sh`
Initialize PostgreSQL database with schema and extensions.
- Creates database if not exists
- Installs pgvector extension
- Applies Alembic migrations
- Creates initial tables

```bash
./setup-database.sh
```

#### `apply-migrations.sh`
Apply Alembic database migrations.
```bash
./apply-migrations.sh
```

---

### Service Setup

#### `start-services.sh`
Start all Docker Compose services.
```bash
./start-services.sh
```

---

### LLM Setup

#### `setup-ollama.sh`
Setup Ollama service and pull default models.
```bash
./setup-ollama.sh
```

#### `setup-local-llm.sh`
Setup local LLM with Ollama and configure integration.
```bash
./setup-local-llm.sh
```

#### `setup-quantized-models.sh`
Setup quantized models for efficient local inference.
```bash
./setup-quantized-models.sh
```

---

## 🚀 Recommended Setup Flow

### 1. Initial Setup
```bash
# Start services
./start-services.sh

# Wait for services to be healthy
sleep 10

# Setup database
./setup-database.sh
```

### 2. Optional: Local LLM
```bash
# Setup Ollama
./setup-ollama.sh

# Or full local LLM setup
./setup-local-llm.sh
```

### 3. Verify Setup
```bash
# Validate all services
../maintenance/validate-services.sh
```

---

## 🔗 Related Documentation

- [../../docs/setup/](../../docs/setup/) - Detailed setup guides
- [../../docs/guides/QUICKSTART.md](../../docs/guides/QUICKSTART.md) - Quick start guide

---

**Last Updated**: 2025-11-16
