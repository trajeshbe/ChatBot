"""Multilingual Content Translator - Business Logic Service"""
import logging
import time
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .multilingual_translator_schemas import *

logger = logging.getLogger(__name__)

class MultilingualTranslatorService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService(db, settings)

        # Import DocumentService for extracting content from documents
        from app.tier_1.document_processing.document_service import DocumentService
        self.document_service = DocumentService(db, settings)

    async def translate_content(self, request: TranslateRequest) -> TranslateResponse:
        """Translate content into multiple target languages with quality assessment"""
        try:
            start_time = time.time()
            translations = []

            # Extract content from document if document_id provided
            content_to_translate = request.content
            if request.document_id:
                content_to_translate = await self._extract_document_content(request.document_id)

            for target_lang in request.target_languages:
                translation_result = await self._translate_to_language(
                    content=content_to_translate,
                    source_lang=request.source_language,
                    target_lang=target_lang,
                    content_type=request.content_type
                )
                translations.append(translation_result)

            processing_time = (time.time() - start_time) * 1000

            total_chars = len(content_to_translate)

            # Generate AI insights about translation quality
            prompt = f"""Analyze translation from {request.source_language.value} to {len(request.target_languages)} languages.
Content type: {request.content_type.value}. Length: {total_chars} chars.
Provide 2 sentences on translation challenges and recommendations."""

            insights = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3
            )

            return TranslateResponse(
                success=True,
                content_id=request.content_id,
                source_language=request.source_language,
                translations=translations,
                total_characters=total_chars,
                processing_time_ms=round(processing_time, 2),
                ai_insights=insights.strip()
            )

        except Exception as e:
            logger.error(f"Translation error: {e}", exc_info=True)
            raise

    async def _extract_document_content(self, document_id: str) -> str:
        """Extract text content from uploaded document"""
        try:
            chunks = await self.document_service.get_chunks_for_document(document_id)
            content = " ".join([chunk.get('content', '') for chunk in chunks])
            logger.info(f"Extracted {len(content)} characters from document {document_id}")
            return content
        except Exception as e:
            logger.error(f"Failed to extract document content: {e}")
            return ""

    async def _translate_to_language(
        self,
        content: str,
        source_lang: LanguageCode,
        target_lang: LanguageCode,
        content_type: ContentType
    ) -> TranslationResult:
        """Translate content to a single target language"""

        # Use LLM for actual translation
        translation_prompt = f"""Translate the following {content_type.value} content from {source_lang.value} to {target_lang.value}.
Preserve formatting and context. Provide only the translation without explanations.

Content:
{content[:2000]}"""  # Limit to 2000 chars for demo

        translated_text = await self.llm_service.generate_response(
            prompt=translation_prompt,
            model="gpt-4o-mini",
            temperature=0.3
        )

        # Quality assessment
        quality_score = self._assess_translation_quality(
            source=content,
            translation=translated_text,
            content_type=content_type
        )

        # Determine quality rating
        if quality_score >= 90:
            quality_rating = TranslationQuality.EXCELLENT
        elif quality_score >= 75:
            quality_rating = TranslationQuality.GOOD
        elif quality_score >= 60:
            quality_rating = TranslationQuality.FAIR
        else:
            quality_rating = TranslationQuality.POOR

        # Detect potential issues
        detected_issues = self._detect_translation_issues(
            source=content,
            translation=translated_text,
            source_lang=source_lang,
            target_lang=target_lang
        )

        # Extract glossary terms (key technical terms)
        glossary = self._extract_glossary_terms(content, content_type)

        return TranslationResult(
            target_language=target_lang,
            translated_content=translated_text.strip(),
            quality_score=round(quality_score, 2),
            quality_rating=quality_rating,
            detected_issues=detected_issues,
            glossary_terms=glossary,
            confidence=round(quality_score / 100, 2)
        )

    def _assess_translation_quality(
        self,
        source: str,
        translation: str,
        content_type: ContentType
    ) -> float:
        """Assess translation quality based on heuristics"""

        quality_score = 85.0  # Base score

        # Length ratio check (translations should be similar length)
        length_ratio = len(translation) / max(len(source), 1)
        if 0.7 <= length_ratio <= 1.5:
            quality_score += 10
        elif 0.5 <= length_ratio <= 2.0:
            quality_score += 5
        else:
            quality_score -= 10

        # Content type adjustments
        if content_type == ContentType.TECHNICAL:
            # Technical content requires higher precision
            if any(term in source.lower() for term in ["api", "function", "class", "method"]):
                quality_score -= 5  # More conservative for technical
        elif content_type == ContentType.LEGAL:
            # Legal content requires exact translation
            quality_score -= 5

        # Check if translation is not empty
        if len(translation.strip()) < 10:
            quality_score -= 20

        return min(100.0, max(0.0, quality_score))

    def _detect_translation_issues(
        self,
        source: str,
        translation: str,
        source_lang: LanguageCode,
        target_lang: LanguageCode
    ) -> List[str]:
        """Detect potential issues in translation"""

        issues = []

        # Check for extremely short translation
        if len(translation) < len(source) * 0.3:
            issues.append("Translation appears too short")

        # Check for extremely long translation
        if len(translation) > len(source) * 3:
            issues.append("Translation appears too long")

        # Check for untranslated technical terms (simple heuristic)
        source_words = set(source.lower().split())
        translation_words = set(translation.lower().split())
        common_words = source_words & translation_words

        if len(common_words) > len(source_words) * 0.7:
            issues.append("Many source words appear untranslated")

        # Language-specific checks
        if target_lang == LanguageCode.CHINESE and not any('\u4e00' <= char <= '\u9fff' for char in translation):
            issues.append("Translation does not contain Chinese characters")

        if target_lang == LanguageCode.ARABIC and not any('\u0600' <= char <= '\u06ff' for char in translation):
            issues.append("Translation does not contain Arabic characters")

        return issues[:3]  # Return top 3 issues

    def _extract_glossary_terms(self, content: str, content_type: ContentType) -> Dict[str, str]:
        """Extract key terms that should be in translation glossary"""

        glossary = {}

        # Technical terms
        if content_type == ContentType.TECHNICAL:
            technical_keywords = ["API", "database", "function", "class", "method", "server", "client"]
            for keyword in technical_keywords:
                if keyword.lower() in content.lower():
                    glossary[keyword] = f"{keyword} (preserve as-is)"

        # Marketing terms
        elif content_type == ContentType.MARKETING:
            marketing_keywords = ["brand", "campaign", "engagement", "conversion"]
            for keyword in marketing_keywords:
                if keyword.lower() in content.lower():
                    glossary[keyword] = f"{keyword} (context-aware translation)"

        return glossary

    async def search_translations(self, request: SearchTranslationsRequest) -> SearchTranslationsResponse:
        """Search historical translations"""
        # Placeholder implementation
        return SearchTranslationsResponse(
            success=True,
            translations=[],
            total_count=0
        )

    async def export_translations(self, request: ExportTranslationsRequest) -> ExportTranslationsResponse:
        """Export translations in specified format"""
        # Placeholder implementation
        export_data = {
            "format": request.format,
            "content_ids": request.content_ids,
            "exported_at": "2026-01-01T00:00:00Z"
        }

        return ExportTranslationsResponse(
            success=True,
            export_data=export_data,
            format=request.format
        )

    async def get_stats(self) -> TranslationStatsResponse:
        """Get translation statistics"""
        # Placeholder implementation
        return TranslationStatsResponse(
            success=True,
            total_translations=0,
            most_common_source_language="en",
            most_common_target_language="es",
            average_quality_score=0.0
        )

    async def get_status(self) -> StatusResponse:
        """Get service status and capabilities"""
        return StatusResponse(
            success=True,
            status="operational",
            capabilities=[
                "Multi-language Translation",
                "Quality Assessment",
                "Issue Detection",
                "Glossary Management",
                "10+ Languages Supported"
            ]
        )
