"""
Template Extraction Service
Extracts structured data from web pages and exports to Excel
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import re
import pandas as pd
from io import BytesIO
# NOTE: playwright imports moved to initialize() method to allow setting env vars first
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class ExtractionField:
    """Defines a field to extract from a webpage"""
    name: str
    selector: Optional[str] = None  # CSS selector
    xpath: Optional[str] = None     # XPath expression
    regex: Optional[str] = None     # Regex pattern
    attribute: Optional[str] = None # HTML attribute to extract (e.g., 'href', 'src')
    data_type: str = 'text'        # text, number, percentage, date
    required: bool = False
    default_value: Any = None
    transform: Optional[callable] = None


@dataclass
class ExtractionTemplate:
    """Template defining how to extract data from a website"""
    name: str
    description: str
    fields: List[ExtractionField]
    wait_for_selector: Optional[str] = None  # Wait for this element before extracting
    pagination_selector: Optional[str] = None  # Selector for "next" button
    max_pages: int = 1


class TemplateExtractionService:
    """Service for extracting structured data from web pages using templates"""

    def __init__(self):
        self.browser: Optional[Any] = None  # Browser type, but imported later
        self._playwright = None

    async def initialize(self):
        """Initialize Playwright browser"""
        if self._playwright is None:
            try:
                import os

                # CRITICAL: Set PLAYWRIGHT_BROWSERS_PATH BEFORE importing playwright
                # Workaround for volume mounting issue where docker-compose env vars aren't seen by Python
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/ms-playwright'
                logger.info(f"Set PLAYWRIGHT_BROWSERS_PATH={os.environ.get('PLAYWRIGHT_BROWSERS_PATH')}")

                # Skip Playwright's dependency check (we have the libs, just different names in Ubuntu 24.04)
                os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = 'true'

                # NOW import playwright AFTER setting env vars
                from playwright.async_api import async_playwright

                logger.info("🚀 Starting Playwright initialization...")
                logger.info("📦 Starting async_playwright()...")
                self._playwright = await async_playwright().start()
                logger.info("✅ Playwright started successfully")

                # Launch with Docker-compatible arguments
                logger.info("🌐 Launching Chromium browser...")
                # Explicitly use chromium-1140 from base image
                # This fixes the mismatch between pip-installed playwright (expects 1097) and base image (has 1140)
                chromium_path = "/ms-playwright/chromium-1140/chrome-linux/chrome"
                logger.info(f"Using Chromium executable: {chromium_path}")
                self.browser = await self._playwright.chromium.launch(
                    executable_path=chromium_path,
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                logger.info(f"✅ Chromium launched successfully, browser object: {self.browser}")
                logger.info("✅ Template extraction service initialized with Playwright")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Playwright: {e}", exc_info=True)
                self._playwright = None
                self.browser = None
                raise

    async def close(self):
        """Close browser and Playwright"""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Template extraction service closed")

    async def extract_data(
        self,
            url: str,
        template: ExtractionTemplate,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from a URL using a template

        Args:
            url: URL to extract data from
            template: Extraction template defining fields to extract
            session_id: Optional session ID for tracking

        Returns:
            Dict containing extracted data and metadata
        """
        if not self.browser:
            await self.initialize()

        logger.info("="*80)
        logger.info(f"🔍 TEMPLATE EXTRACTION STARTED")
        logger.info(f"📍 URL: {url}")
        logger.info(f"📋 Template: {template.name}")
        logger.info(f"🔢 Fields to extract: {len(template.fields)}")
        logger.info(f"🆔 Session ID: {session_id or 'None'}")
        logger.info("="*80)

        # Create context with increased default timeout (60 seconds instead of 10)
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        # Set default navigation timeout to 60 seconds
        context.set_default_navigation_timeout(60000)
        context.set_default_timeout(60000)

        page = await context.new_page()

        all_data = []

        try:
            # Navigate to URL with extended timeout for slow sites like screener.in
            logger.info(f"🌐 Navigating to {url}...")
            logger.info(f"⏱️  Timeout set to 90 seconds, waiting for networkidle...")
            await page.goto(url, wait_until='networkidle', timeout=90000)
            logger.info(f"✅ Page loaded successfully: {url}")
            logger.info(f"📄 Page title: {await page.title()}")

            # Wait for key element if specified
            if template.wait_for_selector:
                logger.info(f"⏳ Waiting for selector: {template.wait_for_selector}")
                await page.wait_for_selector(template.wait_for_selector, timeout=60000)
                logger.info(f"✅ Selector found: {template.wait_for_selector}")

            # Extract data from current page
            page_num = 1
            while page_num <= template.max_pages:
                logger.info("="*60)
                logger.info(f"📃 Extracting data from page {page_num}/{template.max_pages}")
                logger.info("="*60)

                # Get page HTML
                logger.info(f"📥 Fetching page HTML content...")
                html_content = await page.content()
                html_length = len(html_content)
                logger.info(f"✅ HTML fetched: {html_length:,} characters")
                logger.info(f"🔍 Parsing HTML with BeautifulSoup (lxml parser)...")
                soup = BeautifulSoup(html_content, 'lxml')
                logger.info(f"✅ HTML parsed successfully")

                # Extract each field
                logger.info(f"🎯 Starting field extraction for {len(template.fields)} fields...")
                extracted_row, field_errors = await self._extract_fields(page, soup, template.fields)
                all_data.append(extracted_row)

                # Log field extraction results
                successful_fields = len([v for v in extracted_row.values() if v is not None])
                total_fields = len(template.fields)
                logger.info("="*60)
                logger.info(f"📊 EXTRACTION RESULTS FOR PAGE {page_num}")
                logger.info(f"✅ Successfully extracted: {successful_fields}/{total_fields} fields ({successful_fields/total_fields*100:.1f}%)")
                logger.info("="*60)

                if field_errors:
                    logger.warning(f"⚠️  Field extraction issues: {len(field_errors)} fields had errors")
                    for field_name, error in field_errors.items():
                        logger.warning(f"   ✗ {field_name}: {error}")
                else:
                    logger.info(f"✅ All fields extracted without errors!")

                # Check for pagination
                if page_num < template.max_pages and template.pagination_selector:
                    next_button = await page.query_selector(template.pagination_selector)
                    if next_button:
                        await next_button.click()
                        await page.wait_for_load_state('networkidle')
                        page_num += 1
                    else:
                        break
                else:
                    break

            logger.info("="*80)
            logger.info(f"🎉 EXTRACTION COMPLETED SUCCESSFULLY")
            logger.info(f"📊 Total rows extracted: {len(all_data)}")
            logger.info(f"📋 Template: {template.name}")
            logger.info(f"🔢 Fields per row: {len(template.fields)}")
            logger.info(f"✅ Success: True")
            logger.info("="*80)

            return {
                'success': True,
                'url': url,
                'template_name': template.name,
                'data': all_data,
                'row_count': len(all_data),
                'extracted_at': datetime.utcnow().isoformat(),
                'session_id': session_id
            }

        except Exception as e:
            logger.error("="*80)
            logger.error(f"❌ EXTRACTION FAILED")
            logger.error(f"📍 URL: {url}")
            logger.error(f"📋 Template: {template.name}")
            logger.error(f"❌ Error: {str(e)}")
            logger.error(f"📝 Error type: {type(e).__name__}")
            logger.error("="*80)
            logger.error(f"Full traceback:", exc_info=True)

            return {
                'success': False,
                'url': url,
                'template_name': template.name,
                'data': [],
                'row_count': 0,
                'extracted_at': datetime.utcnow().isoformat(),
                'error': str(e),
                'session_id': session_id
            }
        finally:
            await context.close()

    async def _extract_fields(
        self,
        page: Any,  # Playwright Page object, but imported at runtime
        soup: BeautifulSoup,
        fields: List[ExtractionField]
    ) -> tuple[Dict[str, Any], Dict[str, str]]:
        """
        Extract all fields from a page

        Returns:
            tuple: (extracted_data, field_errors)
                - extracted_data: Dict of field_name -> extracted_value
                - field_errors: Dict of field_name -> error_message for failed fields
        """
        extracted = {}
        field_errors = {}

        logger.info("─"*60)
        logger.info(f"🔍 FIELD-BY-FIELD EXTRACTION STARTING")
        logger.info("─"*60)

        for idx, field in enumerate(fields, 1):
            try:
                logger.info(f"\n[{idx}/{len(fields)}] Extracting: '{field.name}'")
                logger.info(f"  📌 Selector: {field.selector or 'None'}")
                logger.info(f"  📌 XPath: {field.xpath or 'None'}")
                logger.info(f"  📌 Regex: {field.regex or 'None'}")
                logger.info(f"  📌 Attribute: {field.attribute or 'None'}")
                logger.info(f"  📌 Data type: {field.data_type}")
                logger.info(f"  📌 Required: {field.required}")
                logger.info(f"  📌 Default value: {field.default_value}")

                value = await self._extract_single_field(page, soup, field)
                extracted[field.name] = value

                # Track if we got a None or default value (potential extraction failure)
                if value is None and field.required:
                    field_errors[field.name] = f"Required field returned None (selector: {field.selector or field.xpath or 'N/A'})"
                    logger.warning(f"  ⚠️  Field '{field.name}' extraction returned None. Selector: {field.selector}")
                    logger.warning(f"  ⚠️  This is a REQUIRED field! Data quality may be affected.")
                elif value == field.default_value and field.default_value is not None:
                    logger.info(f"  ℹ️  Field '{field.name}' used default value: {field.default_value}")
                    logger.info(f"  ✅ Extracted value: {value}")
                else:
                    logger.info(f"  ✅ Extracted value: {value}")

            except Exception as e:
                error_msg = f"Error extracting field: {str(e)}"
                field_errors[field.name] = error_msg
                logger.error(f"  ❌ Error extracting field '{field.name}': {e}")
                logger.error(f"  📝 Error type: {type(e).__name__}")

                if field.required:
                    extracted[field.name] = None
                    logger.error(f"  ⚠️  Setting REQUIRED field to None due to error")
                else:
                    extracted[field.name] = field.default_value
                    logger.info(f"  ℹ️  Using default value: {field.default_value}")

        logger.info("─"*60)
        logger.info(f"✅ FIELD EXTRACTION COMPLETED")
        logger.info("─"*60)

        return extracted, field_errors

    async def _extract_single_field(
        self,
        page: Any,  # Playwright Page object, but imported at runtime
        soup: BeautifulSoup,
        field: ExtractionField
    ) -> Any:
        """Extract a single field value"""
        value = None

        # Try CSS selector first (Playwright)
        if field.selector:
            try:
                element = await page.query_selector(field.selector)
                if element:
                    if field.attribute:
                        value = await element.get_attribute(field.attribute)
                    else:
                        value = await element.text_content()
                    logger.debug(f"✓ Playwright selector succeeded for '{field.name}': {field.selector}")
                else:
                    logger.debug(f"✗ Playwright selector found no element for '{field.name}': {field.selector}")
            except Exception as e:
                logger.debug(f"✗ Playwright selector failed for '{field.name}': {e}")

        # Fallback to BeautifulSoup
        if value is None and field.selector:
            element = soup.select_one(field.selector)
            if element:
                if field.attribute:
                    value = element.get(field.attribute)
                else:
                    value = element.get_text(strip=True)
                logger.debug(f"✓ BeautifulSoup selector succeeded for '{field.name}': {field.selector}")
            else:
                logger.debug(f"✗ BeautifulSoup selector found no element for '{field.name}': {field.selector}")

        # Try XPath (Playwright only)
        if value is None and field.xpath:
            try:
                element = await page.query_selector(f'xpath={field.xpath}')
                if element:
                    if field.attribute:
                        value = await element.get_attribute(field.attribute)
                    else:
                        value = await element.text_content()
            except Exception as e:
                logger.debug(f"XPath failed for {field.name}: {e}")

        # Apply regex if specified
        if value and field.regex:
            match = re.search(field.regex, str(value))
            if match:
                value = match.group(1) if match.groups() else match.group(0)

        # Apply data type conversion
        if value:
            value = self._convert_data_type(value, field.data_type)

        # Apply custom transform
        if value and field.transform:
            value = field.transform(value)

        return value if value is not None else field.default_value

    def _convert_data_type(self, value: str, data_type: str) -> Any:
        """Convert extracted text to appropriate data type"""
        if value is None:
            return None

        value_str = str(value).strip()

        try:
            if data_type == 'number':
                # Remove commas and convert to float
                clean = re.sub(r'[,\s]', '', value_str)
                return float(clean)

            elif data_type == 'percentage':
                # Extract percentage value
                clean = re.sub(r'[%\s,]', '', value_str)
                return float(clean)

            elif data_type == 'date':
                # Try common date formats
                from dateutil import parser
                return parser.parse(value_str)

            elif data_type == 'integer':
                clean = re.sub(r'[,\s]', '', value_str)
                return int(float(clean))

            else:  # text
                return value_str

        except Exception as e:
            logger.warning(f"Error converting '{value_str}' to {data_type}: {e}")
            return value_str

    async def export_to_excel(
        self,
        data: List[Dict[str, Any]],
        filename: str = "extracted_data.xlsx"
    ) -> BytesIO:
        """
        Export extracted data to Excel format

        Args:
            data: List of dictionaries containing extracted data
            filename: Name for the Excel file

        Returns:
            BytesIO object containing Excel file
        """
        try:
            # Log incoming data for diagnostics
            logger.info(f"export_to_excel called with {len(data)} rows")
            logger.debug(f"Data structure: {data[:1] if data else 'empty'}")  # Log first row

            # Validate data
            if not data:
                logger.error("Empty data list provided to export_to_excel")
                raise ValueError("Cannot export empty data to Excel")

            if not isinstance(data, list):
                logger.error(f"Data is not a list, got type: {type(data)}")
                raise ValueError(f"Data must be a list, got {type(data)}")

            # Create DataFrame
            df = pd.DataFrame(data)
            logger.info(f"Created DataFrame with shape: {df.shape} (rows, columns)")
            logger.info(f"DataFrame columns: {df.columns.tolist()}")
            logger.debug(f"DataFrame preview:\n{df.head()}")

            # Log sample of actual values for diagnostics
            if len(data) > 0:
                first_row = data[0]
                logger.info(f"First row data sample: {dict(list(first_row.items())[:3])}")  # First 3 columns

                # Count non-empty values in first row
                non_empty_count = sum(1 for v in first_row.values() if v and v not in ['—', '', None])
                logger.info(f"Non-empty values in first row: {non_empty_count}/{len(first_row)}")

            # Create Excel file in memory
            output = BytesIO()

            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Extracted Data', index=False)
                logger.info(f"DataFrame written to Excel sheet 'Extracted Data'")

                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Extracted Data']

                # Add formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1
                })

                # Format for missing data
                missing_format = workbook.add_format({
                    'bg_color': '#FFF3CD',
                    'font_color': '#856404',
                    'italic': True,
                    'border': 1
                })

                # Format header row
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Format data rows and highlight missing fields
                logger.info(f"Writing {len(data)} data rows to Excel worksheet")
                for row_num, row_data in enumerate(data, start=1):
                    logger.debug(f"Writing row {row_num}: {list(row_data.keys())}")
                    for col_num, col_name in enumerate(df.columns):
                        value = row_data.get(col_name, '')
                        # Check if value is missing (—, empty, or null)
                        if value in ['—', '', None] or (isinstance(value, str) and value.strip() == '—'):
                            worksheet.write(row_num, col_num, value, missing_format)
                            logger.debug(f"  Row {row_num}, Col {col_num} ({col_name}): MISSING VALUE")
                        else:
                            worksheet.write(row_num, col_num, value)
                            logger.debug(f"  Row {row_num}, Col {col_num} ({col_name}): {str(value)[:50]}")

                # Auto-adjust column widths with better error handling
                logger.info("Adjusting column widths")
                for i, col in enumerate(df.columns):
                    try:
                        # Calculate max length safely
                        col_values = df[col].astype(str)
                        if len(col_values) > 0:
                            max_value_len = col_values.str.len().max()
                            # Handle NaN or None from max()
                            if pd.isna(max_value_len):
                                max_value_len = 0
                        else:
                            max_value_len = 0

                        max_len = max(
                            int(max_value_len),
                            len(str(col))
                        ) + 2

                        adjusted_width = min(max_len, 50)
                        # Ensure minimum width of 12
                        adjusted_width = max(adjusted_width, 12)

                        worksheet.set_column(i, i, adjusted_width)
                        logger.debug(f"Column {i} ({col}): width set to {adjusted_width}")

                    except Exception as col_error:
                        logger.warning(f"Error setting width for column {i} ({col}): {col_error}")
                        # Fallback to default width
                        worksheet.set_column(i, i, 15)

            output.seek(0)
            output_size = len(output.getvalue())
            logger.info(f"Exported {len(data)} rows to Excel, file size: {output_size} bytes")

            if output_size < 1000:
                logger.warning(f"Excel file size is suspiciously small: {output_size} bytes")

            return output

        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise


# Predefined templates for common use cases

def get_screener_in_template() -> ExtractionTemplate:
    """Template for extracting company data from Screener.in"""
    return ExtractionTemplate(
        name="Screener.in Company Data",
        description="Extract financial metrics from Screener.in company pages",
        wait_for_selector="#company-ratios",
        fields=[
            ExtractionField(
                name="Company Name",
                selector="h1.h2",
                required=True
            ),
            ExtractionField(
                name="Market Cap",
                selector="#top-ratios > li:nth-child(1) > span.number",
                data_type="number"
            ),
            ExtractionField(
                name="Current Price",
                selector="#top-ratios > li:nth-child(2) > span.number",
                data_type="number"
            ),
            ExtractionField(
                name="Stock P/E",
                selector="#top-ratios > li:nth-child(3) > span.number",
                data_type="number"
            ),
            ExtractionField(
                name="Book Value",
                selector="#top-ratios > li:nth-child(4) > span.number",
                data_type="number"
            ),
            ExtractionField(
                name="Dividend Yield",
                selector="#top-ratios > li:nth-child(5) > span.number",
                data_type="percentage"
            ),
            ExtractionField(
                name="ROCE",
                selector="#top-ratios > li:nth-child(6) > span.number",
                data_type="percentage"
            ),
            ExtractionField(
                name="ROE",
                selector="#top-ratios > li:nth-child(7) > span.number",
                data_type="percentage"
            ),
            ExtractionField(
                name="Face Value",
                selector="#top-ratios > li:nth-child(8) > span.number",
                data_type="number"
            ),
            ExtractionField(
                name="Market Position",
                selector="section:contains('About') p",
                default_value="N/A"
            ),
            ExtractionField(
                name="Source / Notes",
                default_value="Scraped from Screener.in"
            ),
        ]
    )


# Singleton instance
template_extraction_service = TemplateExtractionService()
