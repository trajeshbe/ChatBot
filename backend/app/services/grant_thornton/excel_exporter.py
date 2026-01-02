"""
Grant Thornton Excel Exporter

Generates Excel output with all extracted data, sub-calculations, and financial ratios.

Excel Structure:
- Sheet 1: Extracted Data (50+ datapoints with page numbers, definitions, references)
- Sheet 2: Sub-Calculations (12+ intermediate formulas with results)
- Sheet 3: Financial Ratios (30+ ratios across 4 categories)
- Sheet 4: Summary (metadata, statistics, extraction info)

Author: Claude Code
Date: 2026-01-01
"""

import logging
from typing import List, Optional
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.schemas.grant_thornton_schemas import (
    ExtractedDatapoint,
    SubCalculationFormula,
    FinancialRatios,
    GrantThorntonExtractionResponse
)

logger = logging.getLogger(__name__)


class ExcelExporter:
    """
    Excel exporter for Grant Thornton extraction results.

    Features:
    - Professional formatting (headers, colors, borders)
    - Multiple sheets (Data, Sub-Calcs, Ratios, Summary)
    - Metadata and statistics
    - Conditional formatting (success/failed status)
    """

    def __init__(self):
        # Styling
        self.header_font = Font(bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.success_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        self.failed_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    def export(
        self,
        response: GrantThorntonExtractionResponse,
        output_path: str
    ) -> str:
        """
        Export extraction response to Excel.

        Args:
            response: Complete extraction response
            output_path: Path to save Excel file

        Returns:
            Path to saved Excel file
        """
        logger.info(f"📊 Exporting to Excel: {output_path}")

        # Create workbook
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Sheet 1: Extracted Data
        self._create_datapoints_sheet(wb, response.extracted_datapoints)

        # Sheet 2: Sub-Calculations
        if response.sub_calculations:
            self._create_sub_calculations_sheet(wb, response.sub_calculations)

        # Sheet 3: Financial Ratios
        if response.financial_ratios:
            self._create_ratios_sheet(wb, response.financial_ratios)

        # Sheet 4: Summary
        self._create_summary_sheet(wb, response)

        # Save
        wb.save(output_path)
        logger.info(f"✅ Excel exported: {output_path}")

        return output_path

    def _create_datapoints_sheet(
        self,
        wb: Workbook,
        datapoints: List[ExtractedDatapoint]
    ):
        """Create Extracted Data sheet"""
        ws = wb.create_sheet("Extracted Data")

        # Headers
        headers = [
            "Field Name",
            "Definition",
            "Typical Location",
            "Extracted Value",
            "Page Number",
            "Reference Notes",
            "Status"
        ]

        ws.append(headers)

        # Style header row
        for cell in ws[1]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = self.border

        # Data rows
        for dp in datapoints:
            ws.append([
                dp.field_name,
                dp.definition,
                dp.typical_location or "N/A",
                dp.value,
                dp.page_no,
                dp.reference_notes,
                dp.extraction_status
            ])

        # Apply styling to data rows
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=len(datapoints) + 1), start=2):
            for cell in row:
                cell.border = self.border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

            # Status column conditional formatting
            status_cell = row[6]  # Status column
            if status_cell.value == "success":
                status_cell.fill = self.success_fill
            elif status_cell.value in ["failed", "error", "parse_error"]:
                status_cell.fill = self.failed_fill

        # Column widths
        ws.column_dimensions['A'].width = 30  # Field Name
        ws.column_dimensions['B'].width = 50  # Definition
        ws.column_dimensions['C'].width = 20  # Typical Location
        ws.column_dimensions['D'].width = 15  # Value
        ws.column_dimensions['E'].width = 12  # Page Number
        ws.column_dimensions['F'].width = 40  # Reference Notes
        ws.column_dimensions['G'].width = 12  # Status

        # Freeze header row
        ws.freeze_panes = "A2"

    def _create_sub_calculations_sheet(
        self,
        wb: Workbook,
        sub_calculations: List[SubCalculationFormula]
    ):
        """Create Sub-Calculations sheet"""
        ws = wb.create_sheet("Sub-Calculations")

        # Headers
        headers = [
            "Sub-Field Name",
            "Formula",
            "Calculated Value",
            "Status",
            "Error Message"
        ]

        ws.append(headers)

        # Style header row
        for cell in ws[1]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = self.border

        # Data rows
        for sc in sub_calculations:
            ws.append([
                sc.sub_field_name,
                sc.formula,
                sc.calculated_value if sc.calculated_value is not None else "N/A",
                sc.calculation_status,
                sc.error_message or "N/A"
            ])

        # Apply styling
        for row in ws.iter_rows(min_row=2, max_row=len(sub_calculations) + 1):
            for cell in row:
                cell.border = self.border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

            # Status conditional formatting
            status_cell = row[3]
            if status_cell.value == "success":
                status_cell.fill = self.success_fill
            elif status_cell.value == "failed":
                status_cell.fill = self.failed_fill

        # Column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 30

        ws.freeze_panes = "A2"

    def _create_ratios_sheet(
        self,
        wb: Workbook,
        financial_ratios: FinancialRatios
    ):
        """Create Financial Ratios sheet"""
        ws = wb.create_sheet("Financial Ratios")

        # Headers
        headers = ["Category", "Ratio Name", "Value"]
        ws.append(headers)

        # Style header
        for cell in ws[1]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = self.border

        # Define ratio categories
        ratio_categories = {
            "Liquidity Ratios": [
                ("Current Ratio", financial_ratios.current_ratio),
                ("Quick Ratio", financial_ratios.quick_ratio),
                ("Cash Ratio", financial_ratios.cash_ratio),
            ],
            "Leverage Ratios": [
                ("Debt to Equity", financial_ratios.debt_to_equity),
                ("Debt to Assets", financial_ratios.debt_to_assets),
                ("Equity Ratio", financial_ratios.equity_ratio),
                ("Interest Coverage", financial_ratios.interest_coverage),
            ],
            "Profitability Ratios": [
                ("Return on Equity (ROE)", financial_ratios.return_on_equity),
                ("Return on Assets (ROA)", financial_ratios.return_on_assets),
                ("EBITDA Margin", financial_ratios.ebitda_margin),
                ("Net Profit Margin", financial_ratios.net_profit_margin),
            ],
            "Efficiency Ratios": [
                ("Asset Turnover", financial_ratios.asset_turnover),
                ("Inventory Turnover", financial_ratios.inventory_turnover),
                ("Receivables Turnover", financial_ratios.receivables_turnover),
                ("Days Sales Outstanding (DSO)", financial_ratios.days_sales_outstanding),
                ("Days Inventory Outstanding (DIO)", financial_ratios.days_inventory_outstanding),
                ("Days Payable Outstanding (DPO)", financial_ratios.days_payable_outstanding),
                ("Cash Conversion Cycle", financial_ratios.cash_conversion_cycle),
            ]
        }

        # Populate data
        for category, ratios in ratio_categories.items():
            for ratio_name, value in ratios:
                ws.append([
                    category,
                    ratio_name,
                    value if value is not None else "N/A"
                ])

        # Apply styling
        current_row = 2
        for category, ratios in ratio_categories.items():
            for _ in ratios:
                for cell in ws[current_row]:
                    cell.border = self.border
                    cell.alignment = Alignment(vertical="center")

                current_row += 1

        # Column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 15

        ws.freeze_panes = "A2"

    def _create_summary_sheet(
        self,
        wb: Workbook,
        response: GrantThorntonExtractionResponse
    ):
        """Create Summary sheet"""
        ws = wb.create_sheet("Summary", 0)  # Insert as first sheet

        # Title
        ws['A1'] = "Grant Thornton Financial Analysis - Extraction Summary"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:B1')

        # Document Info
        row = 3
        ws[f'A{row}'] = "Document Information"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        info_data = [
            ("MD5 Hash", response.md5_hash),
            ("Company Name", response.company_name or "N/A"),
            ("Processing Time", f"{response.processing_time_seconds:.1f} seconds" if response.processing_time_seconds else "N/A"),
            ("Status", response.status),
        ]

        for label, value in info_data:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = value
            row += 1

        # Extraction Statistics
        row += 1
        ws[f'A{row}'] = "Extraction Statistics"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        success_count = sum(1 for dp in response.extracted_datapoints if dp.extraction_status == "success")
        total_count = len(response.extracted_datapoints)
        success_rate = success_count / total_count if total_count > 0 else 0

        stats_data = [
            ("Total Datapoints", response.total_datapoints),
            ("Successfully Extracted", success_count),
            ("Failed Extractions", total_count - success_count),
            ("Success Rate", f"{success_rate:.1%}"),
        ]

        for label, value in stats_data:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = value
            row += 1

        # Calculations Info
        if response.sub_calculations:
            row += 1
            ws[f'A{row}'] = "Calculations"
            ws[f'A{row}'].font = Font(bold=True)
            row += 1

            success_sub_calcs = sum(
                1 for sc in response.sub_calculations
                if sc.calculation_status == "success"
            )

            calc_data = [
                ("Sub-Calculations", len(response.sub_calculations)),
                ("Successful", success_sub_calcs),
                ("Financial Ratios", sum(
                    1 for v in vars(response.financial_ratios).values()
                    if v is not None
                ) if response.financial_ratios else 0),
            ]

            for label, value in calc_data:
                ws[f'A{row}'] = label
                ws[f'B{row}'] = value
                row += 1

        # Column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 40


# Singleton instance
_exporter = None


def get_exporter() -> ExcelExporter:
    """Get or create Excel exporter singleton"""
    global _exporter
    if _exporter is None:
        _exporter = ExcelExporter()
    return _exporter


def export_to_excel(
    response: GrantThorntonExtractionResponse,
    output_path: str
) -> str:
    """
    Export extraction response to Excel.

    Args:
        response: Complete extraction response
        output_path: Path to save Excel file

    Returns:
        Path to saved Excel file
    """
    exporter = get_exporter()
    return exporter.export(response, output_path)
