-- Migration: Add agent_tasks table for tracking agent task execution
-- Created: 2025-11-30
-- Description: Stores autonomous agent task execution details including progress, results, and artifacts

CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,  -- Human-readable task identifier

    -- Task details
    task_description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    session_id VARCHAR(255),
    model VARCHAR(100) NOT NULL DEFAULT 'qwen2.5-coder:7b',

    -- Configuration
    max_iterations INTEGER DEFAULT 20,
    timeout_seconds INTEGER DEFAULT 600,

    -- Progress tracking
    current_iteration INTEGER DEFAULT 0,
    current_phase VARCHAR(50),  -- THINK, PLAN, ACT, OBSERVE

    -- Execution details
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT,

    -- Results
    result TEXT,  -- Final answer or result
    artifacts TEXT[],  -- Array of generated artifact paths
    tools_used TEXT[],  -- Array of tools executed
    llm_calls INTEGER DEFAULT 0,

    -- Error handling
    error TEXT,
    error_details JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB,

    -- Project tracking (similar to other tables)
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    department VARCHAR(100),
    team VARCHAR(100)
);

-- Indexes for performance
CREATE INDEX idx_agent_tasks_task_id ON agent_tasks(task_id);
CREATE INDEX idx_agent_tasks_session_id ON agent_tasks(session_id);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX idx_agent_tasks_created_at ON agent_tasks(created_at);
CREATE INDEX idx_agent_tasks_project_id ON agent_tasks(project_id);
CREATE INDEX idx_agent_tasks_created_by ON agent_tasks(created_by);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_agent_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER agent_tasks_updated_at_trigger
    BEFORE UPDATE ON agent_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_tasks_updated_at();

-- Comments for documentation
COMMENT ON TABLE agent_tasks IS 'Tracks autonomous agent task execution with LLM integration';
COMMENT ON COLUMN agent_tasks.task_id IS 'Human-readable task identifier (e.g., task-abc123)';
COMMENT ON COLUMN agent_tasks.status IS 'Current task status: pending, running, completed, failed, cancelled';
COMMENT ON COLUMN agent_tasks.current_phase IS 'Current agentic loop phase: THINK, PLAN, ACT, OBSERVE';
COMMENT ON COLUMN agent_tasks.artifacts IS 'Array of file paths to generated artifacts';
COMMENT ON COLUMN agent_tasks.tools_used IS 'Array of tool names executed during task';
COMMENT ON COLUMN agent_tasks.llm_calls IS 'Number of LLM calls made during task execution';
