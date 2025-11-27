# Auto-template selection endpoint code
# This goes in template_extraction_routes.py before the /preset/{preset_name} endpoint

@router.post("/auto", response_model=ExtractionResponse)
async def extract_with_auto_template(
    request: AutoExtractRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-select best matching template based on URL pattern and extract data

    This endpoint:
    1. Matches the URL against all saved templates' url_patterns
    2. Picks the most specific matching template
    3. Validates the URL matches before extraction
    4. Routes to appropriate extraction method (CSS or AI-powered)
    """
    try:
        # Extract domain + path from URL for matching
        parsed_url = urlparse(request.url)
        url_to_match = f"{parsed_url.netloc}{parsed_url.path}"

        # If URL starts with www., also try without it
        url_alternatives = [url_to_match]
        if url_to_match.startswith("www."):
            url_alternatives.append(url_to_match[4:])  # Remove "www."
        else:
            url_alternatives.append(f"www.{url_to_match}")

        logger.info(f"Auto-selecting template for URL: {request.url}")
        logger.info(f"Matching against: {url_alternatives}")

        # Query all active templates with url_patterns
        from sqlalchemy import text
        query = text("""
            SELECT name, display_name, url_pattern, fields
            FROM saved_css_templates
            WHERE is_active = TRUE AND url_pattern IS NOT NULL
            ORDER BY LENGTH(url_pattern) DESC
        """)

        result = await db.execute(query)
        templates = result.fetchall()

        if not templates:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "No Templates Found",
                    "message": "No extraction templates are configured yet.",
                    "suggestions": [
                        "Create a template using Smart Extraction first",
                        "Save the template for future use",
                        "Templates need a url_pattern to enable auto-selection"
                    ],
                    "url": request.url
                }
            )

        # Find matching templates
        matching_templates = []
        for template_row in templates:
            template_name, display_name, url_pattern, fields = template_row

            if not url_pattern:
                continue

            # Try matching against all URL alternatives
            for url_alt in url_alternatives:
                if fnmatch(url_alt, url_pattern):
                    matching_templates.append({
                        "name": template_name,
                        "display_name": display_name,
                        "url_pattern": url_pattern,
                        "fields": fields,
                        "pattern_specificity": len(url_pattern)  # Longer = more specific
                    })
                    logger.info(f"✓ Template '{template_name}' matches pattern '{url_pattern}'")
                    break

        if not matching_templates:
            # No templates matched
            available_patterns = [t[2] for t in templates if t[2]]
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "No Matching Template",
                    "message": f"No template found for URL: {request.url}",
                    "suggestions": [
                        "Create a new template for this website using Smart Extraction",
                        f"URL pattern needed: {parsed_url.netloc}/*",
                        "Or use Smart Extraction mode instead (no template needed)"
                    ],
                    "url": request.url,
                    "available_patterns": available_patterns
                }
            )

        # Pick most specific match (longest pattern)
        selected_template = max(matching_templates, key=lambda t: t["pattern_specificity"])
        template_name = selected_template["name"]
        fields_data = selected_template["fields"]

        logger.info(f"Auto-selected template: '{template_name}' (pattern: {selected_template['url_pattern']})")

        # Check if template is AI-powered (no CSS selectors)
        has_valid_selector = any(
            field.get("selector") and field.get("selector").strip() and field.get("selector") != "auto"
            for field in fields_data
        )

        # Route to appropriate extractor
        if not has_valid_selector:
            # AI-powered template - use UltraSmartExtractor
            logger.info(f"Template '{template_name}' is AI-powered, routing to Ultra-Smart Extractor")

            field_names = [field.get("name") for field in fields_data if field.get("name")]
            user_instructions = f"Extract the following fields: {', '.join(field_names)}"

            from app.services.webscraper.extractors.ultra_smart_extractor import UltraSmartExtractor
            from app.services.llm_service import llm_service
            from app.services.scraper_service import scraper_service
            from app.services.document_service import document_service

            ultra_extractor = UltraSmartExtractor(
                llm_service=llm_service,
                scraper_service=scraper_service,
                document_service=document_service
            )

            result = await ultra_extractor.extract_to_table(
                source=request.url,
                source_type="url",
                user_instructions=user_instructions,
                llm_provider="openai",
                vision_provider="openai"
            )

            # Store scrape job
            if result.get('success'):
                job = WebScrapeJob(
                    url=request.url,
                    scrape_prompt=f"Auto Template extraction: {template_name} - {user_instructions}",
                    status="completed",
                    completed_at=datetime.utcnow()
                )
                db.add(job)
                await db.commit()

            # Convert to ExtractionResponse format
            return ExtractionResponse(
                success=result.get("success", False),
                url=request.url,
                template_name=template_name,
                data=result.get("table", []),
                row_count=result.get("row_count", 0),
                extracted_at=datetime.utcnow().isoformat(),
                session_id=request.session_id,
                error=result.get("error")
            )

        else:
            # CSS-based template - use standard extraction
            logger.info(f"Template '{template_name}' uses CSS selectors")

            # Forward to preset endpoint logic
            preset_request = ExtractPresetRequest(
                url=request.url,
                preset=template_name,
                session_id=request.session_id
            )

            # Call preset endpoint (will reuse existing logic)
            return await extract_with_preset_template(template_name, preset_request, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto template selection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Auto-Selection Failed",
                "message": f"Failed to auto-select template: {str(e)}",
                "suggestions": [
                    "Try using Smart Extraction mode instead",
                    "Or manually select a template",
                    "Check if the URL is accessible"
                ],
                "url": request.url
            }
        )
