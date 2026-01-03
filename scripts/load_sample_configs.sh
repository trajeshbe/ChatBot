#!/bin/bash

# Load Sample Module Configurations
# Purpose: Upload sample configurations to the database via API

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_BASE="http://localhost:8000/api/v1/module-config"

echo "=========================================="
echo "Loading Sample Module Configurations"
echo "=========================================="
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Backend is not running on http://localhost:8000${NC}"
    echo "Please start the backend first: docker-compose up -d backend"
    exit 1
fi

echo -e "${GREEN}✓ Backend is running${NC}"
echo ""

# Function to load a config file
load_config() {
    local config_file=$1
    local module_name=$(basename "$config_file" .json | sed 's/_config$//')

    echo "Loading configuration: $module_name"
    echo "File: $config_file"

    if [ ! -f "$config_file" ]; then
        echo -e "${RED}✗ File not found: $config_file${NC}"
        return 1
    fi

    # Try to create the configuration
    response=$(curl -s -X POST "$API_BASE/modules" \
        -H "Content-Type: application/json" \
        -d @"$config_file" 2>&1)

    if echo "$response" | jq -e '.module_name' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Successfully loaded: $module_name${NC}"
        return 0
    elif echo "$response" | grep -q "already exists\|duplicate"; then
        echo -e "${YELLOW}⚠ Already exists: $module_name (skipping)${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to load: $module_name${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Load all config files from sample_configs directory
CONFIG_DIR="sample_configs"

if [ ! -d "$CONFIG_DIR" ]; then
    echo -e "${YELLOW}⚠ Config directory not found: $CONFIG_DIR${NC}"
    echo "Creating directory..."
    mkdir -p "$CONFIG_DIR"
    echo ""
    echo "Please add JSON config files to $CONFIG_DIR/ and run this script again."
    exit 1
fi

# Count config files
config_count=$(find "$CONFIG_DIR" -name "*.json" -type f | wc -l)

if [ "$config_count" -eq 0 ]; then
    echo -e "${YELLOW}⚠ No config files found in $CONFIG_DIR${NC}"
    echo ""
    echo "Example config files should have names like:"
    echo "  - talent_search_config.json"
    echo "  - british_council_config.json"
    echo "  - procurement_matcher_config.json"
    exit 1
fi

echo "Found $config_count configuration file(s)"
echo ""

# Load each config file
success_count=0
fail_count=0
skip_count=0

for config_file in "$CONFIG_DIR"/*.json; do
    if load_config "$config_file"; then
        if echo "$config_file" | grep -q "already exists"; then
            ((skip_count++))
        else
            ((success_count++))
        fi
    else
        ((fail_count++))
    fi
    echo ""
done

# Summary
echo "=========================================="
echo "Loading Complete"
echo "=========================================="
echo ""
echo -e "${GREEN}✓ Successfully loaded: $success_count${NC}"
if [ "$skip_count" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Already existed: $skip_count${NC}"
fi
if [ "$fail_count" -gt 0 ]; then
    echo -e "${RED}✗ Failed: $fail_count${NC}"
fi
echo ""

# List all loaded modules
echo "Listing all configured modules:"
echo "-------------------------------"
curl -s "$API_BASE/modules" | jq -r '.[] | "- \(.module_name) (\(.display_name))"' 2>/dev/null || echo "Could not list modules"

echo ""
echo -e "${GREEN}Done! 🎉${NC}"
echo ""
echo "Next steps:"
echo "1. View configurations: curl http://localhost:8000/api/v1/module-config/modules"
echo "2. Test a specific module: curl http://localhost:8000/api/v1/module-config/modules/talent_search"
echo "3. Open API docs: http://localhost:8000/api/docs"
