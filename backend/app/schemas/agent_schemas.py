"""
Pydantic schemas for Agent API

Defines request/response models for agent task management
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Agent task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTaskCreate(BaseModel):
    """Request to create a new agent task"""
    task_description: str = Field(..., description="Natural language task description")
    session_id: Optional[str] = Field(None, description="Session ID to associate with task")
    document_ids: Optional[List[str]] = Field(None, description="List of document IDs to mount in workspace (UUIDs)")
    max_iterations: Optional[int] = Field(20, description="Maximum agentic loop iterations")
    timeout_seconds: Optional[int] = Field(600, description="Task timeout in seconds")
    model: Optional[str] = Field("qwen2.5-coder:7b", description="LLM model to use")

    class Config:
        json_schema_extra = {
            "example": {
                "task_description": "Analyze the sales data in sales1.docx and create a visualization",
                "session_id": "session-123",
                "document_ids": ["3f204a1c-d21d-4dac-b6a8-44d80e8d1215"],
                "max_iterations": 15,
                "timeout_seconds": 300,
                "model": "qwen2.5-coder:7b"
            }
        }


class AgentTaskResponse(BaseModel):
    """Response after creating agent task"""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Task creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-abc123",
                "status": "pending",
                "message": "Task created and queued for execution",
                "created_at": "2025-11-30T10:00:00Z"
            }
        }


class AgentTaskStatusResponse(BaseModel):
    """Detailed task status response"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current status")
    task_description: str = Field(..., description="Original task description")
    session_id: Optional[str] = Field(None, description="Associated session ID")
    model: str = Field(..., description="LLM model being used")

    # Progress tracking
    current_iteration: Optional[int] = Field(None, description="Current iteration number")
    max_iterations: int = Field(..., description="Maximum iterations allowed")

    # Execution details
    started_at: Optional[datetime] = Field(None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    duration_seconds: Optional[float] = Field(None, description="Task duration in seconds")

    # Results
    result: Optional[str] = Field(None, description="Final result or answer")
    artifacts: List[str] = Field(default_factory=list, description="Generated artifacts (file paths)")
    tools_used: List[str] = Field(default_factory=list, description="Tools executed during task")
    llm_calls: Optional[int] = Field(None, description="Number of LLM calls made")

    # Error handling
    error: Optional[str] = Field(None, description="Error message if task failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")

    # Metadata
    created_at: datetime = Field(..., description="Task creation timestamp")
    meta_info: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    # 🆕 Storage path
    minio_base_path: Optional[str] = Field(None, description="MinIO base path for artifacts")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-abc123",
                "status": "completed",
                "task_description": "Analyze sales data",
                "session_id": "session-123",
                "model": "qwen2.5-coder:7b",
                "current_iteration": 3,
                "max_iterations": 20,
                "started_at": "2025-11-30T10:00:05Z",
                "completed_at": "2025-11-30T10:00:12Z",
                "duration_seconds": 7.5,
                "result": "Analysis complete. Found 5 key trends.",
                "artifacts": ["/artifacts/analysis_summary.txt", "/artifacts/chart.png"],
                "tools_used": ["analyze_dataframe", "visualize_data"],
                "llm_calls": 3,
                "error": None,
                "created_at": "2025-11-30T10:00:00Z"
            }
        }


class AgentTaskList(BaseModel):
    """List of agent tasks"""
    tasks: List[AgentTaskStatusResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of tasks per page")

    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [],
                "total": 42,
                "page": 1,
                "page_size": 50
            }
        }


class AgentTaskCancel(BaseModel):
    """Request to cancel a running task"""
    reason: Optional[str] = Field(None, description="Reason for cancellation")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "User requested cancellation"
            }
        }


class AgentTaskCancelResponse(BaseModel):
    """Response after cancelling a task"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="New task status")
    message: str = Field(..., description="Cancellation status message")
    cancelled_at: datetime = Field(..., description="Cancellation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-abc123",
                "status": "cancelled",
                "message": "Task successfully cancelled",
                "cancelled_at": "2025-11-30T10:05:00Z"
            }
        }


class AgentTaskProgress(BaseModel):
    """Real-time progress update (for WebSocket streaming)"""
    task_id: str = Field(..., description="Task identifier")
    iteration: int = Field(..., description="Current iteration number")
    phase: str = Field(..., description="Current phase (THINK, PLAN, ACT, OBSERVE)")
    message: str = Field(..., description="Progress message")
    timestamp: datetime = Field(..., description="Progress update timestamp")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional progress metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-abc123",
                "iteration": 2,
                "phase": "ACT",
                "message": "Executing tool: analyze_dataframe",
                "timestamp": "2025-11-30T10:00:08Z",
                "meta": {"tool": "analyze_dataframe", "args": {"file_path": "/workspace/data.csv"}}
            }
        }
