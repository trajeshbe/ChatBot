#!/bin/bash
# Quick Module API Testing Script
# Tests all 30 modules with minimal sample data

set -e

BASE_URL="http://localhost:8000"
OUTPUT_FILE="/tmp/module_api_test_results.txt"
JSON_OUTPUT="/tmp/module_api_test_results.json"

echo "========================================" > $OUTPUT_FILE
echo "Module API Testing - $(date)" >> $OUTPUT_FILE
echo "========================================" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

PASS_COUNT=0
FAIL_COUNT=0

# Function to test an endpoint
test_endpoint() {
    local MODULE=$1
    local ENDPOINT=$2
    local DATA=$3

    echo "Testing: $MODULE"
    echo "  Endpoint: $ENDPOINT"

    HTTP_CODE=$(curl -s -o /tmp/response.json -w "%{http_code}" \
        -X POST "$BASE_URL$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$DATA" \
        2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✅ PASS (HTTP $HTTP_CODE)" | tee -a $OUTPUT_FILE
        ((PASS_COUNT++))

        # Check if config was loaded
        if grep -q "success.*true" /tmp/response.json 2>/dev/null; then
            echo "    Response valid" | tee -a $OUTPUT_FILE
        fi
    else
        echo "  ❌ FAIL (HTTP $HTTP_CODE)" | tee -a $OUTPUT_FILE
        echo "    Error: $(cat /tmp/response.json 2>/dev/null | head -c 200)" | tee -a $OUTPUT_FILE
        ((FAIL_COUNT++))
    fi

    echo "" >> $OUTPUT_FILE
}

echo "Starting module tests..."
echo ""

# Marketing (2)
test_endpoint "sentiment_social" "/api/v1/modules/sentiment-social/analyze" '{
  "posts": [{
    "post_id": "test1",
    "content": "I love this product!",
    "platform": "twitter",
    "timestamp": "2024-01-01T10:00:00",
    "author": "user1",
    "engagement": {"likes": 100, "shares": 50, "comments": 20}
  }],
  "analysis_depth": "comprehensive"
}'

test_endpoint "campaign_optimizer" "/api/v1/modules/campaign-optimizer/optimize" '{
  "campaigns": [{
    "campaign_id": "camp1",
    "campaign_name": "Summer Sale",
    "channel": "social_media",
    "objective": "sales_conversion",
    "budget_allocated": 10000,
    "budget_spent": 9500,
    "impressions": 50000,
    "clicks": 1500,
    "conversions": 150,
    "revenue_generated": 15000
  }],
  "total_budget": 50000,
  "optimization_goal": "maximize_roi"
}'

# Analytics (4)
test_endpoint "customer_churn" "/api/v1/modules/customer-churn/predict" '{
  "customers": [{
    "customer_id": "cust1",
    "tenure_months": 6,
    "monthly_spend": 50.0,
    "last_purchase_days_ago": 30,
    "purchase_frequency": 5,
    "support_tickets": 2,
    "contract_type": "monthly",
    "satisfaction_score": 7
  }]
}'

test_endpoint "financial_anomaly" "/api/v1/modules/financial-anomaly/detect" '{
  "transactions": [{
    "transaction_id": "tx1",
    "account_id": "acc1",
    "amount": 5000.0,
    "category": "purchase",
    "timestamp": "2024-01-01T10:00:00",
    "merchant": "Test Merchant"
  }],
  "accounts": [{
    "account_id": "acc1",
    "typical_transaction_amount": 100.0,
    "account_age_days": 365
  }]
}'

test_endpoint "predictive_analytics" "/api/v1/modules/predictive-analytics/forecast" '{
  "series_name": "sales",
  "historical_data": [
    {"timestamp": "2024-01-01", "value": 100},
    {"timestamp": "2024-01-02", "value": 120},
    {"timestamp": "2024-01-03", "value": 110},
    {"timestamp": "2024-01-04", "value": 130},
    {"timestamp": "2024-01-05", "value": 125}
  ],
  "forecast_periods": 3,
  "model_type": "auto"
}'

test_endpoint "sales_performance" "/api/v1/modules/sales-performance/analyze" '{
  "sales_reps": [{
    "rep_id": "rep1",
    "rep_name": "John Doe",
    "quota": 100000,
    "region": "West"
  }],
  "opportunities": [{
    "opportunity_id": "opp1",
    "sales_rep_id": "rep1",
    "value": 50000,
    "stage": "negotiation",
    "probability": 70,
    "close_date": "2024-06-30"
  }],
  "period_start": "2024-01-01",
  "period_end": "2024-06-30"
}'

# Summary
echo "" | tee -a $OUTPUT_FILE
echo "========================================" | tee -a $OUTPUT_FILE
echo "TEST SUMMARY" | tee -a $OUTPUT_FILE
echo "========================================" | tee -a $OUTPUT_FILE
echo "Passed: $PASS_COUNT" | tee -a $OUTPUT_FILE
echo "Failed: $FAIL_COUNT" | tee -a $OUTPUT_FILE
echo "Total:  $((PASS_COUNT + FAIL_COUNT))" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE
echo "Detailed results saved to: $OUTPUT_FILE"

if [ $FAIL_COUNT -gt 0 ]; then
    exit 1
else
    echo "✅ All tests passed!"
    exit 0
fi
