"""
API routes for template-based data extraction
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.template_extraction_service import (
    template_extraction_service,
    ExtractionField,
    ExtractionTemplate,
    get_screener_in_template
)
from app.models.database import WebScrapeJob
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/extract", tags=["Template Extraction"])


class ExtractFieldRequest(BaseModel):
    """Request model for defining extraction fields"""
    name: str
    selector: Optional[str] = None
    xpath: Optional[str] = None
    regex: Optional[str] = None
    attribute: Optional[str] = None
    data_type: str = "text"
    required: bool = False
    default_value: Optional[Any] = None


class ExtractTemplateRequest(BaseModel):
    """Request model for custom extraction template"""
    name: str
    description: str = ""
    url: str
    fields: List[ExtractFieldRequest]
    wait_for_selector: Optional[str] = None
    pagination_selector: Optional[str] = None
    max_pages: int = Field(default=1, ge=1, le=10)
    session_id: Optional[str] = None
    use_smart_mapping: bool = Field(
        default=False,
        description="Use LLM-based smart mapping instead of selectors (recommended if null values occur)"
    )


class ExtractPresetRequest(BaseModel):
    """Request model for using a preset template"""
    url: str
    preset: str = "screener_in"
    session_id: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Response model for extraction results"""
    success: bool
    url: str
    template_name: str
    data: List[Dict[str, Any]]
    row_count: int
    extracted_at: str
    session_id: Optional[str] = None
    error: Optional[str] = None


@router.post("/custom", response_model=ExtractionResponse)
async def extract_with_custom_template(
    request: ExtractTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract data from a URL using a custom template

    This endpoint allows you to define custom extraction rules to scrape
    structured data from any website.

    **New Feature:** Set `use_smart_mapping=true` to use LLM-based intelligent
    mapping instead of selectors. This is recommended if you're experiencing
    null values or want more flexible extraction that adapts to page changes.

    **Selector-based extraction (default):**
    - Fast and precise
    - Requires writing CSS/XPath selectors
    - Breaks when page structure changes

    **Smart mapping (use_smart_mapping=true):**
    - Uses AI to map data to template columns
    - No selectors needed
    - Adapts to page structure changes
    - Never hallucinates missing values
    - Clearly marks fields requiring additional research
    """
    try:
        # Check if smart mapping is requested
        if request.use_smart_mapping:
            logger.info(f"Using smart mapping for template: {request.name}")

            # Import required services
            from app.services.scraper_service import scraper_service
            from app.services.llm_service_enhanced import EnhancedLLMService
            from app.services.webscraper.extractors.llm_extractor import LLMExtractor

            # Step 1: Scrape the webpage
            scrape_result = await scraper_service.scrape_url(
                url=request.url,
                scrape_prompt=None
            )

            if not scrape_result:
                raise HTTPException(status_code=500, detail="Scraper returned None")

            scraped_data = scrape_result.get('html') or scrape_result.get('text', '')
            if not scraped_data:
                raise HTTPException(status_code=500, detail="Scraped content is empty")

            # Step 2: Extract template columns from fields
            template_columns = [f.name for f in request.fields]

            # Step 3: Map using LLM with dynamic model selection
            llm_service = EnhancedLLMService()
            await llm_service.initialize()
            extractor = LLMExtractor(llm_service=llm_service)

            mapping_result = await extractor.map_to_custom_template(
                scraped_data=scraped_data,
                template_columns=template_columns,
                template_examples=None,  # Could be enhanced to extract from default_value
                llm_provider=request.llm_provider,
                model_id=request.model_id
            )

            if not mapping_result:
                raise HTTPException(
                    status_code=500,
                    detail="Smart mapping failed. Check LLM service configuration."
                )

            mapped_data = mapping_result['mapped_data']
            missing_fields = mapping_result['missing_fields']

            logger.info(
                f"Smart mapping complete: {len(mapped_data) - len(missing_fields)}/{len(mapped_data)} fields extracted"
            )

            # Store scrape job
            job = WebScrapeJob(
                url=request.url,
                scrape_prompt=f"Smart template mapping: {request.name}",
                status="completed",
                completed_at=datetime.utcnow()
            )
            db.add(job)
            await db.commit()

            # Return result
            return ExtractionResponse(
                success=True,
                url=request.url,
                template_name=request.name,
                data=[mapped_data],
                row_count=1,
                extracted_at=datetime.utcnow().isoformat(),
                session_id=request.session_id,
                error=None
            )

        else:
            # Original selector-based extraction
            logger.info(f"Using selector-based extraction for template: {request.name}")

            # Convert request fields to ExtractionField objects
            fields = [
                ExtractionField(
                    name=f.name,
                    selector=f.selector,
                    xpath=f.xpath,
                    regex=f.regex,
                    attribute=f.attribute,
                    data_type=f.data_type,
                    required=f.required,
                    default_value=f.default_value
                )
                for f in request.fields
            ]

            # Create template
            template = ExtractionTemplate(
                name=request.name,
                description=request.description,
                fields=fields,
                wait_for_selector=request.wait_for_selector,
                pagination_selector=request.pagination_selector,
                max_pages=request.max_pages
            )

            # Extract data
            result = await template_extraction_service.extract_data(
                url=request.url,
                template=template,
                session_id=request.session_id
            )

            # Store scrape job in database
            if result['success']:
                job = WebScrapeJob(
                    url=request.url,
                    scrape_prompt=f"Template extraction: {template.name}",
                    status="completed",
                    completed_at=datetime.utcnow()
                )
                db.add(job)
                await db.commit()

            return ExtractionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in custom template extraction: {e}", exc_info=True)

        # Provide helpful error messages with suggestions
        error_msg = str(e)

        # Bot blocking / 403 errors
        if "403" in error_msg or "Forbidden" in error_msg or "blocking" in error_msg.lower():
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Website Blocking Detected",
                    "message": "The website is blocking automated access. Our system automatically tries different methods, but this site has strong anti-bot protection.",
                    "suggestions": [
                        "Try using Smart Extraction instead (uses AI to extract data)",
                        "Try the Template Mapper for custom column mapping",
                        "The site may require login or have CAPTCHA protection",
                        "Consider using a different page from the same website"
                    ],
                    "alternative_modes": ["smart", "mapper"],
                    "url": request.url
                }
            )

        # Timeout errors
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "Page Load Timeout",
                    "message": "The page took too long to load (exceeded 60 seconds).",
                    "suggestions": [
                        "The website may be slow or temporarily down - try again in a moment",
                        "Try a different page from the same website",
                        "Check if the website is accessible in your browser",
                        "The page may have heavy JavaScript that takes time to load"
                    ],
                    "alternative_modes": ["smart"],
                    "url": request.url
                }
            )

        # Selector not found errors
        elif "selector" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Data Extraction Failed",
                    "message": "Could not find the expected elements on the page. Check your CSS selectors or XPath expressions.",
                    "suggestions": [
                        "Try Smart Extraction (adapts to page changes automatically)",
                        "Verify your CSS selectors are correct using browser DevTools",
                        "The website layout may have changed",
                        "Try using wait_for_selector to ensure elements load first"
                    ],
                    "alternative_modes": ["smart", "mapper"],
                    "url": request.url
                }
            )

        # Network errors
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Network Error",
                    "message": "Unable to connect to the website.",
                    "suggestions": [
                        "Check your internet connection",
                        "The website may be temporarily down",
                        "Verify the URL is correct and accessible",
                        "Try again in a few moments"
                    ],
                    "url": request.url
                }
            )

        # Generic error
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Extraction Failed",
                    "message": f"An error occurred during extraction: {error_msg}",
                    "suggestions": [
                        "Try Smart Extraction for more flexible data extraction",
                        "Try the Template Mapper with custom columns",
                        "Check if the URL is correct and accessible",
                        "Verify your extraction template configuration",
                        "Contact support if the problem persists"
                    ],
                    "alternative_modes": ["smart", "mapper"],
                    "url": request.url
                }
            )


@router.post("/preset/{preset_name}", response_model=ExtractionResponse)
async def extract_with_preset_template(
    preset_name: str,
    request: ExtractPresetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract data from a URL using a preset template

    Available presets:
    - screener_in: Extract company financial data from Screener.in
    """
    try:
        # Get preset template
        if preset_name == "screener_in":
            template = get_screener_in_template()
        elif preset_name == "drenting":
            template = get_drenting_template()
        else:
            # Try to load from database (user-saved templates)
            from sqlalchemy import text

            query = text("""
                SELECT name, display_name, url_pattern, wait_for_selector, fields
                FROM saved_css_templates
                WHERE name = :template_name AND is_active = TRUE
            """)

            result = await db.execute(query, {"template_name": preset_name})
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"Preset template '{preset_name}' not found")

            # Check if template has CSS selectors or is AI-powered
            fields_data = row[4]  # fields column (JSONB)
            has_valid_selector = any(
                field.get("selector") and field.get("selector").strip() and field.get("selector") != "auto"
                for field in fields_data
            )

            # If template has no CSS selectors, route to ultra-smart extraction (AI-powered)
            if not has_valid_selector:
                logger.info(f"Template '{preset_name}' is AI-powered, routing to ultra-smart extraction")

                # Build user instructions from template fields
                field_names = [field.get("name") for field in fields_data if field.get("name")]
                user_instructions = f"Extract the following fields: {', '.join(field_names)}"

                # Use Ultra-Smart Extractor (same as ultra-smart endpoint)
                from app.services.webscraper.extractors.ultra_smart_extractor import UltraSmartExtractor
                from app.services.llm_service import llm_service
                from app.services.scraper_service import scraper_service
                from app.services.document_service import document_service

                # Initialize extractor
                ultra_extractor = UltraSmartExtractor(
                    llm_service=llm_service,
                    scraper_service=scraper_service,
                    document_service=document_service
                )

                # Extract data using extract_to_table (correct method name)
                result = await ultra_extractor.extract_to_table(
                    source=request.url,
                    source_type="url",
                    user_instructions=user_instructions,
                    llm_provider="openai",
                    vision_provider="openai"
                )

                # Store scrape job in database
                if result.get('success'):
                    job = WebScrapeJob(
                        url=request.url,
                        scrape_prompt=f"AI Template extraction: {preset_name} - {user_instructions}",
                        status="completed",
                        completed_at=datetime.utcnow()
                    )
                    db.add(job)
                    await db.commit()

                # Convert to ExtractionResponse format
                return ExtractionResponse(
                    success=result.get("success", False),
                    table=result.get("table", []),
                    columns=result.get("columns", []),
                    row_count=result.get("row_count", 0),
                    extraction_metadata=result.get("extraction_metadata", {}),
                    error=result.get("error")
                )

            # Convert database template to ExtractionTemplate format
            from app.services.template_extraction_service import ExtractionTemplate, FieldDefinition

            template_fields = []
            for field_data in fields_data:
                field_def = FieldDefinition(
                    name=field_data["name"],
                    selector=field_data.get("selector", ""),
                    data_type=field_data.get("data_type", "text"),
                    required=field_data.get("required", False),
                    regex=field_data.get("regex"),
                    xpath=field_data.get("xpath"),
                    attribute=field_data.get("attribute"),
                    default_value=field_data.get("default_value")
                )
                template_fields.append(field_def)

            template = ExtractionTemplate(
                name=row[0],  # name
                display_name=row[1],  # display_name
                url_pattern=row[2],  # url_pattern
                wait_for_selector=row[3],  # wait_for_selector
                fields=template_fields
            )

        # Extract data
        result = await template_extraction_service.extract_data(
            url=request.url,
            template=template,
            session_id=request.session_id
        )

        # Store scrape job in database
        if result['success']:
            job = WebScrapeJob(
                url=request.url,
                scrape_prompt=f"Template extraction: {template.name}",
                status="completed",
                completed_at=datetime.utcnow()
            )
            db.add(job)
            await db.commit()

        return ExtractionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in preset template extraction: {e}", exc_info=True)

        # Provide helpful error messages with suggestions
        error_msg = str(e)

        # Bot blocking / 403 errors
        if "403" in error_msg or "Forbidden" in error_msg or "blocking" in error_msg.lower():
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Website Blocking Detected",
                    "message": "The website is blocking automated access. Our system automatically tries different methods, but this site has strong anti-bot protection.",
                    "suggestions": [
                        "Try using Smart Extraction instead (uses AI to extract data)",
                        "Try the Template Mapper for custom column mapping",
                        "The site may require login or have CAPTCHA protection",
                        "Consider using a different page from the same website"
                    ],
                    "alternative_modes": ["smart", "mapper"],
                    "url": request.url
                }
            )

        # Timeout errors
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "Page Load Timeout",
                    "message": "The page took too long to load (exceeded 60 seconds).",
                    "suggestions": [
                        "The website may be slow or temporarily down - try again in a moment",
                        "Try a different page from the same website",
                        "Check if the website is accessible in your browser",
                        "The page may have heavy JavaScript that takes time to load"
                    ],
                    "alternative_modes": ["smart"],
                    "url": request.url
                }
            )

        # Selector not found errors
        elif "selector" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Data Extraction Failed",
                    "message": "Could not find the expected elements on the page. The page structure may have changed.",
                    "suggestions": [
                        "Try Smart Extraction (adapts to page changes automatically)",
                        "The website may have updated its layout",
                        "Verify the URL points to the correct page type",
                        "Check if the page loaded correctly in your browser"
                    ],
                    "alternative_modes": ["smart", "mapper"],
                    "url": request.url
                }
            )

        # Network errors
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Network Error",
                    "message": "Unable to connect to the website.",
                    "suggestions": [
                        "Check your internet connection",
                        "The website may be temporarily down",
                        "Verify the URL is correct and accessible",
                        "Try again in a few moments"
                    ],
                    "url": request.url
                }
            )

        # Generic error
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Extraction Failed",
                    "message": f"An error occurred during extraction: {error_msg}",
                    "suggestions": [
                        "Try Smart Extraction for more flexible data extraction",
                        "Try the Template Mapper with custom columns",
                        "Check if the URL is correct and accessible",
                        "Contact support if the problem persists"
                    ],
                    "alternative_modes": ["smart", "mapper"],
                    "url": request.url
                }
            )


@router.post("/to-excel")
async def export_extraction_to_excel(
    data: List[Dict[str, Any]],
    filename: str = "extracted_data.xlsx"
):
    """
    Export extracted data to Excel format

    Accepts a list of dictionaries and returns an Excel file.
    """
    try:
        # Log received data for diagnostics
        logger.info(f"Received Excel export request with {len(data) if data else 0} rows, filename: {filename}")
        logger.debug(f"First row of data: {data[0] if data and len(data) > 0 else 'No data'}")

        # Validate data
        if not data or len(data) == 0:
            logger.error("Empty data received in /to-excel endpoint")
            raise HTTPException(status_code=400, detail="No data provided for Excel export")

        # Generate Excel file
        excel_data = await template_extraction_service.export_to_excel(data, filename)

        # Return as streaming response
        return StreamingResponse(
            excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets")
async def list_preset_templates():
    """
    List all available preset templates
    """
    presets = [
        {
            "name": "screener_in",
            "display_name": "Screener.in Company Data",
            "description": "Extract financial metrics from Screener.in company pages",
            "fields": [
                "Company Name", "Market Cap", "Current Price", "Stock P/E",
                "Book Value", "Dividend Yield", "ROCE", "ROE", "Face Value",
                "Market Position", "Source / Notes"
            ]
        },
        {
            "name": "drenting",
            "display_name": "Drenting.com Car Listings",
            "description": "Extract car rental/leasing offers from Drenting.com",
            "fields": [
                "Car Model", "Monthly Price", "Year", "Source / Notes"
            ]
        }
    ]

    return {"presets": presets}


@router.get("/test")
async def test_template_extraction():
    """
    Test endpoint to verify template extraction service is working
    """
    return {
        "status": "ok",
        "service": "template_extraction",
        "message": "Template extraction service is ready"
    }


# ============================================================================
# Auto-Generation Endpoints (NEW)
# ============================================================================

class AutoGenerateTemplateRequest(BaseModel):
    """Request model for auto-generating templates"""
    url: str
    user_instructions: Optional[str] = Field(
        None,
        description="Natural language instructions for what data to extract. "
                   "E.g., 'Extract product names, prices, and ratings' or "
                   "'Get company financial metrics like revenue and profit'"
    )
    template_name: Optional[str] = None
    llm_provider: str = Field(default="openai", description="LLM provider: ollama, openai, or anthropic")
    max_fields: int = Field(default=15, ge=1, le=30, description="Maximum number of fields to generate")
    session_id: Optional[str] = None


class AutoGenerateResponse(BaseModel):
    """Response model for auto-generated template"""
    success: bool
    template: Optional[Dict[str, Any]] = None
    fields: Optional[List[Dict[str, Any]]] = None
    template_type: Optional[str] = None
    confidence: Optional[float] = None
    message: Optional[str] = None
    error: Optional[str] = None


class SmartExtractRequest(BaseModel):
    """Request model for smart extraction without predefined template"""
    url: str
    user_instructions: str = Field(
        ...,
        description="Describe what data you want to extract in natural language"
    )
    llm_provider: str = Field(default="openai")
    model_id: Optional[str] = Field(default="gpt-4-turbo", description="Specific model ID (e.g., gpt-4-turbo, gpt-4o, claude-3-opus-20240229)")
    output_format: str = Field(default="excel", description="Output format: excel, csv, or json")
    session_id: Optional[str] = None


@router.post("/auto-generate", response_model=AutoGenerateResponse)
async def auto_generate_template(
    request: AutoGenerateTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **AUTO-GENERATE EXTRACTION TEMPLATE (Feature #2)**

    Automatically generate an extraction template by analyzing a webpage with LLM.

    When you don't have a predefined Excel template, this endpoint uses AI to:
    1. Analyze the webpage structure and content
    2. Identify the best fields/columns to extract
    3. Determine optimal extraction strategies for each field
    4. Create a ready-to-use template

    **User Instructions (Feature #3):**
    Provide natural language guidance for what you want to extract:
    - "Extract product information including name, price, and reviews"
    - "Get company financial data like revenue, profit margin, and growth rate"
    - "Pull article metadata: title, author, date, and category"

    The LLM will analyze the page and create appropriate field mappings based on your instructions.

    **Example Usage:**
    ```json
    {
        "url": "https://example.com/products/laptop",
        "user_instructions": "Extract laptop specs: model name, processor, RAM, price, and customer rating",
        "llm_provider": "ollama",
        "max_fields": 10
    }
    ```

    **Response:**
    Returns the generated template with field definitions, extraction strategies,
    and validation rules. You can then use this template for extraction or refine it further.
    """
    try:
        # Import auto-generator service
        from app.services.webscraper.templates.template_auto_generator import TemplateAutoGenerator
        from app.services.llm_service import llm_service
        from app.services.scraper_service import scraper_service

        # Initialize auto-generator
        auto_gen = TemplateAutoGenerator(
            llm_service=llm_service,
            scraper_service=scraper_service
        )

        # Generate template
        logger.info(f"Auto-generating template for URL: {request.url}")
        if request.user_instructions:
            logger.info(f"User instructions: {request.user_instructions}")

        template = await auto_gen.analyze_webpage_and_generate_template(
            url=request.url,
            user_instructions=request.user_instructions,
            template_name=request.template_name,
            llm_provider=request.llm_provider,
            max_fields=request.max_fields
        )

        if not template:
            return AutoGenerateResponse(
                success=False,
                error="Failed to auto-generate template. This may be due to: "
                      "1) Website blocking automated access, "
                      "2) Invalid or unreachable URL, "
                      "3) Empty webpage content. "
                      "Please check the URL and try again."
            )

        # Format response
        fields_data = [
            {
                "name": f.name,
                "display_name": f.display_name,
                "description": f.description,
                "type": f.type,
                "required": f.required,
                "extraction_strategy": f.source_hint.type if f.source_hint else "unknown",
                "extraction_hint": (
                    f.source_hint.selector or
                    f.source_hint.xpath or
                    f.source_hint.pattern or
                    f.source_hint.prompt or
                    "N/A"
                ) if f.source_hint else "N/A"
            }
            for f in template.fields
        ]

        template_data = {
            "name": template.name,
            "description": template.description,
            "template_type": template.schema_definition.type,
            "fields_count": len(template.fields),
            "metadata": template.schema_definition.metadata
        }

        # Check if this was generated using fallback
        is_fallback = template.schema_definition.metadata.get('fallback', False)
        success_message = f"Successfully generated template with {len(template.fields)} fields"

        if is_fallback:
            success_message += " (using rule-based analysis). For AI-powered analysis, configure OpenAI API key."

        return AutoGenerateResponse(
            success=True,
            template=template_data,
            fields=fields_data,
            template_type=template.schema_definition.type,
            confidence=template.schema_definition.metadata.get('confidence', 0.8),
            message=success_message
        )

    except Exception as e:
        logger.error(f"Error in auto-generate template: {e}", exc_info=True)
        return AutoGenerateResponse(
            success=False,
            error=f"Auto-generation failed: {str(e)}"
        )


@router.post("/smart-extract", response_model=ExtractionResponse)
async def smart_extract_without_template(
    request: SmartExtractRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **SMART EXTRACTION WITHOUT PREDEFINED TEMPLATE (ENHANCED)**

    Extract data from a webpage using only natural language instructions - no template needed!

    This endpoint now uses **LLM-based mapping** for more reliable extraction:
    1. Auto-generates column names based on your instructions (or auto-detects if not specified)
    2. Scrapes the webpage content
    3. Uses AI to intelligently map scraped data to columns
    4. Returns the extracted data in your chosen format (Excel/CSV/JSON)

    **Two Modes of Operation:**

    **Mode 1: User Specifies Column Names**
    - Example: "Extract financial data and map to columns like Revenue (Annual), EBITDA, EBITDA Margin, Net Profit"
    - The system will extract those exact column names and map data to them

    **Mode 2: Auto-Generate Column Names**
    - Example: "Extract product information from this page"
    - The system will analyze the page and create appropriate column names automatically

    **How it works:**
    1. You provide a URL and describe what you want to extract
    2. If you specify column names, they're used; otherwise, AI auto-generates them
    3. Webpage is scraped
    4. AI maps scraped data to the columns (never hallucinates missing values)
    5. Results are returned in your preferred format

    **Example Usage - With Column Names:**
    ```json
    {
        "url": "https://www.screener.in/company/RELIANCE/",
        "user_instructions": "Extract financial data and map to columns like Market Cap, Stock P/E, ROE, ROCE",
        "llm_provider": "openai",
        "output_format": "excel"
    }
    ```

    **Example Usage - Auto Column Names:**
    ```json
    {
        "url": "https://example.com/products",
        "user_instructions": "Extract all product information from this page",
        "llm_provider": "openai",
        "output_format": "excel"
    }
    ```

    **Benefits:**
    - No need to create templates or write selectors
    - Natural language interface - just describe what you need
    - Intelligent field mapping using LLM (no selector failures)
    - Respects user-specified column names when provided
    - Auto-generates appropriate column names when not specified
    - Never hallucinates - marks missing fields clearly

    **Perfect for:**
    - One-time data extraction tasks
    - Exploring new websites
    - Quick data gathering without setup
    - Dynamic content that changes frequently
    """
    try:
        # Import Ultra-Smart Extractor and required services
        from app.services.webscraper.extractors.ultra_smart_extractor import UltraSmartExtractor
        from app.services.llm_service_enhanced import EnhancedLLMService
        from app.services.scraper_service import scraper_service

        logger.info(f"🚀 Ultra-Smart extraction from: {request.url}")
        logger.info(f"📝 Instructions: {request.user_instructions}")
        logger.info(f"🤖 Model: {request.model_id} (provider: {request.llm_provider})")

        # Initialize Enhanced LLM Service with dynamic model selection
        llm_service = EnhancedLLMService()
        await llm_service.initialize()

        # Initialize Ultra-Smart Extractor
        ultra_extractor = UltraSmartExtractor(
            llm_service=llm_service,
            scraper_service=scraper_service,
            document_service=None
        )

        # Use Ultra-Smart extractor with dynamic model selection
        result = await ultra_extractor.extract_from_any_source(
            source_type="url",
            source=request.url,
            user_instructions=request.user_instructions,
            llm_provider=request.llm_provider,
            model_id=request.model_id
        )

        if not result.get("success"):
            error_msg = result.get("error", "Ultra-Smart extraction failed")
            logger.error(f"❌ Extraction failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )

        # Extract the data
        extracted_table = result.get("table", [])
        if not extracted_table:
            logger.warning("⚠️ No data extracted")
            extracted_table = [{}]

        logger.info(f"✅ Extracted {len(extracted_table)} row(s) of data")

        # Store scrape job
        job = WebScrapeJob(
            url=request.url,
            scrape_prompt=f"Smart extraction: {request.user_instructions}",
            status="completed",
            completed_at=datetime.utcnow()
        )
        db.add(job)
        await db.commit()

        # Return response
        return ExtractionResponse(
            success=True,
            url=request.url,
            template_name="Ultra-Smart Extraction",
            data=extracted_table,
            row_count=len(extracted_table),
            extracted_at=datetime.utcnow().isoformat(),
            session_id=request.session_id,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart extract: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class SmartTemplateMapRequest(BaseModel):
    """Request model for smart template mapping"""
    url: str
    template_columns: List[str] = Field(
        ...,
        description="List of column headers from your custom Excel template"
    )
    template_examples: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional example values for each column to guide extraction"
    )
    llm_provider: str = Field(default="openai", description="LLM provider: openai, anthropic, or ollama")
    output_format: str = Field(default="excel", description="Output format: excel, csv, or json")
    session_id: Optional[str] = None


@router.post("/smart-map-to-template", response_model=ExtractionResponse)
async def smart_map_to_custom_template(
    request: SmartTemplateMapRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **SMART TEMPLATE MAPPING (NEW!)**

    Map scraped web data to your custom template columns using AI - no selectors needed!

    This is the NEW approach that solves the null value problem. It uses an improved
    LLM prompt that:
    - Never hallucinates values
    - Only extracts data that exists in the scraped content
    - Clearly marks missing fields as "— (requires additional research)"
    - Provides transparency about data completeness

    **How it works:**
    1. You provide a URL and your template columns
    2. We scrape the webpage
    3. AI intelligently maps scraped data to your template columns
    4. Missing fields are clearly marked
    5. Results exported in your preferred format

    **Example Usage:**
    ```json
    {
        "url": "https://www.screener.in/company/RELIANCE/",
        "template_columns": [
            "Company Name",
            "Market Cap",
            "Current Price",
            "Stock P/E",
            "Revenue Growth"
        ],
        "template_examples": {
            "Market Cap": "1234 Cr",
            "Stock P/E": "25.3"
        },
        "llm_provider": "openai",
        "output_format": "excel"
    }
    ```

    **Response:**
    Returns extracted data with clear indication of:
    - Successfully mapped fields
    - Fields marked as "— (requires additional research)"
    - List of missing fields

    **Benefits:**
    - No more null values in your data
    - Clear visibility of data completeness
    - No need to write CSS selectors or XPath
    - Works with any custom template structure
    - Handles variations in webpage structure
    """
    try:
        # Import required services
        from app.services.scraper_service import scraper_service
        from app.services.llm_service import llm_service
        from app.services.webscraper.extractors.llm_extractor import LLMExtractor

        logger.info(f"Smart template mapping from: {request.url}")
        logger.info(f"Template columns: {request.template_columns}")

        # Step 1: Scrape the webpage
        logger.info("Scraping webpage...")
        scrape_result = await scraper_service.scrape_url(
            url=request.url,
            scrape_prompt=None
        )

        if not scrape_result:
            logger.error("Scraper returned None")
            raise HTTPException(
                status_code=500,
                detail="Scraper returned None"
            )

        # Get scraped content (prefer HTML, fallback to text)
        scraped_data = scrape_result.get('html') or scrape_result.get('text', '')

        if not scraped_data:
            raise HTTPException(
                status_code=500,
                detail="Scraped content is empty"
            )

        logger.info(f"Successfully scraped {len(scraped_data)} characters")

        # Step 2: Initialize LLM extractor and map to template
        logger.info(f"Mapping to {len(request.template_columns)} template columns using {request.llm_provider}...")

        await llm_service.initialize()
        extractor = LLMExtractor(llm_service=llm_service)

        mapping_result = await extractor.map_to_custom_template(
            scraped_data=scraped_data,
            template_columns=request.template_columns,
            template_examples=request.template_examples,
            llm_provider=request.llm_provider
        )

        if not mapping_result:
            raise HTTPException(
                status_code=500,
                detail="Template mapping failed. Check LLM service configuration and logs."
            )

        mapped_data = mapping_result['mapped_data']
        missing_fields = mapping_result['missing_fields']
        extraction_complete = mapping_result['extraction_complete']

        logger.info(
            f"Mapping complete: {len(mapped_data) - len(missing_fields)}/{len(mapped_data)} fields extracted. "
            f"Missing: {missing_fields}"
        )

        # Step 3: Create response with single row of data
        data_row = mapped_data

        # Store scrape job
        job = WebScrapeJob(
            url=request.url,
            scrape_prompt=f"Smart template mapping: {', '.join(request.template_columns)}",
            status="completed",
            completed_at=datetime.utcnow()
        )
        db.add(job)
        await db.commit()

        # Return response
        return ExtractionResponse(
            success=True,
            url=request.url,
            template_name="Smart Template Mapping",
            data=[data_row],  # Single row
            row_count=1,
            extracted_at=datetime.utcnow().isoformat(),
            session_id=request.session_id,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart template mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class RefineTemplateRequest(BaseModel):
    """Request model for refining templates"""
    template_id: Optional[str] = None
    template_json: Optional[Dict[str, Any]] = None
    user_feedback: str = Field(
        ...,
        description="Feedback for refining the template. "
                   "E.g., 'Add a field for product ratings' or "
                   "'Change the price extraction to use the sale price instead'"
    )
    sample_url: str
    llm_provider: str = Field(default="openai")


@router.post("/refine-template")
async def refine_template_with_feedback(
    request: RefineTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **REFINE TEMPLATE WITH USER FEEDBACK**

    Improve an existing template based on natural language feedback.

    This allows iterative refinement of templates:
    - Add new fields
    - Remove unwanted fields
    - Modify extraction strategies
    - Adjust data types

    **Example Usage:**
    ```json
    {
        "template_json": { ... existing template ... },
        "user_feedback": "The price field should extract the discounted price, not the original price. Also add a field for product availability.",
        "sample_url": "https://example.com/product/123",
        "llm_provider": "ollama"
    }
    ```
    """
    try:
        # Implementation would refine the template based on feedback
        # This is a placeholder for the refinement logic
        return {
            "success": True,
            "message": "Template refinement is in development"
        }

    except Exception as e:
        logger.error(f"Error refining template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# SAVED CSS TEMPLATES MANAGEMENT
# ========================================

class SavedCSSTemplateRequest(BaseModel):
    """Request model for saving a CSS template"""
    template_name: str = Field(..., description="Internal name (lowercase_with_underscores)")
    display_name: str = Field(..., description="User-friendly name shown in dropdown")
    description: Optional[str] = Field(None, description="Brief description of what this template extracts")
    url_pattern: Optional[str] = Field(None, description="URL pattern for auto-detection (e.g., 'drenting.com/*')")
    wait_for_selector: str = Field(..., description="CSS selector to wait for before extraction")
    fields: List[ExtractFieldRequest] = Field(..., description="List of extraction fields with selectors")
    pagination_selector: Optional[str] = Field(None, description="CSS selector for pagination")
    max_pages: int = Field(default=1, ge=1, le=10)


class SavedCSSTemplateResponse(BaseModel):
    """Response model for saved CSS template"""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    url_pattern: Optional[str]
    fields: List[Dict[str, Any]]
    use_count: int
    created_at: str
    is_active: bool


@router.post("/save-template")
async def save_css_template(
    request: SavedCSSTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **SAVE CSS TEMPLATE**

    Save a successful extraction as a reusable CSS selector template.

    This allows users to dynamically create templates from the UI without
    needing to write code. The saved template will appear in the preset
    dropdown alongside built-in templates.

    **Example Usage:**
    ```json
    {
        "template_name": "my_website",
        "display_name": "My Website Data",
        "description": "Extract products from mysite.com",
        "url_pattern": "mysite.com/products/*",
        "wait_for_selector": ".product-card",
        "fields": [
            {
                "name": "Product Name",
                "selector": "h2.title",
                "data_type": "text",
                "required": true
            },
            {
                "name": "Price",
                "selector": "span.price",
                "data_type": "text",
                "required": false
            }
        ]
    }
    ```
    """
    try:
        from sqlalchemy import text

        # Validate template name is unique
        result = await db.execute(
            text("SELECT id FROM saved_css_templates WHERE name = :name"),
            {"name": request.template_name}
        )
        existing = result.fetchone()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"A template with name '{request.template_name}' already exists. Please use a different name."
            )

        # Convert fields to JSONB format
        fields_json = [
            {
                "name": f.name,
                "selector": f.selector,
                "xpath": f.xpath,
                "regex": f.regex,
                "attribute": f.attribute,
                "data_type": f.data_type,
                "required": f.required,
                "default_value": f.default_value
            }
            for f in request.fields
        ]

        # Insert new template
        insert_query = text("""
            INSERT INTO saved_css_templates (
                name, display_name, description, url_pattern,
                wait_for_selector, fields, pagination_selector, max_pages
            )
            VALUES (
                :name, :display_name, :description, :url_pattern,
                :wait_for_selector, :fields, :pagination_selector, :max_pages
            )
            RETURNING id, created_at
        """)

        result = await db.execute(
            insert_query,
            {
                "name": request.template_name,
                "display_name": request.display_name,
                "description": request.description,
                "url_pattern": request.url_pattern,
                "wait_for_selector": request.wait_for_selector,
                "fields": json.dumps(fields_json),
                "pagination_selector": request.pagination_selector,
                "max_pages": request.max_pages
            }
        )
        await db.commit()

        row = result.fetchone()
        template_id = str(row[0])
        created_at = row[1].isoformat()

        logger.info(f"Saved CSS template '{request.template_name}' with ID {template_id}")

        return {
            "success": True,
            "template_id": template_id,
            "name": request.template_name,
            "display_name": request.display_name,
            "created_at": created_at,
            "message": f"Template '{request.display_name}' saved successfully! It's now available in the preset dropdown."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving CSS template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved-templates")
async def list_all_templates(
    db: AsyncSession = Depends(get_db)
):
    """
    **LIST ALL CSS TEMPLATES**

    Returns both built-in preset templates and user-saved CSS templates.

    This endpoint merges:
    - Built-in presets (screener_in, drenting, etc.)
    - User-saved templates from database

    Used by frontend to populate the template dropdown.
    """
    try:
        from sqlalchemy import text

        # Get built-in presets
        from app.services.template_extraction_service import get_screener_in_template, get_drenting_template

        builtin_presets = [
            {
                "name": "screener_in",
                "display_name": "Screener.in Company Data",
                "description": "Extract financial metrics from Screener.in company pages",
                "fields": ["Company Name", "Market Cap", "Current Price", "Stock P/E", "Book Value", "Dividend Yield", "ROCE", "ROE", "Face Value", "Price to Book", "Debt to Equity"],
                "source": "builtin",
                "is_active": True,
                "has_css_selectors": True  # Built-in templates always have CSS selectors
            },
            {
                "name": "drenting",
                "display_name": "Drenting.com Car Listings",
                "description": "Extract car rental/leasing offers from Drenting.com",
                "fields": ["Car Model", "Monthly Price", "Year", "Source / Notes"],
                "source": "builtin",
                "is_active": True,
                "has_css_selectors": True  # Built-in templates always have CSS selectors
            }
        ]

        # Get user-saved templates
        query = text("""
            SELECT id, name, display_name, description, url_pattern,
                   fields, use_count, created_at, is_active
            FROM saved_css_templates
            WHERE is_active = TRUE
            ORDER BY use_count DESC, created_at DESC
        """)

        result = await db.execute(query)
        rows = result.fetchall()

        saved_templates = []
        for row in rows:
            fields_json = row[5]  # fields column
            field_names = [f["name"] for f in fields_json]

            # Check if template has at least one non-empty CSS selector
            has_css_selectors = any(
                f.get("selector") and f.get("selector").strip()
                for f in fields_json
            )

            saved_templates.append({
                "id": str(row[0]),
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "url_pattern": row[4],
                "fields": field_names,
                "use_count": row[6],
                "created_at": row[7].isoformat(),
                "source": "user_saved",
                "is_active": row[8],
                "has_css_selectors": has_css_selectors  # NEW: Flag for frontend filtering
            })

        # Merge and return
        all_templates = builtin_presets + saved_templates

        return {
            "templates": all_templates,
            "total_count": len(all_templates),
            "builtin_count": len(builtin_presets),
            "saved_count": len(saved_templates)
        }

    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/saved-templates/{template_id}")
async def delete_saved_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **DELETE SAVED CSS TEMPLATE**

    Soft-delete a user-saved template (sets is_active = FALSE).

    Built-in presets cannot be deleted.
    """
    try:
        from sqlalchemy import text

        # Soft delete (set is_active = FALSE)
        query = text("""
            UPDATE saved_css_templates
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = :template_id
            RETURNING name, display_name
        """)

        result = await db.execute(query, {"template_id": template_id})
        await db.commit()

        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")

        logger.info(f"Deleted CSS template '{row[1]}' (ID: {template_id})")

        return {
            "success": True,
            "message": f"Template '{row[1]}' deleted successfully",
            "template_name": row[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Save Extracted Data to Vector DB & MinIO
# ==========================================

class SaveToDBRequest(BaseModel):
    """Request to save extracted data to vector store and MinIO"""
    company_name: str = Field(..., description="Company/folder name for organization")
    source_url: str = Field(..., description="Source URL where data was extracted from")
    extraction_type: str = Field(..., description="Type of extraction: css_selector, smart, mapper")
    data: List[Dict[str, Any]] = Field(..., description="Extracted data rows")
    template_name: Optional[str] = Field(None, description="Template name used (if any)")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")


@router.post("/save-to-db")
async def save_extracted_data_to_db(
    request: SaveToDBRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Save extracted data to PostgreSQL vector store and MinIO for RAG consumption.

    This endpoint:
    1. Converts JSON data to text chunks
    2. Generates embeddings using the embedding service
    3. Stores vectors in PostgreSQL with company metadata
    4. Stores raw JSON in MinIO organized by company folders

    Example:
        POST /api/v1/extract/save-to-db
        {
            "company_name": "Reliance Industries",
            "source_url": "https://www.screener.in/company/RELIANCE/",
            "extraction_type": "css_selector",
            "data": [
                {"Company Name": "Reliance", "Market Cap": "18,00,000 Cr", ...}
            ],
            "template_name": "screener_in",
            "session_id": "abc123"
        }
    """
    try:
        from app.models.database import Document, DocumentChunk
        from app.services.embedding_service import embedding_service
        from app.services.document_service import document_service
        from sqlalchemy import text
        from datetime import datetime
        import uuid as uuid_lib
        import io

        # Validate input
        if not request.data or len(request.data) == 0:
            raise HTTPException(status_code=400, detail="No data provided to save")

        # Initialize document service (for MinIO access)
        await document_service.initialize()

        # Create a sanitized company folder name
        company_folder = request.company_name.lower().replace(' ', '_').replace('/', '_')

        # Generate unique identifier for this extraction
        extraction_id = str(uuid_lib.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Create filename for MinIO
        json_filename = f"{timestamp}_{extraction_id}.json"
        minio_path = f"extractions/{company_folder}/{json_filename}"

        # Prepare JSON data for MinIO
        json_data = {
            "extraction_id": extraction_id,
            "company_name": request.company_name,
            "source_url": request.source_url,
            "extraction_type": request.extraction_type,
            "template_name": request.template_name,
            "extracted_at": datetime.utcnow().isoformat(),
            "row_count": len(request.data),
            "data": request.data
        }
        json_bytes = json.dumps(json_data, indent=2, ensure_ascii=False).encode('utf-8')

        # Upload JSON to MinIO
        logger.info(f"📦 Uploading extraction data to MinIO: {minio_path}")
        from app.core.config import settings
        document_service.minio_client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=minio_path,
            data=io.BytesIO(json_bytes),
            length=len(json_bytes),
            content_type="application/json"
        )
        logger.info(f"✅ Uploaded to MinIO: {minio_path}")

        # Create document record
        document_record = Document(
            id=uuid_lib.UUID(extraction_id),
            filename=f"{request.company_name} - {request.extraction_type}",
            file_path=minio_path,
            file_type="application/json",
            file_size=len(json_bytes),
            source_type="extraction",
            source_url=request.source_url,
            meta_info={
                "company_name": request.company_name,
                "extraction_type": request.extraction_type,
                "template_name": request.template_name,
                "row_count": len(request.data),
                "session_id": request.session_id
            },
            processed=False
        )
        db.add(document_record)
        await db.flush()

        logger.info(f"📄 Created document record: {extraction_id}")

        # Convert JSON rows to text chunks
        text_chunks = []
        for idx, row in enumerate(request.data):
            # Convert each row to readable text
            row_text_parts = [
                f"Company: {request.company_name}",
                f"Source: {request.source_url}",
                f"Extraction Type: {request.extraction_type}",
                ""
            ]

            # Add all field-value pairs
            for key, value in row.items():
                row_text_parts.append(f"{key}: {value}")

            row_text = "\n".join(row_text_parts)
            text_chunks.append({
                "content": row_text,
                "row_index": idx,
                "row_data": row
            })

        logger.info(f"📝 Created {len(text_chunks)} text chunks from data")

        # Generate embeddings for all chunks
        chunk_texts = [chunk["content"] for chunk in text_chunks]
        logger.info(f"🔢 Generating embeddings for {len(chunk_texts)} chunks...")
        embeddings = await embedding_service.get_embeddings_batch(chunk_texts)

        if not embeddings or len(embeddings) != len(chunk_texts):
            raise ValueError(f"Expected {len(chunk_texts)} embeddings, got {len(embeddings)}")

        if embeddings and len(embeddings[0]) != 384:
            raise ValueError(f"Expected 384-dimensional embeddings, got {len(embeddings[0])}")

        logger.info(f"✅ Generated {len(embeddings)} embeddings (384 dimensions)")

        # Create chunk records with embeddings
        document_chunks = []
        for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
            chunk_record = DocumentChunk(
                document_id=uuid_lib.UUID(extraction_id),
                chunk_index=i,
                content=chunk["content"],
                embedding=embedding,
                meta_info={
                    "company_name": request.company_name,
                    "source": request.source_url,
                    "source_type": "extraction",
                    "extraction_type": request.extraction_type,
                    "template_name": request.template_name,
                    "row_index": chunk["row_index"],
                    "row_data": chunk["row_data"]
                }
            )
            db.add(chunk_record)
            document_chunks.append(chunk_record)

        # Mark document as processed
        document_record.processed = True

        # Commit all changes
        await db.commit()

        logger.info(f"✅ Saved {len(document_chunks)} chunks to PostgreSQL vector store")

        return {
            "success": True,
            "extraction_id": extraction_id,
            "company_name": request.company_name,
            "minio_path": minio_path,
            "chunks_created": len(document_chunks),
            "embeddings_generated": len(embeddings),
            "message": f"Successfully saved {len(request.data)} rows from {request.company_name} to vector store and MinIO",
            "rag_ready": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving extraction to DB: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save extraction to database: {str(e)}"
        )


# ============================================================================
# 🚀 ULTRA-SMART EXTRACTION - Extract ANYTHING to Tabular Format
# ============================================================================

class UltraSmartExtractRequest(BaseModel):
    """Request model for Ultra-Smart Extraction"""
    url: Optional[str] = Field(None, description="URL to extract from (for web pages)")
    user_instructions: Optional[str] = Field(
        None,
        description="Natural language instructions (e.g., 'Extract Mayor and Deputy Mayor')"
    )
    source_type: str = Field(
        default="auto",
        description="Source type: 'auto', 'url', 'pdf', 'image', 'docx', 'pptx', 'text'"
    )
    llm_provider: str = Field(default="openai", description="LLM provider: openai, anthropic, ollama")
    model_id: Optional[str] = Field(default="gpt-4-turbo", description="Specific model ID (e.g., gpt-4-turbo, gpt-4o, claude-3-opus-20240229)")
    vision_provider: str = Field(default="openai", description="Vision model: openai, anthropic")
    session_id: Optional[str] = None


class UltraSmartExtractResponse(BaseModel):
    """Response model for Ultra-Smart Extraction"""
    success: bool
    table: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted data as tabular rows")
    columns: List[str] = Field(default_factory=list, description="Column names")
    row_count: int = Field(default=0, description="Number of rows extracted")
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


@router.post("/ultra-smart", response_model=UltraSmartExtractResponse)
async def ultra_smart_extract(
    request: UltraSmartExtractRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    🎯 **ULTRA-SMART EXTRACTION - Extract ANY Random Content to Tabular Format**

    This is the ultimate "throw anything at it" endpoint that GUARANTEES structured tabular output.

    **Goal:** Handle ANY random content (web pages, PDFs, images, Word docs, PPTs, text)
    and ALWAYS return clean, structured tabular data.

    **Supported Inputs:**
    - 🌐 **Web Pages** (URL): Any website → Structured table
    - 📄 **PDFs**: Reports, invoices, documents → Structured table
    - 🖼️ **Images**: Screenshots, photos, scans → Structured table (via GPT-4V/Claude Vision)
    - 📝 **DOCX**: Word documents → Structured table
    - 📊 **PPTX**: PowerPoint slides → Structured table
    - 📃 **Plain Text**: Any text → Structured table
    - ❓ **Unknown**: Auto-detects and handles → Structured table

    **Technologies Used:**
    - **Docling**: Advanced PDF/DOCX/PPTX processing (better than PyPDF2)
    - **GPT-4 Vision / Claude Vision**: Analyze images and extract data
    - **Playwright**: Web scraping with bot protection bypass
    - **OpenAI/Anthropic LLMs**: Intelligent field extraction

    **Key Features:**
    - ✅ Auto-detects content type
    - ✅ Multi-modal (text + images + documents)
    - ✅ ALWAYS returns tabular format
    - ✅ Never hallucinates (marks missing data as "—")
    - ✅ Handles complex documents with embedded images
    - ✅ Intelligent fallback chains

    **Example Usage - Web Page:**
    ```json
    {
      "url": "https://en.wikipedia.org/wiki/India",
      "user_instructions": "Extract population, capital, and area",
      "source_type": "url",
      "llm_provider": "openai"
    }
    ```

    **Example Usage - PDF (via file upload - see /ultra-smart-file endpoint):**
    Upload a PDF of annual report, and it extracts revenue, profit, EBITDA into a table.

    **Response Format:**
    ```json
    {
      "success": true,
      "table": [
        {"Population": "1.4 billion", "Capital": "New Delhi", "Area": "3.287 million km²"}
      ],
      "columns": ["Population", "Capital", "Area"],
      "row_count": 1,
      "extraction_metadata": {
        "source_type": "url",
        "extraction_method": "playwright+openai"
      }
    }
    ```

    **Perfect For:**
    - Quick data extraction without manual configuration
    - Exploring new data sources
    - One-time extraction tasks
    - Dynamic content that changes frequently
    - Research and data gathering
    """
    try:
        logger.info("="*80)
        logger.info("🚀 ULTRA-SMART EXTRACTION REQUEST")
        logger.info(f"📍 URL: {request.url}")
        logger.info(f"📋 Instructions: {request.user_instructions}")
        logger.info(f"🎯 Source Type: {request.source_type}")
        logger.info(f"🤖 LLM: {request.llm_provider}, Vision: {request.vision_provider}")
        logger.info("="*80)

        # Import Ultra-Smart Extractor
        from app.services.webscraper.extractors.ultra_smart_extractor import UltraSmartExtractor
        from app.services.llm_service import llm_service
        from app.services.scraper_service import scraper_service
        from app.services.document_service import document_service

        # Initialize extractor
        ultra_extractor = UltraSmartExtractor(
            llm_service=llm_service,
            scraper_service=scraper_service,
            document_service=document_service
        )

        # Validate input
        if not request.url:
            return UltraSmartExtractResponse(
                success=False,
                error="URL is required for Ultra-Smart extraction"
            )

        # Extract to table (guarantees tabular output)
        result = await ultra_extractor.extract_to_table(
            source=request.url,
            source_type=request.source_type,
            user_instructions=request.user_instructions,
            llm_provider=request.llm_provider,
            vision_provider=request.vision_provider
        )

        logger.info(f"✅ Ultra-Smart extraction complete: {result.get('row_count', 0)} rows extracted")

        return UltraSmartExtractResponse(
            success=result.get("success", False),
            table=result.get("table", []),
            columns=result.get("columns", []),
            row_count=result.get("row_count", 0),
            extraction_metadata=result.get("extraction_metadata", {}),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"❌ Ultra-Smart extraction failed: {str(e)}", exc_info=True)
        return UltraSmartExtractResponse(
            success=False,
            error=str(e)
        )


# ====================================================================================================
# 🧭 ULTRA-SMART NAVIGATION EXTRACTION - Complex Website Traversal
# ====================================================================================================

class NavigationAction(BaseModel):
    """Single navigation action"""
    type: str = Field(..., description="Action type: click, scroll, wait, input, pagination, wait_for_load")
    selector: Optional[str] = Field(None, description="CSS selector for click/wait/input actions")
    value: Optional[str] = Field(None, description="Value for input action")
    direction: Optional[str] = Field(None, description="Scroll direction: up/down")
    amount: Optional[Union[int, str]] = Field(None, description="Scroll amount in pixels or 'bottom'")
    timeout: Optional[int] = Field(None, description="Timeout in milliseconds")
    next_selector: Optional[str] = Field(None, description="Next button selector for pagination")
    max_pages: Optional[int] = Field(None, description="Max pages for pagination")


class NavigationConfig(BaseModel):
    """Configuration for complex website navigation"""
    actions: List[NavigationAction] = Field(
        default_factory=list,
        description="Sequence of navigation actions to perform"
    )
    wait_for_load: bool = Field(
        default=True,
        description="Wait for page load after each action"
    )
    scroll_to_bottom: bool = Field(
        default=False,
        description="Auto-scroll to bottom to load lazy content"
    )
    extract_per_page: bool = Field(
        default=False,
        description="Extract data after each action"
    )


class NavigationExtractRequest(BaseModel):
    """Request model for Navigation-based Extraction"""
    url: str = Field(..., description="Starting URL to extract from")
    user_instructions: str = Field(..., description="What to extract (e.g., 'Extract product names and prices')")
    navigation_config: Optional[NavigationConfig] = Field(
        None,
        description="Navigation configuration with actions"
    )
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: openai, anthropic, ollama"
    )
    max_pages: int = Field(
        default=10,
        description="Maximum pages to traverse (safety limit)"
    )
    session_id: Optional[str] = None


class NavigationExtractResponse(BaseModel):
    """Response model for Navigation-based Extraction"""
    success: bool
    table: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted data as tabular rows")
    columns: List[str] = Field(default_factory=list, description="Column names")
    row_count: int = Field(default=0, description="Number of rows extracted")
    pages_visited: int = Field(default=0, description="Number of pages visited")
    navigation_log: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Log of navigation actions performed"
    )
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


@router.post("/ultra-smart-navigation", response_model=NavigationExtractResponse)
async def ultra_smart_navigation_extract(
    request: NavigationExtractRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    🧭 **ULTRA-SMART NAVIGATION EXTRACTION - Complex Website Traversal**

    Extract data from complex websites that require navigation, clicking, scrolling, or pagination.

    **Capabilities:**
    - 🖱️ Click buttons, links, form elements
    - 📜 Scroll to load dynamic content
    - 📄 Handle pagination (next/previous buttons)
    - ⌨️ Fill forms and submit searches
    - ⏳ Wait for dynamic elements to load
    - 🔄 Traverse multiple pages automatically

    **Use Cases:**
    - Product listings with pagination
    - Search results across multiple pages
    - Dynamic content loaded on scroll
    - Interactive forms and filters
    - Multi-step navigation flows

    **Example - Simple Pagination:**
    ```json
    {
      "url": "https://example.com/products",
      "user_instructions": "Extract product name, price, rating",
      "navigation_config": {
        "actions": [
          {
            "type": "pagination",
            "next_selector": ".next-page",
            "max_pages": 5
          }
        ]
      }
    }
    ```

    **Example - Complex Interaction:**
    ```json
    {
      "url": "https://example.com/search",
      "user_instructions": "Extract all search results",
      "navigation_config": {
        "actions": [
          {"type": "input", "selector": "#search", "value": "laptop"},
          {"type": "click", "selector": "#search-button"},
          {"type": "wait", "selector": ".results", "timeout": 3000},
          {"type": "scroll", "direction": "down", "amount": "bottom"}
        ],
        "extract_per_page": true
      }
    }
    ```

    **Example - Lazy Loading:**
    ```json
    {
      "url": "https://example.com/infinite-scroll",
      "user_instructions": "Extract all items",
      "navigation_config": {
        "scroll_to_bottom": true
      }
    }
    ```
    """
    try:
        logger.info("="*80)
        logger.info("🧭 ULTRA-SMART NAVIGATION EXTRACTION REQUEST")
        logger.info("="*80)
        logger.info(f"🌐 URL: {request.url}")
        logger.info(f"📋 Instructions: {request.user_instructions}")
        logger.info(f"📄 Max Pages: {request.max_pages}")
        logger.info(f"🤖 LLM Provider: {request.llm_provider}")
        if request.navigation_config:
            logger.info(f"🔧 Actions: {len(request.navigation_config.actions)} configured")
        logger.info("="*80)

        # Import Ultra-Smart Extractor and services
        from app.services.webscraper.extractors.ultra_smart_extractor import UltraSmartExtractor
        from app.services.llm_service import llm_service
        from app.services.scraper_service import scraper_service

        # Initialize ultra-smart extractor
        ultra_extractor = UltraSmartExtractor(
            llm_service=llm_service,
            scraper_service=scraper_service,
            document_service=None  # Not needed for navigation
        )

        # Convert navigation_config to dict if provided
        navigation_config_dict = None
        if request.navigation_config:
            navigation_config_dict = {
                "actions": [action.dict() for action in request.navigation_config.actions],
                "wait_for_load": request.navigation_config.wait_for_load,
                "scroll_to_bottom": request.navigation_config.scroll_to_bottom,
                "extract_per_page": request.navigation_config.extract_per_page
            }

        # Extract with navigation
        result = await ultra_extractor.extract_with_navigation(
            url=request.url,
            user_instructions=request.user_instructions,
            navigation_config=navigation_config_dict,
            llm_provider=request.llm_provider,
            max_pages=request.max_pages
        )

        return NavigationExtractResponse(
            success=result.get("success", False),
            table=result.get("table", []),
            columns=result.get("columns", []),
            row_count=result.get("row_count", 0),
            pages_visited=result.get("pages_visited", 0),
            navigation_log=result.get("navigation_log", []),
            extraction_metadata=result.get("extraction_metadata", {}),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"❌ Navigation extraction failed: {str(e)}", exc_info=True)
        return NavigationExtractResponse(
            success=False,
            error=str(e)
        )


# ============================================================================
# 🎯 CSS SELECTOR AUTO-GENERATION - Convert Smart Extraction to CSS Templates
# ============================================================================

class GenerateSelectorsRequest(BaseModel):
    """Request model for CSS selector generation"""
    html_content: str = Field(..., description="HTML source where data was extracted from")
    extracted_data: Dict[str, Any] = Field(..., description="Extracted field:value pairs from Smart/Mapper extraction")
    llm_provider: str = Field(default="openai", description="LLM provider for AI-powered generation")
    model_id: Optional[str] = Field(default="gpt-4-turbo", description="Specific model to use")

class GenerateSelectorsResponse(BaseModel):
    """Response model for CSS selector generation"""
    success: bool
    selectors: Dict[str, Any] = Field(default_factory=dict, description="Generated CSS selectors for each field")
    overall_quality: float = Field(default=0.0, description="Quality score (0.0-1.0)")
    fields_total: int = Field(default=0, description="Total fields processed")
    fields_successful: int = Field(default=0, description="Fields with successful selector generation")
    generation_method: str = Field(default="", description="Method used: ai, pattern_matching, or failed")
    message: str = Field(default="", description="Status message")
    error: Optional[str] = None

@router.post("/generate-css-selectors", response_model=GenerateSelectorsResponse)
async def generate_css_selectors(
    request: GenerateSelectorsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    🎯 **AUTO-GENERATE CSS SELECTORS FROM SMART EXTRACTION**

    This endpoint takes extracted data + HTML and uses AI to reverse-engineer CSS selectors.

    **Workflow:**
    1. User performs Smart Extraction or Template Mapping (AI-based)
    2. Frontend sends extracted data + HTML to this endpoint
    3. AI analyzes HTML and generates CSS selectors for each field
    4. Selectors are validated and scored
    5. Frontend saves template with real CSS selectors
    6. Template can now be used for fast CSS-based extraction

    **Benefits:**
    - **Use AI once**: Smart extraction uses AI to learn patterns
    - **Use CSS forever**: Generated selectors work without AI (fast!)
    - **Best of both worlds**: AI flexibility + CSS speed

    **Example Usage:**
    ```json
    {
      "html_content": "<html>...</html>",
      "extracted_data": {
        "title": "Sharp Objects",
        "price": "£47.82",
        "availability": "In stock"
      },
      "llm_provider": "openai",
      "model_id": "gpt-4-turbo"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "selectors": {
        "title": {
          "selector": "h1.product-title",
          "attribute": "text",
          "confidence": 0.95,
          "validation_passed": true
        },
        "price": {
          "selector": ".price_color",
          "attribute": "text",
          "confidence": 0.92,
          "validation_passed": true
        },
        ...
      },
      "overall_quality": 0.93,
      "fields_total": 3,
      "fields_successful": 3,
      "message": "Generated 3/3 CSS selectors successfully"
    }
    ```

    **Use Cases:**
    - Save Smart Extraction results as reusable CSS templates
    - Convert Template Mapper results to CSS selectors
    - Optimize extraction speed after initial AI learning
    - Build template library from successful extractions
    """
    try:
        logger.info("="*80)
        logger.info("🎯 CSS SELECTOR AUTO-GENERATION REQUEST")
        logger.info(f"📊 Fields to generate: {list(request.extracted_data.keys())}")
        logger.info(f"📄 HTML size: {len(request.html_content)} characters")
        logger.info(f"🤖 LLM Provider: {request.llm_provider}")
        logger.info("="*80)

        # Import CSS Selector Generator
        from app.services.webscraper.css_selector_generator import CSSSelectorGenerator
        from app.services.llm_service import llm_service

        # Initialize generator
        selector_generator = CSSSelectorGenerator(llm_service=llm_service)

        # Generate CSS selectors
        result = await selector_generator.generate_selectors_from_extraction(
            html_content=request.html_content,
            extracted_data=request.extracted_data,
            llm_provider=request.llm_provider,
            model_id=request.model_id
        )

        logger.info(f"✅ CSS selector generation complete: {result.get('fields_successful')}/{result.get('fields_total')} selectors generated")

        return GenerateSelectorsResponse(
            success=result.get("success", False),
            selectors=result.get("selectors", {}),
            overall_quality=result.get("overall_quality", 0.0),
            fields_total=result.get("fields_total", 0),
            fields_successful=result.get("fields_successful", 0),
            generation_method=result.get("generation_method", ""),
            message=result.get("message", ""),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"❌ CSS selector generation failed: {str(e)}", exc_info=True)
        return GenerateSelectorsResponse(
            success=False,
            error=str(e),
            message=f"CSS selector generation error: {str(e)}"
        )
