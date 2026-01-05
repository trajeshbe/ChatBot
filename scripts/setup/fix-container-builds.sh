#!/bin/bash
set -e

echo "==================================="
echo "Container Build Fixes - Complete"
echo "==================================="
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Fix 1: Create agent-runtime service files
echo "📝 Step 1: Creating agent-runtime service files..."
mkdir -p backend/app/services

# Create task_complexity_analyzer.py
if [ ! -f backend/app/services/task_complexity_analyzer.py ]; then
    cat > backend/app/services/task_complexity_analyzer.py << 'COMPLEXITY_EOF'
"""Task Complexity Analyzer for Agent Runtime"""
from typing import Dict, Any

class TaskComplexityAnalyzer:
    """Analyzes task complexity for agent runtime resource allocation"""

    COMPLEX_KEYWORDS = ['analyze', 'investigate', 'research', 'comprehensive', 'deep dive',
                       'evaluate', 'assess', 'compare', 'benchmark', 'optimize']
    SIMPLE_KEYWORDS = ['list', 'show', 'display', 'get', 'fetch', 'retrieve', 'view']

    def __init__(self):
        self.complexity_cache = {}

    def analyze(self, task_description: str) -> Dict[str, Any]:
        """Analyze task complexity and resource requirements"""
        text = task_description.lower()
        complex_score = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in text)
        simple_score = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in text)
        word_count = len(text.split())

        if complex_score >= 2 or word_count > 100:
            level, tokens, timeout = "high", 4000, 300
        elif complex_score >= 1 or word_count > 50:
            level, tokens, timeout = "medium", 2000, 120
        else:
            level, tokens, timeout = "low", 1000, 60

        return {
            "complexity_level": level,
            "complexity_score": complex_score - simple_score,
            "estimated_tokens": tokens,
            "recommended_timeout_seconds": timeout,
            "word_count": word_count,
            "requires_reasoning": complex_score > 0
        }

complexity_analyzer = TaskComplexityAnalyzer()
COMPLEXITY_EOF
    echo "✅ Created task_complexity_analyzer.py"
else
    echo "ℹ️  task_complexity_analyzer.py already exists"
fi

# Create api_usage_tracker.py
if [ ! -f backend/app/services/api_usage_tracker.py ]; then
    cat > backend/app/services/api_usage_tracker.py << 'TRACKER_EOF'
"""API Usage Tracker for Agent Runtime"""
from typing import Dict, Any, Optional
from datetime import datetime

class APIUsageTracker:
    """Track API usage metrics for cost monitoring"""

    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "ollama": {"input": 0.0, "output": 0.0}
    }

    def __init__(self):
        self.usage_log = []
        self.session_stats = {}

    def track_call(self, model: str, input_tokens: int, output_tokens: int,
                   execution_time: float, session_id: Optional[str] = None,
                   task_type: str = "general", success: bool = True) -> Dict[str, Any]:
        """Track an API call with cost calculation"""
        pricing = self.PRICING.get(model, {"input": 0.01, "output": 0.01})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "model": model,
            "task_type": task_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "execution_time_seconds": execution_time,
            "cost_usd": round(total_cost, 6),
            "success": success
        }

        self.usage_log.append(record)

        if session_id:
            if session_id not in self.session_stats:
                self.session_stats[session_id] = {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_time": 0.0
                }
            stats = self.session_stats[session_id]
            stats["total_calls"] += 1
            stats["total_tokens"] += input_tokens + output_tokens
            stats["total_cost"] += total_cost
            stats["total_time"] += execution_time

        return record

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a session"""
        return self.session_stats.get(session_id, {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_time": 0.0
        })

usage_tracker = APIUsageTracker()
TRACKER_EOF
    echo "✅ Created api_usage_tracker.py"
else
    echo "ℹ️  api_usage_tracker.py already exists"
fi

# Create __init__.py
cat > backend/app/services/__init__.py << 'INIT_EOF'
"""Services Package - Core service modules for agent runtime"""
from .task_complexity_analyzer import TaskComplexityAnalyzer, complexity_analyzer
from .api_usage_tracker import APIUsageTracker, usage_tracker

__all__ = [
    'TaskComplexityAnalyzer',
    'complexity_analyzer',
    'APIUsageTracker',
    'usage_tracker',
]
INIT_EOF
echo "✅ Created services/__init__.py"

# Fix 2: Update finetuning-runtime Dockerfile path
echo ""
echo "🔧 Step 2: Fixing finetuning-runtime Dockerfile path..."

if [ -f backend/Dockerfile.finetuning-runtime ]; then
    if grep -q "COPY app/services/finetuning/trainers" backend/Dockerfile.finetuning-runtime 2>/dev/null; then
        # Backup original
        cp backend/Dockerfile.finetuning-runtime backend/Dockerfile.finetuning-runtime.backup
        echo "📋 Created backup: Dockerfile.finetuning-runtime.backup"

        # Fix path (source)
        sed -i.tmp 's|COPY app/services/finetuning/trainers/|COPY app/tier_1/finetuning/trainers/|g' backend/Dockerfile.finetuning-runtime

        # Fix path (destination)
        sed -i.tmp 's|/app/app/services/finetuning/trainers/|/app/app/tier_1/finetuning/trainers/|g' backend/Dockerfile.finetuning-runtime

        # Remove temp file
        rm -f backend/Dockerfile.finetuning-runtime.tmp

        echo "✅ Fixed finetuning-runtime Dockerfile paths"
    else
        echo "ℹ️  finetuning-runtime Dockerfile path already correct"
    fi
else
    echo "⚠️  Dockerfile.finetuning-runtime not found (may not exist yet)"
fi

# Verify fixes
echo ""
echo "🔍 Step 3: Verifying fixes..."

# Check agent-runtime files
if [ -f backend/app/services/task_complexity_analyzer.py ] && \
   [ -f backend/app/services/api_usage_tracker.py ] && \
   [ -f backend/app/services/__init__.py ]; then
    echo "✅ Agent-runtime service files exist"
else
    echo "❌ Agent-runtime service files incomplete"
    exit 1
fi

# Check finetuning trainers exist
if [ -d backend/app/tier_1/finetuning/trainers ]; then
    trainer_count=$(find backend/app/tier_1/finetuning/trainers -name "*.py" -type f 2>/dev/null | wc -l)
    echo "✅ Fine-tuning trainers directory exists ($trainer_count trainers found)"
else
    echo "⚠️  Fine-tuning trainers directory not found (may not be needed)"
fi

echo ""
echo "==================================="
echo "✅ Container build fixes complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Rebuild containers:"
echo "   docker-compose build agent-runtime"
echo "   docker-compose --profile finetuning build finetuning-runtime"
echo ""
echo "2. For fine-tuning trainer (if separate build needed):"
echo "   docker build -t chatbot-finetuning-trainer:v1.0.5 \\"
echo "     -f backend/Dockerfile.finetuning-trainer backend/"
echo ""
echo "3. Verify builds:"
echo "   docker images | grep -E '(agent-runtime|finetuning)'"
echo ""
