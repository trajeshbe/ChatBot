-- Migration: Add project_id to chat_sessions
-- Purpose: Link chat sessions to projects for project-scoped conversations

-- Add project_id column to chat_sessions
ALTER TABLE chat_sessions
ADD COLUMN IF NOT EXISTS project_id UUID;

-- Add foreign key constraint
ALTER TABLE chat_sessions
ADD CONSTRAINT chat_sessions_project_id_fkey
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;

-- Add index for faster project-based queries
CREATE INDEX IF NOT EXISTS idx_chat_sessions_project ON chat_sessions(project_id);

-- Add comment for documentation
COMMENT ON COLUMN chat_sessions.project_id IS 'Links chat session to a specific project for scoped conversations';
