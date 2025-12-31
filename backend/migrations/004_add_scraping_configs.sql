-- Migration: Add scraping configuration and compliance tables
-- Description: Stores domain-specific scraping policies, rate limits, and API configurations

-- Scraping configuration table
CREATE TABLE IF NOT EXISTS scraping_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) NOT NULL UNIQUE,

    -- Compliance settings
    allow_scraping BOOLEAN DEFAULT FALSE,
    robots_txt_compliant BOOLEAN DEFAULT TRUE,
    robots_txt_url VARCHAR(512),
    robots_txt_checked_at TIMESTAMP WITH TIME ZONE,

    -- Rate limiting
    rate_limit_enabled BOOLEAN DEFAULT TRUE,
    rate_limit_requests_per_minute INTEGER DEFAULT 10,
    rate_limit_delay_seconds FLOAT DEFAULT 2.0,
    max_concurrent_requests INTEGER DEFAULT 1,

    -- API configuration (for sites with official APIs)
    use_api BOOLEAN DEFAULT FALSE,
    api_endpoint VARCHAR(512),
    api_key_encrypted TEXT,  -- Encrypted API key
    api_documentation_url VARCHAR(512),

    -- Terms of Service compliance
    terms_checked BOOLEAN DEFAULT FALSE,
    terms_url VARCHAR(512),
    terms_checked_at TIMESTAMP WITH TIME ZONE,
    terms_notes TEXT,

    -- Permission tracking
    permission_granted BOOLEAN DEFAULT FALSE,
    permission_contact VARCHAR(255),  -- Email/contact who granted permission
    permission_granted_at TIMESTAMP WITH TIME ZONE,
    permission_expires_at TIMESTAMP WITH TIME ZONE,
    permission_document_url VARCHAR(512),

    -- Scraping method preferences
    preferred_method VARCHAR(50) DEFAULT 'auto',  -- 'api', 'playwright', 'requests', 'auto'
    user_agent VARCHAR(512),
    custom_headers JSONB,

    -- Notes and metadata
    notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_scraped_at TIMESTAMP WITH TIME ZONE,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'blocked', 'suspended', 'deprecated'
    block_reason TEXT
);

-- Scraping audit log (tracks all scraping attempts)
CREATE TABLE IF NOT EXISTS scraping_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID REFERENCES scraping_configs(id) ON DELETE SET NULL,
    domain VARCHAR(255) NOT NULL,
    url VARCHAR(1024) NOT NULL,

    -- Request details
    method VARCHAR(50),  -- 'api', 'playwright', 'requests'
    user_agent VARCHAR(512),

    -- Response details
    status_code INTEGER,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    response_time_ms FLOAT,
    bytes_downloaded INTEGER,

    -- Compliance tracking
    robots_txt_allowed BOOLEAN,
    rate_limit_respected BOOLEAN,
    permission_verified BOOLEAN,

    -- Metadata
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Domain statistics (aggregate scraping stats per domain)
CREATE TABLE IF NOT EXISTS domain_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) NOT NULL UNIQUE,

    -- Request counts
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    blocked_requests INTEGER DEFAULT 0,

    -- Traffic stats
    total_bytes_downloaded BIGINT DEFAULT 0,
    avg_response_time_ms FLOAT,

    -- Rate limiting violations
    rate_limit_violations INTEGER DEFAULT 0,
    robots_txt_violations INTEGER DEFAULT 0,

    -- Time tracking
    first_scraped_at TIMESTAMP WITH TIME ZONE,
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_scraping_configs_domain ON scraping_configs(domain);
CREATE INDEX idx_scraping_configs_status ON scraping_configs(status);
CREATE INDEX idx_scraping_configs_allow_scraping ON scraping_configs(allow_scraping);
CREATE INDEX idx_scraping_audit_domain ON scraping_audit_log(domain);
CREATE INDEX idx_scraping_audit_created_at ON scraping_audit_log(created_at);
CREATE INDEX idx_scraping_audit_success ON scraping_audit_log(success);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_scraping_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_scraping_config_timestamp
BEFORE UPDATE ON scraping_configs
FOR EACH ROW
EXECUTE FUNCTION update_scraping_config_timestamp();

-- Add some default configurations for common sites
INSERT INTO scraping_configs (domain, allow_scraping, notes, status) VALUES
('books.toscrape.com', TRUE, 'Test site designed for web scraping practice', 'active'),
('example.com', TRUE, 'IANA example domain - safe for testing', 'active'),
('httpbin.org', TRUE, 'HTTP testing service - safe for testing', 'active')
ON CONFLICT (domain) DO NOTHING;

-- Insert default blocked domains (known to have strict anti-scraping)
INSERT INTO scraping_configs (domain, allow_scraping, status, block_reason, notes) VALUES
('amazon.com', FALSE, 'blocked', 'Strict anti-scraping policy, use Product Advertising API instead', 'Use official Product Advertising API'),
('google.com', FALSE, 'blocked', 'Against Terms of Service, use Custom Search API instead', 'Use Custom Search JSON API'),
('facebook.com', FALSE, 'blocked', 'Against Terms of Service, use Graph API instead', 'Use Facebook Graph API'),
('twitter.com', FALSE, 'blocked', 'Against Terms of Service, use Twitter API instead', 'Use Twitter API v2'),
('linkedin.com', FALSE, 'blocked', 'Against Terms of Service, use LinkedIn API instead', 'Use LinkedIn Marketing API')
ON CONFLICT (domain) DO NOTHING;
