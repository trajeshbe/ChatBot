# Fresh Installation Complete Fix Strategy

**Date**: 2026-01-05
**Purpose**: Comprehensive analysis and fixes for all installation issues on fresh machines
**Status**: 🔴 CRITICAL ISSUES IDENTIFIED - Fixes Required

---

## Executive Summary

### Critical Discovery: 3 Major Issue Categories

1. **🔴 CRITICAL: DOS Line Endings (Windows/WSL2)**
   - Shell scripts fail with "cannot execute: required file not found"
   - **Impact**: Installation completely blocked
   - **Fix**: dos2unix conversion required

2. **🔴 CRITICAL: Agent-Runtime Container Missing Files**
   - Docker build fails copying non-existent service files
   - `task_complexity_analyzer.py` and `api_usage_tracker.py` not found
   - **Impact**: Agent-runtime container won't build
   - **Root Cause**: Files referenced in Dockerfile don't exist in repo

3. **🟡 MEDIUM: Database Migration Issues**
   - Migration 008 fails due to schema mismatch
   - **Status**: ✅ FIXED (documented in DATABASE_MIGRATION_CHANGES_LOG.md)

### Containers Affected

| Container | Issue | Status | Priority |
|-----------|-------|--------|----------|
| **agent-runtime** | Missing service files in COPY | ❌ BROKEN | CRITICAL |
| **finetuning-runtime** | Needs validation | ⚠️ UNKNOWN | HIGH |
| **backend** | Works | ✅ OK | - |
| **frontend** | Works | ✅ OK | - |
| **postgres** | Works | ✅ OK | - |
| **redis, minio, ollama** | Work | ✅ OK | - |

---

## Issue 1: DOS Line Endings (CRLF → LF)

### Problem

Windows Git clones files with CRLF (`\r\n`) line endings by default. WSL2 bash cannot execute scripts with CRLF endings.

**Error Message**:
```
./scripts/setup/initialize-fresh-install.sh: line 231: /mnt/d/EnterpriseAI/merit-aiml/ChatBot/scripts/setup/setup-database-complete.sh: cannot execute: required file not found
```

### Root Cause

Git on Windows converts LF (`\n`) to CRLF (`\r\n`) during checkout:
```bash
# Git behavior on Windows:
core.autocrlf=true   # Converts LF to CRLF on checkout (DEFAULT on Windows)
```

### Solution A: Fix After Clone (Manual)

```bash
# Install dos2unix if not present
sudo apt-get update && sudo apt-get install -y dos2unix

# Convert all shell scripts to Unix format
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
find . -name "*.sh" -type f -exec dos2unix {} \;

# Make all shell scripts executable
find . -name "*.sh" -type f -exec chmod +x {} \;
```

### Solution B: Prevent During Clone (Recommended)

**Add `.gitattributes` file to repository**:

```bash
cat > .gitattributes << 'EOF'
# Ensure shell scripts always use LF (Unix) line endings
*.sh text eol=lf

# Ensure Python files use LF
*.py text eol=lf

# Ensure Dockerfile files use LF
Dockerfile* text eol=lf

# Ensure Makefile uses LF
Makefile text eol=lf

# Ensure markdown uses LF
*.md text eol=lf

# Ensure YAML/JSON use LF
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.pdf binary
EOF
```

**Then normalize existing files**:

```bash
# On WSL2/Linux
git add --renormalize .
git commit -m "chore: normalize line endings with .gitattributes"
```

### Solution C: Configure Git Globally (User-level)

```bash
# On Windows/WSL2
git config --global core.autocrlf input

# This prevents CRLF conversion on checkout
# Files stay as LF (Unix) format
```

### Verification

```bash
# Check file line endings
file scripts/setup/initialize-fresh-install.sh

# Should output:
# scripts/setup/initialize-fresh-install.sh: Bourne-Again shell script, ASCII text executable

# NOT:
# scripts/setup/initialize-fresh-install.sh: Bourne-Again shell script, ASCII text executable, with CRLF line terminators
```

---

## Issue 2: Agent-Runtime Missing Files

### Problem

**Dockerfile.agent-runtime** (lines 92-94) copies files that don't exist:

```dockerfile
# Copy necessary service files
COPY app/services/task_complexity_analyzer.py /app/services/task_complexity_analyzer.py
COPY app/services/api_usage_tracker.py /app/services/api_usage_tracker.py
COPY app/services/__init__.py /app/services/__init__.py
```

**Error Message**:
```
failed to compute cache key: failed to calculate checksum of ref:
"/app/services/api_usage_tracker.py": not found
```

### Root Cause

These files were planned but never created. The Dockerfile references future functionality.

### Verification

```bash
# Check if files exist
ls -la backend/app/services/task_complexity_analyzer.py
# ls: cannot access 'backend/app/services/task_complexity_analyzer.py': No such file or directory

ls -la backend/app/services/api_usage_tracker.py
# ls: cannot access 'backend/app/services/api_usage_tracker.py': No such file or directory
```

### Solution A: Create Placeholder Files (Quick Fix)

```bash
# Create missing service files as placeholders
mkdir -p backend/app/services

cat > backend/app/services/task_complexity_analyzer.py << 'EOF'
"""
Task Complexity Analyzer
Placeholder for future agent task complexity analysis
"""

class TaskComplexityAnalyzer:
    """Analyzes task complexity for agent execution planning"""

    def analyze(self, task_description: str) -> dict:
        """
        Analyze task complexity

        Returns:
            dict: {
                'complexity': 'low' | 'medium' | 'high',
                'estimated_steps': int,
                'estimated_time_seconds': int
            }
        """
        return {
            'complexity': 'medium',
            'estimated_steps': 5,
            'estimated_time_seconds': 60
        }
EOF

cat > backend/app/services/api_usage_tracker.py << 'EOF'
"""
API Usage Tracker
Placeholder for future API usage tracking
"""

class APIUsageTracker:
    """Tracks API calls and usage metrics for agents"""

    def track_call(self, endpoint: str, tokens: int = 0):
        """Track an API call"""
        pass

    def get_usage_summary(self) -> dict:
        """Get usage summary"""
        return {
            'total_calls': 0,
            'total_tokens': 0,
            'total_cost_usd': 0.0
        }
EOF

# Ensure __init__.py exists
touch backend/app/services/__init__.py
```

### Solution B: Comment Out References (Alternative)

**Update Dockerfile.agent-runtime**:

```dockerfile
# Copy necessary service files (COMMENTED OUT - files don't exist yet)
# COPY app/services/task_complexity_analyzer.py /app/services/task_complexity_analyzer.py
# COPY app/services/api_usage_tracker.py /app/services/api_usage_tracker.py
# COPY app/services/__init__.py /app/services/__init__.py

# Create placeholder directories
RUN mkdir -p /app/services && \
    touch /app/services/__init__.py
```

### Solution C: Use Conditional Copy (Best Practice)

```dockerfile
# Copy service files if they exist
COPY app/services/__init__.py /app/services/__init__.py 2>/dev/null || touch /app/services/__init__.py
# Note: COPY doesn't support conditional logic in Dockerfile
# Use multi-stage build or build script instead
```

**Recommended**: Use Solution A (create placeholder files) for now.

---

## Issue 3: Fine-Tuning Runtime Validation

### Files to Check

```bash
ls -la backend/requirements-finetuning.txt  # Does this exist?
ls -la backend/entrypoint_finetuning.py     # Does this exist?
```

### Expected Dockerfile.finetuning-runtime Issues

Similar pattern to agent-runtime - may reference non-existent files.

### Validation Command

```bash
# Try building the fine-tuning container
docker build -f backend/Dockerfile.finetuning-runtime -t test-finetuning backend/

# Check for missing file errors
```

---

## Comprehensive Fix Implementation

### Step 1: Fix Line Endings (Run First)

```bash
#!/bin/bash
# File: scripts/setup/fix-line-endings.sh

echo "============================================"
echo "Fixing Line Endings for WSL2 Compatibility"
echo "============================================"

# Install dos2unix if not present
if ! command -v dos2unix &> /dev/null; then
    echo "Installing dos2unix..."
    sudo apt-get update && sudo apt-get install -y dos2unix
fi

# Find and convert all shell scripts
echo "Converting .sh files to Unix format..."
find . -name "*.sh" -type f -exec dos2unix {} \; 2>/dev/null

# Make all shell scripts executable
echo "Making .sh files executable..."
find . -name "*.sh" -type f -exec chmod +x {} \;

# Fix Dockerfiles
echo "Converting Dockerfile* to Unix format..."
find . -name "Dockerfile*" -type f -exec dos2unix {} \; 2>/dev/null

# Fix Python files
echo "Converting .py files to Unix format..."
find . -name "*.py" -type f -exec dos2unix {} \; 2>/dev/null

# Fix Makefile
if [ -f "Makefile" ]; then
    dos2unix Makefile 2>/dev/null
    echo "Fixed Makefile"
fi

echo ""
echo "✅ Line ending conversion complete"
echo ""
```

### Step 2: Create Missing Service Files

```bash
#!/bin/bash
# File: scripts/setup/create-missing-agent-files.sh

echo "============================================"
echo "Creating Missing Agent Runtime Files"
echo "============================================"

# Create services directory if it doesn't exist
mkdir -p backend/app/services

# Create task_complexity_analyzer.py
cat > backend/app/services/task_complexity_analyzer.py << 'EOF'
"""
Task Complexity Analyzer for Agent Runtime
Analyzes incoming tasks to estimate complexity and resource requirements
"""
import re
from typing import Dict, Literal

class TaskComplexityAnalyzer:
    """
    Analyzes task complexity for agent execution planning

    Complexity Levels:
    - low: Simple tasks (1-3 steps, <30s)
    - medium: Moderate tasks (4-10 steps, 30s-5min)
    - high: Complex tasks (10+ steps, >5min)
    """

    # Keywords indicating higher complexity
    COMPLEX_KEYWORDS = [
        'analyze', 'investigate', 'research', 'comprehensive',
        'multiple', 'complex', 'detailed', 'thorough'
    ]

    SIMPLE_KEYWORDS = [
        'list', 'show', 'display', 'get', 'fetch', 'find', 'check'
    ]

    def analyze(self, task_description: str) -> Dict[str, any]:
        """
        Analyze task complexity based on description

        Args:
            task_description: Natural language task description

        Returns:
            dict: {
                'complexity': 'low' | 'medium' | 'high',
                'estimated_steps': int,
                'estimated_time_seconds': int,
                'confidence': float (0-1),
                'reasoning': str
            }
        """
        if not task_description:
            return self._default_response()

        task_lower = task_description.lower()

        # Count complexity indicators
        complex_count = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in task_lower)
        simple_count = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in task_lower)

        # Word count as rough proxy
        word_count = len(task_description.split())

        # Determine complexity
        if complex_count > simple_count and word_count > 50:
            complexity = 'high'
            steps = 15
            time = 300  # 5 minutes
            reasoning = f"High complexity due to {complex_count} complex keywords and {word_count} words"
        elif simple_count > complex_count and word_count < 20:
            complexity = 'low'
            steps = 3
            time = 30  # 30 seconds
            reasoning = f"Low complexity due to {simple_count} simple keywords and {word_count} words"
        else:
            complexity = 'medium'
            steps = 7
            time = 120  # 2 minutes
            reasoning = "Medium complexity based on keyword balance"

        return {
            'complexity': complexity,
            'estimated_steps': steps,
            'estimated_time_seconds': time,
            'confidence': 0.7,  # Fixed confidence for placeholder
            'reasoning': reasoning
        }

    def _default_response(self) -> Dict:
        """Default response for empty/invalid input"""
        return {
            'complexity': 'medium',
            'estimated_steps': 5,
            'estimated_time_seconds': 60,
            'confidence': 0.5,
            'reasoning': 'Default estimate (no task description provided)'
        }

# Singleton instance
analyzer = TaskComplexityAnalyzer()

def analyze_task_complexity(task_description: str) -> Dict:
    """Convenience function for analyzing task complexity"""
    return analyzer.analyze(task_description)
EOF

# Create api_usage_tracker.py
cat > backend/app/services/api_usage_tracker.py << 'EOF'
"""
API Usage Tracker for Agent Runtime
Tracks API calls, token usage, and costs for monitoring and billing
"""
import time
from typing import Dict, Optional
from datetime import datetime
import json

class APIUsageTracker:
    """
    Tracks API usage metrics for agent executions

    Metrics tracked:
    - API calls count
    - Tokens used (input + output)
    - Estimated cost
    - Execution time
    """

    # Pricing per 1K tokens (rough estimates, update with actual pricing)
    PRICING = {
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
        'claude-3-opus': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'qwen2.5-coder:7b': {'input': 0.0, 'output': 0.0},  # Free (local)
        'default': {'input': 0.001, 'output': 0.002}
    }

    def __init__(self):
        self.usage_data = {
            'session_start': datetime.now().isoformat(),
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost_usd': 0.0,
            'calls_by_model': {},
            'execution_time_seconds': 0.0
        }

    def track_call(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        execution_time: Optional[float] = None
    ):
        """
        Track an API call

        Args:
            model: Model name (e.g., 'gpt-4', 'claude-3-sonnet')
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            execution_time: Execution time in seconds
        """
        self.usage_data['total_calls'] += 1
        self.usage_data['total_input_tokens'] += input_tokens
        self.usage_data['total_output_tokens'] += output_tokens

        if execution_time:
            self.usage_data['execution_time_seconds'] += execution_time

        # Calculate cost
        pricing = self.PRICING.get(model, self.PRICING['default'])
        cost = (
            (input_tokens / 1000) * pricing['input'] +
            (output_tokens / 1000) * pricing['output']
        )
        self.usage_data['total_cost_usd'] += cost

        # Track by model
        if model not in self.usage_data['calls_by_model']:
            self.usage_data['calls_by_model'][model] = {
                'count': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'cost_usd': 0.0
            }

        model_data = self.usage_data['calls_by_model'][model]
        model_data['count'] += 1
        model_data['input_tokens'] += input_tokens
        model_data['output_tokens'] += output_tokens
        model_data['cost_usd'] += cost

    def get_usage_summary(self) -> Dict:
        """
        Get usage summary

        Returns:
            dict: Complete usage statistics
        """
        return dict(self.usage_data)

    def export_to_json(self, filepath: str):
        """Export usage data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.usage_data, f, indent=2)

    def reset(self):
        """Reset usage tracking"""
        self.__init__()

# Singleton instance
tracker = APIUsageTracker()

def track_api_call(model: str, input_tokens: int = 0, output_tokens: int = 0, execution_time: Optional[float] = None):
    """Convenience function for tracking API calls"""
    tracker.track_call(model, input_tokens, output_tokens, execution_time)

def get_usage_summary() -> Dict:
    """Convenience function for getting usage summary"""
    return tracker.get_usage_summary()
EOF

# Ensure __init__.py exists
touch backend/app/services/__init__.py

echo "✅ Missing agent runtime files created"
echo "   - task_complexity_analyzer.py"
echo "   - api_usage_tracker.py"
echo "   - __init__.py"
```

### Step 3: Add .gitattributes (Prevent Future Issues)

```bash
#!/bin/bash
# File: scripts/setup/add-gitattributes.sh

echo "============================================"
echo "Adding .gitattributes for Line Ending Control"
echo "============================================"

cat > .gitattributes << 'EOF'
# Git Attributes for Cross-Platform Development
# Ensures consistent line endings across Windows/WSL2/Linux/Mac

# Shell scripts - MUST use LF (Unix)
*.sh text eol=lf

# Python - use LF
*.py text eol=lf

# Docker - use LF
Dockerfile* text eol=lf

# Makefile - MUST use LF
Makefile text eol=lf
makefile text eol=lf

# Configuration files - use LF
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.toml text eol=lf
*.ini text eol=lf
*.conf text eol=lf
*.cfg text eol=lf
.env* text eol=lf

# Documentation - use LF
*.md text eol=lf
*.txt text eol=lf
*.rst text eol=lf

# Web files - use LF
*.html text eol=lf
*.css text eol=lf
*.scss text eol=lf
*.js text eol=lf
*.jsx text eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.vue text eol=lf

# SQL - use LF
*.sql text eol=lf

# Binary files - no conversion
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.svg binary
*.pdf binary
*.zip binary
*.tar binary
*.gz binary
*.bz2 binary
*.7z binary
*.mp4 binary
*.mov binary
*.mp3 binary
*.woff binary
*.woff2 binary
*.ttf binary
*.eot binary
EOF

echo "✅ .gitattributes created"
echo ""
echo "To normalize existing files, run:"
echo "  git add --renormalize ."
echo "  git commit -m 'chore: normalize line endings'"
```

### Step 4: Validate Fine-Tuning Container

```bash
#!/bin/bash
# File: scripts/setup/validate-finetuning-container.sh

echo "============================================"
echo "Validating Fine-Tuning Container"
echo "============================================"

# Check if Dockerfile.finetuning-runtime exists
if [ ! -f "backend/Dockerfile.finetuning-runtime" ]; then
    echo "❌ ERROR: Dockerfile.finetuning-runtime not found"
    exit 1
fi

# Check for required files referenced in Dockerfile
echo "Checking required files..."

REQUIRED_FILES=(
    "backend/requirements-finetuning.txt"
    "backend/entrypoint_finetuning.py"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ Found: $file"
    else
        echo "  ✗ Missing: $file"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: ${#MISSING_FILES[@]} required files missing for fine-tuning container"
    echo ""
    echo "Missing files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    echo ""
    echo "Fine-tuning container may fail to build."
    echo "Review backend/Dockerfile.finetuning-runtime and create missing files."
    exit 1
else
    echo ""
    echo "✅ All required files found for fine-tuning container"
fi

# Try building the container (optional)
if [ "$1" == "--build" ]; then
    echo ""
    echo "Attempting to build fine-tuning container..."
    docker build -f backend/Dockerfile.finetuning-runtime -t test-finetuning-runtime backend/

    if [ $? -eq 0 ]; then
        echo "✅ Fine-tuning container built successfully"
        docker rmi test-finetuning-runtime
    else
        echo "❌ Fine-tuning container build failed"
        exit 1
    fi
fi
```

---

## Updated Fresh Installation Procedure

### Complete Fresh Install Script

```bash
#!/bin/bash
# File: scripts/setup/initialize-fresh-install-FIXED.sh
# Version: 2.0 - WSL2/Windows Compatible

set -e  # Exit on error

echo "============================================================"
echo "  Enterprise RAG Chatbot - Fresh Installation (v2.0)"
echo "  WSL2/Windows Compatible with Line Ending Fixes"
echo "============================================================"
echo ""

# Step 0: Fix Line Endings (CRITICAL for WSL2)
echo "Step 0: Fixing line endings for WSL2 compatibility..."
./scripts/setup/fix-line-endings.sh

# Step 1: Create Missing Agent Files
echo ""
echo "Step 1: Creating missing agent runtime files..."
./scripts/setup/create-missing-agent-files.sh

# Step 2: Validate Fine-Tuning Container
echo ""
echo "Step 2: Validating fine-tuning container files..."
./scripts/setup/validate-finetuning-container.sh || echo "⚠️  Fine-tuning validation warnings (continuing...)"

# Step 3: Add Git Attributes
echo ""
echo "Step 3: Adding .gitattributes for future protection..."
./scripts/setup/add-gitattributes.sh

# Step 4: Build Docker Images
echo ""
echo "Step 4: Building Docker images..."
docker-compose build backend frontend

# Step 5: Start Infrastructure Services
echo ""
echo "Step 5: Starting infrastructure services..."
docker-compose up -d postgres redis minio elasticsearch

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Step 6: Initialize Database
echo ""
echo "Step 6: Initializing database..."
./scripts/setup/setup-database-complete-FIXED.sh

# Step 7: Start Application Services
echo ""
echo "Step 7: Starting application services..."
docker-compose up -d backend frontend ollama

# Step 8: Start Monitoring Stack (Optional)
if [ "$1" != "--skip-monitoring" ]; then
    echo ""
    echo "Step 8: Starting monitoring stack..."
    docker-compose up -d prometheus grafana tempo loki
fi

# Step 9: Validation
echo ""
echo "Step 9: Validating installation..."
sleep 5

echo "Checking service health..."
docker-compose ps

echo ""
echo "============================================================"
echo "✅ Fresh Installation Complete!"
echo "============================================================"
echo ""
echo "Services:"
echo "  Frontend:    http://localhost:3001"
echo "  Backend API: http://localhost:8000/api/docs"
echo "  Grafana:     http://localhost:3000 (admin/admin)"
echo "  MinIO:       http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "Next Steps:"
echo "  1. Verify all services are running: docker-compose ps"
echo "  2. Check logs if needed: docker-compose logs -f backend"
echo "  3. Access frontend and create your first user"
echo ""
```

---

## Summary of All Fixes

| Issue | Severity | Fix | Script |
|-------|----------|-----|--------|
| DOS line endings | 🔴 CRITICAL | dos2unix conversion | `fix-line-endings.sh` |
| Missing agent files | 🔴 CRITICAL | Create placeholders | `create-missing-agent-files.sh` |
| Fine-tuning validation | 🟡 MEDIUM | Validate files | `validate-finetuning-container.sh` |
| Future prevention | 🟢 LOW | Add .gitattributes | `add-gitattributes.sh` |
| Database migration 008 | 🟡 MEDIUM | Fixed migrations | Already completed |

---

## Testing Checklist

After implementing fixes, verify:

- [ ] All shell scripts execute without "cannot execute" errors
- [ ] `docker-compose build` completes without file not found errors
- [ ] Agent-runtime container builds successfully
- [ ] Fine-tuning container builds successfully (or skip with warnings)
- [ ] Database setup completes without migration errors
- [ ] All services start: `docker-compose up -d`
- [ ] Frontend accessible at http://localhost:3001
- [ ] Backend API accessible at http://localhost:8000/api/docs
- [ ] Can create user and login
- [ ] File upload works
- [ ] Chat query works

---

## Files to Create

1. **scripts/setup/fix-line-endings.sh** (Step 1 fix)
2. **scripts/setup/create-missing-agent-files.sh** (Step 2 fix)
3. **scripts/setup/validate-finetuning-container.sh** (Step 3 validation)
4. **scripts/setup/add-gitattributes.sh** (Step 4 prevention)
5. **.gitattributes** (root directory)
6. **backend/app/services/task_complexity_analyzer.py** (generated by script 2)
7. **backend/app/services/api_usage_tracker.py** (generated by script 2)
8. **scripts/setup/initialize-fresh-install-FIXED.sh** (updated installation script)

---

**Status**: ✅ **COMPLETE ANALYSIS** - Ready for Implementation
**Next Action**: Create the 8 files listed above and test fresh installation

