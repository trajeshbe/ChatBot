--
-- PostgreSQL database dump
--

\restrict fgkzoRWGjtyMjI6hvbb7QJMscSEiN6V2ncG2Dh5AtBPwZxKxaJxlignZPqPOTge

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg12+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'Export Wizard tables added in migration 026';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: action_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.action_type AS ENUM (
    'login',
    'logout',
    'login_failed',
    'session_create',
    'session_destroy',
    'session_timeout',
    'password_change',
    'password_reset',
    'query',
    'upload',
    'download',
    'scrape',
    'delete',
    'create',
    'update',
    'view',
    'export',
    'module_access',
    'module_exit',
    'feature_usage',
    'user_create',
    'user_update',
    'user_delete',
    'role_assign',
    'role_revoke',
    'permission_grant',
    'permission_deny',
    'settings_change',
    'file_delete',
    'file_move',
    'file_share',
    'project_create',
    'project_update',
    'project_delete',
    'project_archive',
    'api_key_create',
    'api_key_revoke',
    'api_request',
    'error',
    'permission_denied',
    'unauthorized_access',
    'rate_limit_exceeded'
);


--
-- Name: TYPE action_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TYPE public.action_type IS 'Comprehensive audit action types for all user operations';


--
-- Name: actiontype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.actiontype AS ENUM (
    'LOGIN',
    'LOGOUT',
    'LOGIN_FAILED',
    'SESSION_CREATE',
    'SESSION_DESTROY',
    'SESSION_TIMEOUT',
    'PASSWORD_CHANGE',
    'PASSWORD_RESET',
    'QUERY',
    'UPLOAD',
    'DOWNLOAD',
    'SCRAPE',
    'DELETE',
    'CREATE',
    'UPDATE',
    'VIEW',
    'EXPORT',
    'MODULE_ACCESS',
    'MODULE_EXIT',
    'FEATURE_USAGE',
    'USER_CREATE',
    'USER_UPDATE',
    'USER_DELETE',
    'ROLE_ASSIGN',
    'ROLE_REVOKE',
    'PERMISSION_GRANT',
    'PERMISSION_DENY',
    'SETTINGS_CHANGE',
    'FILE_DELETE',
    'FILE_MOVE',
    'FILE_SHARE',
    'PROJECT_CREATE',
    'PROJECT_UPDATE',
    'PROJECT_DELETE',
    'PROJECT_ARCHIVE',
    'API_KEY_CREATE',
    'API_KEY_REVOKE',
    'API_REQUEST',
    'ERROR',
    'PERMISSION_DENIED',
    'UNAUTHORIZED_ACCESS',
    'RATE_LIMIT_EXCEEDED'
);


--
-- Name: deployment_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.deployment_type AS ENUM (
    'docker_compose',
    'docker_compose_ha',
    'kubernetes',
    'aws_cloudformation',
    'aws_terraform',
    'azure_arm',
    'azure_bicep',
    'gcp_deployment_manager',
    'gcp_terraform'
);


--
-- Name: deploymenttype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.deploymenttype AS ENUM (
    'DOCKER_COMPOSE',
    'DOCKER_COMPOSE_HA',
    'KUBERNETES',
    'AWS_CLOUDFORMATION',
    'AWS_TERRAFORM',
    'AZURE_ARM',
    'AZURE_BICEP',
    'GCP_DEPLOYMENT_MANAGER',
    'GCP_TERRAFORM'
);


--
-- Name: export_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.export_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled'
);


--
-- Name: exportstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.exportstatus AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);


--
-- Name: license_tier; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.license_tier AS ENUM (
    'starter',
    'professional',
    'enterprise'
);


--
-- Name: licensetier; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.licensetier AS ENUM (
    'STARTER',
    'PROFESSIONAL',
    'ENTERPRISE'
);


--
-- Name: user_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_role AS ENUM (
    'admin',
    'user',
    'viewer',
    'api_user'
);


--
-- Name: userrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'USER',
    'VIEWER',
    'API_USER'
);


--
-- Name: can_user_access_module(uuid, character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.can_user_access_module(p_user_id uuid, p_module_id character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_module_enabled BOOLEAN;
    v_has_access BOOLEAN := false;
    v_user_override BOOLEAN;
    v_role_permission BOOLEAN;
BEGIN
    -- Check if module is globally enabled
    SELECT is_enabled INTO v_module_enabled
    FROM modules
    WHERE module_id = p_module_id;

    IF v_module_enabled = false THEN
        RETURN false;
    END IF;

    -- Check user-specific override first (highest priority)
    SELECT can_access INTO v_user_override
    FROM user_module_overrides umo
    JOIN modules m ON umo.module_id = m.id
    WHERE umo.user_id = p_user_id
      AND m.module_id = p_module_id
      AND (umo.expires_at IS NULL OR umo.expires_at > NOW());

    IF v_user_override IS NOT NULL THEN
        RETURN v_user_override;
    END IF;

    -- Check role-based permissions
    SELECT COALESCE(bool_or(rmp.can_access), false) INTO v_role_permission
    FROM user_roles ur
    JOIN role_module_permissions rmp ON ur.role_id = rmp.role_id
    JOIN modules m ON rmp.module_id = m.id
    WHERE ur.user_id = p_user_id
      AND m.module_id = p_module_id;

    RETURN COALESCE(v_role_permission, false);
END;
$$;


--
-- Name: FUNCTION can_user_access_module(p_user_id uuid, p_module_id character varying); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.can_user_access_module(p_user_id uuid, p_module_id character varying) IS 'Check if a user can access a specific module considering all permission layers';


--
-- Name: cleanup_evaluation_cache(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.cleanup_evaluation_cache() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    DELETE FROM evaluation_cache
    WHERE created_at < NOW() - INTERVAL '1 hour' * (ttl_seconds / 3600);
END;
$$;


--
-- Name: log_module_usage(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.log_module_usage() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- This can be called from application code via trigger or direct insert
    RETURN NEW;
END;
$$;


--
-- Name: refresh_tool_usage_summary(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.refresh_tool_usage_summary() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY tool_usage_summary;
END;
$$;


--
-- Name: update_agent_tasks_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_agent_tasks_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_api_credentials_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_api_credentials_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_departments_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_departments_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_evaluation_cache_last_accessed(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_evaluation_cache_last_accessed() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.last_accessed = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_evaluation_configs_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_evaluation_configs_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_modules_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_modules_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_permissions_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_permissions_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_roles_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_roles_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_scraping_config_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_scraping_config_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_tasks (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    task_id character varying(255) NOT NULL,
    task_description text NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    session_id character varying(255),
    model character varying(100) DEFAULT 'qwen2.5-coder:7b'::character varying NOT NULL,
    max_iterations integer DEFAULT 20,
    timeout_seconds integer DEFAULT 600,
    current_iteration integer DEFAULT 0,
    current_phase character varying(50),
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    duration_seconds double precision,
    result text,
    artifacts text[],
    tools_used text[],
    llm_calls integer DEFAULT 0,
    error text,
    error_details jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    meta_info jsonb,
    project_id uuid,
    created_by uuid,
    department character varying(100),
    team character varying(100),
    task_name character varying(255),
    minio_base_path text
);


--
-- Name: TABLE agent_tasks; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.agent_tasks IS 'Tracks autonomous agent task execution with LLM integration';


--
-- Name: COLUMN agent_tasks.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.agent_tasks.task_id IS 'Human-readable task identifier (e.g., task-abc123)';


--
-- Name: COLUMN agent_tasks.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.agent_tasks.status IS 'Current task status: pending, running, completed, failed, cancelled';


--
-- Name: COLUMN agent_tasks.current_phase; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.agent_tasks.current_phase IS 'Current agentic loop phase: THINK, PLAN, ACT, OBSERVE';


--
-- Name: COLUMN agent_tasks.artifacts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.agent_tasks.artifacts IS 'Array of file paths to generated artifacts';


--
-- Name: COLUMN agent_tasks.tools_used; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.agent_tasks.tools_used IS 'Array of tool names executed during task';


--
-- Name: COLUMN agent_tasks.llm_calls; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.agent_tasks.llm_calls IS 'Number of LLM calls made during task execution';


--
-- Name: COLUMN agent_tasks.task_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.agent_tasks.task_name IS 'Human-readable task name generated by LLM';


--
-- Name: COLUMN agent_tasks.minio_base_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.agent_tasks.minio_base_path IS 'Base MinIO path for this task execution';


--
-- Name: api_credentials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_credentials (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    provider character varying(50) NOT NULL,
    api_key_encrypted bytea NOT NULL,
    encryption_key_id character varying(100),
    is_active boolean DEFAULT true,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_used_at timestamp with time zone,
    meta_info jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT api_key_encrypted_not_empty CHECK ((length(api_key_encrypted) > 0)),
    CONSTRAINT provider_not_empty CHECK (((provider)::text <> ''::text))
);


--
-- Name: TABLE api_credentials; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.api_credentials IS 'Stores encrypted API keys for LLM providers with audit tracking';


--
-- Name: COLUMN api_credentials.provider; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.api_credentials.provider IS 'Provider identifier (openai, anthropic, huggingface)';


--
-- Name: COLUMN api_credentials.api_key_encrypted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.api_credentials.api_key_encrypted IS 'Fernet-encrypted API key stored as binary data';


--
-- Name: COLUMN api_credentials.encryption_key_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.api_credentials.encryption_key_id IS 'ID of encryption key used for rotation tracking';


--
-- Name: COLUMN api_credentials.last_used_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.api_credentials.last_used_at IS 'Timestamp of last successful API call using this key';


--
-- Name: api_key_access_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_key_access_log (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    provider character varying(50) NOT NULL,
    user_id uuid,
    action character varying(50) NOT NULL,
    ip_address character varying(50),
    user_agent text,
    success boolean DEFAULT true,
    error_message text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT action_valid CHECK (((action)::text = ANY ((ARRAY['created'::character varying, 'updated'::character varying, 'accessed'::character varying, 'deleted'::character varying, 'validated'::character varying, 'failed_validation'::character varying])::text[])))
);


--
-- Name: TABLE api_key_access_log; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.api_key_access_log IS 'Audit log for all API key access and modifications';


--
-- Name: COLUMN api_key_access_log.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.api_key_access_log.action IS 'Type of action performed on the API key';


--
-- Name: COLUMN api_key_access_log.success; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.api_key_access_log.success IS 'Whether the operation succeeded';


--
-- Name: api_keys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_keys (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    key_hash character varying(255) NOT NULL,
    key_prefix character varying(20) NOT NULL,
    name character varying(100) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    last_used timestamp with time zone,
    meta_info jsonb
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    session_id uuid,
    action public.action_type NOT NULL,
    resource_type character varying(50),
    resource_id uuid,
    description text,
    request_data jsonb,
    response_data jsonb,
    ip_address character varying(45),
    user_agent character varying(512),
    status_code integer,
    error_message text,
    latency_ms double precision,
    created_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: TABLE audit_logs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.audit_logs IS 'Comprehensive audit log table tracking all user actions across the platform';


--
-- Name: COLUMN audit_logs.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.action IS 'Type of action performed (see actiontype enum for all 54 types)';


--
-- Name: COLUMN audit_logs.latency_ms; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.latency_ms IS 'Request latency in milliseconds for performance monitoring';


--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_sessions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id character varying(255) NOT NULL,
    user_id uuid,
    title character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_activity timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true NOT NULL,
    meta_info jsonb,
    project_id uuid
);


--
-- Name: TABLE chat_sessions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.chat_sessions IS 'Chat sessions with user tracking';


--
-- Name: COLUMN chat_sessions.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.chat_sessions.project_id IS 'Links chat session to a specific project for scoped conversations';


--
-- Name: config_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config_audit_logs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    module_name character varying(100) NOT NULL,
    action character varying(50) NOT NULL,
    changed_field_path character varying(255),
    old_value jsonb,
    new_value jsonb,
    changed_by uuid,
    changed_at timestamp without time zone DEFAULT now(),
    ip_address inet,
    user_agent text,
    change_reason text,
    metadata jsonb
);


--
-- Name: TABLE config_audit_logs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.config_audit_logs IS 'Detailed audit trail for all configuration changes';


--
-- Name: config_schemas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config_schemas (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    schema_name character varying(100) NOT NULL,
    schema_version character varying(20) DEFAULT '1.0'::character varying NOT NULL,
    module_type character varying(50),
    schema jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    is_active boolean DEFAULT true
);


--
-- Name: TABLE config_schemas; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.config_schemas IS 'JSON schemas for validating module configurations';


--
-- Name: config_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config_templates (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    template_name character varying(100) NOT NULL,
    display_name character varying(255) NOT NULL,
    description text,
    template jsonb NOT NULL,
    category character varying(100),
    tags text[],
    module_type character varying(50),
    created_at timestamp without time zone DEFAULT now(),
    created_by uuid,
    is_public boolean DEFAULT true,
    usage_count integer DEFAULT 0
);


--
-- Name: TABLE config_templates; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.config_templates IS 'Reusable configuration templates for quick module setup';


--
-- Name: config_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config_versions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    module_name character varying(100) NOT NULL,
    version integer NOT NULL,
    config jsonb NOT NULL,
    changed_by uuid,
    changed_at timestamp without time zone DEFAULT now(),
    change_description text,
    diff jsonb
);


--
-- Name: TABLE config_versions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.config_versions IS 'Version history for configuration changes (audit trail)';


--
-- Name: conversation_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_messages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id uuid NOT NULL,
    role character varying(50) NOT NULL,
    content text NOT NULL,
    model_id character varying(100),
    model_name character varying(255),
    prompt_tokens integer,
    completion_tokens integer,
    total_tokens integer,
    latency_ms double precision,
    cost_usd double precision,
    sources jsonb,
    created_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: TABLE conversation_messages; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.conversation_messages IS 'Messages within chat sessions';


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    title character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    parent_department_id uuid,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: TABLE departments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.departments IS 'Organizational departments and teams';


--
-- Name: deployment_instances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_instances (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    instance_name character varying(255) NOT NULL,
    export_package_id uuid NOT NULL,
    deployment_type public.deployment_type NOT NULL,
    deployment_url character varying(512),
    environment character varying(50),
    cloud_provider character varying(50),
    region character varying(100),
    cluster_info jsonb,
    status character varying(50) DEFAULT 'unknown'::character varying NOT NULL,
    last_health_check timestamp without time zone,
    health_data jsonb,
    telemetry_enabled boolean DEFAULT false NOT NULL,
    telemetry_data jsonb,
    deployed_at timestamp without time zone DEFAULT now() NOT NULL,
    last_updated_at timestamp without time zone,
    decommissioned_at timestamp without time zone,
    contact_email character varying(255),
    contact_name character varying(255)
);


--
-- Name: TABLE deployment_instances; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.deployment_instances IS 'Tracks deployed instances and their health status';


--
-- Name: COLUMN deployment_instances.health_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.deployment_instances.health_data IS 'Health check data: API, database, vector DB status, uptime, version';


--
-- Name: COLUMN deployment_instances.telemetry_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.deployment_instances.telemetry_data IS 'Usage telemetry: queries, users, response times, error rates';


--
-- Name: document_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_chunks (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    document_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    meta_info jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    embedding public.vector(384),
    project_id uuid,
    uploaded_by uuid,
    department character varying(100),
    team character varying(100),
    table_embedding public.vector(512),
    visual_embedding public.vector(512),
    numerical_embedding public.vector(256),
    code_embedding public.vector(768),
    embedding_strategy character varying(50),
    embedding_metadata jsonb,
    CONSTRAINT check_embedding_strategy CHECK (((embedding_strategy IS NULL) OR ((embedding_strategy)::text = ANY ((ARRAY['text_semantic'::character varying, 'table_structure'::character varying, 'vision'::character varying, 'numerical'::character varying, 'code'::character varying, 'hybrid'::character varying])::text[]))))
);


--
-- Name: COLUMN document_chunks.embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.document_chunks.embedding IS 'Primary vector embedding (384 dimensions) using sentence-transformers/all-MiniLM-L6-v2 for text semantic search';


--
-- Name: COLUMN document_chunks.table_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.document_chunks.table_embedding IS 'Table structure embedding (512 dimensions) for table-heavy documents, captures structural and numerical patterns';


--
-- Name: COLUMN document_chunks.visual_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.document_chunks.visual_embedding IS 'Vision embedding (512 dimensions) using CLIP for images, diagrams, and charts';


--
-- Name: COLUMN document_chunks.numerical_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.document_chunks.numerical_embedding IS 'Numerical embedding (256 dimensions) for statistical data in Excel/CSV files';


--
-- Name: COLUMN document_chunks.code_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.document_chunks.code_embedding IS 'Code embedding (768 dimensions) using CodeBERT for programming code semantic search';


--
-- Name: COLUMN document_chunks.embedding_strategy; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.document_chunks.embedding_strategy IS 'Embedding strategy used: text_semantic, table_structure, vision, numerical, code, or hybrid';


--
-- Name: COLUMN document_chunks.embedding_metadata; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.document_chunks.embedding_metadata IS 'Metadata from ContentAnalyzer: content_type, confidence, reasoning, analysis results';


--
-- Name: document_extractions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_extractions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    session_id character varying(255),
    project_id uuid,
    user_id uuid,
    module_id character varying(100) DEFAULT 'docu-extract'::character varying,
    extraction_mode character varying(50) DEFAULT 'auto'::character varying,
    model_used character varying(100),
    status character varying(50) DEFAULT 'processing'::character varying,
    fields_extracted integer,
    total_fields integer DEFAULT 18,
    extraction_confidence double precision,
    processing_time_ms integer,
    error_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    CONSTRAINT document_extractions_extraction_mode_check CHECK (((extraction_mode)::text = ANY ((ARRAY['auto'::character varying, 'text'::character varying, 'vision'::character varying, 'hybrid'::character varying])::text[]))),
    CONSTRAINT document_extractions_status_check CHECK (((status)::text = ANY ((ARRAY['processing'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])))
);


--
-- Name: document_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_permissions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    document_id uuid NOT NULL,
    user_id uuid,
    role public.user_role,
    can_read boolean DEFAULT true,
    can_write boolean DEFAULT false,
    can_delete boolean DEFAULT false,
    can_share boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone,
    meta_info jsonb
);


--
-- Name: TABLE document_permissions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.document_permissions IS 'Fine-grained document access control';


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    filename character varying(255) NOT NULL,
    file_path text NOT NULL,
    file_type character varying(255),
    file_size bigint,
    source_type character varying(50) NOT NULL,
    source_url text,
    processing_status character varying(50) DEFAULT 'pending'::character varying,
    error_message text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    project_id uuid,
    department character varying(255),
    team character varying(255),
    uploaded_by uuid,
    user_role character varying(50),
    minio_path character varying(1024)
);


--
-- Name: COLUMN documents.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.documents.project_id IS 'Link to project/module for organization';


--
-- Name: COLUMN documents.department; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.documents.department IS 'Department name for organizational filtering';


--
-- Name: COLUMN documents.team; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.documents.team IS 'Team name for organizational filtering';


--
-- Name: COLUMN documents.uploaded_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.documents.uploaded_by IS 'User who uploaded/scraped the document';


--
-- Name: COLUMN documents.user_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.documents.user_role IS 'Role of uploader at upload time';


--
-- Name: COLUMN documents.minio_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.documents.minio_path IS 'Full hierarchical path: documents/{dept}/{team}/{project}/{user}/documents/{file}';


--
-- Name: domain_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.domain_statistics (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    domain character varying(255) NOT NULL,
    total_requests integer DEFAULT 0,
    successful_requests integer DEFAULT 0,
    failed_requests integer DEFAULT 0,
    blocked_requests integer DEFAULT 0,
    total_bytes_downloaded bigint DEFAULT 0,
    avg_response_time_ms double precision,
    rate_limit_violations integer DEFAULT 0,
    robots_txt_violations integer DEFAULT 0,
    first_scraped_at timestamp with time zone,
    last_scraped_at timestamp with time zone,
    last_updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: evaluation_benchmarks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluation_benchmarks (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    query text NOT NULL,
    ground_truth_answer text NOT NULL,
    context_chunks jsonb NOT NULL,
    expected_scores jsonb,
    dataset_name character varying(100),
    difficulty character varying(50),
    category character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: TABLE evaluation_benchmarks; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.evaluation_benchmarks IS 'Benchmark datasets for evaluation metrics validation';


--
-- Name: evaluation_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluation_cache (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    cache_key character varying(255) NOT NULL,
    result jsonb NOT NULL,
    ttl_seconds integer DEFAULT 3600,
    hit_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    last_accessed timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE evaluation_cache; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.evaluation_cache IS 'Cache for evaluation results to improve performance';


--
-- Name: evaluation_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluation_configs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    session_id uuid,
    enable_ragas boolean DEFAULT false,
    enable_llm_as_judge boolean DEFAULT false,
    enable_deepeval boolean DEFAULT false,
    enable_semantic_similarity boolean DEFAULT false,
    enable_bertscore boolean DEFAULT false,
    enable_citation_accuracy boolean DEFAULT true,
    enable_toxicity boolean DEFAULT true,
    enable_bias_detection boolean DEFAULT true,
    enable_hallucination boolean DEFAULT true,
    enable_answer_relevancy boolean DEFAULT true,
    enable_context_precision boolean DEFAULT false,
    enable_context_recall boolean DEFAULT false,
    enable_faithfulness boolean DEFAULT true,
    llm_judge_model character varying(100) DEFAULT 'gpt-4-turbo-preview'::character varying,
    use_cache boolean DEFAULT true,
    async_evaluation boolean DEFAULT true,
    batch_size integer DEFAULT 10,
    min_score_threshold double precision DEFAULT 0.7,
    cache_ttl_seconds integer DEFAULT 3600,
    auto_evaluate boolean DEFAULT false,
    evaluation_sampling_rate double precision DEFAULT 1.0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: TABLE evaluation_configs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.evaluation_configs IS 'User-specific evaluation configuration with toggleable metrics';


--
-- Name: evaluation_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluation_results (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id uuid,
    message_id uuid,
    user_id uuid,
    query text NOT NULL,
    response text NOT NULL,
    num_contexts integer,
    scores jsonb NOT NULL,
    overall_score double precision,
    evaluation_time_ms double precision,
    enabled_methods jsonb,
    meta_info jsonb,
    errors jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE evaluation_results; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.evaluation_results IS 'Stores comprehensive evaluation results for RAG responses';


--
-- Name: export_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.export_audit_logs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    event_type character varying(100) NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    export_job_id uuid,
    export_package_id uuid,
    deployment_instance_id uuid,
    user_id character varying(255),
    user_email character varying(255),
    ip_address character varying(45),
    details jsonb,
    status character varying(50) NOT NULL,
    error_message text
);


--
-- Name: TABLE export_audit_logs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.export_audit_logs IS 'Audit trail for all export wizard operations';


--
-- Name: export_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.export_jobs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    job_name character varying(255) NOT NULL,
    tenant_id character varying(255) NOT NULL,
    module_name character varying(255) NOT NULL,
    created_by character varying(255),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    deployment_type public.deployment_type NOT NULL,
    license_tier public.license_tier DEFAULT 'professional'::public.license_tier NOT NULL,
    customer_name character varying(255) NOT NULL,
    customer_email character varying(255),
    license_expiry timestamp without time zone,
    max_users integer,
    options jsonb DEFAULT '{}'::jsonb NOT NULL,
    status public.export_status DEFAULT 'pending'::public.export_status NOT NULL,
    progress_percentage double precision DEFAULT 0.0 NOT NULL,
    current_step character varying(255),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    export_package_id uuid,
    package_path text,
    package_size_bytes bigint,
    stats jsonb,
    error_message text,
    error_details jsonb,
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: TABLE export_jobs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.export_jobs IS 'Tracks POC export jobs from initiation to completion';


--
-- Name: COLUMN export_jobs.options; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.export_jobs.options IS 'Export options: embeddings, monitoring, backups, branding, security level, telemetry';


--
-- Name: COLUMN export_jobs.stats; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.export_jobs.stats IS 'Export statistics: documents exported, embeddings, chunks, config items, processing time';


--
-- Name: export_packages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.export_packages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    package_name character varying(255) NOT NULL,
    version character varying(50) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    tenant_id character varying(255) NOT NULL,
    module_name character varying(255) NOT NULL,
    export_job_id uuid NOT NULL,
    deployment_type public.deployment_type NOT NULL,
    package_path text NOT NULL,
    package_size_bytes bigint NOT NULL,
    checksum_sha256 character varying(64) NOT NULL,
    manifest jsonb NOT NULL,
    license_key text NOT NULL,
    license_tier public.license_tier NOT NULL,
    license_issued_at timestamp without time zone DEFAULT now(),
    license_expires_at timestamp without time zone,
    customer_name character varying(255) NOT NULL,
    customer_email character varying(255),
    max_users integer,
    download_count integer DEFAULT 0 NOT NULL,
    last_downloaded_at timestamp without time zone,
    deployed boolean DEFAULT false NOT NULL,
    deployment_url character varying(512),
    deployed_at timestamp without time zone,
    notes text,
    tags jsonb
);


--
-- Name: TABLE export_packages; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.export_packages IS 'Metadata for exported packages ready for customer deployment';


--
-- Name: COLUMN export_packages.manifest; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.export_packages.manifest IS 'Complete manifest of package contents: documents, embeddings, config, infrastructure, images, scripts';


--
-- Name: COLUMN export_packages.license_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.export_packages.license_key IS 'RSA-4096 digitally signed license key';


--
-- Name: export_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.export_templates (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    description text,
    category character varying(100),
    deployment_type public.deployment_type NOT NULL,
    license_tier public.license_tier NOT NULL,
    default_options jsonb DEFAULT '{}'::jsonb NOT NULL,
    infrastructure_config jsonb DEFAULT '{}'::jsonb NOT NULL,
    usage_count integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_by character varying(255),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: TABLE export_templates; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.export_templates IS 'Predefined templates for common export configurations';


--
-- Name: extraction_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.extraction_results (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    extraction_id uuid NOT NULL,
    project_name text,
    address text,
    project_status character varying(50),
    storeys integer,
    gross_floor_area double precision,
    site_area double precision,
    zoning character varying(100),
    heritage_designation text,
    architect character varying(255),
    developer character varying(255),
    planning_consultant character varying(255),
    residential_units integer,
    unit_types jsonb,
    commercial_uses jsonb,
    amenities jsonb,
    parking_levels integer,
    parking_spaces integer,
    public_realm_features jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: finetuned_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.finetuned_models (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    version character varying(50),
    description text,
    job_id uuid,
    base_model character varying(255) NOT NULL,
    finetuning_method character varying(50),
    mlflow_model_uri character varying(512),
    mlflow_run_id character varying(255),
    minio_checkpoint_path character varying(512),
    adapter_config json,
    eval_metrics json,
    status character varying(50),
    deployment_url character varying(512),
    ollama_model_name character varying(255),
    vllm_model_name character varying(255),
    total_inferences integer,
    avg_latency_ms double precision,
    last_inference_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    parent_model_id uuid,
    deprecated_at timestamp with time zone,
    deprecated_by uuid,
    deprecation_reason text,
    project_id uuid,
    tags json,
    merged_model_path text,
    merge_duration_seconds integer,
    merge_requested_at timestamp with time zone,
    merge_error_message text
);


--
-- Name: COLUMN finetuned_models.merged_model_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuned_models.merged_model_path IS 'Path to merged model in MinIO or workspace (/workspace/finetuning/{job_id}/output/merged_model)';


--
-- Name: COLUMN finetuned_models.merge_duration_seconds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuned_models.merge_duration_seconds IS 'Duration of merge operation in seconds (typically 300-900 for 1.5B models)';


--
-- Name: COLUMN finetuned_models.merge_requested_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuned_models.merge_requested_at IS 'Timestamp when merge was requested by user';


--
-- Name: COLUMN finetuned_models.merge_error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuned_models.merge_error_message IS 'Error message if merge failed';


--
-- Name: finetuning_datasets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.finetuning_datasets (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    uploaded_by uuid,
    uploaded_at timestamp with time zone DEFAULT now(),
    filename character varying(255) NOT NULL,
    file_size bigint,
    file_type character varying(50),
    minio_path character varying(512),
    num_samples integer,
    num_train_samples integer,
    num_val_samples integer,
    format_type character varying(100),
    columns json,
    is_valid boolean,
    validation_errors json,
    sample_rows json,
    preprocessing_status character varying(50),
    preprocessed_path character varying(512),
    project_id uuid
);


--
-- Name: finetuning_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.finetuning_jobs (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    base_model character varying(255) NOT NULL,
    quantization character varying(50),
    finetuning_method character varying(50) NOT NULL,
    training_objective character varying(100) NOT NULL,
    dataset_id uuid,
    train_split double precision,
    hyperparameters json,
    status character varying(50),
    progress double precision,
    current_epoch integer,
    current_step integer,
    total_steps integer,
    train_loss double precision,
    eval_loss double precision,
    final_model_name character varying(255),
    mlflow_run_id character varying(255),
    minio_checkpoint_path character varying(512),
    logs text,
    error_message text,
    gpu_type character varying(100),
    gpu_count integer,
    training_time_seconds integer,
    training_start_time timestamp with time zone,
    training_end_time timestamp with time zone,
    project_id uuid,
    department character varying(255),
    team character varying(255),
    celery_task_id character varying(255),
    queued_at timestamp with time zone,
    learning_rate double precision,
    training_stage character varying(50) DEFAULT 'queued'::character varying,
    stage_details jsonb DEFAULT '{}'::jsonb,
    stage_started_at timestamp with time zone,
    stage_completed_at timestamp with time zone,
    debug_log text[] DEFAULT ARRAY[]::text[],
    eval_metrics jsonb DEFAULT '{}'::jsonb,
    custom_metrics jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT check_valid_training_stage CHECK (((training_stage)::text = ANY ((ARRAY['queued'::character varying, 'setup'::character varying, 'tokenizer_load'::character varying, 'model_download'::character varying, 'model_load'::character varying, 'dataset_prep'::character varying, 'training'::character varying, 'checkpoint_save'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])))
);


--
-- Name: COLUMN finetuning_jobs.training_stage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuning_jobs.training_stage IS 'Current stage in the training pipeline (queued, setup, tokenizer_load, model_download, model_load, dataset_prep, training, checkpoint_save, completed, failed)';


--
-- Name: COLUMN finetuning_jobs.stage_details; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuning_jobs.stage_details IS 'Stage-specific metadata (e.g., download progress, current file, substep info)';


--
-- Name: COLUMN finetuning_jobs.stage_started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuning_jobs.stage_started_at IS 'Timestamp when current stage started';


--
-- Name: COLUMN finetuning_jobs.stage_completed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuning_jobs.stage_completed_at IS 'Timestamp when current stage completed';


--
-- Name: COLUMN finetuning_jobs.debug_log; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.finetuning_jobs.debug_log IS 'Array of timestamped debug messages for troubleshooting training pipeline issues';


--
-- Name: human_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.human_feedback (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id uuid,
    message_id uuid,
    evaluation_id uuid,
    user_id uuid,
    rating integer,
    thumbs_up boolean,
    feedback_text text,
    accuracy_rating integer,
    helpfulness_rating integer,
    clarity_rating integer,
    has_hallucination boolean DEFAULT false,
    has_bias boolean DEFAULT false,
    has_toxicity boolean DEFAULT false,
    is_irrelevant boolean DEFAULT false,
    feedback_type character varying(50),
    ip_address character varying(45),
    user_agent character varying(512),
    created_at timestamp with time zone DEFAULT now(),
    meta_info jsonb,
    CONSTRAINT human_feedback_accuracy_rating_check CHECK (((accuracy_rating >= 1) AND (accuracy_rating <= 5))),
    CONSTRAINT human_feedback_clarity_rating_check CHECK (((clarity_rating >= 1) AND (clarity_rating <= 5))),
    CONSTRAINT human_feedback_helpfulness_rating_check CHECK (((helpfulness_rating >= 1) AND (helpfulness_rating <= 5))),
    CONSTRAINT human_feedback_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


--
-- Name: TABLE human_feedback; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.human_feedback IS 'Human feedback on RAG responses for continuous improvement';


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    conversation_id uuid NOT NULL,
    role character varying(50) NOT NULL,
    content text NOT NULL,
    model character varying(100),
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: model_approvals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_approvals (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    model_id uuid NOT NULL,
    requested_by uuid,
    requested_at timestamp with time zone DEFAULT now(),
    request_reason text,
    approved_by uuid,
    reviewed_at timestamp with time zone,
    status character varying(50) DEFAULT 'pending'::character varying,
    review_comments text,
    deployment_environment character varying(100),
    max_concurrent_instances integer,
    resource_limits jsonb,
    CONSTRAINT check_approval_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[])))
);


--
-- Name: TABLE model_approvals; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.model_approvals IS 'Approval workflow for deploying fine-tuned models to production';


--
-- Name: COLUMN model_approvals.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.model_approvals.status IS 'Approval status: pending, approved, rejected';


--
-- Name: COLUMN model_approvals.deployment_environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.model_approvals.deployment_environment IS 'Target environment: production, staging, development';


--
-- Name: COLUMN model_approvals.resource_limits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.model_approvals.resource_limits IS 'JSON constraints: {"max_memory_gb": 16, "max_gpu_count": 1}';


--
-- Name: module_activations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.module_activations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    module_id character varying(100) NOT NULL,
    project_id uuid,
    user_id uuid,
    enabled boolean DEFAULT true,
    activated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    activated_by uuid,
    deactivated_at timestamp without time zone,
    deactivated_by uuid
);


--
-- Name: module_configurations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.module_configurations (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    module_name character varying(100) NOT NULL,
    display_name character varying(255) NOT NULL,
    description text,
    module_type character varying(50) NOT NULL,
    category character varying(100),
    config jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by uuid,
    is_active boolean DEFAULT true,
    current_version integer DEFAULT 1
);


--
-- Name: TABLE module_configurations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.module_configurations IS 'Base configuration for each Tier 2/3 module';


--
-- Name: COLUMN module_configurations.config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.module_configurations.config IS 'JSONB containing llm, prompts, parameters, thresholds, scoring, features';


--
-- Name: module_usage_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.module_usage_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    module_id uuid NOT NULL,
    user_id uuid,
    session_id character varying(255),
    action character varying(50) NOT NULL,
    request_data jsonb,
    response_data jsonb,
    success boolean DEFAULT true,
    error_message text,
    latency_ms integer,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE module_usage_logs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.module_usage_logs IS 'Audit trail of all module usage for analytics and compliance';


--
-- Name: module_user_overrides; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.module_user_overrides (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    module_name character varying(100) NOT NULL,
    overrides jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    variant_name character varying(100),
    experiment_id uuid
);


--
-- Name: TABLE module_user_overrides; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.module_user_overrides IS 'Per-user/customer configuration overrides for A/B testing and personalization';


--
-- Name: modules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.modules (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    module_key character varying(100) NOT NULL,
    module_name character varying(255) NOT NULL,
    description text,
    icon character varying(50),
    is_active boolean DEFAULT true NOT NULL,
    display_order integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    meta_info jsonb,
    module_type character varying(20),
    tier integer,
    category character varying(100),
    tier_2_dependencies text[],
    is_enabled boolean DEFAULT true,
    is_beta boolean DEFAULT false,
    requires_special_permission boolean DEFAULT false,
    created_by uuid,
    updated_by uuid
);


--
-- Name: TABLE modules; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.modules IS 'Master registry of all Tier 2 and Tier 3 modules with enable/disable flags';


--
-- Name: output_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.output_templates (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    template_type character varying(50) NOT NULL,
    template_config jsonb NOT NULL,
    template_file_path character varying(512),
    created_by uuid,
    project_id uuid,
    department_id uuid,
    is_public boolean DEFAULT false,
    usage_count integer DEFAULT 0,
    last_used_at timestamp with time zone,
    meta_info jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE output_templates; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.output_templates IS 'Reusable output format templates for structured exports';


--
-- Name: project_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_members (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    project_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role character varying(50) DEFAULT 'member'::character varying,
    joined_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    owner_id uuid,
    department character varying(100),
    status character varying(50) DEFAULT 'active'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    archived_at timestamp with time zone,
    meta_info jsonb,
    preferred_model character varying(100),
    model_config jsonb DEFAULT '{}'::jsonb,
    department_id uuid,
    team_id uuid
);


--
-- Name: COLUMN projects.preferred_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.projects.preferred_model IS 'Preferred LLM model for this project (e.g., gpt-4-turbo-preview, claude-3-5-sonnet)';


--
-- Name: COLUMN projects.model_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.projects.model_config IS 'Additional model configuration (temperature, max_tokens, etc.)';


--
-- Name: COLUMN projects.department_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.projects.department_id IS 'Foreign key to departments table for organizational hierarchy';


--
-- Name: COLUMN projects.team_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.projects.team_id IS 'Foreign key to teams table for organizational hierarchy';


--
-- Name: prompt_library; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prompt_library (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    prompt_text text NOT NULL,
    prompt_type character varying(100) NOT NULL,
    category character varying(100),
    module character varying(100),
    tags jsonb DEFAULT '[]'::jsonb,
    expected_output_format character varying(50) DEFAULT 'text'::character varying,
    output_schema jsonb,
    example_input text,
    example_output text,
    created_by uuid,
    project_id uuid,
    department_id uuid,
    is_public boolean DEFAULT false,
    is_verified boolean DEFAULT false,
    usage_count integer DEFAULT 0,
    average_rating double precision DEFAULT 0.0,
    total_ratings integer DEFAULT 0,
    last_used_at timestamp with time zone,
    version integer DEFAULT 1,
    parent_prompt_id uuid,
    meta_info jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE prompt_library; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.prompt_library IS 'State-of-the-art prompt library for reusable prompts across users and projects';


--
-- Name: prompt_ratings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prompt_ratings (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    prompt_id uuid,
    user_id uuid,
    rating integer NOT NULL,
    feedback text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT prompt_ratings_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


--
-- Name: TABLE prompt_ratings; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.prompt_ratings IS 'User ratings and feedback for prompts to track quality';


--
-- Name: prompt_usage_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prompt_usage_log (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    prompt_id uuid,
    user_id uuid,
    session_id uuid,
    actual_prompt_used text,
    input_provided text,
    output_generated text,
    execution_time_ms double precision,
    token_count integer,
    was_successful boolean DEFAULT true,
    error_message text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE prompt_usage_log; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.prompt_usage_log IS 'Analytics log for prompt usage patterns and performance';


--
-- Name: query_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.query_cache (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    query_text text NOT NULL,
    response jsonb NOT NULL,
    model_id character varying(100),
    hit_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    last_accessed timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    query_embedding public.vector(384),
    sources jsonb DEFAULT '[]'::jsonb,
    ttl_seconds integer DEFAULT 3600,
    project_id uuid
);


--
-- Name: COLUMN query_cache.last_accessed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_cache.last_accessed IS 'Timestamp when this cache entry was last accessed';


--
-- Name: COLUMN query_cache.query_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_cache.query_embedding IS 'Vector embedding (384 dimensions) using sentence-transformers/all-MiniLM-L6-v2';


--
-- Name: COLUMN query_cache.sources; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_cache.sources IS 'Source documents used to generate the cached response';


--
-- Name: COLUMN query_cache.ttl_seconds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_cache.ttl_seconds IS 'Time-to-live in seconds for this cache entry';


--
-- Name: role_module_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_module_permissions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    role_id uuid NOT NULL,
    module_id uuid NOT NULL,
    can_read boolean DEFAULT false,
    can_write boolean DEFAULT false,
    can_delete boolean DEFAULT false,
    can_share boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE role_module_permissions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.role_module_permissions IS 'RBAC permissions mapping roles to modules';


--
-- Name: COLUMN role_module_permissions.can_read; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.role_module_permissions.can_read IS 'Permission to view/read';


--
-- Name: COLUMN role_module_permissions.can_write; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.role_module_permissions.can_write IS 'Permission to create/edit';


--
-- Name: COLUMN role_module_permissions.can_delete; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.role_module_permissions.can_delete IS 'Permission to delete';


--
-- Name: COLUMN role_module_permissions.can_share; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.role_module_permissions.can_share IS 'Permission to share with others';


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permissions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    role character varying(50) NOT NULL,
    module_id uuid NOT NULL,
    can_access boolean DEFAULT true NOT NULL,
    can_create boolean DEFAULT false,
    can_edit boolean DEFAULT false,
    can_delete boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    parent_role_id uuid,
    description text,
    is_system_role boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE roles; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.roles IS 'User roles for RBAC system';


--
-- Name: COLUMN roles.is_system_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.roles.is_system_role IS 'System roles cannot be deleted';


--
-- Name: saved_css_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saved_css_templates (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    description text,
    url_pattern character varying(512),
    wait_for_selector character varying(512),
    fields jsonb NOT NULL,
    pagination_selector character varying(512),
    max_pages integer DEFAULT 1,
    use_count integer DEFAULT 0,
    last_used_at timestamp with time zone,
    created_by character varying(255),
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE saved_css_templates; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.saved_css_templates IS 'User-created CSS selector templates that can be saved from successful extractions';


--
-- Name: COLUMN saved_css_templates.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.saved_css_templates.name IS 'Unique internal identifier (lowercase_with_underscores)';


--
-- Name: COLUMN saved_css_templates.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.saved_css_templates.display_name IS 'User-friendly name shown in dropdown';


--
-- Name: COLUMN saved_css_templates.url_pattern; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.saved_css_templates.url_pattern IS 'Optional URL pattern for auto-suggesting templates (e.g., "example.com/*")';


--
-- Name: COLUMN saved_css_templates.fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.saved_css_templates.fields IS 'Array of extraction fields with CSS selectors, data types, and requirements';


--
-- Name: scraping_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scraping_audit_log (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    config_id uuid,
    domain character varying(255) NOT NULL,
    url character varying(1024) NOT NULL,
    method character varying(50),
    user_agent character varying(512),
    status_code integer,
    success boolean DEFAULT false,
    error_message text,
    response_time_ms double precision,
    bytes_downloaded integer,
    robots_txt_allowed boolean,
    rate_limit_respected boolean,
    permission_verified boolean,
    user_id uuid,
    session_id character varying(255),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: scraping_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scraping_configs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    domain character varying(255) NOT NULL,
    allow_scraping boolean DEFAULT false,
    robots_txt_compliant boolean DEFAULT true,
    robots_txt_url character varying(512),
    robots_txt_checked_at timestamp with time zone,
    rate_limit_enabled boolean DEFAULT true,
    rate_limit_requests_per_minute integer DEFAULT 10,
    rate_limit_delay_seconds double precision DEFAULT 2.0,
    max_concurrent_requests integer DEFAULT 1,
    use_api boolean DEFAULT false,
    api_endpoint character varying(512),
    api_key_encrypted text,
    api_documentation_url character varying(512),
    terms_checked boolean DEFAULT false,
    terms_url character varying(512),
    terms_checked_at timestamp with time zone,
    terms_notes text,
    permission_granted boolean DEFAULT false,
    permission_contact character varying(255),
    permission_granted_at timestamp with time zone,
    permission_expires_at timestamp with time zone,
    permission_document_url character varying(512),
    preferred_method character varying(50) DEFAULT 'auto'::character varying,
    user_agent character varying(512),
    custom_headers jsonb,
    notes text,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_scraped_at timestamp with time zone,
    status character varying(50) DEFAULT 'active'::character varying,
    block_reason text
);


--
-- Name: session_contexts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_contexts (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id uuid NOT NULL,
    preferred_model character varying(100),
    context_window_size integer DEFAULT 10,
    temperature double precision DEFAULT 0.7,
    max_tokens integer DEFAULT 1024,
    active_document_ids jsonb,
    conversation_summary text,
    conversation_embedding public.vector(384),
    tags jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: TABLE session_contexts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.session_contexts IS 'Session-specific context and preferences (short-term memory)';


--
-- Name: session_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_documents (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    document_id uuid NOT NULL,
    added_at timestamp with time zone DEFAULT now(),
    priority integer DEFAULT 0,
    expires_at timestamp with time zone,
    meta_info jsonb,
    session_id character varying(255) NOT NULL
);


--
-- Name: TABLE session_documents; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.session_documents IS 'Short-term memory: documents associated with active sessions';


--
-- Name: skill_modules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill_modules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    module_id character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    version character varying(50) NOT NULL,
    tier integer NOT NULL,
    category character varying(100),
    status character varying(50) DEFAULT 'disabled'::character varying,
    routes_prefix character varying(255),
    dependencies jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT skill_modules_status_check CHECK (((status)::text = ANY ((ARRAY['enabled'::character varying, 'disabled'::character varying, 'error'::character varying])::text[]))),
    CONSTRAINT skill_modules_tier_check CHECK ((tier = ANY (ARRAY[2, 3])))
);


--
-- Name: teams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teams (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    department_id uuid NOT NULL,
    team_lead_id uuid,
    description text,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: tool_usage_stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tool_usage_stats (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    tool_category character varying(50) NOT NULL,
    tool_name character varying(100) NOT NULL,
    tool_version character varying(50),
    session_id character varying(255),
    user_id uuid,
    operation character varying(100),
    input_size integer,
    output_size integer,
    latency_ms double precision NOT NULL,
    success boolean DEFAULT true NOT NULL,
    error_message text,
    tokens_used integer,
    cost_usd numeric(10,6),
    quality_score double precision,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE tool_usage_stats; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.tool_usage_stats IS 'Records every tool/service invocation with performance and quality metrics';


--
-- Name: COLUMN tool_usage_stats.tool_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tool_usage_stats.tool_category IS 'High-level category: document_processing, web_scraping, rag_service, llm_service, mcp_tool';


--
-- Name: COLUMN tool_usage_stats.tool_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tool_usage_stats.tool_name IS 'Specific tool name: docling, playwright, cross_encoder_reranker, gpt-4, etc.';


--
-- Name: COLUMN tool_usage_stats.operation; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tool_usage_stats.operation IS 'Specific operation performed: parse_pdf, scrape_url, rerank_chunks, etc.';


--
-- Name: COLUMN tool_usage_stats.cost_usd; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.tool_usage_stats.cost_usd IS 'Estimated cost in USD for paid API calls (OpenAI, Anthropic, etc.)';


--
-- Name: tool_usage_summary; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.tool_usage_summary AS
 SELECT tool_category,
    tool_name,
    count(*) AS total_invocations,
    count(*) FILTER (WHERE (success = true)) AS successful_invocations,
    count(*) FILTER (WHERE (success = false)) AS failed_invocations,
    avg(latency_ms) AS avg_latency_ms,
    percentile_cont((0.5)::double precision) WITHIN GROUP (ORDER BY latency_ms) AS median_latency_ms,
    percentile_cont((0.95)::double precision) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency_ms,
    min(latency_ms) AS min_latency_ms,
    max(latency_ms) AS max_latency_ms,
    sum(tokens_used) AS total_tokens_used,
    sum(cost_usd) AS total_cost_usd,
    avg(quality_score) AS avg_quality_score,
    min(created_at) AS first_used,
    max(created_at) AS last_used,
    round(((100.0 * (count(*) FILTER (WHERE (success = true)))::numeric) / (NULLIF(count(*), 0))::numeric), 2) AS success_rate_pct
   FROM public.tool_usage_stats
  GROUP BY tool_category, tool_name
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW tool_usage_summary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON MATERIALIZED VIEW public.tool_usage_summary IS 'Aggregated tool usage statistics for quick dashboard queries';


--
-- Name: training_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_metrics (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    epoch integer,
    step integer,
    train_loss double precision,
    eval_loss double precision,
    gradient_norm double precision,
    learning_rate double precision,
    gpu_utilization double precision,
    gpu_memory_allocated bigint,
    gpu_memory_reserved bigint,
    gpu_temperature double precision,
    samples_per_second double precision,
    tokens_per_second double precision,
    batch_processing_time_ms double precision,
    custom_metrics json
);


--
-- Name: usage_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usage_metrics (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    date timestamp with time zone NOT NULL,
    model_id character varying(100),
    total_queries integer DEFAULT 0,
    total_tokens integer DEFAULT 0,
    total_cost_usd double precision DEFAULT 0.0,
    avg_latency_ms double precision DEFAULT 0.0,
    documents_uploaded integer DEFAULT 0,
    pages_scraped integer DEFAULT 0,
    cache_hits integer DEFAULT 0,
    cache_misses integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    meta_info jsonb
);


--
-- Name: TABLE usage_metrics; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.usage_metrics IS 'Aggregated usage metrics for analytics';


--
-- Name: user_module_overrides; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_module_overrides (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    module_id uuid NOT NULL,
    can_access boolean DEFAULT true,
    can_execute boolean DEFAULT true,
    can_view_results boolean DEFAULT true,
    override_reason text,
    granted_at timestamp with time zone DEFAULT now(),
    granted_by uuid,
    expires_at timestamp with time zone
);


--
-- Name: TABLE user_module_overrides; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.user_module_overrides IS 'User-specific module access overrides that bypass role permissions';


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    role_id uuid NOT NULL,
    department_id uuid,
    assigned_at timestamp with time zone DEFAULT now(),
    assigned_by uuid,
    expires_at timestamp with time zone,
    is_active boolean DEFAULT true
);


--
-- Name: TABLE user_roles; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.user_roles IS 'User role assignments';


--
-- Name: user_teams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_teams (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    team_id uuid NOT NULL,
    assigned_at timestamp with time zone DEFAULT now(),
    assigned_by uuid,
    is_primary boolean
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    username character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255),
    hashed_password character varying(255) NOT NULL,
    role public.user_role DEFAULT 'user'::public.user_role NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    is_verified boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_login timestamp with time zone,
    meta_info jsonb,
    default_project_id uuid,
    department_id uuid,
    function character varying(100)
);


--
-- Name: TABLE users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.users IS 'User accounts with RBAC support';


--
-- Name: web_scrape_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.web_scrape_jobs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    url text NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying,
    document_id uuid,
    scrape_prompt text,
    error_message text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp with time zone,
    project_id uuid,
    scraped_by uuid,
    department character varying(255),
    team character varying(255)
);


--
-- Name: COLUMN web_scrape_jobs.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.web_scrape_jobs.project_id IS 'Link to project/module for organization';


--
-- Name: COLUMN web_scrape_jobs.scraped_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.web_scrape_jobs.scraped_by IS 'User who initiated the scraping job';


--
-- Name: COLUMN web_scrape_jobs.department; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.web_scrape_jobs.department IS 'Department name for organizational filtering';


--
-- Name: COLUMN web_scrape_jobs.team; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.web_scrape_jobs.team IS 'Team name for organizational filtering';


--
-- Name: agent_tasks agent_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_tasks
    ADD CONSTRAINT agent_tasks_pkey PRIMARY KEY (id);


--
-- Name: agent_tasks agent_tasks_task_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_tasks
    ADD CONSTRAINT agent_tasks_task_id_key UNIQUE (task_id);


--
-- Name: api_credentials api_credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_credentials
    ADD CONSTRAINT api_credentials_pkey PRIMARY KEY (id);


--
-- Name: api_credentials api_credentials_provider_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_credentials
    ADD CONSTRAINT api_credentials_provider_key UNIQUE (provider);


--
-- Name: api_key_access_log api_key_access_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key_access_log
    ADD CONSTRAINT api_key_access_log_pkey PRIMARY KEY (id);


--
-- Name: api_keys api_keys_key_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_key_hash_key UNIQUE (key_hash);


--
-- Name: api_keys api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_session_id_key UNIQUE (session_id);


--
-- Name: config_audit_logs config_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_audit_logs
    ADD CONSTRAINT config_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: config_schemas config_schemas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_schemas
    ADD CONSTRAINT config_schemas_pkey PRIMARY KEY (id);


--
-- Name: config_schemas config_schemas_schema_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_schemas
    ADD CONSTRAINT config_schemas_schema_name_key UNIQUE (schema_name);


--
-- Name: config_templates config_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_templates
    ADD CONSTRAINT config_templates_pkey PRIMARY KEY (id);


--
-- Name: config_versions config_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_versions
    ADD CONSTRAINT config_versions_pkey PRIMARY KEY (id);


--
-- Name: conversation_messages conversation_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: departments departments_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_name_key UNIQUE (name);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: deployment_instances deployment_instances_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_instances
    ADD CONSTRAINT deployment_instances_pkey PRIMARY KEY (id);


--
-- Name: document_chunks document_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_pkey PRIMARY KEY (id);


--
-- Name: document_extractions document_extractions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_extractions
    ADD CONSTRAINT document_extractions_pkey PRIMARY KEY (id);


--
-- Name: document_permissions document_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_permissions
    ADD CONSTRAINT document_permissions_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: domain_statistics domain_statistics_domain_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_statistics
    ADD CONSTRAINT domain_statistics_domain_key UNIQUE (domain);


--
-- Name: domain_statistics domain_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_statistics
    ADD CONSTRAINT domain_statistics_pkey PRIMARY KEY (id);


--
-- Name: evaluation_benchmarks evaluation_benchmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_benchmarks
    ADD CONSTRAINT evaluation_benchmarks_pkey PRIMARY KEY (id);


--
-- Name: evaluation_cache evaluation_cache_cache_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_cache
    ADD CONSTRAINT evaluation_cache_cache_key_key UNIQUE (cache_key);


--
-- Name: evaluation_cache evaluation_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_cache
    ADD CONSTRAINT evaluation_cache_pkey PRIMARY KEY (id);


--
-- Name: evaluation_configs evaluation_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_configs
    ADD CONSTRAINT evaluation_configs_pkey PRIMARY KEY (id);


--
-- Name: evaluation_results evaluation_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_results
    ADD CONSTRAINT evaluation_results_pkey PRIMARY KEY (id);


--
-- Name: export_audit_logs export_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_audit_logs
    ADD CONSTRAINT export_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: export_jobs export_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_jobs
    ADD CONSTRAINT export_jobs_pkey PRIMARY KEY (id);


--
-- Name: export_packages export_packages_package_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_packages
    ADD CONSTRAINT export_packages_package_name_key UNIQUE (package_name);


--
-- Name: export_packages export_packages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_packages
    ADD CONSTRAINT export_packages_pkey PRIMARY KEY (id);


--
-- Name: export_templates export_templates_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_templates
    ADD CONSTRAINT export_templates_name_key UNIQUE (name);


--
-- Name: export_templates export_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_templates
    ADD CONSTRAINT export_templates_pkey PRIMARY KEY (id);


--
-- Name: extraction_results extraction_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraction_results
    ADD CONSTRAINT extraction_results_pkey PRIMARY KEY (id);


--
-- Name: finetuned_models finetuned_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuned_models
    ADD CONSTRAINT finetuned_models_pkey PRIMARY KEY (id);


--
-- Name: finetuning_datasets finetuning_datasets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuning_datasets
    ADD CONSTRAINT finetuning_datasets_pkey PRIMARY KEY (id);


--
-- Name: finetuning_jobs finetuning_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuning_jobs
    ADD CONSTRAINT finetuning_jobs_pkey PRIMARY KEY (id);


--
-- Name: human_feedback human_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.human_feedback
    ADD CONSTRAINT human_feedback_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: model_approvals model_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_approvals
    ADD CONSTRAINT model_approvals_pkey PRIMARY KEY (id);


--
-- Name: module_activations module_activations_module_id_project_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_activations
    ADD CONSTRAINT module_activations_module_id_project_id_user_id_key UNIQUE (module_id, project_id, user_id);


--
-- Name: module_activations module_activations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_activations
    ADD CONSTRAINT module_activations_pkey PRIMARY KEY (id);


--
-- Name: module_configurations module_configurations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_configurations
    ADD CONSTRAINT module_configurations_pkey PRIMARY KEY (id);


--
-- Name: module_usage_logs module_usage_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_usage_logs
    ADD CONSTRAINT module_usage_logs_pkey PRIMARY KEY (id);


--
-- Name: module_user_overrides module_user_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_user_overrides
    ADD CONSTRAINT module_user_overrides_pkey PRIMARY KEY (id);


--
-- Name: modules modules_module_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_module_key_key UNIQUE (module_key);


--
-- Name: modules modules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_pkey PRIMARY KEY (id);


--
-- Name: output_templates output_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.output_templates
    ADD CONSTRAINT output_templates_pkey PRIMARY KEY (id);


--
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (id);


--
-- Name: project_members project_members_project_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_user_id_key UNIQUE (project_id, user_id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: prompt_library prompt_library_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_library
    ADD CONSTRAINT prompt_library_pkey PRIMARY KEY (id);


--
-- Name: prompt_ratings prompt_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_ratings
    ADD CONSTRAINT prompt_ratings_pkey PRIMARY KEY (id);


--
-- Name: prompt_ratings prompt_ratings_prompt_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_ratings
    ADD CONSTRAINT prompt_ratings_prompt_id_user_id_key UNIQUE (prompt_id, user_id);


--
-- Name: prompt_usage_log prompt_usage_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_usage_log
    ADD CONSTRAINT prompt_usage_log_pkey PRIMARY KEY (id);


--
-- Name: query_cache query_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_cache
    ADD CONSTRAINT query_cache_pkey PRIMARY KEY (id);


--
-- Name: role_module_permissions role_module_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_module_permissions
    ADD CONSTRAINT role_module_permissions_pkey PRIMARY KEY (id);


--
-- Name: role_module_permissions role_module_permissions_role_id_module_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_module_permissions
    ADD CONSTRAINT role_module_permissions_role_id_module_id_key UNIQUE (role_id, module_id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_role_module_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_module_id_key UNIQUE (role, module_id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: saved_css_templates saved_css_templates_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_css_templates
    ADD CONSTRAINT saved_css_templates_name_key UNIQUE (name);


--
-- Name: saved_css_templates saved_css_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saved_css_templates
    ADD CONSTRAINT saved_css_templates_pkey PRIMARY KEY (id);


--
-- Name: scraping_audit_log scraping_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraping_audit_log
    ADD CONSTRAINT scraping_audit_log_pkey PRIMARY KEY (id);


--
-- Name: scraping_configs scraping_configs_domain_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraping_configs
    ADD CONSTRAINT scraping_configs_domain_key UNIQUE (domain);


--
-- Name: scraping_configs scraping_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraping_configs
    ADD CONSTRAINT scraping_configs_pkey PRIMARY KEY (id);


--
-- Name: session_contexts session_contexts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_contexts
    ADD CONSTRAINT session_contexts_pkey PRIMARY KEY (id);


--
-- Name: session_contexts session_contexts_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_contexts
    ADD CONSTRAINT session_contexts_session_id_key UNIQUE (session_id);


--
-- Name: session_documents session_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_documents
    ADD CONSTRAINT session_documents_pkey PRIMARY KEY (id);


--
-- Name: skill_modules skill_modules_module_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_modules
    ADD CONSTRAINT skill_modules_module_id_key UNIQUE (module_id);


--
-- Name: skill_modules skill_modules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_modules
    ADD CONSTRAINT skill_modules_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: tool_usage_stats tool_usage_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_usage_stats
    ADD CONSTRAINT tool_usage_stats_pkey PRIMARY KEY (id);


--
-- Name: training_metrics training_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_metrics
    ADD CONSTRAINT training_metrics_pkey PRIMARY KEY (id);


--
-- Name: module_configurations unique_module_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_configurations
    ADD CONSTRAINT unique_module_name UNIQUE (module_name);


--
-- Name: config_versions unique_module_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_versions
    ADD CONSTRAINT unique_module_version UNIQUE (module_name, version);


--
-- Name: config_schemas unique_schema_name_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_schemas
    ADD CONSTRAINT unique_schema_name_version UNIQUE (schema_name, schema_version);


--
-- Name: config_templates unique_template_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_templates
    ADD CONSTRAINT unique_template_name UNIQUE (template_name);


--
-- Name: module_user_overrides unique_user_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_user_overrides
    ADD CONSTRAINT unique_user_module UNIQUE (user_id, module_name);


--
-- Name: teams uq_team_department_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT uq_team_department_name UNIQUE (department_id, name);


--
-- Name: user_teams uq_user_team; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_teams
    ADD CONSTRAINT uq_user_team UNIQUE (user_id, team_id);


--
-- Name: usage_metrics usage_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usage_metrics
    ADD CONSTRAINT usage_metrics_pkey PRIMARY KEY (id);


--
-- Name: usage_metrics usage_metrics_user_id_date_model_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usage_metrics
    ADD CONSTRAINT usage_metrics_user_id_date_model_id_key UNIQUE (user_id, date, model_id);


--
-- Name: user_module_overrides user_module_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_module_overrides
    ADD CONSTRAINT user_module_overrides_pkey PRIMARY KEY (id);


--
-- Name: user_module_overrides user_module_overrides_user_id_module_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_module_overrides
    ADD CONSTRAINT user_module_overrides_user_id_module_id_key UNIQUE (user_id, module_id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_user_id_role_id_department_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_role_id_department_id_key UNIQUE (user_id, role_id, department_id);


--
-- Name: user_teams user_teams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_teams
    ADD CONSTRAINT user_teams_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: web_scrape_jobs web_scrape_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_scrape_jobs
    ADD CONSTRAINT web_scrape_jobs_pkey PRIMARY KEY (id);


--
-- Name: idx_agent_tasks_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_tasks_created_at ON public.agent_tasks USING btree (created_at);


--
-- Name: idx_agent_tasks_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_tasks_created_by ON public.agent_tasks USING btree (created_by);


--
-- Name: idx_agent_tasks_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_tasks_project_id ON public.agent_tasks USING btree (project_id);


--
-- Name: idx_agent_tasks_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_tasks_session_id ON public.agent_tasks USING btree (session_id);


--
-- Name: idx_agent_tasks_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_tasks_status ON public.agent_tasks USING btree (status);


--
-- Name: idx_agent_tasks_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_tasks_task_id ON public.agent_tasks USING btree (task_id);


--
-- Name: idx_agent_tasks_task_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_agent_tasks_task_name ON public.agent_tasks USING btree (task_name);


--
-- Name: idx_api_credentials_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_credentials_is_active ON public.api_credentials USING btree (is_active);


--
-- Name: idx_api_credentials_provider; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_credentials_provider ON public.api_credentials USING btree (provider);


--
-- Name: idx_api_key_access_log_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_access_log_action ON public.api_key_access_log USING btree (action);


--
-- Name: idx_api_key_access_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_access_log_created_at ON public.api_key_access_log USING btree (created_at DESC);


--
-- Name: idx_api_key_access_log_provider; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_access_log_provider ON public.api_key_access_log USING btree (provider);


--
-- Name: idx_api_key_access_log_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_access_log_user_id ON public.api_key_access_log USING btree (user_id);


--
-- Name: idx_api_keys_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_keys_hash ON public.api_keys USING btree (key_hash);


--
-- Name: idx_api_keys_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_keys_user ON public.api_keys USING btree (user_id);


--
-- Name: idx_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_action ON public.config_audit_logs USING btree (action);


--
-- Name: idx_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: idx_audit_logs_action_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_action_category ON public.audit_logs USING btree (action) WHERE (action = ANY (ARRAY['login'::public.action_type, 'logout'::public.action_type, 'login_failed'::public.action_type]));


--
-- Name: idx_audit_logs_action_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_action_created ON public.audit_logs USING btree (action, created_at DESC);


--
-- Name: idx_audit_logs_admin_actions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_admin_actions ON public.audit_logs USING btree (action) WHERE (action = ANY (ARRAY['user_create'::public.action_type, 'user_update'::public.action_type, 'user_delete'::public.action_type, 'role_assign'::public.action_type, 'role_revoke'::public.action_type]));


--
-- Name: idx_audit_logs_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_created ON public.audit_logs USING btree (created_at DESC);


--
-- Name: idx_audit_logs_resource; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_resource ON public.audit_logs USING btree (resource_type, resource_id);


--
-- Name: idx_audit_logs_security_events; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_security_events ON public.audit_logs USING btree (action) WHERE (action = ANY (ARRAY['permission_denied'::public.action_type, 'unauthorized_access'::public.action_type, 'rate_limit_exceeded'::public.action_type]));


--
-- Name: idx_audit_logs_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_session ON public.audit_logs USING btree (session_id);


--
-- Name: idx_audit_logs_session_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_session_created ON public.audit_logs USING btree (session_id, created_at DESC) WHERE (session_id IS NOT NULL);


--
-- Name: idx_audit_logs_status_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_status_created ON public.audit_logs USING btree (status_code, created_at DESC) WHERE (status_code >= 400);


--
-- Name: idx_audit_logs_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_user ON public.audit_logs USING btree (user_id);


--
-- Name: idx_audit_logs_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_user_created ON public.audit_logs USING btree (user_id, created_at DESC) WHERE (user_id IS NOT NULL);


--
-- Name: idx_audit_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_module ON public.config_audit_logs USING btree (module_name);


--
-- Name: idx_audit_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_time ON public.config_audit_logs USING btree (changed_at DESC);


--
-- Name: idx_audit_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_user ON public.config_audit_logs USING btree (changed_by);


--
-- Name: idx_chat_sessions_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_active ON public.chat_sessions USING btree (is_active);


--
-- Name: idx_chat_sessions_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_project ON public.chat_sessions USING btree (project_id);


--
-- Name: idx_chat_sessions_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_session_id ON public.chat_sessions USING btree (session_id);


--
-- Name: idx_chat_sessions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_sessions_user ON public.chat_sessions USING btree (user_id);


--
-- Name: idx_chunks_code_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_code_embedding ON public.document_chunks USING ivfflat (code_embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_chunks_embedding_strategy; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_embedding_strategy ON public.document_chunks USING btree (embedding_strategy);


--
-- Name: idx_chunks_numerical_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_numerical_embedding ON public.document_chunks USING ivfflat (numerical_embedding) WITH (lists='100');


--
-- Name: idx_chunks_table_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_table_embedding ON public.document_chunks USING ivfflat (table_embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_chunks_visual_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_visual_embedding ON public.document_chunks USING ivfflat (visual_embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_conversation_messages_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversation_messages_role ON public.conversation_messages USING btree (role);


--
-- Name: idx_conversation_messages_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversation_messages_session ON public.conversation_messages USING btree (session_id, created_at);


--
-- Name: idx_departments_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_departments_active ON public.departments USING btree (is_active);


--
-- Name: idx_departments_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_departments_name ON public.departments USING btree (name);


--
-- Name: idx_departments_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_departments_parent ON public.departments USING btree (parent_department_id);


--
-- Name: idx_deployment_instances_deployed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_deployment_instances_deployed_at ON public.deployment_instances USING btree (deployed_at DESC);


--
-- Name: idx_deployment_instances_environment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_deployment_instances_environment ON public.deployment_instances USING btree (environment);


--
-- Name: idx_deployment_instances_package_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_deployment_instances_package_id ON public.deployment_instances USING btree (export_package_id);


--
-- Name: idx_deployment_instances_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_deployment_instances_status ON public.deployment_instances USING btree (status);


--
-- Name: idx_document_chunks_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_department ON public.document_chunks USING btree (department);


--
-- Name: idx_document_chunks_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_document_id ON public.document_chunks USING btree (document_id);


--
-- Name: idx_document_chunks_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_embedding ON public.document_chunks USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_document_chunks_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_project_id ON public.document_chunks USING btree (project_id);


--
-- Name: idx_document_chunks_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_team ON public.document_chunks USING btree (team);


--
-- Name: idx_document_chunks_uploaded_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_uploaded_by ON public.document_chunks USING btree (uploaded_by);


--
-- Name: idx_document_extractions_document; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_extractions_document ON public.document_extractions USING btree (document_id);


--
-- Name: idx_document_extractions_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_extractions_module ON public.document_extractions USING btree (module_id);


--
-- Name: idx_document_extractions_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_extractions_session ON public.document_extractions USING btree (session_id);


--
-- Name: idx_document_extractions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_extractions_status ON public.document_extractions USING btree (status);


--
-- Name: idx_document_permissions_document; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_permissions_document ON public.document_permissions USING btree (document_id);


--
-- Name: idx_document_permissions_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_permissions_role ON public.document_permissions USING btree (role);


--
-- Name: idx_document_permissions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_permissions_user ON public.document_permissions USING btree (user_id);


--
-- Name: idx_documents_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_created_at ON public.documents USING btree (created_at DESC);


--
-- Name: idx_documents_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_department ON public.documents USING btree (department);


--
-- Name: idx_documents_minio_path; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_minio_path ON public.documents USING btree (minio_path);


--
-- Name: idx_documents_processing_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_processing_status ON public.documents USING btree (processing_status);


--
-- Name: idx_documents_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_project_id ON public.documents USING btree (project_id);


--
-- Name: idx_documents_project_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_project_source ON public.documents USING btree (project_id, source_type);


--
-- Name: idx_documents_source_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_source_type ON public.documents USING btree (source_type);


--
-- Name: idx_documents_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_team ON public.documents USING btree (team);


--
-- Name: idx_documents_uploaded_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_uploaded_by ON public.documents USING btree (uploaded_by);


--
-- Name: idx_documents_user_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_user_role ON public.documents USING btree (user_role);


--
-- Name: idx_evaluation_benchmarks_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_benchmarks_category ON public.evaluation_benchmarks USING btree (category);


--
-- Name: idx_evaluation_benchmarks_dataset_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_benchmarks_dataset_name ON public.evaluation_benchmarks USING btree (dataset_name);


--
-- Name: idx_evaluation_benchmarks_difficulty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_benchmarks_difficulty ON public.evaluation_benchmarks USING btree (difficulty);


--
-- Name: idx_evaluation_cache_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_cache_created_at ON public.evaluation_cache USING btree (created_at);


--
-- Name: idx_evaluation_cache_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_cache_key ON public.evaluation_cache USING btree (cache_key);


--
-- Name: idx_evaluation_configs_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_configs_session_id ON public.evaluation_configs USING btree (session_id);


--
-- Name: idx_evaluation_configs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_configs_user_id ON public.evaluation_configs USING btree (user_id);


--
-- Name: idx_evaluation_results_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_results_created_at ON public.evaluation_results USING btree (created_at);


--
-- Name: idx_evaluation_results_message_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_results_message_id ON public.evaluation_results USING btree (message_id);


--
-- Name: idx_evaluation_results_overall_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_results_overall_score ON public.evaluation_results USING btree (overall_score);


--
-- Name: idx_evaluation_results_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_evaluation_results_session_id ON public.evaluation_results USING btree (session_id);


--
-- Name: idx_export_audit_logs_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_audit_logs_event_type ON public.export_audit_logs USING btree (event_type);


--
-- Name: idx_export_audit_logs_export_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_audit_logs_export_job_id ON public.export_audit_logs USING btree (export_job_id);


--
-- Name: idx_export_audit_logs_export_package_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_audit_logs_export_package_id ON public.export_audit_logs USING btree (export_package_id);


--
-- Name: idx_export_audit_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_audit_logs_timestamp ON public.export_audit_logs USING btree ("timestamp" DESC);


--
-- Name: idx_export_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_audit_logs_user_id ON public.export_audit_logs USING btree (user_id);


--
-- Name: idx_export_jobs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_jobs_created_at ON public.export_jobs USING btree (created_at DESC);


--
-- Name: idx_export_jobs_module_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_jobs_module_name ON public.export_jobs USING btree (module_name);


--
-- Name: idx_export_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_jobs_status ON public.export_jobs USING btree (status);


--
-- Name: idx_export_jobs_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_jobs_tenant_id ON public.export_jobs USING btree (tenant_id);


--
-- Name: idx_export_packages_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_packages_created_at ON public.export_packages USING btree (created_at DESC);


--
-- Name: idx_export_packages_export_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_packages_export_job_id ON public.export_packages USING btree (export_job_id);


--
-- Name: idx_export_packages_module_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_packages_module_name ON public.export_packages USING btree (module_name);


--
-- Name: idx_export_packages_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_packages_tenant_id ON public.export_packages USING btree (tenant_id);


--
-- Name: idx_export_templates_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_templates_category ON public.export_templates USING btree (category);


--
-- Name: idx_export_templates_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_export_templates_is_active ON public.export_templates USING btree (is_active);


--
-- Name: idx_extraction_results_extraction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_extraction_results_extraction ON public.extraction_results USING btree (extraction_id);


--
-- Name: idx_extraction_results_project_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_extraction_results_project_name ON public.extraction_results USING btree (project_name);


--
-- Name: idx_finetuned_models_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_finetuned_models_status ON public.finetuned_models USING btree (status);


--
-- Name: idx_finetuning_jobs_dataset_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_finetuning_jobs_dataset_id ON public.finetuning_jobs USING btree (dataset_id);


--
-- Name: idx_finetuning_jobs_debug_log; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_finetuning_jobs_debug_log ON public.finetuning_jobs USING gin (debug_log);


--
-- Name: idx_finetuning_jobs_training_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_finetuning_jobs_training_stage ON public.finetuning_jobs USING btree (training_stage);


--
-- Name: idx_human_feedback_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_human_feedback_created_at ON public.human_feedback USING btree (created_at);


--
-- Name: idx_human_feedback_evaluation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_human_feedback_evaluation_id ON public.human_feedback USING btree (evaluation_id);


--
-- Name: idx_human_feedback_message_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_human_feedback_message_id ON public.human_feedback USING btree (message_id);


--
-- Name: idx_human_feedback_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_human_feedback_session_id ON public.human_feedback USING btree (session_id);


--
-- Name: idx_messages_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_conversation_id ON public.messages USING btree (conversation_id);


--
-- Name: idx_messages_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_created_at ON public.messages USING btree (created_at DESC);


--
-- Name: idx_model_approvals_approved_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_approvals_approved_by ON public.model_approvals USING btree (approved_by);


--
-- Name: idx_model_approvals_model_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_approvals_model_id ON public.model_approvals USING btree (model_id);


--
-- Name: idx_model_approvals_requested_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_approvals_requested_by ON public.model_approvals USING btree (requested_by);


--
-- Name: idx_model_approvals_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_approvals_status ON public.model_approvals USING btree (status);


--
-- Name: idx_module_activations_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_activations_enabled ON public.module_activations USING btree (enabled);


--
-- Name: idx_module_activations_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_activations_module ON public.module_activations USING btree (module_id);


--
-- Name: idx_module_activations_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_activations_project ON public.module_activations USING btree (project_id);


--
-- Name: idx_module_configs_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_configs_active ON public.module_configurations USING btree (is_active);


--
-- Name: idx_module_configs_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_configs_category ON public.module_configurations USING btree (category);


--
-- Name: idx_module_configs_config; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_configs_config ON public.module_configurations USING gin (config);


--
-- Name: idx_module_configs_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_configs_name ON public.module_configurations USING btree (module_name);


--
-- Name: idx_module_configs_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_configs_type ON public.module_configurations USING btree (module_type);


--
-- Name: idx_module_usage_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_usage_created ON public.module_usage_logs USING btree (created_at);


--
-- Name: idx_module_usage_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_usage_module ON public.module_usage_logs USING btree (module_id);


--
-- Name: idx_module_usage_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_usage_success ON public.module_usage_logs USING btree (success);


--
-- Name: idx_module_usage_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_module_usage_user ON public.module_usage_logs USING btree (user_id);


--
-- Name: idx_modules_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_modules_active ON public.modules USING btree (is_active);


--
-- Name: idx_modules_display_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_modules_display_order ON public.modules USING btree (display_order);


--
-- Name: idx_modules_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_modules_is_active ON public.modules USING btree (is_active);


--
-- Name: idx_modules_module_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_modules_module_key ON public.modules USING btree (module_key);


--
-- Name: idx_modules_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_modules_order ON public.modules USING btree (display_order);


--
-- Name: idx_output_templates_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_output_templates_created_by ON public.output_templates USING btree (created_by);


--
-- Name: idx_output_templates_is_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_output_templates_is_public ON public.output_templates USING btree (is_public);


--
-- Name: idx_output_templates_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_output_templates_project_id ON public.output_templates USING btree (project_id);


--
-- Name: idx_output_templates_template_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_output_templates_template_type ON public.output_templates USING btree (template_type);


--
-- Name: idx_permissions_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permissions_module ON public.role_module_permissions USING btree (module_id);


--
-- Name: idx_permissions_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permissions_read ON public.role_module_permissions USING btree (can_read);


--
-- Name: idx_permissions_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_permissions_role ON public.role_module_permissions USING btree (role_id);


--
-- Name: idx_project_members_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_members_project_id ON public.project_members USING btree (project_id);


--
-- Name: idx_project_members_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_members_user_id ON public.project_members USING btree (user_id);


--
-- Name: idx_projects_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_department ON public.projects USING btree (department);


--
-- Name: idx_projects_owner_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_owner_id ON public.projects USING btree (owner_id);


--
-- Name: idx_projects_preferred_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_preferred_model ON public.projects USING btree (preferred_model) WHERE (preferred_model IS NOT NULL);


--
-- Name: idx_projects_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_status ON public.projects USING btree (status);


--
-- Name: idx_projects_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_team ON public.projects USING btree (team_id);


--
-- Name: idx_prompt_library_average_rating; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_average_rating ON public.prompt_library USING btree (average_rating DESC);


--
-- Name: idx_prompt_library_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_category ON public.prompt_library USING btree (category);


--
-- Name: idx_prompt_library_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_created_by ON public.prompt_library USING btree (created_by);


--
-- Name: idx_prompt_library_is_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_is_public ON public.prompt_library USING btree (is_public);


--
-- Name: idx_prompt_library_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_module ON public.prompt_library USING btree (module);


--
-- Name: idx_prompt_library_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_project_id ON public.prompt_library USING btree (project_id);


--
-- Name: idx_prompt_library_prompt_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_prompt_type ON public.prompt_library USING btree (prompt_type);


--
-- Name: idx_prompt_library_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_tags ON public.prompt_library USING gin (tags);


--
-- Name: idx_prompt_library_usage_count; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_library_usage_count ON public.prompt_library USING btree (usage_count DESC);


--
-- Name: idx_prompt_ratings_prompt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_ratings_prompt_id ON public.prompt_ratings USING btree (prompt_id);


--
-- Name: idx_prompt_ratings_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_ratings_user_id ON public.prompt_ratings USING btree (user_id);


--
-- Name: idx_prompt_usage_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_usage_log_created_at ON public.prompt_usage_log USING btree (created_at DESC);


--
-- Name: idx_prompt_usage_log_prompt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_usage_log_prompt_id ON public.prompt_usage_log USING btree (prompt_id);


--
-- Name: idx_prompt_usage_log_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prompt_usage_log_user_id ON public.prompt_usage_log USING btree (user_id);


--
-- Name: idx_query_cache_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_cache_created_at ON public.query_cache USING btree (created_at DESC);


--
-- Name: idx_query_cache_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_cache_embedding ON public.query_cache USING ivfflat (query_embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_query_cache_ttl; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_cache_ttl ON public.query_cache USING btree (created_at, ttl_seconds);


--
-- Name: idx_role_module_perms_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_module_perms_module ON public.role_module_permissions USING btree (module_id);


--
-- Name: idx_role_module_perms_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_module_perms_role ON public.role_module_permissions USING btree (role_id);


--
-- Name: idx_role_permissions_module_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_permissions_module_id ON public.role_permissions USING btree (module_id);


--
-- Name: idx_role_permissions_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_permissions_role ON public.role_permissions USING btree (role);


--
-- Name: idx_roles_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roles_name ON public.roles USING btree (name);


--
-- Name: idx_roles_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roles_parent ON public.roles USING btree (parent_role_id);


--
-- Name: idx_saved_css_templates_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_saved_css_templates_active ON public.saved_css_templates USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_saved_css_templates_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_saved_css_templates_name ON public.saved_css_templates USING btree (name);


--
-- Name: idx_saved_css_templates_url_pattern; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_saved_css_templates_url_pattern ON public.saved_css_templates USING btree (url_pattern) WHERE (url_pattern IS NOT NULL);


--
-- Name: idx_saved_css_templates_use_count; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_saved_css_templates_use_count ON public.saved_css_templates USING btree (use_count DESC);


--
-- Name: idx_schemas_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schemas_active ON public.config_schemas USING btree (is_active);


--
-- Name: idx_schemas_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schemas_name ON public.config_schemas USING btree (schema_name);


--
-- Name: idx_schemas_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schemas_type ON public.config_schemas USING btree (module_type);


--
-- Name: idx_scraping_audit_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraping_audit_created_at ON public.scraping_audit_log USING btree (created_at);


--
-- Name: idx_scraping_audit_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraping_audit_domain ON public.scraping_audit_log USING btree (domain);


--
-- Name: idx_scraping_audit_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraping_audit_success ON public.scraping_audit_log USING btree (success);


--
-- Name: idx_scraping_configs_allow_scraping; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraping_configs_allow_scraping ON public.scraping_configs USING btree (allow_scraping);


--
-- Name: idx_scraping_configs_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraping_configs_domain ON public.scraping_configs USING btree (domain);


--
-- Name: idx_scraping_configs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scraping_configs_status ON public.scraping_configs USING btree (status);


--
-- Name: idx_session_contexts_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_session_contexts_session ON public.session_contexts USING btree (session_id);


--
-- Name: idx_session_documents_document; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_session_documents_document ON public.session_documents USING btree (document_id);


--
-- Name: idx_session_documents_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_session_documents_session_id ON public.session_documents USING btree (session_id);


--
-- Name: idx_skill_modules_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skill_modules_category ON public.skill_modules USING btree (category);


--
-- Name: idx_skill_modules_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skill_modules_status ON public.skill_modules USING btree (status);


--
-- Name: idx_skill_modules_tier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skill_modules_tier ON public.skill_modules USING btree (tier);


--
-- Name: idx_templates_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_templates_category ON public.config_templates USING btree (category);


--
-- Name: idx_templates_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_templates_public ON public.config_templates USING btree (is_public);


--
-- Name: idx_templates_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_templates_tags ON public.config_templates USING gin (tags);


--
-- Name: idx_templates_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_templates_type ON public.config_templates USING btree (module_type);


--
-- Name: idx_tool_summary_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_summary_category ON public.tool_usage_summary USING btree (tool_category);


--
-- Name: idx_tool_summary_invocations; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_summary_invocations ON public.tool_usage_summary USING btree (total_invocations DESC);


--
-- Name: idx_tool_summary_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_summary_name ON public.tool_usage_summary USING btree (tool_name);


--
-- Name: idx_tool_usage_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_usage_category ON public.tool_usage_stats USING btree (tool_category);


--
-- Name: idx_tool_usage_category_name_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_usage_category_name_date ON public.tool_usage_stats USING btree (tool_category, tool_name, created_at DESC);


--
-- Name: idx_tool_usage_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_usage_created_at ON public.tool_usage_stats USING btree (created_at DESC);


--
-- Name: idx_tool_usage_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_usage_name ON public.tool_usage_stats USING btree (tool_name);


--
-- Name: idx_tool_usage_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_usage_session ON public.tool_usage_stats USING btree (session_id);


--
-- Name: idx_tool_usage_session_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_usage_session_date ON public.tool_usage_stats USING btree (session_id, created_at DESC);


--
-- Name: idx_tool_usage_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_usage_success ON public.tool_usage_stats USING btree (success);


--
-- Name: idx_tool_usage_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tool_usage_user ON public.tool_usage_stats USING btree (user_id);


--
-- Name: idx_usage_metrics_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usage_metrics_date ON public.usage_metrics USING btree (date DESC);


--
-- Name: idx_usage_metrics_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usage_metrics_model ON public.usage_metrics USING btree (model_id);


--
-- Name: idx_usage_metrics_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usage_metrics_user ON public.usage_metrics USING btree (user_id);


--
-- Name: idx_user_module_overrides_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_module_overrides_expires ON public.user_module_overrides USING btree (expires_at);


--
-- Name: idx_user_module_overrides_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_module_overrides_module ON public.user_module_overrides USING btree (module_id);


--
-- Name: idx_user_module_overrides_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_module_overrides_user ON public.user_module_overrides USING btree (user_id);


--
-- Name: idx_user_overrides_experiment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_overrides_experiment ON public.module_user_overrides USING btree (experiment_id);


--
-- Name: idx_user_overrides_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_overrides_module ON public.module_user_overrides USING btree (module_name);


--
-- Name: idx_user_overrides_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_overrides_user ON public.module_user_overrides USING btree (user_id);


--
-- Name: idx_user_overrides_variant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_overrides_variant ON public.module_user_overrides USING btree (variant_name);


--
-- Name: idx_user_roles_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_roles_active ON public.user_roles USING btree (is_active);


--
-- Name: idx_user_roles_assigned_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_roles_assigned_by ON public.user_roles USING btree (assigned_by);


--
-- Name: idx_user_roles_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_roles_department ON public.user_roles USING btree (department_id);


--
-- Name: idx_user_roles_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_roles_role ON public.user_roles USING btree (role_id);


--
-- Name: idx_user_roles_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_roles_user ON public.user_roles USING btree (user_id);


--
-- Name: idx_users_default_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_default_project ON public.users USING btree (default_project_id);


--
-- Name: idx_users_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_department ON public.users USING btree (department_id);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_function; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_function ON public.users USING btree (function);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: idx_versions_changed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_versions_changed_at ON public.config_versions USING btree (changed_at DESC);


--
-- Name: idx_versions_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_versions_module ON public.config_versions USING btree (module_name);


--
-- Name: idx_versions_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_versions_version ON public.config_versions USING btree (version DESC);


--
-- Name: idx_web_scrape_jobs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_web_scrape_jobs_created_at ON public.web_scrape_jobs USING btree (created_at DESC);


--
-- Name: idx_web_scrape_jobs_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_web_scrape_jobs_department ON public.web_scrape_jobs USING btree (department);


--
-- Name: idx_web_scrape_jobs_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_web_scrape_jobs_project_id ON public.web_scrape_jobs USING btree (project_id);


--
-- Name: idx_web_scrape_jobs_project_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_web_scrape_jobs_project_status ON public.web_scrape_jobs USING btree (project_id, status);


--
-- Name: idx_web_scrape_jobs_scraped_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_web_scrape_jobs_scraped_by ON public.web_scrape_jobs USING btree (scraped_by);


--
-- Name: idx_web_scrape_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_web_scrape_jobs_status ON public.web_scrape_jobs USING btree (status);


--
-- Name: idx_web_scrape_jobs_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_web_scrape_jobs_team ON public.web_scrape_jobs USING btree (team);


--
-- Name: ix_teams_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teams_department_id ON public.teams USING btree (department_id);


--
-- Name: ix_teams_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teams_is_active ON public.teams USING btree (is_active);


--
-- Name: ix_user_teams_team_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_teams_team_id ON public.user_teams USING btree (team_id);


--
-- Name: ix_user_teams_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_teams_user_id ON public.user_teams USING btree (user_id);


--
-- Name: agent_tasks agent_tasks_updated_at_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER agent_tasks_updated_at_trigger BEFORE UPDATE ON public.agent_tasks FOR EACH ROW EXECUTE FUNCTION public.update_agent_tasks_updated_at();


--
-- Name: departments departments_update_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER departments_update_timestamp BEFORE UPDATE ON public.departments FOR EACH ROW EXECUTE FUNCTION public.update_departments_timestamp();


--
-- Name: evaluation_cache evaluation_cache_last_accessed; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER evaluation_cache_last_accessed BEFORE UPDATE ON public.evaluation_cache FOR EACH ROW EXECUTE FUNCTION public.update_evaluation_cache_last_accessed();


--
-- Name: evaluation_configs evaluation_configs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER evaluation_configs_updated_at BEFORE UPDATE ON public.evaluation_configs FOR EACH ROW EXECUTE FUNCTION public.update_evaluation_configs_updated_at();


--
-- Name: modules modules_update_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER modules_update_timestamp BEFORE UPDATE ON public.modules FOR EACH ROW EXECUTE FUNCTION public.update_modules_timestamp();


--
-- Name: role_module_permissions permissions_update_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER permissions_update_timestamp BEFORE UPDATE ON public.role_module_permissions FOR EACH ROW EXECUTE FUNCTION public.update_permissions_timestamp();


--
-- Name: roles roles_update_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER roles_update_timestamp BEFORE UPDATE ON public.roles FOR EACH ROW EXECUTE FUNCTION public.update_roles_timestamp();


--
-- Name: api_credentials trigger_update_api_credentials_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_api_credentials_timestamp BEFORE UPDATE ON public.api_credentials FOR EACH ROW EXECUTE FUNCTION public.update_api_credentials_updated_at();


--
-- Name: scraping_configs trigger_update_scraping_config_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_scraping_config_timestamp BEFORE UPDATE ON public.scraping_configs FOR EACH ROW EXECUTE FUNCTION public.update_scraping_config_timestamp();


--
-- Name: chat_sessions update_chat_sessions_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON public.chat_sessions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: conversations update_conversations_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON public.conversations FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: documents update_documents_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON public.documents FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: export_jobs update_export_jobs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_export_jobs_updated_at BEFORE UPDATE ON public.export_jobs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: export_templates update_export_templates_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_export_templates_updated_at BEFORE UPDATE ON public.export_templates FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: output_templates update_output_templates_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_output_templates_updated_at BEFORE UPDATE ON public.output_templates FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: prompt_library update_prompt_library_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_prompt_library_updated_at BEFORE UPDATE ON public.prompt_library FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: saved_css_templates update_saved_css_templates_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_saved_css_templates_updated_at BEFORE UPDATE ON public.saved_css_templates FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: session_contexts update_session_contexts_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_session_contexts_updated_at BEFORE UPDATE ON public.session_contexts FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: agent_tasks agent_tasks_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_tasks
    ADD CONSTRAINT agent_tasks_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: agent_tasks agent_tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_tasks
    ADD CONSTRAINT agent_tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: api_credentials api_credentials_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_credentials
    ADD CONSTRAINT api_credentials_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: api_key_access_log api_key_access_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key_access_log
    ADD CONSTRAINT api_key_access_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: api_keys api_keys_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE SET NULL;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: chat_sessions chat_sessions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: config_audit_logs config_audit_logs_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_audit_logs
    ADD CONSTRAINT config_audit_logs_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(id);


--
-- Name: config_templates config_templates_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_templates
    ADD CONSTRAINT config_templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: config_versions config_versions_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_versions
    ADD CONSTRAINT config_versions_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(id);


--
-- Name: conversation_messages conversation_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: departments departments_parent_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_parent_department_id_fkey FOREIGN KEY (parent_department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: deployment_instances deployment_instances_export_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_instances
    ADD CONSTRAINT deployment_instances_export_package_id_fkey FOREIGN KEY (export_package_id) REFERENCES public.export_packages(id) ON DELETE CASCADE;


--
-- Name: document_chunks document_chunks_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: document_chunks document_chunks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: document_chunks document_chunks_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: document_extractions document_extractions_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_extractions
    ADD CONSTRAINT document_extractions_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- Name: document_extractions document_extractions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_extractions
    ADD CONSTRAINT document_extractions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: document_extractions document_extractions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_extractions
    ADD CONSTRAINT document_extractions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: document_permissions document_permissions_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_permissions
    ADD CONSTRAINT document_permissions_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: document_permissions document_permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_permissions
    ADD CONSTRAINT document_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: documents documents_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: documents documents_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: evaluation_configs evaluation_configs_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_configs
    ADD CONSTRAINT evaluation_configs_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: evaluation_configs evaluation_configs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_configs
    ADD CONSTRAINT evaluation_configs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: evaluation_results evaluation_results_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_results
    ADD CONSTRAINT evaluation_results_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.conversation_messages(id) ON DELETE CASCADE;


--
-- Name: evaluation_results evaluation_results_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_results
    ADD CONSTRAINT evaluation_results_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: evaluation_results evaluation_results_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_results
    ADD CONSTRAINT evaluation_results_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: export_packages export_packages_export_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_packages
    ADD CONSTRAINT export_packages_export_job_id_fkey FOREIGN KEY (export_job_id) REFERENCES public.export_jobs(id) ON DELETE CASCADE;


--
-- Name: extraction_results extraction_results_extraction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraction_results
    ADD CONSTRAINT extraction_results_extraction_id_fkey FOREIGN KEY (extraction_id) REFERENCES public.document_extractions(id) ON DELETE CASCADE;


--
-- Name: finetuned_models finetuned_models_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuned_models
    ADD CONSTRAINT finetuned_models_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: finetuned_models finetuned_models_deprecated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuned_models
    ADD CONSTRAINT finetuned_models_deprecated_by_fkey FOREIGN KEY (deprecated_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: finetuned_models finetuned_models_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuned_models
    ADD CONSTRAINT finetuned_models_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.finetuning_jobs(id) ON DELETE SET NULL;


--
-- Name: finetuned_models finetuned_models_parent_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuned_models
    ADD CONSTRAINT finetuned_models_parent_model_id_fkey FOREIGN KEY (parent_model_id) REFERENCES public.finetuned_models(id) ON DELETE SET NULL;


--
-- Name: finetuned_models finetuned_models_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuned_models
    ADD CONSTRAINT finetuned_models_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: finetuning_datasets finetuning_datasets_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuning_datasets
    ADD CONSTRAINT finetuning_datasets_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: finetuning_datasets finetuning_datasets_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuning_datasets
    ADD CONSTRAINT finetuning_datasets_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: finetuning_jobs finetuning_jobs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuning_jobs
    ADD CONSTRAINT finetuning_jobs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: finetuning_jobs finetuning_jobs_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuning_jobs
    ADD CONSTRAINT finetuning_jobs_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.finetuning_datasets(id) ON DELETE SET NULL;


--
-- Name: finetuning_jobs finetuning_jobs_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuning_jobs
    ADD CONSTRAINT finetuning_jobs_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: export_jobs fk_export_jobs_export_package_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_jobs
    ADD CONSTRAINT fk_export_jobs_export_package_id FOREIGN KEY (export_package_id) REFERENCES public.export_packages(id) ON DELETE SET NULL;


--
-- Name: finetuning_jobs fk_finetuning_jobs_dataset_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finetuning_jobs
    ADD CONSTRAINT fk_finetuning_jobs_dataset_id FOREIGN KEY (dataset_id) REFERENCES public.finetuning_datasets(id) ON DELETE SET NULL;


--
-- Name: human_feedback human_feedback_evaluation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.human_feedback
    ADD CONSTRAINT human_feedback_evaluation_id_fkey FOREIGN KEY (evaluation_id) REFERENCES public.evaluation_results(id) ON DELETE CASCADE;


--
-- Name: human_feedback human_feedback_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.human_feedback
    ADD CONSTRAINT human_feedback_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.conversation_messages(id) ON DELETE CASCADE;


--
-- Name: human_feedback human_feedback_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.human_feedback
    ADD CONSTRAINT human_feedback_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: human_feedback human_feedback_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.human_feedback
    ADD CONSTRAINT human_feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: model_approvals model_approvals_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_approvals
    ADD CONSTRAINT model_approvals_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: model_approvals model_approvals_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_approvals
    ADD CONSTRAINT model_approvals_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.finetuned_models(id) ON DELETE CASCADE;


--
-- Name: model_approvals model_approvals_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_approvals
    ADD CONSTRAINT model_approvals_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: module_activations module_activations_activated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_activations
    ADD CONSTRAINT module_activations_activated_by_fkey FOREIGN KEY (activated_by) REFERENCES public.users(id);


--
-- Name: module_activations module_activations_deactivated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_activations
    ADD CONSTRAINT module_activations_deactivated_by_fkey FOREIGN KEY (deactivated_by) REFERENCES public.users(id);


--
-- Name: module_activations module_activations_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_activations
    ADD CONSTRAINT module_activations_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.skill_modules(module_id);


--
-- Name: module_activations module_activations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_activations
    ADD CONSTRAINT module_activations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: module_activations module_activations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_activations
    ADD CONSTRAINT module_activations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: module_configurations module_configurations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_configurations
    ADD CONSTRAINT module_configurations_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: module_usage_logs module_usage_logs_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_usage_logs
    ADD CONSTRAINT module_usage_logs_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id) ON DELETE CASCADE;


--
-- Name: module_usage_logs module_usage_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_usage_logs
    ADD CONSTRAINT module_usage_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: module_user_overrides module_user_overrides_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.module_user_overrides
    ADD CONSTRAINT module_user_overrides_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: output_templates output_templates_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.output_templates
    ADD CONSTRAINT output_templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: output_templates output_templates_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.output_templates
    ADD CONSTRAINT output_templates_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: output_templates output_templates_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.output_templates
    ADD CONSTRAINT output_templates_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: projects projects_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: projects projects_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: projects projects_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE SET NULL;


--
-- Name: prompt_library prompt_library_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_library
    ADD CONSTRAINT prompt_library_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: prompt_library prompt_library_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_library
    ADD CONSTRAINT prompt_library_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: prompt_library prompt_library_parent_prompt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_library
    ADD CONSTRAINT prompt_library_parent_prompt_id_fkey FOREIGN KEY (parent_prompt_id) REFERENCES public.prompt_library(id) ON DELETE SET NULL;


--
-- Name: prompt_library prompt_library_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_library
    ADD CONSTRAINT prompt_library_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: prompt_ratings prompt_ratings_prompt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_ratings
    ADD CONSTRAINT prompt_ratings_prompt_id_fkey FOREIGN KEY (prompt_id) REFERENCES public.prompt_library(id) ON DELETE CASCADE;


--
-- Name: prompt_ratings prompt_ratings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_ratings
    ADD CONSTRAINT prompt_ratings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: prompt_usage_log prompt_usage_log_prompt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_usage_log
    ADD CONSTRAINT prompt_usage_log_prompt_id_fkey FOREIGN KEY (prompt_id) REFERENCES public.prompt_library(id) ON DELETE CASCADE;


--
-- Name: prompt_usage_log prompt_usage_log_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_usage_log
    ADD CONSTRAINT prompt_usage_log_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE SET NULL;


--
-- Name: prompt_usage_log prompt_usage_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prompt_usage_log
    ADD CONSTRAINT prompt_usage_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: query_cache query_cache_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_cache
    ADD CONSTRAINT query_cache_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: role_module_permissions role_module_permissions_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_module_permissions
    ADD CONSTRAINT role_module_permissions_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id) ON DELETE CASCADE;


--
-- Name: role_module_permissions role_module_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_module_permissions
    ADD CONSTRAINT role_module_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id) ON DELETE CASCADE;


--
-- Name: roles roles_parent_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_parent_role_id_fkey FOREIGN KEY (parent_role_id) REFERENCES public.roles(id) ON DELETE SET NULL;


--
-- Name: scraping_audit_log scraping_audit_log_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraping_audit_log
    ADD CONSTRAINT scraping_audit_log_config_id_fkey FOREIGN KEY (config_id) REFERENCES public.scraping_configs(id) ON DELETE SET NULL;


--
-- Name: scraping_audit_log scraping_audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraping_audit_log
    ADD CONSTRAINT scraping_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: scraping_configs scraping_configs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scraping_configs
    ADD CONSTRAINT scraping_configs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: session_contexts session_contexts_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_contexts
    ADD CONSTRAINT session_contexts_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: session_documents session_documents_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_documents
    ADD CONSTRAINT session_documents_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: session_documents session_documents_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_documents
    ADD CONSTRAINT session_documents_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(session_id) ON DELETE CASCADE;


--
-- Name: teams teams_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: teams teams_team_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_team_lead_id_fkey FOREIGN KEY (team_lead_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: tool_usage_stats tool_usage_stats_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tool_usage_stats
    ADD CONSTRAINT tool_usage_stats_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: training_metrics training_metrics_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_metrics
    ADD CONSTRAINT training_metrics_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.finetuning_jobs(id) ON DELETE CASCADE;


--
-- Name: usage_metrics usage_metrics_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usage_metrics
    ADD CONSTRAINT usage_metrics_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_module_overrides user_module_overrides_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_module_overrides
    ADD CONSTRAINT user_module_overrides_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public.users(id);


--
-- Name: user_module_overrides user_module_overrides_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_module_overrides
    ADD CONSTRAINT user_module_overrides_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id) ON DELETE CASCADE;


--
-- Name: user_module_overrides user_module_overrides_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_module_overrides
    ADD CONSTRAINT user_module_overrides_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: user_roles user_roles_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_teams user_teams_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_teams
    ADD CONSTRAINT user_teams_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: user_teams user_teams_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_teams
    ADD CONSTRAINT user_teams_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE CASCADE;


--
-- Name: user_teams user_teams_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_teams
    ADD CONSTRAINT user_teams_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_default_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_default_project_id_fkey FOREIGN KEY (default_project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: users users_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: web_scrape_jobs web_scrape_jobs_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_scrape_jobs
    ADD CONSTRAINT web_scrape_jobs_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE SET NULL;


--
-- Name: web_scrape_jobs web_scrape_jobs_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_scrape_jobs
    ADD CONSTRAINT web_scrape_jobs_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: web_scrape_jobs web_scrape_jobs_scraped_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_scrape_jobs
    ADD CONSTRAINT web_scrape_jobs_scraped_by_fkey FOREIGN KEY (scraped_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict fgkzoRWGjtyMjI6hvbb7QJMscSEiN6V2ncG2Dh5AtBPwZxKxaJxlignZPqPOTge

