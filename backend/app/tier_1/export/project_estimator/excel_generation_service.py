"""
Excel Generation Service - Enhanced for LangGraph State

Generates multi-sheet Excel cost estimation files from LangGraph workflow state.

This service consumes the ProjectEstimatorState from the 6-agent workflow:
- Master Summary (rollup from costs_by_team)
- Project Workflow & Timeline (from project_workflow)
- Per-Team Sheets (one sheet per team from tasks_by_team)
- Infrastructure Details
- BAU Monthly Costs (if Full Service)

Author: AI Assistant
Date: 2025-11-21
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelGenerationService:
    """
    Generate multi-sheet Excel cost estimation files from LangGraph state.

    Consumes ProjectEstimatorState with:
    - costs_by_team: Per-team cost breakdown with summary
    - tasks_by_team: Per-team task lists
    - project_workflow: Execution phases and timeline
    - rate_config: UI-provided rates
    - project_type: POC, Staff Augmentation, or Full Service
    """

    def __init__(self):
        """Initialize Excel generation service"""
        logger.info("ExcelGenerationService initialized (LangGraph-enhanced)")

    def generate_from_state(
        self,
        state: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate complete Excel cost estimation from LangGraph workflow state.

        Args:
            state: ProjectEstimatorState from LangGraph workflow containing:
                - user_prompt: Project description
                - project_type: POC, Staff Augmentation, or Full Service
                - scenario: baseline, conservative, or aggressive
                - costs_by_team: Per-team cost breakdown with summary
                - tasks_by_team: Per-team task lists
                - project_workflow: Execution phases and timeline
                - rate_config: UI-provided rates
                - overhead_config: Overhead percentages
            output_path: Path where Excel file should be saved

        Returns:
            Path to generated Excel file
        """
        logger.info(f"Generating cost estimation Excel from LangGraph state at {output_path}")

        try:
            wb = Workbook()

            # Remove default sheet
            if 'Sheet' in wb.sheetnames:
                wb.remove(wb['Sheet'])

            # Extract data from state
            costs_by_team = state.get("costs_by_team", {})
            tasks_by_team = state.get("tasks_by_team", {})
            project_workflow = state.get("project_workflow", {})
            rate_config = state.get("rate_config", {})
            overhead_config = state.get("overhead_config", {})
            project_type = state.get("project_type", "")
            scenario = state.get("scenario", "baseline")
            user_prompt = state.get("user_prompt", "")

            # Sheet 1: Master Summary (rollup from costs_by_team)
            self._create_master_summary_sheet(
                wb, costs_by_team, project_workflow, project_type, scenario, user_prompt
            )

            # Sheet 2: Project Workflow & Timeline (NEW!)
            if project_workflow and project_workflow.get("workflow"):
                self._create_workflow_timeline_sheet(wb, project_workflow)

            # Sheets 3-N: Per-Team Sheets (one for each team)
            for team_name, team_tasks in tasks_by_team.items():
                if team_tasks:  # Only create sheet if team has tasks
                    team_costs = costs_by_team.get(team_name, {})
                    self._create_team_sheet(
                        wb, team_name, team_tasks, team_costs, rate_config
                    )

            # Sheet N-1: Infrastructure Details
            self._create_infrastructure_sheet(wb, costs_by_team, project_type)

            # Sheet N: BAU Monthly Costs (if Full Service)
            if project_type == "Full Service":
                self._create_bau_sheet(wb, costs_by_team)

            # Save workbook
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            wb.save(output_path)

            logger.info(f"Excel file created successfully: {output_path}")
            logger.info(f"  - Teams: {len(tasks_by_team)}")
            logger.info(f"  - Total sheets: {len(wb.sheetnames)}")
            return output_path

        except Exception as e:
            logger.error(f"Error creating Excel file: {e}", exc_info=True)
            raise

    # ========================================================================
    # SHEET CREATION METHODS
    # ========================================================================

    def _create_master_summary_sheet(
        self,
        wb: Workbook,
        costs_by_team: Dict[str, Any],
        project_workflow: Dict[str, Any],
        project_type: str,
        scenario: str,
        user_prompt: str
    ):
        """
        Create Master Summary sheet with rollup from costs_by_team.

        Sheet structure:
        - Project information
        - High-level cost summary (from costs_by_team['summary'])
        - Team breakdown
        - Phase breakdown (from project_workflow)
        """
        ws = wb.create_sheet("Master Summary", 0)

        # Title section
        ws['A1'] = "Project Cost Estimation - Master Summary"
        ws['A1'].font = Font(size=16, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws.merge_cells('A1:D1')

        # Project info
        row = 3
        ws[f'A{row}'] = "Project Information"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1

        # Extract summary from costs_by_team
        summary = costs_by_team.get("summary", {})
        workflow = project_workflow.get("workflow", {})

        info_items = [
            ("Project Type:", project_type),
            ("Scenario:", scenario.capitalize()),
            ("Total Duration:", f"{workflow.get('total_duration_weeks', 0)} weeks"),
            ("Total Teams:", summary.get("team_count", 0)),
            ("Generated:", datetime.now().strftime('%Y-%m-%d %H:%M'))
        ]

        for label, value in info_items:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = value
            ws[f'A{row}'].font = Font(bold=True)
            row += 1

        # Cost summary
        row += 2
        ws[f'A{row}'] = "Cost Summary"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1

        total_cost = summary.get("total_cost", 0)
        total_hours = summary.get("total_hours", 0)
        base_cost = summary.get("base_cost", 0)
        overhead_cost = summary.get("overhead_cost", 0)

        summary_data = [
            ("Total Development Hours:", total_hours, "hours"),
            ("Base Development Cost:", base_cost, "$"),
            ("Overhead & Contingency:", overhead_cost, "$"),
            ("", "", ""),
            ("Total Project Cost:", total_cost, "$"),
        ]

        for label, value, unit in summary_data:
            if label:
                ws[f'A{row}'] = label
                ws[f'A{row}'].font = Font(bold=True)
                if isinstance(value, (int, float)):
                    ws[f'B{row}'] = value
                    ws[f'B{row}'].number_format = '#,##0.00' if unit == "$" else '#,##0'
                else:
                    ws[f'B{row}'] = value
                ws[f'C{row}'] = unit
            row += 1

        # Highlight total row
        total_row = row - 1
        for col in ['A', 'B', 'C']:
            ws[f'{col}{total_row}'].font = Font(size=12, bold=True, color="FFFFFF")
            ws[f'{col}{total_row}'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        # Team breakdown
        row += 2
        ws[f'A{row}'] = "Cost Breakdown by Team"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1

        # Headers
        ws[f'A{row}'] = "Team"
        ws[f'B{row}'] = "Hours"
        ws[f'C{row}'] = "Cost ($)"
        for col in ['A', 'B', 'C']:
            ws[f'{col}{row}'].font = Font(bold=True)
            ws[f'{col}{row}'].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        row += 1

        # Team rows
        for team_name, team_data in costs_by_team.items():
            if team_name != "summary" and isinstance(team_data, dict):
                ws[f'A{row}'] = team_data.get("team_name", team_name)
                ws[f'B{row}'] = team_data.get("total_hours", 0)
                ws[f'B{row}'].number_format = '#,##0'
                ws[f'C{row}'] = team_data.get("total_cost", 0)
                ws[f'C{row}'].number_format = '$#,##0.00'
                row += 1

        # Column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 20

    def _create_workflow_timeline_sheet(
        self,
        wb: Workbook,
        project_workflow: Dict[str, Any]
    ):
        """
        Create Project Workflow & Timeline sheet (NEW!).

        Sheet structure:
        - Project phases with durations
        - Deliverables per phase
        - Dependencies
        - Milestones
        """
        ws = wb.create_sheet("Project Workflow & Timeline")

        # Title
        ws['A1'] = "Project Workflow & Timeline"
        ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws.merge_cells('A1:E1')

        workflow = project_workflow.get("workflow", {})
        phases = workflow.get("phases", [])
        milestones = workflow.get("milestones", [])

        # Phases section
        row = 3
        ws[f'A{row}'] = "Execution Phases"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1

        # Headers
        headers = ["Phase", "Phase Name", "Duration", "Tasks", "Deliverables"]
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col_num)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        row += 1

        # Phase rows
        for phase in phases:
            phase_num = phase.get("phase_number", "")
            phase_name = phase.get("phase_name", "")
            duration = f"{phase.get('duration_weeks', 0)} weeks"
            tasks = ", ".join(phase.get("tasks", []))[:50] + "..." if len(", ".join(phase.get("tasks", []))) > 50 else ", ".join(phase.get("tasks", []))
            deliverables = "\n".join(f"• {d}" for d in phase.get("deliverables", [])[:3])

            ws[f'A{row}'] = phase_num
            ws[f'B{row}'] = phase_name
            ws[f'C{row}'] = duration
            ws[f'D{row}'] = tasks
            ws[f'E{row}'] = deliverables
            ws[f'E{row}'].alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[row].height = max(15 * len(phase.get("deliverables", [])[:3]), 20)

            row += 1

        # Milestones section
        row += 2
        ws[f'A{row}'] = "Project Milestones"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1

        # Milestone headers
        ws[f'A{row}'] = "Milestone"
        ws[f'B{row}'] = "Week"
        for col in ['A', 'B']:
            ws[f'{col}{row}'].font = Font(bold=True)
            ws[f'{col}{row}'].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        row += 1

        # Milestone rows
        for milestone in milestones:
            ws[f'A{row}'] = milestone.get("name", "")
            ws[f'B{row}'] = f"Week {milestone.get('week', 0)}"
            row += 1

        # Column widths
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 50

    def _create_team_sheet(
        self,
        wb: Workbook,
        team_name: str,
        team_tasks: List[Dict[str, Any]],
        team_costs: Dict[str, Any],
        rate_config: Dict[str, Any]
    ):
        """
        Create per-team sheet with task breakdown.

        Sheet structure:
        - Team summary (hours, cost)
        - Detailed task list with effort and rates
        - Task-level cost calculations
        """
        # Clean team name for sheet title (Excel limit: 31 chars)
        sheet_title = team_name[:31]
        ws = wb.create_sheet(sheet_title)

        # Title
        ws['A1'] = f"{team_name} - Task Breakdown"
        ws['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws.merge_cells('A1:F1')

        # Team summary
        row = 3
        ws[f'A{row}'] = "Team Summary"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1

        total_hours = team_costs.get("total_hours", 0)
        total_cost = team_costs.get("total_cost", 0)

        ws[f'A{row}'] = "Total Hours:"
        ws[f'B{row}'] = total_hours
        ws[f'B{row}'].number_format = '#,##0'
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        ws[f'A{row}'] = "Total Cost:"
        ws[f'B{row}'] = total_cost
        ws[f'B{row}'].number_format = '$#,##0.00'
        ws[f'A{row}'].font = Font(bold=True)
        row += 2

        # Task breakdown
        ws[f'A{row}'] = "Task Breakdown"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1

        # Headers
        headers = ["Task #", "Task Description", "Rate Category", "Effort (Hours)", "Rate ($/hr)", "Cost ($)"]
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col_num)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        row += 1

        # Task rows
        for task in team_tasks:
            task_num = task.get("task_number", "")
            task_name = task.get("task_name", "")
            rate_category = task.get("rate_category", "")
            effort_hours = task.get("effort_hours", 0)
            rate = task.get("rate", 0)
            cost = task.get("cost", effort_hours * rate)

            ws.cell(row=row, column=1, value=task_num)
            ws.cell(row=row, column=2, value=task_name)
            ws.cell(row=row, column=3, value=rate_category)
            ws.cell(row=row, column=4, value=effort_hours).number_format = '#,##0'
            ws.cell(row=row, column=5, value=rate).number_format = '$#,##0.00'
            ws.cell(row=row, column=6, value=cost).number_format = '$#,##0.00'

            # Bold main task numbers (no decimal)
            if '.' not in str(task_num):
                for col in range(1, 7):
                    ws.cell(row=row, column=col).font = Font(bold=True)

            row += 1

        # Team total row
        row += 1
        ws[f'A{row}'] = "TEAM TOTAL"
        ws[f'D{row}'] = total_hours
        ws[f'F{row}'] = total_cost
        for col in ['A', 'D', 'F']:
            ws[f'{col}{row}'].font = Font(size=11, bold=True, color="FFFFFF")
            ws[f'{col}{row}'].fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        ws[f'D{row}'].number_format = '#,##0'
        ws[f'F{row}'].number_format = '$#,##0.00'

        # Column widths
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 15

    def _create_infrastructure_sheet(
        self,
        wb: Workbook,
        costs_by_team: Dict[str, Any],
        project_type: str
    ):
        """Create infrastructure costs sheet"""
        ws = wb.create_sheet("Infrastructure")

        # Title
        ws['A1'] = "Infrastructure Costs"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:D1')

        # One-time costs
        row = 3
        ws[f'A{row}'] = "One-Time Setup Costs"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        ws[f'A{row}'].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        ws.merge_cells(f'A{row}:C{row}')
        row += 1

        # Headers
        ws[f'A{row}'] = "Item"
        ws[f'B{row}'] = "Description"
        ws[f'C{row}'] = "Cost ($)"
        for col in ['A', 'B', 'C']:
            ws[f'{col}{row}'].font = Font(bold=True)
        row += 1

        # Infrastructure items
        infra_items = [
            ("Cloud Infrastructure", "VM setup and configuration", 500),
            ("Database Setup", "PostgreSQL with pgvector", 200),
            ("Storage", "S3/MinIO storage setup", 100),
            ("CI/CD Pipeline", "GitHub Actions / GitLab CI", 150),
        ]

        total_infra = 0
        for item, desc, cost in infra_items:
            ws[f'A{row}'] = item
            ws[f'B{row}'] = desc
            ws[f'C{row}'] = cost
            ws[f'C{row}'].number_format = '$#,##0.00'
            total_infra += cost
            row += 1

        # Total
        row += 1
        ws[f'A{row}'] = "TOTAL INFRASTRUCTURE"
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'C{row}'] = total_infra
        ws[f'C{row}'].number_format = '$#,##0.00'
        ws[f'C{row}'].font = Font(bold=True)

        # Column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 15

    def _create_bau_sheet(
        self,
        wb: Workbook,
        costs_by_team: Dict[str, Any]
    ):
        """Create BAU (Business As Usual) monthly costs sheet"""
        ws = wb.create_sheet("BAU Monthly Costs")

        # Title
        ws['A1'] = "Business As Usual (BAU) Monthly Costs"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:D1')

        row = 3
        ws[f'A{row}'] = "Cost Component"
        ws[f'B{row}'] = "Description"
        ws[f'C{row}'] = "Monthly Cost ($)"
        for col in ['A', 'B', 'C']:
            ws[f'{col}{row}'].font = Font(bold=True)
            ws[f'{col}{row}'].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        row += 1

        # BAU components
        bau_items = [
            ("Infrastructure", "Cloud hosting + Database + Storage", 400),
            ("LLM API Costs", "Monthly API usage (@$0.10/doc, 1000 docs)", 100),
            ("Support Hours", "20 hours/month @ $30/hr", 600),
            ("Monitoring & Logging", "APM and observability tools", 100),
        ]

        total_bau = 0
        for component, desc, cost in bau_items:
            ws[f'A{row}'] = component
            ws[f'B{row}'] = desc
            ws[f'C{row}'] = cost
            ws[f'C{row}'].number_format = '$#,##0.00'
            total_bau += cost
            row += 1

        # Total
        row += 1
        ws[f'A{row}'] = "TOTAL MONTHLY BAU"
        ws[f'A{row}'].font = Font(size=12, bold=True, color="FFFFFF")
        ws[f'A{row}'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws[f'C{row}'] = total_bau
        ws[f'C{row}'].number_format = '$#,##0.00'
        ws[f'C{row}'].font = Font(size=12, bold=True, color="FFFFFF")
        ws[f'C{row}'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        # Column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 45
        ws.column_dimensions['C'].width = 18
