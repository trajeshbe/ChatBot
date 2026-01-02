"""CRU POC - Data Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class CruRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict] = None

class CruResponse(BaseModel):
    success: bool
    session_id: str
    result: Dict
    insights: str
    recommendations: List[str]

class StatusResponse(BaseModel):
    success: bool
    status: str
    description: str
    tier_2_modules_used: List[str]
    capabilities: Optional[List[str]] = None

class QueryType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    TABLE_DATA = "table_data"

class SourceDocument(BaseModel):
    document_id: str
    document_name: str
    page: Optional[int]
    score: float
    snippet: str
