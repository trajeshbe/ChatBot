# Test Auto-Validation Implementation

## Quick Test Instructions

### Option 1: Test with Existing Dataset (story1)

The existing "story1" dataset can be manually validated to verify the endpoint works:

```bash
bash /tmp/validate_story1.sh
```

### Option 2: Upload New Dataset via UI

1. **Go to Fine-Tuning UI**:
   - Navigate to: http://localhost:3001
   - Login as admin
   - Go to Fine-Tuning → Datasets

2. **Upload a new CSV dataset**:
   - Create a simple test CSV:
   ```csv
   Question,Answer
   What is AI?,Artificial Intelligence is the simulation of human intelligence by machines.
   What is ML?,Machine Learning is a subset of AI that learns from data.
   What is NLP?,Natural Language Processing is AI that understands human language.
   ```

3. **Watch for auto-validation**:
   - Upload the file
   - Immediately check database:
   ```bash
   docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
   SELECT
     name,
     preprocessing_status,
     is_valid,
     num_samples
   FROM finetuning_datasets
   ORDER BY uploaded_at DESC
   LIMIT 1;"
   ```

4. **Wait 5 seconds and check again**:
   - Should show:
     - `preprocessing_status = 'completed'`
     - `is_valid = true`
     - `num_samples = 3`

5. **Refresh UI**:
   - Dataset should show as "Valid" ✅
   - Click on dataset to see Overview/Samples/Quality tabs populated

### Option 3: Monitor Backend Logs

Watch the auto-validation in action:

```bash
# Terminal 1: Watch backend logs
docker-compose logs -f backend | grep -E "(Created dataset|Queued background|Validating|validation complete)"

# Terminal 2: Upload dataset via UI
# (You'll see logs appear in Terminal 1)
```

**Expected Log Output**:
```
INFO - Created dataset: <uuid> - test_dataset.csv
INFO - Queued background validation for dataset: <uuid>
INFO - Validating dataset <uuid>...
INFO - Dataset validation complete: is_valid=True, num_samples=3
```

---

## Verification Checklist

- [x] Backend restarted successfully
- [x] Health endpoint returns healthy status
- [ ] Upload new dataset via UI
- [ ] Dataset shows "processing" immediately after upload
- [ ] Dataset shows "completed" + "valid" within 5 seconds
- [ ] Overview/Samples/Quality tabs populate automatically
- [ ] Backend logs show validation queued and completed

---

## If Auto-Validation Fails

Check these:

1. **Backend logs for errors**:
   ```bash
   docker-compose logs backend --tail=100 | grep -i error
   ```

2. **FineTuningService.validate_dataset() exists**:
   ```bash
   docker-compose exec backend grep -n "def validate_dataset" app/services/finetuning/finetuning_service.py
   ```

3. **Database connection working**:
   ```bash
   docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "\dt finetuning_datasets"
   ```

4. **MinIO accessible**:
   ```bash
   docker-compose exec backend curl -s http://minio:9000/minio/health/live
   ```

---

**Status**: Ready to test! 🚀
