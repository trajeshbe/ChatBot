-- Migration: Add saved_css_templates table
-- Purpose: Store user-created CSS selector templates for reuse
-- Date: 2025-11-19

-- Create saved_css_templates table
CREATE TABLE IF NOT EXISTS saved_css_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Template identification
    name VARCHAR(255) UNIQUE NOT NULL,           -- Internal ID (lowercase, underscore-separated)
    display_name VARCHAR(255) NOT NULL,          -- User-friendly name shown in UI
    description TEXT,

    -- URL pattern matching
    url_pattern VARCHAR(512),                    -- Optional URL pattern for auto-detection (e.g., "drenting.com/*")

    -- Extraction configuration
    wait_for_selector VARCHAR(512),              -- CSS selector to wait for before extraction
    fields JSONB NOT NULL,                       -- Array of ExtractionField objects with selectors

    -- Pagination (optional)
    pagination_selector VARCHAR(512),            -- CSS selector for next page button
    max_pages INTEGER DEFAULT 1,

    -- Usage tracking
    use_count INTEGER DEFAULT 0,                 -- How many times this template has been used
    last_used_at TIMESTAMP WITH TIME ZONE,       -- When it was last used

    -- Ownership (optional - for future multi-user support)
    created_by VARCHAR(255),                     -- User who created this template

    -- Status
    is_active BOOLEAN DEFAULT TRUE,              -- Whether template is available in dropdown

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for saved_css_templates
CREATE INDEX IF NOT EXISTS idx_saved_css_templates_name
ON saved_css_templates(name);

CREATE INDEX IF NOT EXISTS idx_saved_css_templates_active
ON saved_css_templates(is_active)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_saved_css_templates_url_pattern
ON saved_css_templates(url_pattern)
WHERE url_pattern IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_saved_css_templates_use_count
ON saved_css_templates(use_count DESC);

-- Add trigger for updated_at timestamp
CREATE TRIGGER update_saved_css_templates_updated_at
    BEFORE UPDATE ON saved_css_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add sample user-saved template (Drenting.com)
INSERT INTO saved_css_templates (
    name,
    display_name,
    description,
    url_pattern,
    wait_for_selector,
    fields
)
VALUES (
    'drenting_cars',
    'Drenting.com Car Listings',
    'Extract car rental/leasing offers from Drenting.com',
    'drenting.com/*',
    '.card',
    '[
        {
            "name": "Car Model",
            "selector": ".card h3",
            "data_type": "text",
            "required": true
        },
        {
            "name": "Monthly Price",
            "selector": ".card span:has-text(\"€\")",
            "data_type": "text",
            "required": false
        },
        {
            "name": "Year",
            "selector": ".card p",
            "data_type": "text",
            "required": false
        },
        {
            "name": "Source / Notes",
            "default_value": "Scraped from Drenting.com using CSS selectors",
            "data_type": "text",
            "required": false
        }
    ]'::JSONB
);

COMMENT ON TABLE saved_css_templates IS 'User-created CSS selector templates that can be saved from successful extractions';
COMMENT ON COLUMN saved_css_templates.name IS 'Unique internal identifier (lowercase_with_underscores)';
COMMENT ON COLUMN saved_css_templates.display_name IS 'User-friendly name shown in dropdown';
COMMENT ON COLUMN saved_css_templates.fields IS 'Array of extraction fields with CSS selectors, data types, and requirements';
COMMENT ON COLUMN saved_css_templates.url_pattern IS 'Optional URL pattern for auto-suggesting templates (e.g., "example.com/*")';
