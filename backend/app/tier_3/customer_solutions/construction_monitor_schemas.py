"""Construction Monitor POC - Data Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class Construction_monitorRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict] = None

class Construction_monitorResponse(BaseModel):
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
