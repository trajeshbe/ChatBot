"""
Document Intelligence Module

AI-powered document data extraction for planning documents, architectural drawings, and construction files.

Features:
- 18-field structured extraction from PDF/DOCX/Images
- GPT-4o Vision for image-based documents
- Schema validation and export (CSV/JSON)
- Template-based and hybrid extraction

Leverages tier_1 services:
- tier_1.llm.llm_service (GPT-4, Claude)
- tier_1.document_processing.vision_service
- tier_1.document_processing.document_service
- tier_1.document_processing.ocr_service
- tier_1.data_extraction.hybrid_extraction_service
"""

__all__ = ["DocumentExtractionService"]
