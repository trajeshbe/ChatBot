"""
Excel Generator

This module generates rich Excel files with formatting, charts, and summaries.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows
import os

logger = logging.getLogger(__name__)


class ExcelGenerator:
    """
    Generate rich Excel files with formatting

    Features:
    - Header formatting
    - Column auto-sizing
    - Data formatting
    - Summary sheet
    - Charts (optional)
    """

    def __init__(self):
        """Initialize Excel generator"""
        pass

    async def generate(
        self,
        data: pd.DataFrame,
        output_path: str,
        template_schema: Optional[Dict[str, Any]] = None,
        include_summary: bool = True,
        include_charts: bool = False,
        sheet_name: str = "Data"
    ) -> str:
        """
        Generate Excel file with rich formatting

        Args:
            data: DataFrame to export
            output_path: Path to save Excel file
            template_schema: Optional template schema for formatting hints
            include_summary: Whether to include summary sheet
            include_charts: Whether to include charts
            sheet_name: Name of the data sheet

        Returns:
            Path to generated Excel file
        """
        logger.info(f"Generating Excel file: {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write DataFrame to Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write data sheet
                data.to_excel(writer, sheet_name=sheet_name, index=False)

                # Write summary sheet if requested
                if include_summary:
                    summary = self._create_summary(data)
                    summary.to_excel(writer, sheet_name='Summary', index=False)

            # Apply formatting
            self._apply_formatting(output_path, sheet_name)

            # Add charts if requested
            if include_charts and include_summary:
                self._add_charts(output_path, data)

            file_size = os.path.getsize(output_path)
            logger.info(f"Excel file generated: {output_path} ({file_size} bytes)")

            return output_path

        except Exception as e:
            logger.error(f"Error generating Excel file: {str(e)}")
            raise

    def _create_summary(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create summary statistics sheet

        Args:
            data: DataFrame to summarize

        Returns:
            Summary DataFrame
        """
        summary_data = {
            'Metric': [],
            'Value': []
        }

        # Total records
        summary_data['Metric'].append('Total Records')
        summary_data['Value'].append(len(data))

        # Complete records (no nulls)
        complete_records = data.dropna().shape[0]
        summary_data['Metric'].append('Complete Records')
        summary_data['Value'].append(complete_records)

        # Completion rate
        completion_rate = (complete_records / len(data) * 100) if len(data) > 0 else 0
        summary_data['Metric'].append('Completion Rate')
        summary_data['Value'].append(f"{completion_rate:.2f}%")

        # Total columns
        summary_data['Metric'].append('Total Columns')
        summary_data['Value'].append(len(data.columns))

        # Column completeness
        for col in data.columns:
            non_null = data[col].notna().sum()
            col_completeness = (non_null / len(data) * 100) if len(data) > 0 else 0
            summary_data['Metric'].append(f"{col} Completeness")
            summary_data['Value'].append(f"{col_completeness:.2f}%")

        return pd.DataFrame(summary_data)

    def _apply_formatting(self, file_path: str, sheet_name: str):
        """
        Apply rich formatting to Excel file

        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to format
        """
        try:
            # Load workbook
            wb = load_workbook(file_path)
            ws = wb[sheet_name]

            # Define styles
            header_fill = PatternFill(
                start_color="4472C4",
                end_color="4472C4",
                fill_type="solid"
            )
            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_alignment = Alignment(horizontal='center', vertical='center')

            border = Border(
                left=Side(style='thin', color='000000'),
                right=Side(style='thin', color='000000'),
                top=Side(style='thin', color='000000'),
                bottom=Side(style='thin', color='000000')
            )

            # Apply header formatting
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border

            # Apply borders to all cells
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=ws.max_column):
                for cell in row:
                    cell.border = border
                    cell.alignment = Alignment(vertical='top', wrap_text=True)

            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass

                # Set width (with limits)
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = max(adjusted_width, 12)

            # Freeze header row
            ws.freeze_panes = 'A2'

            # Save workbook
            wb.save(file_path)

        except Exception as e:
            logger.warning(f"Could not apply Excel formatting: {str(e)}")

    def _add_charts(self, file_path: str, data: pd.DataFrame):
        """
        Add charts to Excel file

        Args:
            file_path: Path to Excel file
            data: DataFrame for chart data
        """
        try:
            wb = load_workbook(file_path)

            # Only add charts if Summary sheet exists
            if 'Summary' not in wb.sheetnames:
                return

            ws_summary = wb['Summary']

            # Create bar chart for column completeness
            # (This is a simple example - can be expanded)
            chart = BarChart()
            chart.title = "Data Completeness"
            chart.x_axis.title = "Metric"
            chart.y_axis.title = "Percentage"

            # Add chart to summary sheet
            # Note: This is a simplified version
            # Real implementation would parse summary data properly

            wb.save(file_path)

        except Exception as e:
            logger.warning(f"Could not add charts to Excel: {str(e)}")


# Export
__all__ = ['ExcelGenerator']
