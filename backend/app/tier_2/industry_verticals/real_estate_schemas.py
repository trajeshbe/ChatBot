"""Real Estate Valuation AI - Data Schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class PropertyType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    LAND = "land"


class ValuationRequest(BaseModel):
    property_id: str
    property_type: PropertyType
    location: str
    square_footage: float = Field(..., gt=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    year_built: Optional[int] = None
    features: Optional[List[str]] = None


class ValuationResponse(BaseModel):
    success: bool
    property_id: str
    estimated_value: float
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    comparable_properties: List[Dict]
    market_trends: Dict[str, float]
    ai_insights: str


class SearchValuationsRequest(BaseModel):
    property_types: Optional[List[PropertyType]] = None
    limit: int = Field(default=100, ge=1, le=1000)


class SearchValuationsResponse(BaseModel):
    success: bool
    valuations: List[Dict]
    total_count: int


class ExportValuationsRequest(BaseModel):
    property_ids: List[str]
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")


class ExportValuationsResponse(BaseModel):
    success: bool
    export_data: Dict
    format: str


class ValuationStatsResponse(BaseModel):
    success: bool
    total_valuations: int
    average_property_value: float


class StatusResponse(BaseModel):
    success: bool
    status: str
    capabilities: List[str]
