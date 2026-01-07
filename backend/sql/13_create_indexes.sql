-- ============================================================================
-- Create Performance Indexes - Complete Index Strategy
-- ============================================================================
--
-- Purpose: Create all performance indexes for optimal query performance
--
-- Index Types:
--   - B-Tree:     Standard indexes for equality/range queries
--   - IVFFlat:    Vector similarity search indexes
--   - GIN:        JSONB and array indexes
--   - GiST:       Full-text search and geometric data
--
-- Coverage:
--   - Foreign key columns (for JOIN optimization)
--   - Frequently queried columns (status, dates, flags)
--   - Vector embeddings (for semantic search)
--   - JSONB columns (for metadata queries)
--   - Composite indexes (for multi-column queries)
--
-- Dependencies: All tables from 02_complete_schema.sql
--
-- Idempotent: Yes (CREATE INDEX IF NOT EXISTS)
--
-- ============================================================================

-- ============================================================================
-- VECTOR INDEXES (Critical for RAG Performance)
-- ============================================================================
-- These are already created in schema but verified here

-- Primary embedding index (384-dim)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Specialized embedding indexes
CREATE INDEX IF NOT EXISTS idx_chunks_table_embedding
    ON document_chunks USING ivfflat (table_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chunks_visual_embedding
    ON document_chunks USING ivfflat (visual_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chunks_numerical_embedding
    ON document_chunks USING ivfflat (numerical_embedding vector_l2_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chunks_code_embedding
    ON document_chunks USING ivfflat (code_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Query cache embedding index
CREATE INDEX IF NOT EXISTS idx_query_cache_embedding
    ON query_cache USING ivfflat (query_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Session context embedding index
CREATE INDEX IF NOT EXISTS idx_session_contexts_embedding
    ON session_contexts USING ivfflat (conversation_embedding vector_cosine_ops)
    WITH (lists = 50);

RAISE NOTICE '✓ Vector indexes created (7 indexes)';

-- ============================================================================
-- FOREIGN KEY INDEXES (Essential for JOIN Performance)
-- ============================================================================

-- Users table FKs
CREATE INDEX IF NOT EXISTS idx_users_department_id ON users(department_id);
CREATE INDEX IF NOT EXISTS idx_users_team_id ON users(team_id);

-- Teams table FKs
CREATE INDEX IF NOT EXISTS idx_teams_department_id ON teams(department_id);
CREATE INDEX IF NOT EXISTS idx_teams_team_lead_id ON teams(team_lead_id);

-- Projects table FKs
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_department_id ON projects(department_id);
CREATE INDEX IF NOT EXISTS idx_projects_team_id ON projects(team_id);

-- Documents table FKs
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_department_id ON documents(department_id);
CREATE INDEX IF NOT EXISTS idx_documents_team_id ON documents(team_id);

-- Document chunks table FKs
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_project_id ON document_chunks(project_id);
CREATE INDEX IF NOT EXISTS idx_chunks_uploaded_by ON document_chunks(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_chunks_department_id ON document_chunks(department_id);
CREATE INDEX IF NOT EXISTS idx_chunks_team_id ON document_chunks(team_id);

-- Chat sessions table FKs
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_project_id ON chat_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_sessions_department_id ON chat_sessions(department_id);
CREATE INDEX IF NOT EXISTS idx_sessions_team_id ON chat_sessions(team_id);

-- Session documents table FKs
CREATE INDEX IF NOT EXISTS idx_session_documents_session ON session_documents(session_id);
CREATE INDEX IF NOT EXISTS idx_session_documents_document ON session_documents(document_id);

-- Conversation messages table FKs
CREATE INDEX IF NOT EXISTS idx_conversation_messages_session ON conversation_messages(session_id);

-- Messages table FKs (legacy)
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- Conversations table FKs (legacy)
CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);

-- Web scrape jobs table FKs
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_project_id ON web_scrape_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_scraped_by ON web_scrape_jobs(scraped_by);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_department_id ON web_scrape_jobs(department_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_team_id ON web_scrape_jobs(team_id);

-- Audit logs table FKs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_session ON audit_logs(session_id);

-- Usage metrics table FKs
CREATE INDEX IF NOT EXISTS idx_usage_metrics_user ON usage_metrics(user_id);

-- Tool usage stats table FKs
CREATE INDEX IF NOT EXISTS idx_tool_usage_user ON tool_usage_stats(user_id);

-- Agent tasks table FKs
CREATE INDEX IF NOT EXISTS idx_agent_tasks_project_id ON agent_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_by ON agent_tasks(created_by);

-- Prompt library table FKs
CREATE INDEX IF NOT EXISTS idx_prompt_library_created_by ON prompt_library(created_by);
CREATE INDEX IF NOT EXISTS idx_prompt_library_project_id ON prompt_library(project_id);
CREATE INDEX IF NOT EXISTS idx_prompt_library_department_id ON prompt_library(department_id);

-- Output templates table FKs
CREATE INDEX IF NOT EXISTS idx_output_templates_created_by ON output_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_output_templates_project_id ON output_templates(project_id);
CREATE INDEX IF NOT EXISTS idx_output_templates_department_id ON output_templates(department_id);

-- Extraction templates table FKs
CREATE INDEX IF NOT EXISTS idx_extraction_templates_active ON extraction_templates(is_active) WHERE is_active = TRUE;

-- Extraction jobs table FKs
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_template ON extraction_jobs(template_id);

-- Extraction results table FKs
CREATE INDEX IF NOT EXISTS idx_extraction_results_job ON extraction_results(job_id);

-- Fine-tuning datasets table FKs
CREATE INDEX IF NOT EXISTS idx_finetuning_datasets_uploaded_by ON finetuning_datasets(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_finetuning_datasets_project ON finetuning_datasets(project_id);

-- Fine-tuning jobs table FKs
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_created_by ON finetuning_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_project ON finetuning_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_dataset ON finetuning_jobs(dataset_id);

-- Fine-tuned models table FKs
CREATE INDEX IF NOT EXISTS idx_finetuned_models_job ON finetuned_models(job_id);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_project ON finetuned_models(project_id);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_created_by ON finetuned_models(created_by);

-- Training metrics table FKs
CREATE INDEX IF NOT EXISTS idx_training_metrics_job_timestamp ON training_metrics(job_id, timestamp DESC);

-- Evaluation tables FKs
CREATE INDEX IF NOT EXISTS idx_evaluation_configs_user_id ON evaluation_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_configs_session_id ON evaluation_configs(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_session_id ON evaluation_results(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_message_id ON evaluation_results(message_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_session_id ON human_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_message_id ON human_feedback(message_id);

-- RBAC tables FKs
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_department ON user_roles(department_id);
CREATE INDEX IF NOT EXISTS idx_user_teams_user ON user_teams(user_id);
CREATE INDEX IF NOT EXISTS idx_user_teams_team ON user_teams(team_id);
CREATE INDEX IF NOT EXISTS idx_permissions_role ON role_module_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_permissions_module ON role_module_permissions(module_id);

RAISE NOTICE '✓ Foreign key indexes created (60+ indexes)';

-- ============================================================================
-- QUERY OPTIMIZATION INDEXES (Frequently Queried Columns)
-- ============================================================================

-- User lookup indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active) WHERE is_active = TRUE;

-- Module indexes
CREATE INDEX IF NOT EXISTS idx_modules_module_key ON modules(module_key);
CREATE INDEX IF NOT EXISTS idx_modules_code ON modules(code);
CREATE INDEX IF NOT EXISTS idx_modules_is_active ON modules(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_modules_display_order ON modules(display_order);

-- Role indexes
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_roles_parent ON roles(parent_role_id);

-- Department indexes
CREATE INDEX IF NOT EXISTS idx_departments_name ON departments(name);
CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_is_active ON departments(is_active) WHERE is_active = TRUE;

-- Team indexes
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code);
CREATE INDEX IF NOT EXISTS idx_teams_is_active ON teams(is_active) WHERE is_active = TRUE;

-- Project indexes
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_primary_embedding ON projects(primary_embedding_config);

-- Document indexes
CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed) WHERE processed = FALSE;
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_minio_path ON documents(minio_path);

-- Document chunks indexes
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_strategy ON document_chunks(embedding_strategy);

-- Chat session indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(is_active) WHERE is_active = TRUE;

-- Web scraping indexes
CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_status ON web_scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_configs_domain ON scraping_configs(domain);
CREATE INDEX IF NOT EXISTS idx_scraping_configs_status ON scraping_configs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_configs_allow_scraping ON scraping_configs(allow_scraping);

-- Models registry indexes
CREATE INDEX IF NOT EXISTS idx_models_model_id ON models(model_id);
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_models_type ON models(model_type);
CREATE INDEX IF NOT EXISTS idx_models_is_active ON models(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_models_is_default ON models(is_default) WHERE is_default = TRUE;

-- System config indexes
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);
CREATE INDEX IF NOT EXISTS idx_system_config_active ON system_config(is_active) WHERE is_active = TRUE;

-- API keys indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Tool usage indexes
CREATE INDEX IF NOT EXISTS idx_tool_usage_category ON tool_usage_stats(tool_category);
CREATE INDEX IF NOT EXISTS idx_tool_usage_name ON tool_usage_stats(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_usage_session ON tool_usage_stats(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_success ON tool_usage_stats(success);

-- Agent tasks indexes
CREATE INDEX IF NOT EXISTS idx_agent_tasks_task_id ON agent_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_session_id ON agent_tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);

-- Prompt library indexes
CREATE INDEX IF NOT EXISTS idx_prompt_library_prompt_type ON prompt_library(prompt_type);
CREATE INDEX IF NOT EXISTS idx_prompt_library_category ON prompt_library(category);
CREATE INDEX IF NOT EXISTS idx_prompt_library_module ON prompt_library(module);
CREATE INDEX IF NOT EXISTS idx_prompt_library_is_public ON prompt_library(is_public);
CREATE INDEX IF NOT EXISTS idx_prompt_library_usage_count ON prompt_library(usage_count DESC);

-- Extraction jobs indexes
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_status ON extraction_jobs(status);

-- Fine-tuning indexes
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_status ON finetuning_jobs(status);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_method ON finetuning_jobs(finetuning_method);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_training_stage ON finetuning_jobs(training_stage);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_status ON finetuned_models(status);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_ollama_name ON finetuned_models(ollama_model_name);

-- Evaluation indexes
CREATE INDEX IF NOT EXISTS idx_evaluation_results_overall_score ON evaluation_results(overall_score);
CREATE INDEX IF NOT EXISTS idx_evaluation_cache_key ON evaluation_cache(cache_key);

RAISE NOTICE '✓ Query optimization indexes created (50+ indexes)';

-- ============================================================================
-- DATE/TIME INDEXES (For Time-Series Queries)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_cache_created_at ON query_cache(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_created_at ON web_scrape_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_usage_created_at ON tool_usage_stats(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_at ON agent_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_metrics_date ON usage_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_usage_log_created_at ON prompt_usage_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_created ON extraction_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_created_at ON finetuning_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_created_at ON evaluation_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_human_feedback_created_at ON human_feedback(created_at DESC);

RAISE NOTICE '✓ Date/time indexes created (14 indexes)';

-- ============================================================================
-- COMPOSITE INDEXES (Multi-Column Queries)
-- ============================================================================

-- Document access patterns
CREATE INDEX IF NOT EXISTS idx_documents_dept_team
    ON documents(department, team);
CREATE INDEX IF NOT EXISTS idx_documents_dept_team_user
    ON documents(department, team, uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_role_dept
    ON documents(user_role, department);
CREATE INDEX IF NOT EXISTS idx_documents_project_user
    ON documents(project_id, uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_user_date
    ON documents(uploaded_by, upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_documents_project_date
    ON documents(project_id, upload_date DESC);

-- Document chunks access patterns
CREATE INDEX IF NOT EXISTS idx_chunks_dept_team
    ON document_chunks(department, team);
CREATE INDEX IF NOT EXISTS idx_chunks_project_user
    ON document_chunks(project_id, uploaded_by);

-- Session context queries
CREATE INDEX IF NOT EXISTS idx_sessions_department
    ON chat_sessions(department);
CREATE INDEX IF NOT EXISTS idx_sessions_team
    ON chat_sessions(team);

-- Session documents priority
CREATE INDEX IF NOT EXISTS idx_session_documents_priority
    ON session_documents(session_id, priority DESC);

-- Conversation messages with time
CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_time
    ON conversation_messages(session_id, created_at DESC);

-- Tool usage analytics
CREATE INDEX IF NOT EXISTS idx_tool_usage_category_name_date
    ON tool_usage_stats(tool_category, tool_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_usage_session_date
    ON tool_usage_stats(session_id, created_at DESC);

-- Usage metrics aggregation
CREATE INDEX IF NOT EXISTS idx_usage_metrics_user_date
    ON usage_metrics(user_id, date DESC);

-- Training metrics time-series
CREATE INDEX IF NOT EXISTS idx_training_metrics_job_step
    ON training_metrics(job_id, step);

-- User roles composite
CREATE INDEX IF NOT EXISTS idx_user_roles_active
    ON user_roles(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_teams_primary
    ON user_teams(user_id, is_primary) WHERE is_primary = TRUE;

RAISE NOTICE '✓ Composite indexes created (18 indexes)';

-- ============================================================================
-- JSONB INDEXES (For Metadata Queries)
-- ============================================================================

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_prompt_library_tags
    ON prompt_library USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_tags
    ON finetuned_models USING gin(tags);

-- Specific JSONB path indexes for common queries
CREATE INDEX IF NOT EXISTS idx_modules_tier
    ON modules((meta_info->>'tier'));
CREATE INDEX IF NOT EXISTS idx_modules_category
    ON modules((meta_info->>'category'));

RAISE NOTICE '✓ JSONB indexes created (4 indexes)';

-- ============================================================================
-- FULL-TEXT SEARCH INDEXES (For Text Search)
-- ============================================================================

-- GIN trigram indexes for fuzzy text search
CREATE INDEX IF NOT EXISTS idx_documents_filename_trgm
    ON documents USING gin(filename gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_users_username_trgm
    ON users USING gin(username gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_users_email_trgm
    ON users USING gin(email gin_trgm_ops);

-- If full-text search needed on document chunks (optional, can be memory intensive)
-- CREATE INDEX IF NOT EXISTS idx_chunks_content_fts
--     ON document_chunks USING gin(to_tsvector('english', content));

RAISE NOTICE '✓ Full-text search indexes created (3 indexes)';

-- ============================================================================
-- PARTIAL INDEXES (For Specific Query Patterns)
-- ============================================================================

-- Active records only (reduces index size)
CREATE INDEX IF NOT EXISTS idx_users_active
    ON users(id) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_departments_active
    ON departments(id) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_teams_active
    ON teams(id) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_modules_active
    ON modules(id) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_extraction_templates_active_type
    ON extraction_templates(template_type) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_extraction_schedules_active
    ON extraction_job_schedules(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_extraction_schedules_next_run
    ON extraction_job_schedules(next_run_at) WHERE is_active = TRUE;

-- Pending documents (for processing queue)
CREATE INDEX IF NOT EXISTS idx_documents_pending
    ON documents(upload_date DESC) WHERE processing_status = 'pending';

-- Failed jobs (for retry logic)
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_failed
    ON web_scrape_jobs(created_at DESC) WHERE status = 'failed';

CREATE INDEX IF NOT EXISTS idx_extraction_jobs_failed
    ON extraction_jobs(created_at DESC) WHERE status = 'failed';

RAISE NOTICE '✓ Partial indexes created (10 indexes)';

-- ============================================================================
-- COVERING INDEXES (For Index-Only Scans)
-- ============================================================================

-- Include commonly selected columns in index
CREATE INDEX IF NOT EXISTS idx_users_lookup
    ON users(username) INCLUDE (email, full_name, role);

CREATE INDEX IF NOT EXISTS idx_modules_lookup
    ON modules(module_key) INCLUDE (name, icon, is_active);

CREATE INDEX IF NOT EXISTS idx_documents_lookup
    ON documents(id) INCLUDE (filename, file_type, processed, upload_date);

RAISE NOTICE '✓ Covering indexes created (3 indexes)';

-- ============================================================================
-- INDEX MAINTENANCE COMMANDS
-- ============================================================================

-- Analyze tables to update statistics (run after large data loads)
-- ANALYZE users;
-- ANALYZE documents;
-- ANALYZE document_chunks;
-- ANALYZE chat_sessions;
-- ANALYZE modules;
-- ANALYZE roles;

-- Reindex vector indexes periodically (recommended: monthly)
-- REINDEX INDEX CONCURRENTLY idx_document_chunks_embedding;
-- REINDEX INDEX CONCURRENTLY idx_chunks_table_embedding;

-- ============================================================================
-- FINAL VERIFICATION & SUMMARY
-- ============================================================================

DO $$
DECLARE
    total_indexes INTEGER;
    vector_indexes INTEGER;
    gin_indexes INTEGER;
    partial_indexes INTEGER;
BEGIN
    -- Count all indexes
    SELECT COUNT(*)
    INTO total_indexes
    FROM pg_indexes
    WHERE schemaname = 'public';

    -- Count vector indexes
    SELECT COUNT(*)
    INTO vector_indexes
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexdef LIKE '%ivfflat%';

    -- Count GIN indexes
    SELECT COUNT(*)
    INTO gin_indexes
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexdef LIKE '%gin%';

    -- Count partial indexes
    SELECT COUNT(*)
    INTO partial_indexes
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexdef LIKE '%WHERE%';

    -- Report
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'INDEX CREATION COMPLETE';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Total indexes in schema: %', total_indexes;
    RAISE NOTICE '';
    RAISE NOTICE 'Index breakdown:';
    RAISE NOTICE '  Vector (IVFFlat):  % indexes', vector_indexes;
    RAISE NOTICE '  GIN (JSONB/FTS):   % indexes', gin_indexes;
    RAISE NOTICE '  Partial:           % indexes', partial_indexes;
    RAISE NOTICE '  B-Tree:            % indexes', (total_indexes - vector_indexes - gin_indexes);
    RAISE NOTICE '';
    RAISE NOTICE '✓ All performance indexes successfully created';
    RAISE NOTICE '';
    RAISE NOTICE 'Recommendation: Run ANALYZE on all tables';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
END
$$;

-- ============================================================================
-- NOTES
-- ============================================================================
--
-- Performance Tips:
-- 1. Vector indexes (IVFFlat): Tune 'lists' parameter based on table size
--    - Small tables (<100K rows): lists = 100
--    - Medium tables (100K-1M rows): lists = 500
--    - Large tables (>1M rows): lists = 1000+
--
-- 2. Partial indexes: Most efficient for filtering on boolean flags or enums
--
-- 3. Covering indexes: Use INCLUDE for frequently accessed columns to enable
--    index-only scans
--
-- 4. Composite indexes: Order columns by selectivity (most selective first)
--
-- 5. GIN indexes: Efficient for JSONB and array queries but slower to update
--
-- 6. Regular maintenance:
--    - Run VACUUM ANALYZE weekly
--    - REINDEX CONCURRENTLY vector indexes monthly
--    - Monitor index usage with pg_stat_user_indexes
--
-- 7. Unused indexes: Periodically check for unused indexes and drop them
--    SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
--
-- ============================================================================
