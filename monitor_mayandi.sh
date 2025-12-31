#!/bin/bash

JOB_ID="5e82184c-5859-4c56-8447-a9a902a68ee1"
CONTAINER_NAME="finetuning-${JOB_ID}"

echo "🔍 Monitoring Training Job: mayandi_manzil_1"
echo "Job ID: $JOB_ID"
echo "Started at: $(date)"
echo "=========================================="
echo ""

LAST_LOG_LINE=""
STAGE=""

while true; do
    # Check if container is still running
    if ! docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        echo ""
        echo "❌ Container stopped!"

        # Check exit code
        EXIT_CODE=$(docker inspect $CONTAINER_NAME --format='{{.State.ExitCode}}' 2>/dev/null)
        echo "Exit code: $EXIT_CODE"

        if [ "$EXIT_CODE" = "0" ]; then
            echo "✅ Training completed successfully!"
        else
            echo "❌ Training failed!"
        fi

        # Show final database status
        echo ""
        echo "Final database status:"
        docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
            "SELECT name, status, progress, training_stage, train_loss FROM finetuning_jobs WHERE id='$JOB_ID';" 2>/dev/null

        break
    fi

    # Get latest log line
    CURRENT_LOG=$(docker logs $CONTAINER_NAME --tail=1 2>&1)

    # Only print if log line changed
    if [ "$CURRENT_LOG" != "$LAST_LOG_LINE" ]; then
        echo "[$(date +%H:%M:%S)] $CURRENT_LOG"
        LAST_LOG_LINE="$CURRENT_LOG"

        # Detect stage changes
        if echo "$CURRENT_LOG" | grep -q "Model loaded successfully"; then
            echo ""
            echo "✅ MODEL LOADED! Training will start soon..."
            echo ""
        fi

        if echo "$CURRENT_LOG" | grep -q "Dataset loaded"; then
            echo ""
            echo "✅ DATASET LOADED! Training starting..."
            echo ""
        fi

        if echo "$CURRENT_LOG" | grep -q "Training started"; then
            echo ""
            echo "🔥 TRAINING IN PROGRESS..."
            echo ""
        fi

        if echo "$CURRENT_LOG" | grep -q "Training completed"; then
            echo ""
            echo "✅ TRAINING COMPLETED!"
            echo ""
        fi

        if echo "$CURRENT_LOG" | grep -q "Saving checkpoint"; then
            echo ""
            echo "💾 SAVING CHECKPOINT..."
            echo ""
        fi

        if echo "$CURRENT_LOG" | grep -q "ERROR\|Error\|FAILED"; then
            echo ""
            echo "❌ ERROR DETECTED!"
            echo ""
        fi
    fi

    # Check database every 30 seconds
    if [ $((SECONDS % 30)) -eq 0 ]; then
        DB_STATUS=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
            "SELECT status, progress, training_stage FROM finetuning_jobs WHERE id='$JOB_ID';" 2>/dev/null | grep -v "status\|----\|(1 row)")

        if [ ! -z "$DB_STATUS" ]; then
            echo ""
            echo "📊 Status: $DB_STATUS"
            echo ""
        fi
    fi

    sleep 5
done

echo ""
echo "=========================================="
echo "Monitoring ended at: $(date)"
echo ""
echo "📋 Final logs (last 30 lines):"
docker logs $CONTAINER_NAME --tail=30 2>&1
