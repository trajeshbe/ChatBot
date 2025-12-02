-- Fix web_scrape_jobs foreign key constraint
-- Date: 2025-12-02
-- Issue: web_scrape_jobs.project_id was pointing to modules table instead of projects table
-- Impact: Web scraping was failing with foreign key violation error

-- Drop incorrect foreign key
ALTER TABLE web_scrape_jobs
DROP CONSTRAINT IF EXISTS web_scrape_jobs_project_id_fkey;

-- Add correct foreign key to projects table
ALTER TABLE web_scrape_jobs
ADD CONSTRAINT web_scrape_jobs_project_id_fkey
FOREIGN KEY (project_id)
REFERENCES projects(id)
ON DELETE SET NULL;

-- Verify the fix
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'web_scrape_jobs'
    AND kcu.column_name = 'project_id';
