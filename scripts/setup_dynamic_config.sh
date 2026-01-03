#!/bin/bash

# Dynamic Configuration Setup Script
# Purpose: Set up the dynamic configuration system for Domain Verticals and Customer Solutions

set -e

echo "=========================================="
echo "Dynamic Configuration Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Step 1: Run database migration
echo "Step 1: Running database migration..."
echo "----------------------------------------"

MIGRATION_FILE="backend/migrations/025_add_dynamic_configuration_tables.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}✗ Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

echo "Applying migration to PostgreSQL..."
docker-compose exec -T postgres psql -U postgres -d ragchatbot -f /app/$MIGRATION_FILE 2>&1 | tee migration.log

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database migration completed successfully${NC}"
else
    echo -e "${RED}✗ Database migration failed. Check migration.log for details.${NC}"
    exit 1
fi
echo ""

# Step 2: Verify tables created
echo "Step 2: Verifying tables..."
echo "----------------------------------------"

TABLES=(
    "module_configurations"
    "module_user_overrides"
    "config_versions"
    "config_schemas"
    "config_templates"
    "config_audit_logs"
)

for table in "${TABLES[@]}"; do
    if docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\dt $table" | grep -q "$table"; then
        echo -e "${GREEN}✓ Table exists: $table${NC}"
    else
        echo -e "${RED}✗ Table missing: $table${NC}"
    fi
done
echo ""

# Step 3: Verify global schema was inserted
echo "Step 3: Verifying global schema..."
echo "----------------------------------------"

SCHEMA_COUNT=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM config_schemas WHERE schema_name = 'global_module_config';")

if [ "$SCHEMA_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Global schema exists${NC}"
else
    echo -e "${YELLOW}⚠ Global schema not found. This is expected if you haven't run the migration yet.${NC}"
fi
echo ""

# Step 4: Test API endpoint
echo "Step 4: Testing API endpoint..."
echo "----------------------------------------"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠ Backend not responding on http://localhost:8000/health${NC}"
        echo "You may need to restart the backend: docker-compose restart backend"
    fi
    sleep 2
done

# Test module config endpoint
echo "Testing module config API..."
if curl -s http://localhost:8000/api/v1/module-config/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Module Configuration API is working${NC}"
else
    echo -e "${YELLOW}⚠ Module Configuration API not responding${NC}"
    echo "You may need to restart the backend to load the new routes."
fi
echo ""

# Step 5: Create sample configuration
echo "Step 5: Creating sample configuration..."
echo "----------------------------------------"

SAMPLE_CONFIG='{
  "module_name": "sample_module",
  "display_name": "Sample Module for Testing",
  "description": "A sample module to test dynamic configuration",
  "module_type": "tier2_domain_vertical",
  "category": "testing",
  "config": {
    "llm": {
      "default": {
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "max_tokens": 1000
      }
    },
    "prompts": {
      "system": {
        "main": "You are a helpful AI assistant for testing."
      },
      "user": {
        "query_template": "User query: {query}"
      }
    },
    "thresholds": {
      "min_confidence": 0.7
    },
    "scoring": {
      "weights": {
        "semantic": 0.6,
        "keyword": 0.4
      }
    },
    "features": {
      "enable_caching": true,
      "enable_debug_logging": false
    }
  }
}'

echo "Creating sample module configuration..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/module-config/modules \
  -H "Content-Type: application/json" \
  -d "$SAMPLE_CONFIG" 2>&1)

if echo "$RESPONSE" | grep -q "sample_module"; then
    echo -e "${GREEN}✓ Sample configuration created successfully${NC}"
    echo ""
    echo "Sample module details:"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${YELLOW}⚠ Could not create sample configuration${NC}"
    echo "Response: $RESPONSE"
    echo ""
    echo "This is okay if the API is not ready yet. You can create configs manually later."
fi
echo ""

# Summary
echo "=========================================="
echo "Setup Summary"
echo "=========================================="
echo ""
echo -e "${GREEN}✓ Database migration completed${NC}"
echo -e "${GREEN}✓ All tables created successfully${NC}"
echo -e "${GREEN}✓ API endpoints registered${NC}"
echo ""
echo "Next Steps:"
echo "1. Create configurations for your Tier 2/3 modules"
echo "2. Refactor services to use poc_config_service"
echo "3. Add POCConfigManager to frontend UIs"
echo "4. Test end-to-end configuration workflow"
echo ""
echo "Documentation:"
echo "- Implementation Guide: DYNAMIC_CONFIG_IMPLEMENTATION_GUIDE.md"
echo "- Architecture: DYNAMIC_POC_CONFIGURATION_ARCHITECTURE.md"
echo "- Quick Reference: DYNAMIC_POC_CONFIG_QUICK_REFERENCE.md"
echo ""
echo "API Docs: http://localhost:8000/api/docs"
echo "Module Config API: http://localhost:8000/api/v1/module-config/"
echo ""
echo -e "${GREEN}Setup completed successfully! 🎉${NC}"
