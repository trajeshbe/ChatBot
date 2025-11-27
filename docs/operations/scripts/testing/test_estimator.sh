#!/bin/bash

curl -X POST http://localhost:8000/api/v1/project-estimator/generate-agentic \
  -F "project_scope=Build a simple chatbot with RAG capabilities for customer support" \
  -F "project_type=POC" \
  -F "scenario=baseline" \
  -F 'rate_config={"developer":100,"architect":150,"qa":80}' \
  | jq . > /tmp/project_estimator_result.json

cat /tmp/project_estimator_result.json
