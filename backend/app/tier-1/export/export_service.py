"""
Export Service - Generate files from templates
Supports: Excel, Word, Markdown, JSON
Enhanced with markdown parsing for chat responses
"""

import json
import io
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from uuid import UUID

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting data using templates.
    Generates files in various formats: Excel, Word, Markdown, JSON, PDF
    Enhanced with markdown parsing for chat responses
    """

    def __init__(self):
        self.supported_formats = ['excel', 'word', 'markdown', 'json', 'pdf']

    # ==================== Markdown Parsing Helpers ====================

    def _parse_markdown_tables(self, content: str) -> List[Tuple[int, List[List[str]]]]:
        """
        Extract markdown tables from content.

        Returns:
            List of (start_position, table_data) tuples
            table_data is a list of rows (including headers)
        """
        tables = []
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check if this looks like a table row (contains |)
            if '|' in line and line.count('|') >= 2:
                # Check if next line is a separator (---|---|)
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'\|[\s\-:\|]+\|', next_line):
                        # This is a table!
                        table_start = i
                        table_rows = []

                        # Parse header
                        header_cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                        table_rows.append(header_cells)

                        # Skip separator
                        i += 2

                        # Parse data rows
                        while i < len(lines):
                            row_line = lines[i].strip()
                            if '|' in row_line and row_line.count('|') >= 2:
                                row_cells = [cell.strip() for cell in row_line.split('|') if cell.strip()]
                                table_rows.append(row_cells)
                                i += 1
                            else:
                                break

                        tables.append((table_start, table_rows))
                        continue

            i += 1

        return tables

    def _parse_markdown_headers(self, content: str) -> List[Tuple[int, str, str]]:
        """
        Extract markdown headers.

        Returns:
            List of (level, text, original_line) tuples
        """
        headers = []
        for line in content.split('\n'):
            # Match # Header or ## Header etc.
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headers.append((level, text, line))

        return headers

    def _parse_markdown_lists(self, content: str) -> List[Tuple[str, List[str]]]:
        """
        Extract markdown lists (bullet and numbered).

        Returns:
            List of (list_type, items) tuples
            list_type: 'bullet' or 'numbered'
        """
        lists = []
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Bullet list (-, *, +)
            if re.match(r'^[\-\*\+]\s+', line):
                list_items = []
                while i < len(lines):
                    item_match = re.match(r'^[\-\*\+]\s+(.+)$', lines[i].strip())
                    if item_match:
                        list_items.append(item_match.group(1))
                        i += 1
                    else:
                        break
                lists.append(('bullet', list_items))
                continue

            # Numbered list (1., 2., etc.)
            elif re.match(r'^\d+\.\s+', line):
                list_items = []
                while i < len(lines):
                    item_match = re.match(r'^\d+\.\s+(.+)$', lines[i].strip())
                    if item_match:
                        list_items.append(item_match.group(1))
                        i += 1
                    else:
                        break
                lists.append(('numbered', list_items))
                continue

            i += 1

        return lists

    def _parse_markdown_code_blocks(self, content: str) -> List[Tuple[str, str]]:
        """
        Extract code blocks with language info.

        Returns:
            List of (language, code) tuples
        """
        code_blocks = []

        # Find code blocks with ```language
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            code_blocks.append((language, code))

        return code_blocks

    def _strip_markdown_formatting(self, text: str) -> str:
        """
        Remove markdown formatting for plain text extraction.

        Removes: **bold**, *italic*, `code`, [links](url), etc.
        """
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Remove bold
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)

        # Remove italic
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)

        # Remove links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove images ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        return text

    async def export_data(
        self,
        template_config: Dict[str, Any],
        template_type: str,
        content: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> tuple[bytes, str]:
        """
        Export data using a template.

        Args:
            template_config: Template configuration (JSONB)
            template_type: Type of export (excel, word, markdown, json)
            content: Content to export
            variables: Additional variables for template substitution

        Returns:
            Tuple of (file_bytes, mime_type)
        """
        if template_type not in self.supported_formats:
            raise ValueError(f"Unsupported template type: {template_type}")

        # Parse content if it's JSON string
        try:
            data = json.loads(content) if isinstance(content, str) and content.startswith('{') else content
        except json.JSONDecodeError:
            data = content

        # Generate file based on type
        if template_type == 'excel':
            return await self._generate_excel(template_config, data, variables)
        elif template_type == 'word':
            return await self._generate_word(template_config, data, variables)
        elif template_type == 'markdown':
            return await self._generate_markdown(template_config, data, variables)
        elif template_type == 'json':
            return await self._generate_json(template_config, data, variables)
        else:
            raise ValueError(f"Template type {template_type} not yet implemented")

    async def _generate_excel(
        self,
        config: Dict[str, Any],
        data: Any,
        variables: Optional[Dict[str, Any]] = None
    ) -> tuple[bytes, str]:
        """
        Generate Excel file from template.
        Enhanced to extract markdown tables from chat responses.

        Config format:
        {
            "sheets": [
                {
                    "name": "Sheet1",
                    "columns": ["Col1", "Col2", ...],
                    "formatting": {
                        "header_style": {"bold": true, "bg_color": "#4472C4", "font_color": "white"},
                        "freeze_panes": "A2"
                    }
                }
            ]
        }
        """
        try:
            wb = Workbook()
            wb.remove(wb.active)  # Remove default sheet

            # If data is a markdown string, extract tables
            if isinstance(data, str):
                markdown_tables = self._parse_markdown_tables(data)

                if markdown_tables:
                    # Create sheets from extracted tables
                    for idx, (start_pos, table_data) in enumerate(markdown_tables, start=1):
                        sheet_name = f"Table_{idx}"
                        ws = wb.create_sheet(title=sheet_name)

                        # Write table data
                        for row_idx, row_data in enumerate(table_data, start=1):
                            for col_idx, cell_value in enumerate(row_data, start=1):
                                cell = ws.cell(row=row_idx, column=col_idx, value=cell_value)

                                # Apply header formatting to first row
                                if row_idx == 1:
                                    cell.font = Font(bold=True, color='FFFFFF')
                                    cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
                                    cell.alignment = Alignment(horizontal='center', vertical='center')

                        # Auto-adjust column widths
                        for column in ws.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 50)
                            ws.column_dimensions[column_letter].width = adjusted_width

                        # Freeze header row
                        ws.freeze_panes = 'A2'

                    # Save to bytes
                    output = io.BytesIO()
                    wb.save(output)
                    output.seek(0)

                    logger.info(f"Generated Excel file with {len(markdown_tables)} extracted tables")
                    return output.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

                else:
                    # No tables found, create sheet with plain text
                    ws = wb.create_sheet(title="Content")
                    ws.cell(row=1, column=1, value="Content")
                    ws.cell(row=1, column=1).font = Font(bold=True)

                    # Split content into lines
                    lines = data.split('\n')
                    for idx, line in enumerate(lines[:1000], start=2):  # Limit to 1000 lines
                        if line.strip():
                            ws.cell(row=idx, column=1, value=self._strip_markdown_formatting(line))

                    ws.column_dimensions['A'].width = 100

                    output = io.BytesIO()
                    wb.save(output)
                    output.seek(0)

                    logger.info("Generated Excel file with plain text content (no tables found)")
                    return output.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

            sheets_config = config.get('sheets', [])

            for sheet_config in sheets_config:
                sheet_name = sheet_config.get('name', 'Sheet1')
                columns = sheet_config.get('columns', [])
                formatting = sheet_config.get('formatting', {})

                ws = wb.create_sheet(title=sheet_name)

                # Write headers
                for col_idx, col_name in enumerate(columns, start=1):
                    cell = ws.cell(row=1, column=col_idx, value=col_name)

                    # Apply header formatting
                    header_style = formatting.get('header_style', {})
                    if header_style.get('bold'):
                        cell.font = Font(bold=True, color=header_style.get('font_color', 'FFFFFF'))

                    bg_color = header_style.get('bg_color', '#4472C4').replace('#', '')
                    cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type='solid')
                    cell.alignment = Alignment(horizontal='center', vertical='center')

                # Write data
                if isinstance(data, dict):
                    # Handle different data structures
                    if sheet_name == "Entities" and 'entities' in data:
                        entities = data.get('entities', [])
                        for row_idx, entity in enumerate(entities, start=2):
                            ws.cell(row=row_idx, column=1, value=entity.get('type', ''))
                            ws.cell(row=row_idx, column=2, value=entity.get('name', ''))
                            ws.cell(row=row_idx, column=3, value=len(entity.get('mentions', [])))
                            ws.cell(row=row_idx, column=4, value=entity.get('first_mentioned', ''))

                    elif sheet_name == "Relationships" and 'relationships' in data:
                        relationships = data.get('relationships', [])
                        for row_idx, rel in enumerate(relationships, start=2):
                            ws.cell(row=row_idx, column=1, value=rel.get('source', ''))
                            ws.cell(row=row_idx, column=2, value=rel.get('relation', ''))
                            ws.cell(row=row_idx, column=3, value=rel.get('target', ''))
                            ws.cell(row=row_idx, column=4, value=rel.get('confidence', ''))

                    else:
                        # Generic key-value export
                        for row_idx, (key, value) in enumerate(data.items(), start=2):
                            ws.cell(row=row_idx, column=1, value=str(key))
                            ws.cell(row=row_idx, column=2, value=str(value))

                elif isinstance(data, list):
                    # List of dictionaries or lists
                    for row_idx, row_data in enumerate(data, start=2):
                        if isinstance(row_data, dict):
                            for col_idx, col_name in enumerate(columns, start=1):
                                ws.cell(row=row_idx, column=col_idx, value=str(row_data.get(col_name, '')))
                        elif isinstance(row_data, (list, tuple)):
                            for col_idx, value in enumerate(row_data, start=1):
                                ws.cell(row=row_idx, column=col_idx, value=str(value))

                # Auto-adjust column widths
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter].width = adjusted_width

                # Freeze panes
                freeze_panes = formatting.get('freeze_panes')
                if freeze_panes:
                    ws.freeze_panes = freeze_panes

            # Save to bytes
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            logger.info(f"Generated Excel file with {len(sheets_config)} sheets")
            return output.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        except Exception as e:
            logger.error(f"Error generating Excel file: {e}")
            raise

    async def _generate_word(
        self,
        config: Dict[str, Any],
        data: Any,
        variables: Optional[Dict[str, Any]] = None
    ) -> tuple[bytes, str]:
        """
        Generate Word document from template.
        Enhanced to parse markdown formatting from chat responses.

        Config format:
        {
            "sections": [
                {"type": "title", "style": "Heading 1"},
                {"type": "executive_summary", "style": "Normal"},
                {"type": "key_findings", "style": "Bullet List"}
            ],
            "formatting": {
                "font": "Calibri",
                "font_size": 11,
                "line_spacing": 1.15
            }
        }
        """
        try:
            doc = Document()
            sections_config = config.get('sections', [])
            formatting = config.get('formatting', {})

            # Parse content
            if isinstance(data, str):
                content_dict = {'content': data}
            else:
                content_dict = data

            # Handle simple title/content format (when no sections provided)
            if not sections_config:
                # Check if config has title/content directly (frontend format)
                title = config.get('title', content_dict.get('title', 'Exported Content'))
                content = config.get('content', content_dict.get('content', data if isinstance(data, str) else str(data)))

                # Add title
                heading = doc.add_heading(title, level=1)
                heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

                # Add content with markdown parsing
                if content:
                    self._add_markdown_to_word(doc, str(content), formatting)

                logger.info(f"Generated Word document with markdown-parsed content")
            else:
                # Add sections (original logic)
                for section_config in sections_config:
                    section_type = section_config.get('type')
                    style = section_config.get('style', 'Normal')

                    if section_type == 'title':
                        title = content_dict.get('title', 'Document Title')
                        heading = doc.add_heading(title, level=1)
                        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    elif section_type == 'executive_summary':
                        doc.add_heading('Executive Summary', level=2)
                        summary = content_dict.get('executive_summary', content_dict.get('summary', ''))
                        p = doc.add_paragraph(str(summary))
                        p.paragraph_format.line_spacing = formatting.get('line_spacing', 1.15)

                    elif section_type == 'key_findings':
                        doc.add_heading('Key Findings', level=2)
                        findings = content_dict.get('key_findings', content_dict.get('findings', []))
                        if isinstance(findings, list):
                            for finding in findings:
                                doc.add_paragraph(str(finding), style='List Bullet')
                        else:
                            doc.add_paragraph(str(findings), style='List Bullet')

                    elif section_type == 'recommendations':
                        doc.add_heading('Recommendations', level=2)
                        recommendations = content_dict.get('recommendations', [])
                        if isinstance(recommendations, list):
                            for idx, rec in enumerate(recommendations, start=1):
                                doc.add_paragraph(str(rec), style='List Number')
                        else:
                            doc.add_paragraph(str(recommendations), style='List Number')

                    elif section_type == 'conclusion':
                        doc.add_heading('Conclusion', level=2)
                        conclusion = content_dict.get('conclusion', '')
                        p = doc.add_paragraph(str(conclusion))
                        p.paragraph_format.line_spacing = formatting.get('line_spacing', 1.15)

                    else:
                        # Generic section
                        if section_type in content_dict:
                            doc.add_heading(section_type.replace('_', ' ').title(), level=2)
                            doc.add_paragraph(str(content_dict[section_type]))

            # Apply global formatting
            font_name = formatting.get('font', 'Calibri')
            font_size = formatting.get('font_size', 11)

            for paragraph in doc.paragraphs:
                for run in paragraph.runs:
                    run.font.name = font_name
                    run.font.size = Pt(font_size)

            # Save to bytes
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)

            logger.info(f"Generated Word document with {len(sections_config)} sections")
            return output.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

        except Exception as e:
            logger.error(f"Error generating Word document: {e}")
            raise

    def _add_markdown_to_word(self, doc: Document, content: str, formatting: Dict[str, Any]):
        """
        Parse markdown content and add formatted elements to Word document.
        Handles: headers, bold, italic, lists, code blocks, tables
        """
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check for headers (# Header)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2)
                doc.add_heading(text, level=min(level, 3))  # Word supports up to level 9, but keep it clean
                i += 1
                continue

            # Check for code blocks (```)
            if line.startswith('```'):
                # Extract code block
                code_lines = []
                i += 1  # Skip opening ```
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1

                if code_lines:
                    # Add code block with monospace font
                    code_text = '\n'.join(code_lines)
                    p = doc.add_paragraph(code_text)
                    p.style = 'No Spacing'

                    for run in p.runs:
                        run.font.name = 'Courier New'
                        run.font.size = Pt(9)

                    # Add light gray background
                    shading_elm = OxmlElement('w:shd')
                    shading_elm.set(qn('w:fill'), 'F5F5F5')
                    p._element.get_or_add_pPr().append(shading_elm)

                i += 1  # Skip closing ```
                continue

            # Check for tables (| col1 | col2 |)
            if '|' in line and line.count('|') >= 2:
                # Check if next line is separator
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'\|[\s\-:\|]+\|', next_line):
                        # This is a table!
                        table_rows = []

                        # Parse header
                        header_cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                        table_rows.append(header_cells)

                        # Skip separator
                        i += 2

                        # Parse data rows
                        while i < len(lines):
                            row_line = lines[i].strip()
                            if '|' in row_line and row_line.count('|') >= 2:
                                row_cells = [cell.strip() for cell in row_line.split('|') if cell.strip()]
                                table_rows.append(row_cells)
                                i += 1
                            else:
                                break

                        # Add table to Word document
                        if table_rows:
                            num_cols = len(table_rows[0])
                            table = doc.add_table(rows=len(table_rows), cols=num_cols)
                            table.style = 'Light Grid Accent 1'

                            for row_idx, row_data in enumerate(table_rows):
                                for col_idx, cell_value in enumerate(row_data):
                                    if col_idx < num_cols:
                                        cell = table.rows[row_idx].cells[col_idx]
                                        cell.text = cell_value

                                        # Bold header row
                                        if row_idx == 0:
                                            for paragraph in cell.paragraphs:
                                                for run in paragraph.runs:
                                                    run.font.bold = True

                        continue

            # Check for bullet list (-, *, +)
            if re.match(r'^[\-\*\+]\s+', line):
                list_items = []
                while i < len(lines):
                    item_match = re.match(r'^[\-\*\+]\s+(.+)$', lines[i].strip())
                    if item_match:
                        list_items.append(item_match.group(1))
                        i += 1
                    else:
                        break

                # Add bullet list
                for item in list_items:
                    p = doc.add_paragraph(item, style='List Bullet')
                    self._apply_inline_formatting(p, formatting)

                continue

            # Check for numbered list (1., 2., etc.)
            if re.match(r'^\d+\.\s+', line):
                list_items = []
                while i < len(lines):
                    item_match = re.match(r'^\d+\.\s+(.+)$', lines[i].strip())
                    if item_match:
                        list_items.append(item_match.group(1))
                        i += 1
                    else:
                        break

                # Add numbered list
                for item in list_items:
                    p = doc.add_paragraph(item, style='List Number')
                    self._apply_inline_formatting(p, formatting)

                continue

            # Regular paragraph with inline formatting
            p = doc.add_paragraph()
            self._add_formatted_text(p, line)
            p.paragraph_format.line_spacing = formatting.get('line_spacing', 1.15)

            i += 1

    def _add_formatted_text(self, paragraph, text: str):
        """
        Add text to paragraph with inline markdown formatting.
        Handles: **bold**, *italic*, `code`
        """
        # Parse inline formatting with regex
        # Pattern matches: **bold**, *italic*, `code`
        pattern = r'(\*\*[^\*]+\*\*|\*[^\*]+\*|`[^`]+`)'
        parts = re.split(pattern, text)

        for part in parts:
            if not part:
                continue

            # Bold (**text**)
            if part.startswith('**') and part.endswith('**'):
                run = paragraph.add_run(part[2:-2])
                run.bold = True

            # Italic (*text*)
            elif part.startswith('*') and part.endswith('*') and not part.startswith('**'):
                run = paragraph.add_run(part[1:-1])
                run.italic = True

            # Code (`text`)
            elif part.startswith('`') and part.endswith('`'):
                run = paragraph.add_run(part[1:-1])
                run.font.name = 'Courier New'
                run.font.size = Pt(9)

            # Regular text
            else:
                paragraph.add_run(part)

    def _apply_inline_formatting(self, paragraph, formatting: Dict[str, Any]):
        """Apply formatting config to paragraph"""
        paragraph.paragraph_format.line_spacing = formatting.get('line_spacing', 1.15)

        font_name = formatting.get('font', 'Calibri')
        font_size = formatting.get('font_size', 11)

        for run in paragraph.runs:
            run.font.name = font_name
            run.font.size = Pt(font_size)

    async def _generate_markdown(
        self,
        config: Dict[str, Any],
        data: Any,
        variables: Optional[Dict[str, Any]] = None
    ) -> tuple[bytes, str]:
        """
        Generate Markdown file from template.

        Config format:
        {
            "template": "# {title}\n\n## Overview\n{overview}\n\n...",
            "table_format": "github_flavored_markdown"
        }
        """
        try:
            template = config.get('template', '')

            # Parse data
            if isinstance(data, str):
                # If data is already formatted text, use it directly
                markdown_content = data
            elif isinstance(data, dict):
                # Substitute variables in template
                markdown_content = template
                for key, value in data.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in markdown_content:
                        # Handle table formatting
                        if isinstance(value, list) and key == 'table':
                            table_md = self._format_table_markdown(value)
                            markdown_content = markdown_content.replace(placeholder, table_md)
                        else:
                            markdown_content = markdown_content.replace(placeholder, str(value))

                # Add any remaining data not in template
                if not template:
                    markdown_content = self._dict_to_markdown(data)
            else:
                markdown_content = str(data)

            # Add metadata footer
            markdown_content += f"\n\n---\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

            logger.info("Generated Markdown document")
            return markdown_content.encode('utf-8'), 'text/markdown'

        except Exception as e:
            logger.error(f"Error generating Markdown: {e}")
            raise

    async def _generate_json(
        self,
        config: Dict[str, Any],
        data: Any,
        variables: Optional[Dict[str, Any]] = None
    ) -> tuple[bytes, str]:
        """
        Generate JSON file from template.
        Enhanced to extract structured data from markdown.

        Config format:
        {
            "structure": {
                "metadata": {...},
                "summary_stats": {...},
                "detailed_data": "array"
            }
        }
        """
        try:
            structure = config.get('structure', {})

            # If data already matches structure, use it
            if isinstance(data, dict):
                output_data = data
            elif isinstance(data, str):
                # Extract structured data from markdown string
                output_data = {
                    'content': data,
                    'generated_at': datetime.now().isoformat(),
                    'structured_data': self._extract_structured_data_from_markdown(data)
                }
            else:
                # Try to structure the data
                output_data = {
                    'content': str(data),
                    'generated_at': datetime.now().isoformat()
                }

            # Add metadata if not present
            if 'metadata' not in output_data and structure.get('metadata'):
                output_data['metadata'] = {
                    'generated_at': datetime.now().isoformat(),
                    'template_applied': True
                }

            # Format with indentation
            json_content = json.dumps(output_data, indent=2, ensure_ascii=False)

            logger.info("Generated JSON document with structured data extraction")
            return json_content.encode('utf-8'), 'application/json'

        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            raise

    def _extract_structured_data_from_markdown(self, content: str) -> Dict[str, Any]:
        """
        Extract structured data from markdown content.
        Returns a dictionary with parsed elements (headers, lists, tables, etc.)
        """
        structured = {
            'headers': [],
            'tables': [],
            'lists': [],
            'code_blocks': [],
            'plain_text': []
        }

        # Extract headers
        headers = self._parse_markdown_headers(content)
        structured['headers'] = [
            {'level': level, 'text': text}
            for level, text, _ in headers
        ]

        # Extract tables
        tables = self._parse_markdown_tables(content)
        structured['tables'] = [
            {
                'headers': table_data[0] if table_data else [],
                'rows': table_data[1:] if len(table_data) > 1 else [],
                'num_rows': len(table_data) - 1 if table_data else 0,
                'num_columns': len(table_data[0]) if table_data else 0
            }
            for _, table_data in tables
        ]

        # Extract lists
        lists = self._parse_markdown_lists(content)
        structured['lists'] = [
            {'type': list_type, 'items': items}
            for list_type, items in lists
        ]

        # Extract code blocks
        code_blocks = self._parse_markdown_code_blocks(content)
        structured['code_blocks'] = [
            {'language': lang, 'code': code}
            for lang, code in code_blocks
        ]

        # Extract plain text (without formatting)
        plain_text = self._strip_markdown_formatting(content)
        structured['plain_text'] = plain_text.strip()

        return structured

    def _format_table_markdown(self, table_data: list) -> str:
        """Format list of dicts/lists as markdown table"""
        if not table_data:
            return ""

        if isinstance(table_data[0], dict):
            headers = list(table_data[0].keys())
            rows = [[str(row.get(h, '')) for h in headers] for row in table_data]
        elif isinstance(table_data[0], (list, tuple)):
            headers = [f"Column {i+1}" for i in range(len(table_data[0]))]
            rows = [[str(cell) for cell in row] for row in table_data]
        else:
            return str(table_data)

        # Build markdown table
        header_row = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"
        data_rows = ["| " + " | ".join(row) + " |" for row in rows]

        return "\n".join([header_row, separator] + data_rows)

    def _dict_to_markdown(self, data: dict) -> str:
        """Convert dict to readable markdown"""
        md_lines = []

        for key, value in data.items():
            title = key.replace('_', ' ').title()
            md_lines.append(f"## {title}")

            if isinstance(value, list):
                for item in value:
                    md_lines.append(f"- {item}")
            elif isinstance(value, dict):
                md_lines.append(json.dumps(value, indent=2))
            else:
                md_lines.append(str(value))

            md_lines.append("")  # Blank line

        return "\n".join(md_lines)


# Singleton instance
export_service = ExportService()
