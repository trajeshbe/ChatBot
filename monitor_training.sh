#!/bin/bash
# Training Monitor for mayandi_manzil_2_improved
# Checks progress every 30 seconds

echo "🔍 Monitoring training job: mayandi_manzil_2_improved"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

while true; do
    clear
    echo "🔍 Mayandi Manzil v2 Training Monitor"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Get job status
    docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
      "SELECT
         name,
         status,
         training_stage,
         current_epoch,
         current_step,
         total_steps,
         ROUND((current_step::float / NULLIF(total_steps, 0) * 100)::numeric, 1) as progress_pct,
         ROUND(train_loss::numeric, 4) as loss,
         ROUND(eval_loss::numeric, 4) as eval_loss
       FROM finetuning_jobs
       WHERE name='mayandi_manzil_2_improved';" 2>/dev/null

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check if completed
    STATUS=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -t -c \
      "SELECT status FROM finetuning_jobs WHERE name='mayandi_manzil_2_improved';" 2>/dev/null | xargs)

    if [ "$STATUS" == "completed" ]; then
        echo "✅ Training completed!"
        echo ""
        echo "Next steps:"
        echo "1. Deploy model to Ollama"
        echo "2. Test with: 'What is Mayandi_Manzil?'"
        echo "3. Compare with old hallucinating model"
        break
    elif [ "$STATUS" == "failed" ]; then
        echo "❌ Training failed!"
        echo ""
        echo "Check logs:"
        echo "  docker-compose logs backend --tail=100 | grep -i mayandi"
        break
    fi

    echo "Refreshing in 30 seconds... (Ctrl+C to stop)"
    sleep 30
done
