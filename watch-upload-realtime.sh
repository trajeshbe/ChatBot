#!/bin/bash

echo "=========================================="
echo "  Watch Upload Logs in Real-Time"
echo "=========================================="
echo ""
echo "Monitoring backend logs for upload activity..."
echo "Upload a file in the UI now and watch what happens below:"
echo ""
echo "=========================================="
echo ""

# Follow backend logs, filtering for relevant info
docker compose logs backend -f 2>&1 | grep -i --line-buffered "upload\|document\|process\|chunk\|embed\|error\|exception\|minio\|session" | grep -v "opentelemetry\|tempo:4317"
