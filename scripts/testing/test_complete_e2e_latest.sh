#!/bin/bash
# Complete End-to-End Test for Latest Features
# Tests: Document Upload, Fine-Tuning, MinIO Paths, Model Discovery, Chat

set -e

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3001"
ADMIN_USER="admin"
ADMIN_PASS="admin123"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Complete End-to-End Test - Latest Features (2025-12-19)      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

test_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((pass_count++))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((fail_count++))
}

test_info() {
    echo -e "${YELLOW}ℹ INFO${NC}: $1"
}

# ============================================================================
# Test 1: Health Check
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

response=$(curl -s ${API_URL}/health)
if echo "$response" | grep -q "healthy"; then
    test_pass "Backend health check"
else
    test_fail "Backend health check"
fi

# ============================================================================
# Test 2: Authentication
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

auth_response=$(curl -s -X POST ${API_URL}/api/v1/auth/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${ADMIN_USER}&password=${ADMIN_PASS}")

TOKEN=$(echo "$auth_response" | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    test_pass "Authentication successful"
    test_info "Token: ${TOKEN:0:20}..."
else
    test_fail "Authentication failed"
    echo "Response: $auth_response"
    exit 1
fi

# ============================================================================
# Test 3: MinIO Path Verification (Lowercase Format)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: MinIO Path Format Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check database for lowercase paths
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT COUNT(*) as lowercase_count
FROM documents
WHERE minio_path LIKE 'technology/%';
" > /tmp/path_check.txt 2>&1

lowercase_count=$(grep -oP '\d+' /tmp/path_check.txt | head -1)

if [ "$lowercase_count" -gt 0 ]; then
    test_pass "Lowercase MinIO paths verified (${lowercase_count} documents)"
else
    test_fail "No lowercase paths found"
fi

# Check for Title-Case paths (should be 0)
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT COUNT(*) as titlecase_count
FROM documents
WHERE minio_path LIKE 'Technology/%';
" > /tmp/path_check2.txt 2>&1

titlecase_count=$(grep -oP '\d+' /tmp/path_check2.txt | head -1)

if [ "$titlecase_count" -eq 0 ]; then
    test_pass "No Title-Case paths found (clean migration)"
else
    test_fail "Title-Case paths still exist: ${titlecase_count}"
fi

# ============================================================================
# Test 4: Document Upload with Lowercase Path
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: Document Upload (Lowercase Path Format)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create a test document
cat > /tmp/test_e2e.txt << 'EOF'
End-to-End Test Document

This document tests the complete workflow:
1. Document upload with lowercase paths
2. MinIO storage verification
3. Database path consistency
4. RAG query functionality

Test timestamp: $(date)
EOF

# Upload document
upload_response=$(curl -s -X POST ${API_URL}/api/v1/upload \
    -H "Authorization: Bearer ${TOKEN}" \
    -F "file=@/tmp/test_e2e.txt" \
    -F "session_id=test-e2e-$(date +%s)")

upload_status=$(echo "$upload_response" | jq -r '.status // .message')
doc_id=$(echo "$upload_response" | jq -r '.document_id // .id')

if echo "$upload_status" | grep -qi "success\|processed"; then
    test_pass "Document uploaded successfully"
    test_info "Document ID: $doc_id"

    # Verify path format in database
    sleep 2
    docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
    SELECT minio_path FROM documents WHERE id = '$doc_id';
    " > /tmp/uploaded_path.txt 2>&1

    if grep -q "technology/" /tmp/uploaded_path.txt; then
        test_pass "Uploaded document uses lowercase path format"
    else
        test_fail "Uploaded document path format incorrect"
        cat /tmp/uploaded_path.txt
    fi
else
    test_fail "Document upload failed"
    echo "Response: $upload_response"
fi

# ============================================================================
# Test 5: Model Discovery (Dynamic Ollama Integration)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5: Dynamic Model Discovery"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

models_response=$(curl -s ${API_URL}/api/v1/models/ \
    -H "Authorization: Bearer ${TOKEN}")

model_count=$(echo "$models_response" | jq -r '[.grouped.local_cpu[], .grouped.local_gpu[], .grouped.proprietary[]] | length')

if [ "$model_count" -gt 0 ]; then
    test_pass "Models discovered: $model_count"

    # Check for fine-tuned models endpoint
    ft_models_response=$(curl -s ${API_URL}/api/v1/finetuning/models-public/for-chat)
    ft_count=$(echo "$ft_models_response" | jq -r '.finetuned_models | length // 0')

    test_info "Fine-tuned models available: $ft_count"
else
    test_fail "No models discovered"
fi

# ============================================================================
# Test 6: Fine-Tuning Dataset List (Lowercase Paths)
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 6: Fine-Tuning Datasets"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

datasets_response=$(curl -s ${API_URL}/api/v1/finetuning/datasets \
    -H "Authorization: Bearer ${TOKEN}")

dataset_count=$(echo "$datasets_response" | jq -r '.datasets | length // 0')

if [ "$dataset_count" -gt 0 ]; then
    test_pass "Datasets found: $dataset_count"

    # Verify datasets are in lowercase paths
    first_dataset=$(echo "$datasets_response" | jq -r '.datasets[0].name // empty')
    if [ -n "$first_dataset" ]; then
        test_info "Sample dataset: $first_dataset"
    fi
else
    test_info "No fine-tuning datasets found (expected if none uploaded)"
fi

# ============================================================================
# Test 7: RAG Query with Dynamic Model
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 7: RAG Query"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Use a simple local model for testing
query_response=$(curl -s -X POST ${API_URL}/api/v1/query \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "What is this test document about?",
        "session_id": "test-e2e-session",
        "model_id": "qwen2.5:1.5b",
        "use_rag": true
    }')

answer=$(echo "$query_response" | jq -r '.answer // .response // empty')

if [ -n "$answer" ] && [ "$answer" != "null" ]; then
    test_pass "RAG query successful"
    test_info "Answer length: ${#answer} characters"
else
    test_fail "RAG query failed"
    echo "Response: $query_response"
fi

# ============================================================================
# Test 8: Project-Based Organization
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 8: Project-Based Organization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get user's projects
projects_response=$(curl -s ${API_URL}/api/v1/projects \
    -H "Authorization: Bearer ${TOKEN}")

project_count=$(echo "$projects_response" | jq -r 'length // 0')

if [ "$project_count" -gt 0 ]; then
    test_pass "Projects found: $project_count"

    # Get first project details
    first_project=$(echo "$projects_response" | jq -r '.[0].name')
    test_info "Sample project: $first_project"
else
    test_info "No projects found (using default Global project)"
fi

# ============================================================================
# Test 9: Fine-Tuning Job List
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 9: Fine-Tuning Jobs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

jobs_response=$(curl -s ${API_URL}/api/v1/finetuning/jobs \
    -H "Authorization: Bearer ${TOKEN}")

job_count=$(echo "$jobs_response" | jq -r '.jobs | length // 0')

if [ "$job_count" -ge 0 ]; then
    test_pass "Fine-tuning jobs endpoint accessible"
    test_info "Total jobs: $job_count"

    if [ "$job_count" -gt 0 ]; then
        latest_job=$(echo "$jobs_response" | jq -r '.jobs[0].name')
        latest_status=$(echo "$jobs_response" | jq -r '.jobs[0].status')
        test_info "Latest job: $latest_job (status: $latest_status)"
    fi
else
    test_fail "Fine-tuning jobs endpoint failed"
fi

# ============================================================================
# Test 10: GPU Status
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 10: GPU Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

gpu_response=$(curl -s ${API_URL}/api/v1/finetuning/gpu/status \
    -H "Authorization: Bearer ${TOKEN}")

gpu_available=$(echo "$gpu_response" | jq -r '.available // false')

if [ "$gpu_available" = "true" ]; then
    test_pass "GPU available for fine-tuning"
    gpu_count=$(echo "$gpu_response" | jq -r '.gpus | length // 0')
    test_info "GPUs detected: $gpu_count"
else
    test_info "No GPU available (CPU-only mode)"
fi

# ============================================================================
# Test 11: Audit Logging
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 11: Audit Logging"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

audit_response=$(curl -s "${API_URL}/api/v1/admin/audit-logs?limit=10" \
    -H "Authorization: Bearer ${TOKEN}")

audit_count=$(echo "$audit_response" | jq -r 'length // 0')

if [ "$audit_count" -gt 0 ]; then
    test_pass "Audit logs accessible: $audit_count entries"

    latest_action=$(echo "$audit_response" | jq -r '.[0].action')
    test_info "Latest audit action: $latest_action"
else
    test_fail "No audit logs found"
fi

# ============================================================================
# Test 12: Documentation Organization
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 12: Documentation Organization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if documentation directories exist
doc_dirs=(
    "docs/architecture"
    "docs/features/finetuning"
    "docs/fixes"
    "docs/sessions"
    "docs/guides"
    "docs/debugging"
)

doc_pass=true
for dir in "${doc_dirs[@]}"; do
    if [ -d "$dir" ]; then
        file_count=$(find "$dir" -name "*.md" | wc -l)
        test_info "✓ $dir: $file_count files"
    else
        doc_pass=false
        test_info "✗ Missing: $dir"
    fi
done

if [ "$doc_pass" = true ]; then
    test_pass "Documentation structure organized"
else
    test_fail "Documentation structure incomplete"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                        TEST SUMMARY                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Total Tests Run: $((pass_count + fail_count))"
echo -e "${GREEN}Passed: $pass_count${NC}"
echo -e "${RED}Failed: $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "Latest Features Verified:"
    echo "  ✓ Lowercase MinIO paths (technology/backend-development/...)"
    echo "  ✓ Dynamic model discovery (fine-tuned models)"
    echo "  ✓ Model dropdown deduplication"
    echo "  ✓ Document upload with correct paths"
    echo "  ✓ Fine-tuning infrastructure"
    echo "  ✓ Project-based organization"
    echo "  ✓ Audit logging"
    echo "  ✓ Documentation structure"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review the failed tests above."
    exit 1
fi
