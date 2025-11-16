-- Migration: Add Enhanced Scraping Fields to web_scrape_jobs
-- Created: 2025-11-16
-- Description: Adds compliance level, proxy info, user agent, auth method, and LLM provider fields

-- Add new columns to web_scrape_jobs table
ALTER TABLE web_scrape_jobs
ADD COLUMN IF NOT EXISTS compliance_level VARCHAR(50) DEFAULT 'balanced',
ADD COLUMN IF NOT EXISTS proxy_used VARCHAR(255),
ADD COLUMN IF NOT EXISTS user_agent_used VARCHAR(512),
ADD COLUMN IF NOT EXISTS auth_method VARCHAR(50),
ADD COLUMN IF NOT EXISTS llm_provider VARCHAR(50),
ADD COLUMN IF NOT EXISTS scraping_time_ms FLOAT,
ADD COLUMN IF NOT EXISTS protocols_detected JSONB;

-- Add index on compliance_level for filtering
CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_compliance_level
ON web_scrape_jobs(compliance_level);

-- Add index on status for job monitoring
CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_status
ON web_scrape_jobs(status);

-- Add comment to document the compliance levels
COMMENT ON COLUMN web_scrape_jobs.compliance_level IS 'Compliance level used: strict, balanced, or aggressive';
COMMENT ON COLUMN web_scrape_jobs.proxy_used IS 'Proxy URL used for the scraping request';
COMMENT ON COLUMN web_scrape_jobs.user_agent_used IS 'User agent string used for the request';
COMMENT ON COLUMN web_scrape_jobs.auth_method IS 'Authentication method used: none, basic, bearer, api_key, oauth2, jwt, session, custom';
COMMENT ON COLUMN web_scrape_jobs.llm_provider IS 'LLM provider used for smart scraping: ollama, openai, anthropic';
COMMENT ON COLUMN web_scrape_jobs.scraping_time_ms IS 'Time taken to scrape in milliseconds';
COMMENT ON COLUMN web_scrape_jobs.protocols_detected IS 'Detected site protocols and recommendations';
