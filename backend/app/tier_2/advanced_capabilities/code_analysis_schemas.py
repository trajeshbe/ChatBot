"""Code Analysis & Review AI - Data Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"

class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IssueCategory(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    BUG = "bug"
    CODE_SMELL = "code_smell"
    BEST_PRACTICE = "best_practice"

class AnalyzeCodeRequest(BaseModel):
    code_id: str
    language: ProgrammingLanguage
    code: str = Field(..., min_length=1, max_length=100000)
    check_security: bool = True
    check_performance: bool = True
    check_style: bool = True

class CodeIssue(BaseModel):
    line_number: int
    severity: IssueSeverity
    category: IssueCategory
    message: str
    suggested_fix: Optional[str] = None
    explanation: str

class CodeMetrics(BaseModel):
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    complexity_score: float = Field(..., ge=0.0, le=100.0)
    maintainability_index: float = Field(..., ge=0.0, le=100.0)
    estimated_technical_debt_hours: float

class AnalyzeCodeResponse(BaseModel):
    success: bool
    code_id: str
    language: ProgrammingLanguage
    issues: List[CodeIssue]
    metrics: CodeMetrics
    overall_quality_score: float = Field(..., ge=0.0, le=100.0)
    recommendations: List[str]
    ai_insights: str

class SearchAnalysesRequest(BaseModel):
    code_ids: Optional[List[str]] = None
    language: Optional[ProgrammingLanguage] = None
    limit: int = Field(default=100, ge=1, le=1000)

class SearchAnalysesResponse(BaseModel):
    success: bool
    analyses: List[Dict]
    total_count: int

class ExportAnalysesRequest(BaseModel):
    code_ids: List[str]
    format: str = Field(default="json", pattern="^(json|csv|html)$")

class ExportAnalysesResponse(BaseModel):
    success: bool
    export_data: Dict
    format: str

class CodeAnalysisStatsResponse(BaseModel):
    success: bool
    total_analyses: int
    most_common_language: str
    average_quality_score: float
    total_issues_found: int

class StatusResponse(BaseModel):
    success: bool
    status: str
    capabilities: List[str]
