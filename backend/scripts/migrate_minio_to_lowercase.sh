#!/bin/bash
# Migrate MinIO paths from Title-Case to lowercase (sanitized) format
#
# Standard format: technology/backend-development/global/admin/...
# Old format:      Technology/Backend-Development/Global/admin/...

set -e

echo "=== MinIO Path Migration: Title-Case → lowercase ==="
echo ""
echo "This script will:"
echo "1. Copy files from Technology/Backend-Development/ to technology/backend-development/"
echo "2. Update database minio_path fields to use lowercase"
echo "3. Optionally delete old Title-Case folders"
echo ""

# Check if running in docker
if [ ! -f /.dockerenv ]; then
    echo "⚠️  This script should run inside the backend container"
    echo "Run: docker-compose exec backend bash scripts/migrate_minio_to_lowercase.sh"
    exit 1
fi

# MinIO configuration
MINIO_ALIAS="myminio"
BUCKET="documents"

# Step 1: Copy files from Title-Case to lowercase
echo "Step 1: Copying files to lowercase paths..."
echo ""

# Technology/Backend-Development → technology/backend-development
echo "Migrating: Technology/Backend-Development/ → technology/backend-development/"
mc cp --recursive \
    ${MINIO_ALIAS}/${BUCKET}/Technology/Backend-Development/ \
    ${MINIO_ALIAS}/${BUCKET}/technology/backend-development/ \
    2>&1 || echo "⚠️  No files in Technology/Backend-Development/ or already migrated"

# Technology/Frontend-Development → technology/frontend-development (if exists)
if mc ls ${MINIO_ALIAS}/${BUCKET}/Technology/Frontend-Development/ >/dev/null 2>&1; then
    echo "Migrating: Technology/Frontend-Development/ → technology/frontend-development/"
    mc cp --recursive \
        ${MINIO_ALIAS}/${BUCKET}/Technology/Frontend-Development/ \
        ${MINIO_ALIAS}/${BUCKET}/technology/frontend-development/
fi

# AI-ML → ai-ml (if exists)
if mc ls ${MINIO_ALIAS}/${BUCKET}/AI-ML/ >/dev/null 2>&1; then
    echo "Migrating: AI-ML/ → ai-ml/"
    mc cp --recursive \
        ${MINIO_ALIAS}/${BUCKET}/AI-ML/ \
        ${MINIO_ALIAS}/${BUCKET}/ai-ml/
fi

echo ""
echo "✅ Step 1 complete: Files copied to lowercase paths"
echo ""

# Step 2: Update database
echo "Step 2: Updating database minio_path fields..."
echo ""

psql -U postgres -d ragchatbot <<EOF
-- Update documents table
UPDATE documents
SET minio_path = REPLACE(
    REPLACE(
        REPLACE(minio_path, 'Technology/', 'technology/'),
        'Backend-Development/', 'backend-development/'
    ),
    'Global/', 'global/'
)
WHERE minio_path LIKE 'Technology/%' OR minio_path LIKE 'AI-ML/%';

-- Show updated count
SELECT COUNT(*) as updated_documents
FROM documents
WHERE minio_path LIKE 'technology/%' OR minio_path LIKE 'ai-ml/%';
EOF

echo ""
echo "✅ Step 2 complete: Database updated"
echo ""

# Step 3: Verify migration
echo "Step 3: Verifying migration..."
echo ""

echo "Files in lowercase paths:"
mc ls ${MINIO_ALIAS}/${BUCKET}/technology/ 2>&1 || echo "No files yet"

echo ""
echo "Database paths sample:"
psql -U postgres -d ragchatbot -c "SELECT filename, minio_path FROM documents WHERE minio_path LIKE 'technology/%' LIMIT 5;"

echo ""
echo "=== Migration Complete ==="
echo ""
echo "⚠️  IMPORTANT: Review the migration before deleting old files!"
echo ""
echo "To delete old Title-Case folders (AFTER VERIFICATION):"
echo "  mc rm --recursive ${MINIO_ALIAS}/${BUCKET}/Technology/"
echo "  mc rm --recursive ${MINIO_ALIAS}/${BUCKET}/AI-ML/"
echo ""
echo "Current storage:"
echo "  Lowercase (new): technology/, ai-ml/"
echo "  Title-Case (old): Technology/, AI-ML/ ← Safe to delete after verification"
echo ""
