-- Migration: Add Prompt Library and Output Templates
-- Description: Adds comprehensive prompt library system and output template management
-- Created: 2025-11-29

-- ============================================================================
-- 1. PROMPT LIBRARY TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS prompt_library (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,

    -- Classification
    prompt_type VARCHAR(100) NOT NULL, -- 'entity_extraction', 'summarization', 'analysis', 'qa', 'translation', 'comparison', etc.
    category VARCHAR(100), -- 'business', 'technical', 'research', 'general', etc.
    module VARCHAR(100), -- 'chat', 'scraping', 'project_estimator', 'web_scraper', etc. - which app feature uses this prompt
    tags JSONB DEFAULT '[]'::jsonb, -- Flexible categorization ['data-analysis', 'financial', etc.]

    -- Output Configuration
    expected_output_format VARCHAR(50) DEFAULT 'text', -- 'json', 'markdown', 'table', 'list', 'structured', 'text'
    output_schema JSONB, -- JSON schema for structured outputs

    -- Examples (for better user understanding)
    example_input TEXT,
    example_output TEXT,

    -- Ownership & Visibility
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL, -- NULL = global, otherwise project-specific
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT false, -- Share with all users
    is_verified BOOLEAN DEFAULT false, -- Admin-verified quality prompt

    -- Usage Metrics
    usage_count INTEGER DEFAULT 0,
    average_rating FLOAT DEFAULT 0.0,
    total_ratings INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Versioning
    version INTEGER DEFAULT 1,
    parent_prompt_id UUID REFERENCES prompt_library(id) ON DELETE SET NULL, -- For tracking prompt evolution

    -- Metadata
    meta_info JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_prompt_library_created_by ON prompt_library(created_by);
CREATE INDEX idx_prompt_library_project_id ON prompt_library(project_id);
CREATE INDEX idx_prompt_library_prompt_type ON prompt_library(prompt_type);
CREATE INDEX idx_prompt_library_category ON prompt_library(category);
CREATE INDEX idx_prompt_library_module ON prompt_library(module);
CREATE INDEX idx_prompt_library_is_public ON prompt_library(is_public);
CREATE INDEX idx_prompt_library_tags ON prompt_library USING gin(tags);
CREATE INDEX idx_prompt_library_usage_count ON prompt_library(usage_count DESC);
CREATE INDEX idx_prompt_library_average_rating ON prompt_library(average_rating DESC);

-- ============================================================================
-- 2. PROMPT RATINGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS prompt_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID REFERENCES prompt_library(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure one rating per user per prompt
    UNIQUE(prompt_id, user_id)
);

CREATE INDEX idx_prompt_ratings_prompt_id ON prompt_ratings(prompt_id);
CREATE INDEX idx_prompt_ratings_user_id ON prompt_ratings(user_id);

-- ============================================================================
-- 3. OUTPUT TEMPLATES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS output_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Template Configuration
    template_type VARCHAR(50) NOT NULL, -- 'excel', 'word', 'ppt', 'markdown', 'json', 'pdf'
    template_config JSONB NOT NULL, -- Structure definition (columns, sections, formatting, etc.)

    -- Template Content
    template_file_path VARCHAR(512), -- Path to template file if using file-based templates

    -- Ownership & Visibility
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT false,

    -- Usage Metrics
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    meta_info JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_output_templates_created_by ON output_templates(created_by);
CREATE INDEX idx_output_templates_project_id ON output_templates(project_id);
CREATE INDEX idx_output_templates_template_type ON output_templates(template_type);
CREATE INDEX idx_output_templates_is_public ON output_templates(is_public);

-- ============================================================================
-- 4. PROMPT USAGE LOG (Optional - for analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS prompt_usage_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID REFERENCES prompt_library(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,

    -- Usage details
    actual_prompt_used TEXT, -- The final prompt after variable substitution
    input_provided TEXT,
    output_generated TEXT,

    -- Performance
    execution_time_ms FLOAT,
    token_count INTEGER,

    -- Outcome
    was_successful BOOLEAN DEFAULT true,
    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_prompt_usage_log_prompt_id ON prompt_usage_log(prompt_id);
CREATE INDEX idx_prompt_usage_log_user_id ON prompt_usage_log(user_id);
CREATE INDEX idx_prompt_usage_log_created_at ON prompt_usage_log(created_at DESC);

-- ============================================================================
-- 5. SEED DATA - Common Prompts
-- ============================================================================

-- Entity Extraction Prompts
INSERT INTO prompt_library (name, description, prompt_text, prompt_type, category, module, expected_output_format, example_input, example_output, is_public, is_verified)
VALUES
(
    'Entity Relationship Extraction',
    'Extract entities and their relationships from text data',
    'Analyze the following text and extract all entities (people, organizations, locations, dates, etc.) and their relationships. Format the output as a structured JSON with entity types and relationship mappings.

Text: {input_text}

Provide the output in this format:
{
  "entities": [{"type": "...", "name": "...", "mentions": [...]}],
  "relationships": [{"source": "...", "relation": "...", "target": "..."}]
}',
    'entity_extraction',
    'data-analysis',
    'chat',
    'json',
    'Apple Inc. announced that Tim Cook will speak at the conference in San Francisco on March 15, 2024.',
    '{"entities": [{"type": "organization", "name": "Apple Inc."}, {"type": "person", "name": "Tim Cook"}, {"type": "location", "name": "San Francisco"}, {"type": "date", "name": "March 15, 2024"}], "relationships": [{"source": "Tim Cook", "relation": "employed_by", "target": "Apple Inc."}, {"source": "Tim Cook", "relation": "will_speak_at", "target": "San Francisco"}]}',
    true,
    true
),
(
    'Document Summarization',
    'Create a concise summary of long documents',
    'Please provide a comprehensive yet concise summary of the following document. Focus on key points, main arguments, and critical information.

Document: {input_text}

Structure your summary with:
1. Main Topic (1 sentence)
2. Key Points (3-5 bullet points)
3. Conclusion/Implications (1-2 sentences)',
    'summarization',
    'general',
    'chat',
    'markdown',
    'Long research paper about climate change impacts...',
    '# Summary\n## Main Topic\nAnalysis of climate change impacts on coastal ecosystems.\n## Key Points\n- Rising sea levels threaten biodiversity\n- Temperature increases affect marine life\n- Policy recommendations for mitigation\n## Conclusion\nImmediate action needed to preserve coastal habitats.',
    true,
    true
),
(
    'Comparative Analysis',
    'Compare multiple items or concepts',
    'Perform a detailed comparison of the following items based on the specified criteria:

Items to compare: {items}
Criteria: {criteria}

Provide a structured comparison table and a summary highlighting key differences and similarities.',
    'comparison',
    'business',
    'chat',
    'table',
    'Items: Product A, Product B; Criteria: price, features, customer satisfaction',
    '| Criteria | Product A | Product B |\n|----------|-----------|----------|\n| Price | $199 | $249 |\n| Features | Basic | Advanced |\n| Satisfaction | 4.2/5 | 4.7/5 |',
    true,
    true
),
(
    'Meeting Minutes Extraction',
    'Extract structured information from meeting transcripts',
    'Extract and organize the following information from this meeting transcript:
- Attendees
- Key Discussion Points
- Decisions Made
- Action Items (with owners and deadlines)
- Next Steps

Meeting Transcript: {input_text}

Format as JSON with clear sections.',
    'entity_extraction',
    'business',
    'chat',
    'json',
    'Meeting transcript discussing Q4 budget allocation...',
    '{"attendees": ["John Doe", "Jane Smith"], "discussion_points": ["Budget review", "Resource allocation"], "decisions": ["Approve $500K for marketing"], "action_items": [{"task": "Prepare budget proposal", "owner": "John Doe", "deadline": "2024-03-15"}]}',
    true,
    true
),
(
    'Data Table Extraction',
    'Extract tabular data from unstructured text',
    'Extract all tabular information from the following text and format it as a structured table (JSON or Markdown).

Text: {input_text}

Identify column headers and data rows, maintaining data types and relationships.',
    'entity_extraction',
    'data-analysis',
    'scraping',
    'json',
    'Sales data for Q1: Region North had $500K, Region South had $750K, Region East had $600K.',
    '{"headers": ["Region", "Sales"], "rows": [["North", "$500K"], ["South", "$750K"], ["East", "$600K"]]}',
    true,
    true
);

-- ============================================================================
-- 6. SEED DATA - Common Output Templates
-- ============================================================================

INSERT INTO output_templates (name, description, template_type, template_config, is_public)
VALUES
(
    'Entity Relationship Excel',
    'Excel format for entity-relationship data',
    'excel',
    '{
        "sheets": [
            {
                "name": "Entities",
                "columns": ["Entity Type", "Entity Name", "Mentions Count", "First Mentioned"],
                "formatting": {
                    "header_style": {"bold": true, "bg_color": "#4472C4", "font_color": "white"},
                    "freeze_panes": "A2"
                }
            },
            {
                "name": "Relationships",
                "columns": ["Source Entity", "Relationship Type", "Target Entity", "Confidence"],
                "formatting": {
                    "header_style": {"bold": true, "bg_color": "#70AD47", "font_color": "white"},
                    "freeze_panes": "A2"
                }
            }
        ]
    }',
    true
),
(
    'Summary Report (Word)',
    'Professional summary report in Word format',
    'word',
    '{
        "sections": [
            {"type": "title", "style": "Heading 1"},
            {"type": "executive_summary", "style": "Normal"},
            {"type": "key_findings", "style": "Bullet List"},
            {"type": "recommendations", "style": "Numbered List"},
            {"type": "conclusion", "style": "Normal"}
        ],
        "formatting": {
            "font": "Calibri",
            "font_size": 11,
            "line_spacing": 1.15,
            "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}
        }
    }',
    true
),
(
    'Comparison Matrix (Markdown)',
    'Comparison table in Markdown format',
    'markdown',
    '{
        "template": "# Comparison Analysis\n\n## Overview\n{overview}\n\n## Comparison Table\n{table}\n\n## Key Insights\n{insights}\n\n## Recommendation\n{recommendation}",
        "table_format": "github_flavored_markdown"
    }',
    true
),
(
    'Data Analysis Dashboard (JSON)',
    'Structured JSON for data visualization dashboards',
    'json',
    '{
        "structure": {
            "metadata": {
                "title": "string",
                "generated_at": "datetime",
                "data_source": "string"
            },
            "summary_stats": {
                "total_count": "number",
                "average": "number",
                "min": "number",
                "max": "number"
            },
            "detailed_data": "array",
            "insights": "array"
        }
    }',
    true
);

-- ============================================================================
-- 7. UPDATE TRIGGER FOR updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_prompt_library_updated_at
    BEFORE UPDATE ON prompt_library
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_output_templates_updated_at
    BEFORE UPDATE ON output_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE prompt_library IS 'State-of-the-art prompt library for reusable prompts across users and projects';
COMMENT ON TABLE prompt_ratings IS 'User ratings and feedback for prompts to track quality';
COMMENT ON TABLE output_templates IS 'Reusable output format templates for structured exports';
COMMENT ON TABLE prompt_usage_log IS 'Analytics log for prompt usage patterns and performance';
