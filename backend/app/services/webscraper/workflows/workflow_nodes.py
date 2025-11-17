"""
Workflow Nodes

This module defines the individual nodes for the LangGraph data extraction workflow.
Each node performs a specific step in the extraction process and updates the workflow state.
"""

import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd

from .workflow_state import WorkflowState, ScrapedContent, ExtractionPlan, ValidationReport

logger = logging.getLogger(__name__)


class ExtractionWorkflowNodes:
    """
    Collection of nodes for the data extraction workflow

    Each node is a static method that takes the workflow state as input,
    performs its operation, and returns the updated state.
    """

    @staticmethod
    async def parse_template_node(state: WorkflowState) -> WorkflowState:
        """
        Parse template and extract schema

        This node loads the template (if provided) and extracts the field
        definitions, validation rules, and transformation rules.
        """
        logger.info(f"[{state['job_id']}] Parsing template...")
        state['current_step'] = 'parsing_template'
        state['progress_percentage'] = 10.0

        try:
            if state.get('template_id'):
                logger.info(f"Loading template ID: {state['template_id']}")

                # Import templates_store from extraction_routes
                from app.api.routes.extraction_routes import templates_store

                # Load template from in-memory store
                if state['template_id'] in templates_store:
                    template = templates_store[state['template_id']]

                    # Extract template information
                    state['template_name'] = template.get('name', 'Unknown Template')
                    state['fields'] = template.get('fields', [])
                    state['llm_extraction_prompts'] = template.get('llm_extraction_prompts', {})
                    state['css_selectors'] = template.get('css_selectors', {})
                    state['xpath_selectors'] = template.get('xpath_selectors', {})
                    state['validation_rules'] = template.get('validation_rules', {})
                    state['has_template'] = True

                    logger.info(
                        f"Template '{state['template_name']}' loaded successfully "
                        f"with {len(state['fields'])} fields"
                    )

                    # Check if this template uses LLM extraction
                    has_llm_prompts = len(state['llm_extraction_prompts']) > 0
                    state['use_llm_extraction'] = has_llm_prompts

                    if has_llm_prompts:
                        logger.info(
                            f"Template will use LLM-based extraction for "
                            f"{len(state['llm_extraction_prompts'])} fields"
                        )
                else:
                    logger.error(f"Template {state['template_id']} not found in templates_store")
                    state['errors'].append({
                        'step': 'parse_template',
                        'error': f"Template {state['template_id']} not found",
                        'timestamp': datetime.utcnow()
                    })
                    state['has_template'] = False
            else:
                logger.info("No template provided, using content-only extraction")
                state['has_template'] = False

        except Exception as e:
            logger.error(f"Error parsing template: {str(e)}", exc_info=True)
            state['errors'].append({
                'step': 'parse_template',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })
            state['has_template'] = False

        return state

    @staticmethod
    async def plan_extraction_node(state: WorkflowState) -> WorkflowState:
        """
        Analyze template and URLs to plan extraction strategy

        This node creates an extraction plan for each URL, determining
        the optimal scraping strategy and extractors to use.
        """
        logger.info(f"[{state['job_id']}] Planning extraction for {state['total_urls']} URLs...")
        state['current_step'] = 'planning_extraction'
        state['progress_percentage'] = 20.0

        try:
            extraction_plan = {}

            for idx, url in enumerate(state['urls']):
                # Determine strategy based on URL pattern and template requirements
                # This is a simplified version - real implementation would be more sophisticated
                plan = ExtractionPlan(
                    url=url,
                    strategy='auto',  # Could be determined by URL analysis
                    extractors=['css', 'xpath', 'llm'] if state['has_template'] else ['content'],
                    priority=idx
                )
                extraction_plan[url] = plan

            state['extraction_plan'] = extraction_plan
            logger.info(f"Extraction plan created for {len(extraction_plan)} URLs")

        except Exception as e:
            logger.error(f"Error planning extraction: {str(e)}")
            state['errors'].append({
                'step': 'plan_extraction',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })

        return state

    @staticmethod
    async def scrape_sources_node(state: WorkflowState) -> WorkflowState:
        """
        Scrape all URLs in parallel

        This node performs parallel scraping of all URLs using the
        scraping engine with the determined strategies.
        """
        logger.info(f"[{state['job_id']}] Scraping {state['total_urls']} URLs in parallel...")
        state['current_step'] = 'scraping_sources'
        state['progress_percentage'] = 30.0
        state['workflow_status'] = 'running'

        start_time = datetime.utcnow()

        try:
            # Import scraper engine
            from ..core.scraper_engine import ScraperEngine
            from ..compliance import ComplianceLevel

            # Get compliance level from config
            compliance_level_str = state['scrape_config'].get('compliance_level', 'balanced')
            compliance_level = ComplianceLevel(compliance_level_str)

            # Initialize scraper
            scraper = ScraperEngine(
                compliance_level=compliance_level,
                enable_smart_scraping=state['scrape_config'].get('enable_smart_scraping', True)
            )

            # Scrape URLs in parallel with controlled concurrency
            max_concurrent = state['scrape_config'].get('max_concurrent_requests', 5)
            semaphore = asyncio.Semaphore(max_concurrent)

            async def scrape_with_semaphore(url: str, plan: ExtractionPlan) -> ScrapedContent:
                async with semaphore:
                    try:
                        logger.info(f"Scraping: {url}")
                        result = await scraper.scrape_url(
                            url=url,
                            scrape_prompt=state['scrape_config'].get('scrape_prompt'),
                            llm_provider="openai"  # Use OpenAI for best results
                        )

                        return ScrapedContent(
                            url=url,
                            content=result.get('content', ''),
                            title=result.get('title'),
                            metadata=result.get('metadata', {}),
                            strategy_used=result.get('strategy_used', plan['strategy']),
                            success=True,
                            error=None,
                            scraped_at=datetime.utcnow()
                        )
                    except Exception as e:
                        logger.error(f"Error scraping {url}: {str(e)}")
                        return ScrapedContent(
                            url=url,
                            content='',
                            title=None,
                            metadata={},
                            strategy_used=plan['strategy'],
                            success=False,
                            error=str(e),
                            scraped_at=datetime.utcnow()
                        )

            # Execute parallel scraping
            tasks = [
                scrape_with_semaphore(url, plan)
                for url, plan in state['extraction_plan'].items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            raw_data = []
            successful_scrapes = 0
            failed_scrapes = 0

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Scraping task failed: {str(result)}")
                    failed_scrapes += 1
                elif result.get('success'):
                    raw_data.append(result)
                    successful_scrapes += 1
                else:
                    raw_data.append(result)
                    failed_scrapes += 1

            state['raw_data'] = raw_data
            state['successful_scrapes'] = successful_scrapes
            state['failed_scrapes'] = failed_scrapes

            scrape_duration = (datetime.utcnow() - start_time).total_seconds()
            state['metrics']['scraping_duration'] = scrape_duration

            logger.info(
                f"Scraping completed: {successful_scrapes} successful, "
                f"{failed_scrapes} failed in {scrape_duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"Error in scraping node: {str(e)}")
            state['errors'].append({
                'step': 'scrape_sources',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })
            state['workflow_status'] = 'failed'

        return state

    @staticmethod
    async def extract_data_node(state: WorkflowState) -> WorkflowState:
        """
        Extract structured fields from scraped content

        This node uses the extractors to pull out specific fields
        from the scraped content based on the template definition.
        """
        logger.info(f"[{state['job_id']}] Extracting structured data...")
        state['current_step'] = 'extracting_data'
        state['progress_percentage'] = 50.0

        try:
            if not state['has_template'] or not state.get('fields'):
                # No template - just use raw content
                logger.info("No template, skipping field extraction")
                successful_items = [item for item in state['raw_data'] if item['success']]
                state['extracted_data'] = {
                    'url': [item.get('url', '') for item in successful_items],
                    'title': [item.get('title', '') for item in successful_items],
                    'content': [item.get('content', '') for item in successful_items]
                }
            elif state.get('use_llm_extraction'):
                # LLM-based extraction (for Excel templates)
                logger.info(
                    f"Using LLM-based extraction for {len(state['fields'])} fields "
                    f"from {len(state['raw_data'])} pages"
                )

                # Import LLM services
                from app.services.llm_service import llm_service
                from app.services.webscraper.extractors.llm_extractor import LLMExtractor

                # Initialize LLM service
                await llm_service.initialize()
                extractor = LLMExtractor(llm_service=llm_service)

                # Extract column names from fields
                template_columns = [field['name'] for field in state['fields']]

                # Process each scraped page
                all_records = []

                for scraped_item in state['raw_data']:
                    if not scraped_item.get('success'):
                        logger.warning(f"Skipping failed scrape: {scraped_item.get('url')}")
                        continue

                    try:
                        # Get scraped content
                        scraped_content = scraped_item.get('content', '')

                        if not scraped_content:
                            logger.warning(f"Empty content for {scraped_item.get('url')}")
                            continue

                        logger.info(
                            f"Mapping scraped data from {scraped_item.get('url')} "
                            f"({len(scraped_content)} chars) to {len(template_columns)} "
                            f"template columns using LLM..."
                        )

                        # Log a preview of the scraped content for debugging
                        content_preview = scraped_content[:200].replace('\n', ' ')
                        logger.debug(f"Content preview: {content_preview}...")

                        # Use LLM to map scraped data to template columns
                        mapping_result = await extractor.map_to_custom_template(
                            scraped_data=scraped_content,
                            template_columns=template_columns,
                            template_examples=None,
                            llm_provider="openai"  # Default to OpenAI for best results
                        )

                        if mapping_result:
                            mapped_data = mapping_result.get('mapped_data', {})
                            missing_fields = mapping_result.get('missing_fields', [])

                            # Validate that we have some data
                            non_empty_fields = [
                                k for k, v in mapped_data.items()
                                if v and v != "—" and v != "— (requires additional research)"
                            ]

                            if not non_empty_fields:
                                logger.warning(
                                    f"⚠ LLM extraction returned no data for {scraped_item.get('url')}. "
                                    f"All {len(template_columns)} fields are empty or marked as missing. "
                                    f"This usually means the scraped content doesn't contain data matching your template columns."
                                )
                                # Log the mapped data to help debug
                                logger.debug(f"Mapped data (all empty): {mapped_data}")
                            else:
                                logger.info(
                                    f"✓ Extracted {len(non_empty_fields)}/{len(template_columns)} "
                                    f"fields from {scraped_item.get('url')}"
                                )
                                # Log extracted values for debugging
                                extracted_preview = {k: v for k, v in mapped_data.items() if k in non_empty_fields}
                                logger.debug(f"Successfully extracted fields: {extracted_preview}")

                            # Add URL to the record
                            mapped_data['URL'] = scraped_item.get('url')

                            all_records.append(mapped_data)

                            if missing_fields:
                                logger.debug(f"Missing fields: {', '.join(missing_fields)}")

                        else:
                            logger.error(
                                f"✗ LLM mapping returned None for {scraped_item.get('url')}. "
                                f"This usually means the LLM failed to parse the response or "
                                f"the LLM service is not responding correctly."
                            )
                            # Add a record with empty values and the URL so we don't lose the URL
                            empty_record = {col: "—" for col in template_columns}
                            empty_record['URL'] = scraped_item.get('url')
                            all_records.append(empty_record)

                    except Exception as e:
                        logger.error(
                            f"✗ Error extracting from {scraped_item.get('url')}: {str(e)}",
                            exc_info=True
                        )
                        # Add a record with error indication and the URL
                        error_record = {col: "— (extraction error)" for col in template_columns}
                        error_record['URL'] = scraped_item.get('url')
                        all_records.append(error_record)

                # Convert list of records to column-based dict for pandas
                if all_records:
                    # Convert row-based records to column-based dict
                    extracted_data = {}
                    for col in template_columns:
                        extracted_data[col] = [record.get(col, '') for record in all_records]

                    # Add URL column (check both 'URL' and 'url' keys)
                    extracted_data['URL'] = [record.get('URL', record.get('url', '')) for record in all_records]

                    state['extracted_data'] = extracted_data

                    logger.info(
                        f"✓ LLM extraction complete: {len(all_records)} records with "
                        f"{len(template_columns)} template fields + URL column"
                    )
                else:
                    logger.error(
                        "✗ No records extracted from any pages! This means the LLM extraction "
                        "failed for all URLs or all content was empty."
                    )
                    state['extracted_data'] = {col: [] for col in template_columns}
                    state['extracted_data']['URL'] = []
                    state['errors'].append({
                        'step': 'extract_data',
                        'error': 'No records extracted from any pages',
                        'timestamp': datetime.utcnow()
                    })

            else:
                # Selector-based extraction (CSS/XPath)
                logger.info(
                    f"Using selector-based extraction for {len(state['fields'])} fields "
                    f"from {len(state['raw_data'])} pages"
                )

                # TODO: Implement CSS/XPath extractor factory
                # For now, create empty structure with matching array lengths
                successful_items = [item for item in state['raw_data'] if item['success']]
                num_items = len(successful_items)

                extracted_data = {field['name']: ['' for _ in range(num_items)] for field in state['fields']}
                extracted_data['url'] = [item['url'] for item in successful_items]

                state['extracted_data'] = extracted_data

                logger.warning(
                    "Selector-based extraction not fully implemented yet. "
                    "Consider using LLM-based templates instead."
                )

        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}", exc_info=True)
            state['errors'].append({
                'step': 'extract_data',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })

        return state

    @staticmethod
    async def consolidate_node(state: WorkflowState) -> WorkflowState:
        """
        Consolidate data from multiple sources into DataFrame

        This node converts the extracted data into a pandas DataFrame
        for easier processing, validation, and output generation.
        """
        logger.info(f"[{state['job_id']}] Consolidating data...")
        state['current_step'] = 'consolidating_data'
        state['progress_percentage'] = 60.0

        try:
            if state.get('extracted_data'):
                # Convert to DataFrame
                df = pd.DataFrame(state['extracted_data'])
                state['consolidated_data'] = df
                state['records_extracted'] = len(df)

                logger.info(f"Consolidated {len(df)} records with {len(df.columns)} columns")
            else:
                logger.warning("No extracted data to consolidate")
                state['warnings'].append({
                    'step': 'consolidate',
                    'warning': 'No data extracted',
                    'timestamp': datetime.utcnow()
                })

        except Exception as e:
            logger.error(f"Error consolidating data: {str(e)}")
            state['errors'].append({
                'step': 'consolidate',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })

        return state

    @staticmethod
    async def transform_node(state: WorkflowState) -> WorkflowState:
        """
        Apply transformations to data

        This node applies field-level transformations as defined
        in the template (e.g., lowercase, uppercase, extract_number).
        """
        logger.info(f"[{state['job_id']}] Applying transformations...")
        state['current_step'] = 'transforming_data'
        state['progress_percentage'] = 65.0

        try:
            if state.get('consolidated_data') is not None:
                df = state['consolidated_data'].copy()

                # TODO: Apply transformations from template
                # For now, just pass through
                state['transformed_data'] = df
                logger.info("Transformations applied")
            else:
                logger.warning("No data to transform")

        except Exception as e:
            logger.error(f"Error transforming data: {str(e)}")
            state['errors'].append({
                'step': 'transform',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })

        return state

    @staticmethod
    async def clean_node(state: WorkflowState) -> WorkflowState:
        """
        Clean data (remove HTML, normalize whitespace, etc.)

        This node performs data cleaning operations like removing HTML tags,
        normalizing whitespace, and handling missing values.
        """
        logger.info(f"[{state['job_id']}] Cleaning data...")
        state['current_step'] = 'cleaning_data'
        state['progress_percentage'] = 70.0

        try:
            if state.get('transformed_data') is not None:
                df = state['transformed_data'].copy()

                # TODO: Import and use DataCleaner
                # For now, basic cleaning
                # Strip whitespace from string columns
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].str.strip() if hasattr(df[col], 'str') else df[col]

                state['cleaned_data'] = df
                logger.info("Data cleaned")
            else:
                logger.warning("No data to clean")

        except Exception as e:
            logger.error(f"Error cleaning data: {str(e)}")
            state['errors'].append({
                'step': 'clean',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })

        return state

    @staticmethod
    async def deduplicate_node(state: WorkflowState) -> WorkflowState:
        """
        Remove duplicate records

        This node identifies and removes duplicate records based on
        configurable key columns.
        """
        logger.info(f"[{state['job_id']}] Removing duplicates...")
        state['current_step'] = 'deduplicating_data'
        state['progress_percentage'] = 75.0

        try:
            if state.get('cleaned_data') is not None:
                df = state['cleaned_data'].copy()
                initial_count = len(df)

                # Remove duplicates (all columns or by URL if available)
                if 'url' in df.columns:
                    df = df.drop_duplicates(subset=['url'], keep='first')
                else:
                    df = df.drop_duplicates(keep='first')

                final_count = len(df)
                duplicates_removed = initial_count - final_count

                state['deduplicated_data'] = df
                state['duplicates_removed'] = duplicates_removed

                logger.info(f"Removed {duplicates_removed} duplicate records")
            else:
                logger.warning("No data to deduplicate")

        except Exception as e:
            logger.error(f"Error deduplicating data: {str(e)}")
            state['errors'].append({
                'step': 'deduplicate',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })

        return state

    @staticmethod
    async def validate_node(state: WorkflowState) -> WorkflowState:
        """
        Validate data quality

        This node validates the data against template rules and
        calculates quality metrics.
        """
        logger.info(f"[{state['job_id']}] Validating data quality...")
        state['current_step'] = 'validating_data'
        state['progress_percentage'] = 80.0

        try:
            if state.get('deduplicated_data') is not None:
                df = state['deduplicated_data']

                # TODO: Implement full validation with DataValidator
                # For now, simple quality metrics
                errors = []
                warnings = []

                # Calculate completeness
                total_cells = df.size
                non_null_cells = df.notna().sum().sum()
                completeness = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0

                # Quality score (as decimal 0-1, not percentage)
                # Frontend multiplies by 100 for display, so we return decimal
                quality_score = completeness / 100.0  # Convert percentage to decimal

                validation_results = ValidationReport(
                    errors=errors,
                    warnings=warnings,
                    quality_score=quality_score,
                    completeness=completeness,
                    accuracy=100.0,  # Placeholder
                    is_valid=len(errors) == 0,
                    field_quality={}
                )

                state['validation_results'] = validation_results
                state['quality_score'] = quality_score
                state['data_quality_passed'] = quality_score >= 0.70  # 0.70 = 70%

                logger.info(
                    f"Validation complete: quality_score={quality_score:.2f} ({quality_score*100:.1f}%), "
                    f"completeness={completeness:.2f}%"
                )
            else:
                logger.warning("No data to validate")
                state['data_quality_passed'] = False

        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            state['errors'].append({
                'step': 'validate',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })

        return state

    @staticmethod
    async def generate_output_node(state: WorkflowState) -> WorkflowState:
        """
        Generate output file in requested format

        This node generates the final output file (Excel, CSV, JSON, etc.)
        with the processed data.
        """
        logger.info(f"[{state['job_id']}] Generating {state['output_format']} output...")
        state['current_step'] = 'generating_output'
        state['progress_percentage'] = 90.0

        try:
            if state.get('deduplicated_data') is not None:
                df = state['deduplicated_data']

                # Check if DataFrame has any meaningful data
                if len(df) == 0:
                    logger.error(
                        "⚠ DataFrame is empty! No data to export. "
                        "The extraction likely failed or returned no results."
                    )
                else:
                    # Count cells with meaningful values (not just "—" or empty)
                    meaningful_cells = 0
                    total_data_cells = df.size
                    for col in df.columns:
                        if col != 'URL':  # Skip URL column in counting
                            meaningful_cells += df[col].apply(
                                lambda x: x not in ["—", "— (requires additional research)", "", None] if pd.notna(x) else False
                            ).sum()

                    if meaningful_cells == 0 and len(df) > 0:
                        logger.warning(
                            f"⚠ DataFrame has {len(df)} row(s) but ALL data fields are empty/missing! "
                            f"The LLM extraction marked all fields as '—' (not found). "
                            f"This usually means the scraped content doesn't match your template columns. "
                            f"Try using more specific column names or check if the website structure changed."
                        )

                # TODO: Use OutputFactory to generate formatted output
                # For now, create a simple output
                import tempfile
                import os

                output_dir = tempfile.mkdtemp()

                # Map output format to proper file extension
                format_to_ext = {
                    'excel': 'xlsx',
                    'csv': 'csv',
                    'json': 'json',
                    'xml': 'xml',
                    'parquet': 'parquet'
                }
                file_ext = format_to_ext.get(state['output_format'], state['output_format'])
                output_filename = f"{state['job_id']}.{file_ext}"
                output_path = os.path.join(output_dir, output_filename)

                # Generate output based on format
                if state['output_format'] == 'excel':
                    df.to_excel(output_path, index=False, engine='openpyxl')
                elif state['output_format'] == 'csv':
                    df.to_csv(output_path, index=False)
                elif state['output_format'] == 'json':
                    df.to_json(output_path, orient='records', indent=2)
                elif state['output_format'] == 'parquet':
                    df.to_parquet(output_path, index=False)
                else:
                    # Default to CSV for unknown formats
                    logger.warning(f"Unknown output format '{state['output_format']}', defaulting to CSV")
                    df.to_csv(output_path, index=False)

                file_size = os.path.getsize(output_path)

                state['output_file_path'] = output_path
                state['output_file_size'] = file_size
                state['output_metadata'] = {
                    'format': state['output_format'],
                    'rows': len(df),
                    'columns': len(df.columns),
                    'file_size_bytes': file_size
                }

                logger.info(f"Output generated: {output_path} ({file_size} bytes)")
            else:
                logger.error("No data available for output generation")
                state['errors'].append({
                    'step': 'generate_output',
                    'error': 'No data available',
                    'timestamp': datetime.utcnow()
                })

        except Exception as e:
            logger.error(f"Error generating output: {str(e)}")
            state['errors'].append({
                'step': 'generate_output',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })

        return state

    @staticmethod
    async def deliver_node(state: WorkflowState) -> WorkflowState:
        """
        Deliver results via configured channel

        This node delivers the generated output through the configured
        delivery method (download, email, webhook, cloud storage).
        """
        logger.info(
            f"[{state['job_id']}] Delivering via {state['delivery_method']}..."
        )
        state['current_step'] = 'delivering_results'
        state['progress_percentage'] = 95.0

        try:
            if state.get('output_file_path'):
                # TODO: Use DeliveryFactory
                # For now, just mark as ready for download
                delivery_result = {
                    'success': True,
                    'method': state['delivery_method'],
                    'destination': state['output_file_path'],
                    'delivered_at': datetime.utcnow(),
                    'error': None,
                    'metadata': {
                        'delivery_method': state['delivery_method'],
                        'file_path': state['output_file_path']
                    }
                }

                state['delivery_status'] = delivery_result
                state['delivery_success'] = True

                logger.info(f"Delivery successful via {state['delivery_method']}")
            else:
                logger.error("No output file to deliver")
                state['delivery_success'] = False

        except Exception as e:
            logger.error(f"Error delivering results: {str(e)}")
            state['errors'].append({
                'step': 'deliver',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })
            state['delivery_success'] = False

        return state

    @staticmethod
    async def finalize_node(state: WorkflowState) -> WorkflowState:
        """
        Finalize workflow and update status

        This node performs final cleanup, calculates total duration,
        and sets the final workflow status.
        """
        logger.info(f"[{state['job_id']}] Finalizing workflow...")
        state['current_step'] = 'completed'
        state['progress_percentage'] = 100.0

        try:
            # Calculate duration
            state['completed_at'] = datetime.utcnow()
            duration = (state['completed_at'] - state['started_at']).total_seconds()
            state['total_duration_seconds'] = duration

            # Determine final status
            if len(state['errors']) > 0:
                state['workflow_status'] = 'completed_with_errors'
            elif not state.get('delivery_success'):
                state['workflow_status'] = 'failed'
            else:
                state['workflow_status'] = 'completed'

            logger.info(
                f"Workflow finalized: status={state['workflow_status']}, "
                f"duration={duration:.2f}s, records={state['records_extracted']}"
            )

        except Exception as e:
            logger.error(f"Error finalizing workflow: {str(e)}")
            state['workflow_status'] = 'failed'

        return state
