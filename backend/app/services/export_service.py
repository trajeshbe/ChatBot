"""
Export Service - Generate files from templates
Supports: Excel, Word, Markdown, JSON
"""

import json
import io
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting data using templates.
    Generates files in various formats: Excel, Word, Markdown, JSON, PDF
    """

    def __init__(self):
        self.supported_formats = ['excel', 'word', 'markdown', 'json', 'pdf']

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

                # Add content
                if content:
                    # Split content by paragraphs and add each
                    paragraphs = str(content).split('\n')
                    for para_text in paragraphs:
                        if para_text.strip():  # Skip empty lines
                            p = doc.add_paragraph(para_text)
                            p.paragraph_format.line_spacing = formatting.get('line_spacing', 1.15)

                logger.info(f"Generated Word document with simple title/content format")
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

            logger.info("Generated JSON document")
            return json_content.encode('utf-8'), 'application/json'

        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            raise

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
