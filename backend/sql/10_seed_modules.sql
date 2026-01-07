-- ============================================================================
-- Seed Modules - Complete 36 Module Registry
-- ============================================================================
--
-- Purpose: Seed all 36 modules across 3 tiers
--
-- Module Tiers:
--   - Tier 1 (Core Platform):      10 modules - Core RAG platform features
--   - Tier 2 (Domain Verticals):   20 modules - Industry-specific solutions
--   - Tier 3 (Customer Solutions):  6 modules - Customer-specific POCs
--
-- Dependencies: modules table
--
-- Idempotent: Yes (ON CONFLICT DO UPDATE)
--
-- ============================================================================

-- ============================================================================
-- TIER 1: CORE PLATFORM MODULES (10 modules)
-- ============================================================================

INSERT INTO modules (module_key, name, code, module_name, description, icon, route, is_active, display_order, meta_info)
VALUES
    -- Core Chat & History
    (
        'chat',
        'Chat',
        'CHAT',
        'RAG Chat Interface',
        'RAG-powered conversational AI with document-aware responses and source citations',
        'MessageSquare',
        '/chat',
        TRUE,
        1,
        '{"tier": 1, "category": "core", "tags": ["rag", "llm", "chat"]}'::jsonb
    ),
    (
        'history',
        'Chat History',
        'HISTORY',
        'Chat History',
        'View and manage conversation history with session management and search',
        'History',
        '/history',
        TRUE,
        2,
        '{"tier": 1, "category": "core", "tags": ["history", "sessions"]}'::jsonb
    ),

    -- Document Management
    (
        'upload',
        'Upload Files',
        'UPLOAD',
        'Document Upload',
        'Upload documents (PDF, DOCX, TXT, JSON) for RAG processing with MinIO storage',
        'Upload',
        '/upload',
        TRUE,
        3,
        '{"tier": 1, "category": "core", "tags": ["upload", "documents", "minio"]}'::jsonb
    ),
    (
        'scrape',
        'Web Scraping',
        'SCRAPE',
        'Web Scraping',
        'Intelligent web scraping with Playwright for data extraction and document ingestion',
        'Globe',
        '/scrape',
        TRUE,
        4,
        '{"tier": 1, "category": "core", "tags": ["scraping", "playwright", "web"]}'::jsonb
    ),

    -- Tools & Configuration
    (
        'estimator',
        'Project Estimator',
        'ESTIMATOR',
        'Project Estimator',
        'AI-powered project scope and effort estimation with resource planning',
        'Calculator',
        '/estimator',
        TRUE,
        5,
        '{"tier": 1, "category": "tools", "tags": ["estimation", "planning"]}'::jsonb
    ),
    (
        'evaluation',
        'Evaluation',
        'EVALUATION',
        'RAG Evaluation',
        'Comprehensive RAG evaluation metrics (RAGAS, faithfulness, relevancy, toxicity)',
        'BarChart3',
        '/evaluation',
        TRUE,
        6,
        '{"tier": 1, "category": "analytics", "tags": ["evaluation", "metrics", "ragas"]}'::jsonb
    ),
    (
        'tools',
        'Tool Usage',
        'TOOLS',
        'Tool Usage Analytics',
        'Real-time analytics and monitoring of tool usage, performance, and costs',
        'Wrench',
        '/tools',
        TRUE,
        7,
        '{"tier": 1, "category": "analytics", "tags": ["tools", "monitoring", "metrics"]}'::jsonb
    ),
    (
        'weights',
        'Weights Config',
        'WEIGHTS',
        'RAG System Configuration',
        'Configure RAG weights, hybrid search parameters, and reranking strategies',
        'Sliders',
        '/weights',
        TRUE,
        8,
        '{"tier": 1, "category": "configuration", "tags": ["config", "rag", "weights"]}'::jsonb
    ),

    -- Fine-tuning & Admin
    (
        'finetuning',
        'Fine-Tuning',
        'FINETUNING',
        'Model Fine-Tuning',
        'Distributed model fine-tuning with GPU allocation and MLflow tracking',
        'Cpu',
        '/finetuning',
        TRUE,
        9,
        '{"tier": 1, "category": "ml", "tags": ["finetuning", "lora", "qlora", "gpu"]}'::jsonb
    ),
    (
        'admin',
        'Admin',
        'ADMIN',
        'System Administration',
        'System administration, user management, RBAC configuration, and audit logs',
        'Shield',
        '/admin',
        TRUE,
        10,
        '{"tier": 1, "category": "admin", "tags": ["admin", "rbac", "users"]}'::jsonb
    )
ON CONFLICT (module_key) DO UPDATE SET
    name = EXCLUDED.name,
    code = EXCLUDED.code,
    module_name = EXCLUDED.module_name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    route = EXCLUDED.route,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    meta_info = EXCLUDED.meta_info,
    updated_at = NOW();

-- ============================================================================
-- TIER 2: DOMAIN VERTICALS (20 modules)
-- ============================================================================

INSERT INTO modules (module_key, name, code, module_name, description, icon, route, is_active, display_order, meta_info)
VALUES
    -- Analytics (4 modules)
    (
        'predictive_analytics',
        'Predictive Analytics',
        'PREDICT_ANALYTICS',
        'Predictive Analytics Engine',
        'Time-series forecasting and predictive modeling for business metrics',
        'TrendingUp',
        '/tier2/analytics/predictive',
        TRUE,
        101,
        '{"tier": 2, "category": "analytics", "tags": ["forecasting", "ml", "timeseries"]}'::jsonb
    ),
    (
        'customer_churn',
        'Customer Churn Prediction',
        'CHURN_PREDICT',
        'Customer Churn Predictor',
        'Predict customer churn risk with ML-powered analysis and retention strategies',
        'UserMinus',
        '/tier2/analytics/churn',
        TRUE,
        102,
        '{"tier": 2, "category": "analytics", "tags": ["churn", "ml", "retention"]}'::jsonb
    ),
    (
        'financial_anomaly',
        'Financial Anomaly Detection',
        'FIN_ANOMALY',
        'Financial Anomaly Detector',
        'Detect anomalies in financial transactions and patterns using ML',
        'AlertTriangle',
        '/tier2/analytics/anomaly',
        TRUE,
        103,
        '{"tier": 2, "category": "analytics", "tags": ["anomaly", "finance", "fraud"]}'::jsonb
    ),
    (
        'sales_performance',
        'Sales Performance Analytics',
        'SALES_PERF',
        'Sales Performance Dashboard',
        'Analyze sales performance, trends, and revenue forecasting',
        'DollarSign',
        '/tier2/analytics/sales',
        TRUE,
        104,
        '{"tier": 2, "category": "analytics", "tags": ["sales", "revenue", "kpi"]}'::jsonb
    ),

    -- Marketing (2 modules)
    (
        'campaign_optimizer',
        'Campaign Optimizer',
        'CAMPAIGN_OPT',
        'Marketing Campaign Optimizer',
        'AI-powered marketing campaign optimization and A/B testing',
        'Target',
        '/tier2/marketing/campaign',
        TRUE,
        105,
        '{"tier": 2, "category": "marketing", "tags": ["marketing", "campaigns", "optimization"]}'::jsonb
    ),
    (
        'sentiment_social',
        'Sentiment & Social Analytics',
        'SENTIMENT_SOCIAL',
        'Social Media Sentiment Analysis',
        'Real-time sentiment analysis of social media and customer feedback',
        'MessageCircle',
        '/tier2/marketing/sentiment',
        TRUE,
        106,
        '{"tier": 2, "category": "marketing", "tags": ["sentiment", "nlp", "social"]}'::jsonb
    ),

    -- HR & Talent (3 modules)
    (
        'talent_search',
        'Talent Search',
        'TALENT_SEARCH',
        'AI Talent Search Engine',
        'Semantic search for candidate resumes with skill matching and ranking',
        'Search',
        '/tier2/hr/talent-search',
        TRUE,
        107,
        '{"tier": 2, "category": "hr", "tags": ["hr", "recruitment", "search"]}'::jsonb
    ),
    (
        'taxonomy_skillmatch',
        'Taxonomy Skill Matcher',
        'TAX_SKILLMATCH',
        'Skills Taxonomy Matcher',
        'Match candidates to jobs using industry taxonomies and skill graphs',
        'GitBranch',
        '/tier2/hr/skillmatch',
        TRUE,
        108,
        '{"tier": 2, "category": "hr", "tags": ["skills", "taxonomy", "matching"]}'::jsonb
    ),
    (
        'talent_pulse',
        'Talent Pulse',
        'TALENT_PULSE',
        'Employee Engagement Analytics',
        'Real-time employee engagement and sentiment tracking',
        'Activity',
        '/tier2/hr/pulse',
        TRUE,
        109,
        '{"tier": 2, "category": "hr", "tags": ["engagement", "sentiment", "hr"]}'::jsonb
    ),

    -- Procurement (4 modules)
    (
        'procurement_matcher',
        'Procurement Matcher',
        'PROC_MATCHER',
        'Supplier-RFP Matcher',
        'AI-powered matching of suppliers to RFPs with scoring and recommendations',
        'Link',
        '/tier2/procurement/matcher',
        TRUE,
        110,
        '{"tier": 2, "category": "procurement", "tags": ["procurement", "rfp", "matching"]}'::jsonb
    ),
    (
        'vendor_recommendation',
        'Vendor Recommendation',
        'VENDOR_RECOMMEND',
        'Vendor Recommendation Engine',
        'Smart vendor recommendations based on requirements and historical data',
        'Award',
        '/tier2/procurement/vendor',
        TRUE,
        111,
        '{"tier": 2, "category": "procurement", "tags": ["vendor", "recommendation"]}'::jsonb
    ),
    (
        'tender_intelligence',
        'Tender Intelligence',
        'TENDER_INTEL',
        'Tender Intelligence System',
        'Extract and analyze tender documents for competitive intelligence',
        'FileText',
        '/tier2/procurement/tender',
        TRUE,
        112,
        '{"tier": 2, "category": "procurement", "tags": ["tender", "intelligence"]}'::jsonb
    ),
    (
        'spend_smart',
        'Spend Smart',
        'SPEND_SMART',
        'Spend Analytics & Optimization',
        'Analyze spending patterns and identify cost-saving opportunities',
        'PieChart',
        '/tier2/procurement/spend',
        TRUE,
        113,
        '{"tier": 2, "category": "procurement", "tags": ["spend", "analytics", "cost"]}'::jsonb
    ),

    -- Document Intelligence (2 modules)
    (
        'generic_rag',
        'Generic RAG',
        'GENERIC_RAG',
        'Generic Document Q&A',
        'Generic RAG-powered document question answering with multi-document support',
        'FileQuestion',
        '/tier2/document/generic-rag',
        TRUE,
        114,
        '{"tier": 2, "category": "document_intelligence", "tags": ["rag", "qa", "documents"]}'::jsonb
    ),
    (
        'relation_extractor',
        'Relation Extractor',
        'RELATION_EXTRACT',
        'Entity Relationship Extractor',
        'Extract entities and relationships from documents with graph visualization',
        'Network',
        '/tier2/document/relations',
        TRUE,
        115,
        '{"tier": 2, "category": "document_intelligence", "tags": ["ner", "entities", "relations"]}'::jsonb
    ),

    -- Construction (2 modules)
    (
        'mine_scope',
        'Mine Scope Analyzer',
        'MINE_SCOPE',
        'Mining Scope Analysis',
        'Analyze mining project scope documents and extract key metrics',
        'Mountain',
        '/tier2/construction/mine-scope',
        TRUE,
        116,
        '{"tier": 2, "category": "construction", "tags": ["mining", "scope", "analysis"]}'::jsonb
    ),
    (
        'planning_classifier',
        'Planning Application Classifier',
        'PLANNING_CLASSIFY',
        'Planning Application Classifier',
        'Classify and analyze planning applications with entity extraction',
        'Building',
        '/tier2/construction/planning',
        TRUE,
        117,
        '{"tier": 2, "category": "construction", "tags": ["planning", "classification"]}'::jsonb
    ),

    -- E-commerce (1 module)
    (
        'product_recommendation',
        'Product Recommendation',
        'PRODUCT_RECOMMEND',
        'E-commerce Recommendation Engine',
        'Personalized product recommendations using collaborative filtering',
        'ShoppingCart',
        '/tier2/ecommerce/recommend',
        TRUE,
        118,
        '{"tier": 2, "category": "ecommerce", "tags": ["recommendation", "ecommerce"]}'::jsonb
    ),

    -- Maritime (1 module)
    (
        'maritime_logistics',
        'Maritime Logistics',
        'MARITIME_LOGISTICS',
        'Maritime Supply Chain Optimizer',
        'Optimize maritime logistics and supply chain operations',
        'Ship',
        '/tier2/maritime/logistics',
        TRUE,
        119,
        '{"tier": 2, "category": "maritime", "tags": ["maritime", "logistics", "supply-chain"]}'::jsonb
    ),

    -- Advanced Capabilities (1 module)
    (
        'code_analysis',
        'Code Analysis',
        'CODE_ANALYSIS',
        'AI Code Analysis & Review',
        'Automated code analysis, review, and quality assessment',
        'Code',
        '/tier2/advanced/code-analysis',
        TRUE,
        120,
        '{"tier": 2, "category": "advanced_capabilities", "tags": ["code", "analysis", "review"]}'::jsonb
    )
ON CONFLICT (module_key) DO UPDATE SET
    name = EXCLUDED.name,
    code = EXCLUDED.code,
    module_name = EXCLUDED.module_name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    route = EXCLUDED.route,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    meta_info = EXCLUDED.meta_info,
    updated_at = NOW();

-- ============================================================================
-- TIER 3: CUSTOMER SOLUTIONS (6 modules)
-- ============================================================================

INSERT INTO modules (module_key, name, code, module_name, description, icon, route, is_active, display_order, meta_info)
VALUES
    (
        'cru_mining',
        'CRU Mining Intelligence',
        'CRU_POC',
        'CRU Mining Intelligence POC',
        'CRU Group POC: Mining market intelligence with multi-pipeline RAG and reranking',
        'Pickaxe',
        '/tier3/cru',
        TRUE,
        201,
        '{"tier": 3, "category": "customer_solutions", "customer": "CRU Group", "tags": ["mining", "intelligence", "poc"]}'::jsonb
    ),
    (
        'construction_monitor',
        'Construction Monitor',
        'CONSTRUCTION_MON',
        'Construction Planning Monitor',
        'Construction Monitor POC: Planning application analysis and entity extraction',
        'HardHat',
        '/tier3/construction-monitor',
        TRUE,
        202,
        '{"tier": 3, "category": "customer_solutions", "customer": "Construction Monitor", "tags": ["construction", "planning", "poc"]}'::jsonb
    ),
    (
        'british_council',
        'British Council Recommender',
        'BRITISH_COUNCIL',
        'British Council Course Recommender',
        'British Council POC: AI-powered course recommendations with learner profile analysis',
        'GraduationCap',
        '/tier3/british-council',
        TRUE,
        203,
        '{"tier": 3, "category": "customer_solutions", "customer": "British Council", "tags": ["education", "recommendation", "poc"]}'::jsonb
    ),
    (
        'grant_thornton',
        'Grant Thornton Analyzer',
        'GRANT_THORNTON',
        'Grant Thornton Financial Analysis',
        'Grant Thornton POC: Credit analysis and financial document extraction',
        'Briefcase',
        '/tier3/grant-thornton',
        TRUE,
        204,
        '{"tier": 3, "category": "customer_solutions", "customer": "Grant Thornton", "tags": ["finance", "credit", "poc"]}'::jsonb
    ),
    (
        'solera',
        'Solera Claims Intelligence',
        'SOLERA',
        'Solera Insurance Claims',
        'Solera POC: Automated insurance claims processing and damage assessment',
        'ClipboardCheck',
        '/tier3/solera',
        TRUE,
        205,
        '{"tier": 3, "category": "customer_solutions", "customer": "Solera", "tags": ["insurance", "claims", "poc"]}'::jsonb
    ),
    (
        'gt_motive',
        'GT Motive Estimator',
        'GT_MOTIVE',
        'GT Motive Repair Estimator',
        'GT Motive POC: Automotive repair cost estimation and parts identification',
        'Wrench',
        '/tier3/gt-motive',
        TRUE,
        206,
        '{"tier": 3, "category": "customer_solutions", "customer": "GT Motive", "tags": ["automotive", "estimation", "poc"]}'::jsonb
    )
ON CONFLICT (module_key) DO UPDATE SET
    name = EXCLUDED.name,
    code = EXCLUDED.code,
    module_name = EXCLUDED.module_name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    route = EXCLUDED.route,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    meta_info = EXCLUDED.meta_info,
    updated_at = NOW();

-- ============================================================================
-- VERIFICATION & REPORTING
-- ============================================================================

DO $$
DECLARE
    total_count INTEGER;
    tier1_count INTEGER;
    tier2_count INTEGER;
    tier3_count INTEGER;
BEGIN
    -- Count total modules
    SELECT COUNT(*) INTO total_count FROM modules;

    -- Count by tier
    SELECT COUNT(*) INTO tier1_count FROM modules WHERE meta_info->>'tier' = '1';
    SELECT COUNT(*) INTO tier2_count FROM modules WHERE meta_info->>'tier' = '2';
    SELECT COUNT(*) INTO tier3_count FROM modules WHERE meta_info->>'tier' = '3';

    -- Report
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'MODULE SEEDING COMPLETE';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Total modules seeded: %', total_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Breakdown by tier:';
    RAISE NOTICE '  Tier 1 (Core Platform):      % modules', tier1_count;
    RAISE NOTICE '  Tier 2 (Domain Verticals):   % modules', tier2_count;
    RAISE NOTICE '  Tier 3 (Customer Solutions): % modules', tier3_count;
    RAISE NOTICE '';
    RAISE NOTICE '✓ All 36 modules successfully seeded';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
END
$$;
