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
from playwright.async_api import async_playwright, Page, Browser
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
        self.browser: Optional[Browser] = None
        self._playwright = None

    async def initialize(self):
        """Initialize Playwright browser"""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(headless=True)
            logger.info("Template extraction service initialized with Playwright")

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

        logger.info(f"Extracting data from {url} using template: {template.name}")

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
            await page.goto(url, wait_until='networkidle', timeout=90000)
            logger.info(f"Page loaded: {url}")

            # Wait for key element if specified
            if template.wait_for_selector:
                await page.wait_for_selector(template.wait_for_selector, timeout=60000)
                logger.info(f"Waited for selector: {template.wait_for_selector}")

            # Extract data from current page
            page_num = 1
            while page_num <= template.max_pages:
                logger.info(f"Extracting data from page {page_num}")

                # Get page HTML
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'lxml')

                # Extract each field
                extracted_row, field_errors = await self._extract_fields(page, soup, template.fields)
                all_data.append(extracted_row)

                # Log field extraction results
                successful_fields = len([v for v in extracted_row.values() if v is not None])
                total_fields = len(template.fields)
                logger.info(f"Extracted {successful_fields}/{total_fields} fields successfully")

                if field_errors:
                    logger.warning(f"Field extraction issues: {len(field_errors)} fields had errors")
                    for field_name, error in field_errors.items():
                        logger.warning(f"  - {field_name}: {error}")

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

            logger.info(f"Extracted {len(all_data)} rows of data")

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
            logger.error(f"Error extracting data from {url}: {e}")
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
        page: Page,
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

        for field in fields:
            try:
                value = await self._extract_single_field(page, soup, field)
                extracted[field.name] = value

                # Track if we got a None or default value (potential extraction failure)
                if value is None and field.required:
                    field_errors[field.name] = f"Required field returned None (selector: {field.selector or field.xpath or 'N/A'})"
                    logger.warning(f"⚠ Field '{field.name}' extraction returned None. Selector: {field.selector}")
                elif value == field.default_value and field.default_value is not None:
                    logger.info(f"Field '{field.name}' used default value: {field.default_value}")

            except Exception as e:
                error_msg = f"Error extracting field: {str(e)}"
                field_errors[field.name] = error_msg
                logger.error(f"✗ Error extracting field '{field.name}': {e}")

                if field.required:
                    extracted[field.name] = None
                else:
                    extracted[field.name] = field.default_value

        return extracted, field_errors

    async def _extract_single_field(
        self,
        page: Page,
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
            # Create DataFrame
            df = pd.DataFrame(data)

            # Create Excel file in memory
            output = BytesIO()

            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Extracted Data', index=False)

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
                for row_num, row_data in enumerate(data, start=1):
                    for col_num, col_name in enumerate(df.columns):
                        value = row_data.get(col_name, '')
                        # Check if value is missing (—, empty, or null)
                        if value in ['—', '', None] or (isinstance(value, str) and value.strip() == '—'):
                            worksheet.write(row_num, col_num, value, missing_format)
                        else:
                            worksheet.write(row_num, col_num, value)

                # Auto-adjust column widths
                for i, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).str.len().max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(i, i, min(max_len, 50))

            output.seek(0)
            logger.info(f"Exported {len(data)} rows to Excel")

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
