"""Multilingual Content Translator - Data Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class LanguageCode(str, Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    JAPANESE = "ja"
    ARABIC = "ar"
    HINDI = "hi"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"

class TranslationQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class ContentType(str, Enum):
    TEXT = "text"
    DOCUMENT = "document"
    TECHNICAL = "technical"
    MARKETING = "marketing"
    LEGAL = "legal"

class TranslateRequest(BaseModel):
    content_id: str
    source_language: LanguageCode
    target_languages: List[LanguageCode]
    content: str = Field(..., min_length=1, max_length=50000)
    content_type: ContentType = ContentType.TEXT
    preserve_formatting: bool = True

class TranslationResult(BaseModel):
    target_language: LanguageCode
    translated_content: str
    quality_score: float = Field(..., ge=0.0, le=100.0)
    quality_rating: TranslationQuality
    detected_issues: List[str]
    glossary_terms: Dict[str, str]
    confidence: float

class TranslateResponse(BaseModel):
    success: bool
    content_id: str
    source_language: LanguageCode
    translations: List[TranslationResult]
    total_characters: int
    processing_time_ms: float
    ai_insights: str

class SearchTranslationsRequest(BaseModel):
    content_ids: Optional[List[str]] = None
    source_language: Optional[LanguageCode] = None
    limit: int = Field(default=100, ge=1, le=1000)

class SearchTranslationsResponse(BaseModel):
    success: bool
    translations: List[Dict]
    total_count: int

class ExportTranslationsRequest(BaseModel):
    content_ids: List[str]
    format: str = Field(default="json", pattern="^(json|csv|tmx)$")

class ExportTranslationsResponse(BaseModel):
    success: bool
    export_data: Dict
    format: str

class TranslationStatsResponse(BaseModel):
    success: bool
    total_translations: int
    most_common_source_language: str
    most_common_target_language: str
    average_quality_score: float

class StatusResponse(BaseModel):
    success: bool
    status: str
    capabilities: List[str]
