#!/bin/bash
echo "=== Monitoring RAG Config Changes ==="
echo "Watching backend logs for threshold updates..."
echo ""

docker-compose logs backend -f --tail=0 2>&1 | grep --line-buffered -E "RAG Config:|top_k=|threshold=|Searching with threshold|Database status:|Found.*chunks|Classification:" | while read line; do
    timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] $line"
done
