#!/bin/bash
# RAG Pipeline Debug Helper Script
# Easy wrapper for debug_rag_pipeline.py

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if backend container is running
check_backend() {
    if ! docker-compose ps backend | grep -q "Up"; then
        echo -e "${RED}Error: Backend container is not running${NC}"
        echo "Start with: docker-compose up -d backend"
        exit 1
    fi
}

# Show usage
show_usage() {
    echo -e "${BLUE}RAG Pipeline Debug Tool${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 query \"your question here\"              # Debug a specific query"
    echo "  $0 trace \"your question\" [session-id]      # Full pipeline trace"
    echo "  $0 docs                                     # Analyze all documents"
    echo "  $0 chunks                                   # Analyze document chunks"
    echo "  $0 pgvector                                 # Check pgvector installation"
    echo "  $0 embedding \"test text\"                   # Test embedding generation"
    echo "  $0 full                                     # Run all checks"
    echo ""
    echo "Examples:"
    echo "  $0 query \"what is the revenue of TCS?\""
    echo "  $0 trace \"tell me about TCS\" abc123"
    echo "  $0 docs"
    echo ""
}

# Run in Docker container
run_in_docker() {
    docker-compose exec -T backend python /app/debug_rag_pipeline.py "$@"
}

# Main logic
case "${1:-}" in
    query)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Query text required${NC}"
            echo "Usage: $0 query \"your question\""
            exit 1
        fi
        check_backend
        echo -e "${GREEN}Debugging query: $2${NC}"
        run_in_docker "$2" "${@:3}"
        ;;

    trace)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Query text required${NC}"
            echo "Usage: $0 trace \"your question\" [session-id]"
            exit 1
        fi
        check_backend
        echo -e "${GREEN}Full pipeline trace for: $2${NC}"
        if [ -n "$3" ]; then
            run_in_docker "$2" --session-id "$3" --full-trace
        else
            run_in_docker "$2" --full-trace
        fi
        ;;

    docs|documents)
        check_backend
        echo -e "${GREEN}Analyzing documents...${NC}"
        run_in_docker --analyze-documents
        ;;

    chunks)
        check_backend
        echo -e "${GREEN}Analyzing chunks...${NC}"
        run_in_docker --analyze-chunks
        ;;

    pgvector|vector)
        check_backend
        echo -e "${GREEN}Checking pgvector installation...${NC}"
        run_in_docker --check-pgvector
        ;;

    embedding)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Text required${NC}"
            echo "Usage: $0 embedding \"your text\""
            exit 1
        fi
        check_backend
        echo -e "${GREEN}Testing embedding for: $2${NC}"
        run_in_docker --test-embedding "$2"
        ;;

    full|all)
        check_backend
        echo -e "${GREEN}Running full diagnostic suite...${NC}"
        echo ""
        echo -e "${BLUE}=== Checking pgvector ===${NC}"
        run_in_docker --check-pgvector
        echo ""
        echo -e "${BLUE}=== Analyzing documents ===${NC}"
        run_in_docker --analyze-documents
        echo ""
        echo -e "${BLUE}=== Analyzing chunks ===${NC}"
        run_in_docker --analyze-chunks
        ;;

    help|--help|-h|"")
        show_usage
        ;;

    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
