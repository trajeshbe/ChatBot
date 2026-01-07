-- ============================================================================
-- Seed Prompt Library - Production-Ready Prompts
-- ============================================================================
--
-- Purpose: Seed 25+ production-ready prompts across multiple categories
--
-- Categories:
--   - general          - General-purpose prompts
--   - business         - Business analysis and reporting
--   - data-analysis    - Data extraction and analysis
--   - technical        - Technical documentation and code
--   - legal            - Legal and compliance
--   - education        - Educational content
--
-- Dependencies: prompt_library table, users table (optional)
--
-- Idempotent: Yes (ON CONFLICT DO UPDATE)
--
-- ============================================================================

-- ============================================================================
-- GENERAL CATEGORY (5 prompts)
-- ============================================================================

INSERT INTO prompt_library (
    name, description, prompt_text, prompt_type, category, module,
    expected_output_format, example_input, example_output,
    is_public, is_verified, tags
) VALUES
    (
        'Document Summarization',
        'Create a concise summary of long documents with key points',
        E'Please provide a comprehensive yet concise summary of the following document. Focus on key points, main arguments, and critical information.

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
        E'# Summary\n## Main Topic\nAnalysis of climate change impacts on coastal ecosystems.\n## Key Points\n- Rising sea levels threaten biodiversity\n- Temperature increases affect marine life\n- Policy recommendations for mitigation\n## Conclusion\nImmediate action needed to preserve coastal habitats.',
        TRUE,
        TRUE,
        '["summarization", "documents", "general"]'::jsonb
    ),
    (
        'Q&A Answering',
        'Answer questions based on provided context with citations',
        E'Based on the following context, answer the user''s question accurately and concisely. If the answer is not in the context, say so.

Context: {context}

Question: {question}

Instructions:
- Provide a clear, direct answer
- Cite specific passages from the context
- If uncertain, acknowledge limitations
- Keep response focused and relevant',
        'qa',
        'general',
        'chat',
        'text',
        'Context: The company was founded in 2010... Question: When was the company founded?',
        'The company was founded in 2010. [Source: paragraph 1]',
        TRUE,
        TRUE,
        '["qa", "rag", "general"]'::jsonb
    ),
    (
        'Content Generation',
        'Generate creative content based on specifications',
        E'Generate {content_type} content based on the following specifications:

Topic: {topic}
Tone: {tone}
Length: {length}
Target Audience: {audience}

Additional Requirements: {requirements}

Create engaging, well-structured content that meets all specifications.',
        'generation',
        'general',
        'chat',
        'text',
        'Topic: AI in Healthcare, Tone: Professional, Length: 500 words',
        'Artificial Intelligence is revolutionizing healthcare delivery...',
        TRUE,
        TRUE,
        '["generation", "content", "writing"]'::jsonb
    ),
    (
        'Translation',
        'Translate text between languages while preserving meaning',
        E'Translate the following text from {source_language} to {target_language}. Maintain the original meaning, tone, and context.

Text to translate: {input_text}

Important:
- Preserve technical terms where appropriate
- Maintain formatting
- Ensure cultural appropriateness
- Provide natural, fluent translation',
        'translation',
        'general',
        'chat',
        'text',
        'Text: Hello, how are you? Source: English, Target: Spanish',
        'Hola, ¿cómo estás?',
        TRUE,
        TRUE,
        '["translation", "multilingual", "i18n"]'::jsonb
    ),
    (
        'Text Classification',
        'Classify text into predefined categories',
        E'Classify the following text into one or more of these categories: {categories}

Text: {input_text}

Provide:
1. Primary category with confidence score
2. Secondary categories if applicable
3. Brief reasoning for classification

Output as JSON.',
        'classification',
        'general',
        'chat',
        'json',
        'Text: "Urgent security patch required", Categories: ["bug", "feature", "security", "documentation"]',
        '{"primary": {"category": "security", "confidence": 0.95}, "reasoning": "Contains keywords urgent and security patch"}',
        TRUE,
        TRUE,
        '["classification", "nlp", "categorization"]'::jsonb
    )
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    prompt_text = EXCLUDED.prompt_text,
    prompt_type = EXCLUDED.prompt_type,
    category = EXCLUDED.category,
    module = EXCLUDED.module,
    expected_output_format = EXCLUDED.expected_output_format,
    example_input = EXCLUDED.example_input,
    example_output = EXCLUDED.example_output,
    is_public = EXCLUDED.is_public,
    is_verified = EXCLUDED.is_verified,
    tags = EXCLUDED.tags,
    updated_at = NOW();

-- ============================================================================
-- BUSINESS CATEGORY (6 prompts)
-- ============================================================================

INSERT INTO prompt_library (
    name, description, prompt_text, prompt_type, category, module,
    expected_output_format, example_input, example_output,
    is_public, is_verified, tags
) VALUES
    (
        'Meeting Minutes Extraction',
        'Extract structured information from meeting transcripts',
        E'Extract and organize the following information from this meeting transcript:
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
        '{"attendees": ["John Doe", "Jane Smith"], "discussion_points": ["Budget review"], "decisions": ["Approve $500K for marketing"], "action_items": [{"task": "Prepare proposal", "owner": "John", "deadline": "2024-03-15"}]}',
        TRUE,
        TRUE,
        '["meetings", "extraction", "business"]'::jsonb
    ),
    (
        'Report Generation',
        'Generate professional business reports from data',
        E'Generate a professional business report based on the following data:

Data: {data}
Report Type: {report_type}
Time Period: {time_period}

Include:
- Executive Summary
- Key Metrics and Trends
- Analysis and Insights
- Recommendations
- Conclusion

Use clear headings and bullet points.',
        'generation',
        'business',
        'chat',
        'markdown',
        'Q4 sales data showing 15% growth...',
        '# Q4 Sales Report\n## Executive Summary\nStrong performance with 15% YoY growth...',
        TRUE,
        TRUE,
        '["reports", "business", "analytics"]'::jsonb
    ),
    (
        'Email Drafting',
        'Draft professional business emails',
        E'Draft a professional email based on the following:

Purpose: {purpose}
Recipient: {recipient}
Key Points: {key_points}
Tone: {tone}

Create a well-structured email with:
- Appropriate subject line
- Professional greeting
- Clear body with paragraphs
- Call to action if needed
- Professional closing',
        'generation',
        'business',
        'chat',
        'text',
        'Purpose: Follow-up on proposal, Recipient: Client, Tone: Professional',
        'Subject: Follow-up on Our Proposal\n\nDear [Client Name],\n\nI hope this email finds you well...',
        TRUE,
        TRUE,
        '["email", "communication", "business"]'::jsonb
    ),
    (
        'Comparative Analysis',
        'Compare multiple items or concepts',
        E'Perform a detailed comparison of the following items based on the specified criteria:

Items to compare: {items}
Criteria: {criteria}

Provide:
1. Comparison table with all criteria
2. Summary of key differences
3. Summary of similarities
4. Recommendations based on comparison',
        'comparison',
        'business',
        'chat',
        'markdown',
        'Items: Product A vs Product B; Criteria: price, features, customer satisfaction',
        '| Criteria | Product A | Product B |\n|----------|-----------|----------|\n| Price | $199 | $249 |\n| Features | Basic | Advanced |\n\nRecommendation: Product B offers better value...',
        TRUE,
        TRUE,
        '["comparison", "analysis", "business"]'::jsonb
    ),
    (
        'SWOT Analysis',
        'Generate comprehensive SWOT analysis',
        E'Conduct a SWOT analysis for:

Subject: {subject}
Context: {context}

Analyze and provide:
- Strengths (internal positive factors)
- Weaknesses (internal negative factors)
- Opportunities (external positive factors)
- Threats (external negative factors)

Format as structured JSON with detailed points.',
        'analysis',
        'business',
        'chat',
        'json',
        'Subject: New product launch, Context: Competitive market...',
        '{"strengths": ["Strong brand"], "weaknesses": ["Limited budget"], "opportunities": ["Growing market"], "threats": ["Competition"]}',
        TRUE,
        TRUE,
        '["swot", "strategy", "business"]'::jsonb
    ),
    (
        'Executive Briefing',
        'Create executive briefings from detailed reports',
        E'Create an executive briefing from the following detailed information:

Content: {input_text}

Generate a concise executive briefing (max 500 words) that includes:
- Situation Overview (2-3 sentences)
- Key Findings (3-5 bullet points)
- Critical Decisions Required
- Recommended Actions
- Timeline and Next Steps

Focus on actionable insights for decision-makers.',
        'summarization',
        'business',
        'chat',
        'markdown',
        'Detailed market analysis report with 50 pages...',
        '## Executive Briefing\n\n### Situation Overview\nMarket shows strong growth potential...',
        TRUE,
        TRUE,
        '["executive", "briefing", "summary"]'::jsonb
    )
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    prompt_text = EXCLUDED.prompt_text,
    prompt_type = EXCLUDED.prompt_type,
    category = EXCLUDED.category,
    updated_at = NOW();

-- ============================================================================
-- DATA ANALYSIS CATEGORY (5 prompts)
-- ============================================================================

INSERT INTO prompt_library (
    name, description, prompt_text, prompt_type, category, module,
    expected_output_format, example_input, example_output,
    is_public, is_verified, tags
) VALUES
    (
        'Data Table Extraction',
        'Extract tabular data from unstructured text',
        E'Extract all tabular information from the following text and format it as a structured table.

Text: {input_text}

Instructions:
- Identify column headers
- Extract all data rows
- Maintain data types and relationships
- Handle missing values appropriately

Output as JSON with "headers" and "rows" arrays.',
        'entity_extraction',
        'data-analysis',
        'scraping',
        'json',
        'Sales data for Q1: Region North had $500K, Region South had $750K, Region East had $600K.',
        '{"headers": ["Region", "Sales"], "rows": [["North", "$500K"], ["South", "$750K"], ["East", "$600K"]]}',
        TRUE,
        TRUE,
        '["tables", "extraction", "data"]'::jsonb
    ),
    (
        'Chart Analysis',
        'Analyze charts and visualizations from descriptions',
        E'Analyze the following chart/visualization and provide insights:

Chart Description: {chart_description}
Data Points: {data_points}

Provide:
1. Key trends identified
2. Notable patterns or anomalies
3. Comparative analysis
4. Actionable insights
5. Recommendations',
        'analysis',
        'data-analysis',
        'chat',
        'markdown',
        'Line chart showing website traffic over 6 months with declining trend...',
        '## Chart Analysis\n\n### Key Trends\n- 25% decline in traffic over 6 months...',
        TRUE,
        TRUE,
        '["charts", "visualization", "analysis"]'::jsonb
    ),
    (
        'Data Validation',
        'Validate data quality and consistency',
        E'Validate the following dataset for quality and consistency:

Data: {data}
Expected Schema: {schema}

Check for:
- Missing values
- Data type mismatches
- Duplicate entries
- Outliers
- Constraint violations

Output validation report as JSON with issues categorized by severity.',
        'validation',
        'data-analysis',
        'chat',
        'json',
        'Dataset with customer records including emails, phone numbers...',
        '{"errors": [{"field": "email", "issue": "Invalid format", "count": 5}], "warnings": [{"field": "age", "issue": "Outlier detected"}]}',
        TRUE,
        TRUE,
        '["validation", "quality", "data"]'::jsonb
    ),
    (
        'Entity Relationship Extraction',
        'Extract entities and their relationships from text',
        E'Analyze the following text and extract all entities (people, organizations, locations, dates, etc.) and their relationships.

Text: {input_text}

Provide the output in this format:
{
  "entities": [{"type": "...", "name": "...", "mentions": [...]}],
  "relationships": [{"source": "...", "relation": "...", "target": "..."}]
}

Focus on business-relevant relationships.',
        'entity_extraction',
        'data-analysis',
        'chat',
        'json',
        'Apple Inc. announced that Tim Cook will speak at the conference in San Francisco on March 15, 2024.',
        '{"entities": [{"type": "organization", "name": "Apple Inc."}, {"type": "person", "name": "Tim Cook"}], "relationships": [{"source": "Tim Cook", "relation": "employed_by", "target": "Apple Inc."}]}',
        TRUE,
        TRUE,
        '["ner", "entities", "relationships"]'::jsonb
    ),
    (
        'Statistical Summary',
        'Generate statistical summaries of datasets',
        E'Generate a comprehensive statistical summary of the following dataset:

Data: {data}
Variables: {variables}

Include:
- Descriptive statistics (mean, median, mode, std dev)
- Distribution analysis
- Correlation insights
- Key observations
- Data quality notes

Format as structured report.',
        'analysis',
        'data-analysis',
        'chat',
        'markdown',
        'Sales data with 1000 records across 5 regions...',
        '## Statistical Summary\n\n### Descriptive Statistics\n- Mean: $125K\n- Median: $118K...',
        TRUE,
        TRUE,
        '["statistics", "summary", "analysis"]'::jsonb
    )
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    prompt_text = EXCLUDED.prompt_text,
    updated_at = NOW();

-- ============================================================================
-- TECHNICAL CATEGORY (5 prompts)
-- ============================================================================

INSERT INTO prompt_library (
    name, description, prompt_text, prompt_type, category, module,
    expected_output_format, example_input, example_output,
    is_public, is_verified, tags
) VALUES
    (
        'Code Review',
        'Review code for quality, bugs, and improvements',
        E'Review the following code and provide a comprehensive analysis:

Code: {code}
Language: {language}

Analyze:
1. Code quality and style
2. Potential bugs or issues
3. Security concerns
4. Performance considerations
5. Suggested improvements

Format as structured markdown with severity levels.',
        'analysis',
        'technical',
        'chat',
        'markdown',
        'Python function for user authentication...',
        '## Code Review\n\n### Critical Issues\n- SQL injection vulnerability on line 45\n\n### Improvements\n- Add input validation...',
        TRUE,
        TRUE,
        '["code", "review", "quality"]'::jsonb
    ),
    (
        'API Documentation',
        'Generate API documentation from code or specifications',
        E'Generate comprehensive API documentation for:

API Endpoint: {endpoint}
Method: {method}
Code/Spec: {input}

Include:
- Endpoint description
- Request parameters
- Request body schema
- Response format
- Status codes
- Example requests/responses
- Authentication requirements
- Rate limits

Format as OpenAPI/Swagger style documentation.',
        'generation',
        'technical',
        'chat',
        'markdown',
        'POST /api/users endpoint for creating users...',
        '## POST /api/users\n\nCreate a new user account.\n\n### Parameters\n- email (required): string...',
        TRUE,
        TRUE,
        '["api", "documentation", "technical"]'::jsonb
    ),
    (
        'Debug Analysis',
        'Analyze error logs and suggest fixes',
        E'Analyze the following error/log and provide debugging assistance:

Error/Log: {error_log}
Context: {context}

Provide:
1. Root cause analysis
2. Explanation of the error
3. Step-by-step debugging approach
4. Suggested fix with code examples
5. Prevention recommendations

Be specific and actionable.',
        'analysis',
        'technical',
        'chat',
        'markdown',
        'NullPointerException at line 127 in UserService.java...',
        '## Debug Analysis\n\n### Root Cause\nNull user object passed to method...\n\n### Fix\n```java\nif (user != null) {...',
        TRUE,
        TRUE,
        '["debug", "troubleshooting", "errors"]'::jsonb
    ),
    (
        'Test Case Generation',
        'Generate comprehensive test cases',
        E'Generate comprehensive test cases for:

Function/Feature: {feature}
Code: {code}
Requirements: {requirements}

Create test cases covering:
- Happy path scenarios
- Edge cases
- Error conditions
- Boundary values
- Integration scenarios

Format as structured test suite.',
        'generation',
        'technical',
        'chat',
        'markdown',
        'User registration function with email validation...',
        '## Test Suite: User Registration\n\n### Test 1: Valid Registration\n**Input**: valid email, password\n**Expected**: User created...',
        TRUE,
        TRUE,
        '["testing", "qa", "test-cases"]'::jsonb
    ),
    (
        'Architecture Design',
        'Design system architecture and provide recommendations',
        E'Design system architecture for:

Requirements: {requirements}
Constraints: {constraints}
Scale: {scale}

Provide:
1. High-level architecture diagram (text description)
2. Component breakdown
3. Technology stack recommendations
4. Data flow
5. Scalability considerations
6. Security measures
7. Trade-offs and alternatives',
        'analysis',
        'technical',
        'chat',
        'markdown',
        'E-commerce platform handling 1M users with real-time inventory...',
        '## System Architecture\n\n### Overview\nMicroservices-based architecture...\n\n### Components\n1. API Gateway...',
        TRUE,
        TRUE,
        '["architecture", "design", "system"]'::jsonb
    )
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    prompt_text = EXCLUDED.prompt_text,
    updated_at = NOW();

-- ============================================================================
-- LEGAL CATEGORY (2 prompts)
-- ============================================================================

INSERT INTO prompt_library (
    name, description, prompt_text, prompt_type, category, module,
    expected_output_format, example_input, example_output,
    is_public, is_verified, tags
) VALUES
    (
        'Contract Review',
        'Review contracts for key terms and risks',
        E'Review the following contract and extract key information:

Contract: {input_text}

Extract and analyze:
1. Parties involved
2. Key obligations
3. Payment terms
4. Termination clauses
5. Liability limitations
6. Risk factors
7. Notable clauses requiring attention

Format as structured JSON with risk assessment.',
        'analysis',
        'legal',
        'chat',
        'json',
        'Service agreement between Company A and Company B...',
        '{"parties": ["Company A", "Company B"], "key_terms": {...}, "risks": ["Unlimited liability clause"], "risk_level": "high"}',
        TRUE,
        TRUE,
        '["contract", "legal", "review"]'::jsonb
    ),
    (
        'Compliance Check',
        'Check documents for regulatory compliance',
        E'Review the following for compliance with {regulation}:

Document/Process: {input_text}
Applicable Regulations: {regulation}

Check for:
1. Regulatory requirements coverage
2. Gaps in compliance
3. Non-compliant sections
4. Required additions
5. Risk assessment

Provide detailed compliance report.',
        'analysis',
        'legal',
        'chat',
        'markdown',
        'Data processing policy against GDPR requirements...',
        '## Compliance Report\n\n### Compliant Areas\n- Data subject rights documented...\n\n### Gaps\n- Missing DPO contact...',
        TRUE,
        TRUE,
        '["compliance", "legal", "regulatory"]'::jsonb
    )
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    prompt_text = EXCLUDED.prompt_text,
    updated_at = NOW();

-- ============================================================================
-- EDUCATION CATEGORY (2 prompts)
-- ============================================================================

INSERT INTO prompt_library (
    name, description, prompt_text, prompt_type, category, module,
    expected_output_format, example_input, example_output,
    is_public, is_verified, tags
) VALUES
    (
        'Course Material Generation',
        'Generate educational course materials',
        E'Generate course material for:

Topic: {topic}
Level: {level}
Duration: {duration}
Learning Objectives: {objectives}

Create:
1. Course outline with modules
2. Key concepts explanation
3. Examples and exercises
4. Assessment questions
5. Additional resources

Make it engaging and pedagogically sound.',
        'generation',
        'education',
        'chat',
        'markdown',
        'Topic: Introduction to Python, Level: Beginner, Duration: 4 weeks',
        '## Course: Introduction to Python\n\n### Week 1: Basics\n- Variables and data types...',
        TRUE,
        TRUE,
        '["education", "course", "learning"]'::jsonb
    ),
    (
        'Quiz Generation',
        'Generate assessment quizzes from content',
        E'Generate a quiz based on the following content:

Content: {input_text}
Quiz Type: {quiz_type}
Difficulty: {difficulty}
Number of Questions: {num_questions}

Create questions with:
- Clear question text
- Multiple choice options (if applicable)
- Correct answer
- Explanation for correct answer
- Difficulty level

Format as JSON array of questions.',
        'generation',
        'education',
        'chat',
        'json',
        'Content about photosynthesis, 5 questions, multiple choice, medium difficulty',
        '[{"question": "What is the primary product of photosynthesis?", "options": ["Oxygen", "Carbon dioxide", "Glucose", "Water"], "answer": "Glucose", "explanation": "..."}]',
        TRUE,
        TRUE,
        '["quiz", "assessment", "education"]'::jsonb
    )
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    prompt_text = EXCLUDED.prompt_text,
    updated_at = NOW();

-- ============================================================================
-- VERIFICATION & REPORTING
-- ============================================================================

DO $$
DECLARE
    total_count INTEGER;
    general_count INTEGER;
    business_count INTEGER;
    data_count INTEGER;
    technical_count INTEGER;
    legal_count INTEGER;
    education_count INTEGER;
    public_count INTEGER;
    verified_count INTEGER;
BEGIN
    -- Count total prompts
    SELECT COUNT(*) INTO total_count FROM prompt_library;

    -- Count by category
    SELECT COUNT(*) INTO general_count FROM prompt_library WHERE category = 'general';
    SELECT COUNT(*) INTO business_count FROM prompt_library WHERE category = 'business';
    SELECT COUNT(*) INTO data_count FROM prompt_library WHERE category = 'data-analysis';
    SELECT COUNT(*) INTO technical_count FROM prompt_library WHERE category = 'technical';
    SELECT COUNT(*) INTO legal_count FROM prompt_library WHERE category = 'legal';
    SELECT COUNT(*) INTO education_count FROM prompt_library WHERE category = 'education';

    -- Count public and verified
    SELECT COUNT(*) INTO public_count FROM prompt_library WHERE is_public = TRUE;
    SELECT COUNT(*) INTO verified_count FROM prompt_library WHERE is_verified = TRUE;

    -- Report
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'PROMPT LIBRARY SEEDING COMPLETE';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Total prompts seeded: %', total_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Breakdown by category:';
    RAISE NOTICE '  General:        % prompts', general_count;
    RAISE NOTICE '  Business:       % prompts', business_count;
    RAISE NOTICE '  Data Analysis:  % prompts', data_count;
    RAISE NOTICE '  Technical:      % prompts', technical_count;
    RAISE NOTICE '  Legal:          % prompts', legal_count;
    RAISE NOTICE '  Education:      % prompts', education_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Status:';
    RAISE NOTICE '  Public prompts:    %', public_count;
    RAISE NOTICE '  Verified prompts:  %', verified_count;
    RAISE NOTICE '';
    RAISE NOTICE '✓ Prompt library successfully seeded';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
END
$$;
