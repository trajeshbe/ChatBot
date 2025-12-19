-- Add model approval workflow table
-- Migration: 022_add_model_approvals_table.sql
-- Date: 2025-12-19

-- Create model_approvals table for deployment governance
CREATE TABLE IF NOT EXISTS model_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES finetuned_models(id) ON DELETE CASCADE,

    -- Request details
    requested_by UUID REFERENCES users(id) ON DELETE SET NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    request_reason TEXT,

    -- Approval/rejection
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    review_comments TEXT,

    -- Deployment constraints (optional)
    deployment_environment VARCHAR(100),
    max_concurrent_instances INTEGER,
    resource_limits JSONB,

    -- Ensure valid status values
    CONSTRAINT check_approval_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_model_approvals_model_id ON model_approvals(model_id);
CREATE INDEX IF NOT EXISTS idx_model_approvals_status ON model_approvals(status);
CREATE INDEX IF NOT EXISTS idx_model_approvals_requested_by ON model_approvals(requested_by);
CREATE INDEX IF NOT EXISTS idx_model_approvals_approved_by ON model_approvals(approved_by);

-- Comments
COMMENT ON TABLE model_approvals IS 'Approval workflow for deploying fine-tuned models to production';
COMMENT ON COLUMN model_approvals.status IS 'Approval status: pending, approved, rejected';
COMMENT ON COLUMN model_approvals.deployment_environment IS 'Target environment: production, staging, development';
COMMENT ON COLUMN model_approvals.resource_limits IS 'JSON constraints: {"max_memory_gb": 16, "max_gpu_count": 1}';
