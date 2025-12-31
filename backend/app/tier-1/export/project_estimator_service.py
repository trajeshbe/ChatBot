"""
Project Estimator Service

Generates Business Requirement Documents (BRD) and cost estimation sheets
from project scope descriptions using LLM-powered analysis.
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.services.llm_service import llm_service
from app.services.template_parser_service import template_parser_service

logger = logging.getLogger(__name__)


class ProjectEstimatorService:
    """
    Service for generating project estimation documents.

    Features:
    - LLM-powered project scope analysis
    - BRD (Business Requirement Document) generation in Word format
    - Cost estimation spreadsheet generation with formulas
    """

    def __init__(self):
        self.output_dir = Path(tempfile.gettempdir()) / "project_estimates"
        self.output_dir.mkdir(exist_ok=True)

    async def generate_estimation(
        self,
        project_scope: str,
        scope_file_content: Optional[str] = None,
        sample_data_content: Optional[str] = None,
        reference_brd_content: Optional[str] = None,
        cost_template_content: Optional[str] = None,
        model_id: str = "gpt-4-turbo",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate BRD and cost estimation from project scope.

        Args:
            project_scope: Text description of project scope
            scope_file_content: Optional file content (extracted from uploaded scope files)
            sample_data_content: Optional sample data content (for complexity analysis)
            reference_brd_content: Optional reference BRD templates (for structure guidance)
            cost_template_content: Optional historical cost templates (for rate extraction)
            model_id: LLM model to use for analysis
            config: Configuration parameters (hourly_rate, contingency, etc.)

        Returns:
            Dict with paths to generated documents and summary data
        """
        try:
            # Merge text and file content
            full_scope = project_scope
            if scope_file_content:
                full_scope = f"{project_scope}\n\n{scope_file_content}"

            # Default configuration
            if config is None:
                config = {
                    "hourly_rate": 100,
                    "infrastructure_cost_percentage": 15,
                    "contingency_percentage": 10,
                    "project_manager_hours_percentage": 15,
                    "qa_hours_percentage": 20
                }

            # Step 1: Analyze project scope with LLM
            logger.info("Analyzing project scope with LLM...")
            analysis = await self._analyze_project_scope(full_scope, model_id)

            # Step 2: Generate BRD document
            logger.info("Generating BRD document...")
            brd_path = await self._generate_brd(analysis)

            # Step 3: Generate cost estimation Excel
            logger.info("Generating cost estimation Excel...")
            excel_path = await self._generate_cost_estimation(analysis, config)

            # Calculate summary metrics
            total_effort_hours = sum(
                phase.get("effort_hours", 0)
                for phase in analysis.get("phases", [])
            )
            # Use development_rate as base for quick estimate
            base_rate = config.get("development_rate", 30)
            total_cost = total_effort_hours * base_rate

            # Add infrastructure and contingency
            one_time_infra = config.get("one_time_infrastructure", 280)
            monthly_bau = config.get("monthly_bau", 1030)
            infrastructure_cost = one_time_infra + (monthly_bau * 12)  # 1 year BAU

            contingency_pct = config.get("contingency_percentage", 10)
            contingency_cost = total_cost * (contingency_pct / 100)
            total_cost_final = total_cost + infrastructure_cost + contingency_cost

            # PHASE 3: Template Analysis (if reference files provided)
            template_analysis = None
            if any([sample_data_content, reference_brd_content, cost_template_content]):
                logger.info("Performing template analysis on uploaded reference files")

                try:
                    # Count files
                    sample_file_count = len(sample_data_content.split("=== Sample File:")) - 1 if sample_data_content else 0
                    brd_file_count = 1 if reference_brd_content else 0
                    cost_template_count = len(cost_template_content.split("=== Cost Template:")) - 1 if cost_template_content else 0

                    # Parse cost templates
                    parsed_cost_templates = []
                    if cost_template_content:
                        for template_section in cost_template_content.split("=== Cost Template:")[1:]:
                            parsed = template_parser_service.parse_excel_cost_template(template_section)
                            parsed_cost_templates.append(parsed)

                    # Parse BRD template
                    parsed_brd = None
                    if reference_brd_content:
                        parsed_brd = template_parser_service.parse_brd_template(reference_brd_content)

                    # Analyze sample data
                    sample_analysis = None
                    if sample_data_content:
                        sample_analysis = template_parser_service.analyze_sample_data(
                            sample_data_content,
                            sample_file_count
                        )

                    # Match to best template
                    best_match = template_parser_service.match_templates(
                        full_scope,
                        parsed_cost_templates
                    )

                    # Generate quality metrics
                    quality_metrics = template_parser_service.generate_quality_metrics(
                        scope_file_content is not None,
                        sample_file_count,
                        reference_brd_content is not None,
                        cost_template_count
                    )

                    # Build template analysis response
                    template_analysis = {
                        "files_processed": {
                            "scope_documents": 1 if scope_file_content else 0,
                            "sample_files": sample_file_count,
                            "brd_templates": brd_file_count,
                            "cost_templates": cost_template_count
                        },
                        "best_match": {
                            "template_name": best_match.get("best_match", "N/A"),
                            "similarity_score": best_match.get("similarity_score", 0.0),
                            "match_reasons": best_match.get("match_reasons", []),
                            "confidence": best_match.get("confidence_level", "LOW")
                        },
                        "applied_rates": None,
                        "quality_metrics": quality_metrics,
                        "sample_data_analysis": sample_analysis,
                        "brd_structure": parsed_brd,
                        "recommendations": []
                    }

                    # Extract and apply rates if found
                    if parsed_cost_templates and parsed_cost_templates[0].get("averaged_rates"):
                        template_analysis["applied_rates"] = {
                            "source": best_match.get("best_match", "Historical templates"),
                            "rates": parsed_cost_templates[0]["averaged_rates"],
                            "confidence": best_match.get("confidence_level", "LOW")
                        }

                    # Generate recommendations
                    recommendations = []
                    if sample_analysis and sample_analysis.get("complexity_level") == "high":
                        recommendations.append(
                            f"Project complexity is {sample_analysis['complexity_level']} based on "
                            f"{sample_file_count} sample files. Consider increasing testing allocation by 10%."
                        )
                    if quality_metrics.get("completeness_score", 0) < 70:
                        recommendations.append(
                            "Estimation quality could be improved by providing more reference documents."
                        )
                    if parsed_brd:
                        recommendations.append(
                            f"BRD template structure identified with {len(parsed_brd.get('sections_found', []))} sections. "
                            "Generated BRD will follow this structure."
                        )

                    template_analysis["recommendations"] = recommendations

                    logger.info(f"Template analysis complete: {quality_metrics.get('confidence_level')} confidence")

                except Exception as e:
                    logger.error(f"Error during template analysis: {e}")
                    # Continue without template analysis rather than failing
                    template_analysis = {
                        "error": str(e),
                        "files_processed": {
                            "scope_documents": 1 if scope_file_content else 0,
                            "sample_files": 0,
                            "brd_templates": 1 if reference_brd_content else 0,
                            "cost_templates": 0
                        }
                    }

            # Build response
            response = {
                "brd_url": f"/api/v1/project-estimator/download/{os.path.basename(brd_path)}",
                "cost_estimation_url": f"/api/v1/project-estimator/download/{os.path.basename(excel_path)}",
                "project_name": analysis.get("project_name", "Untitled Project"),
                "total_cost": round(total_cost_final, 2),
                "total_effort_hours": round(total_effort_hours, 2),
                "generated_at": datetime.now().isoformat()
            }

            # Add template analysis if available
            if template_analysis:
                response["template_analysis"] = template_analysis

            return response

        except Exception as e:
            logger.error(f"Error generating estimation: {e}")
            raise

    async def _analyze_project_scope(
        self,
        scope: str,
        model_id: str
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze project scope and extract structured information.
        """
        prompt = f"""
You are an expert project manager and business analyst. Analyze the following project scope and extract detailed information.

Project Scope:
{scope}

Please provide a comprehensive analysis in JSON format with the following structure:
{{
    "project_name": "Short project name",
    "executive_summary": "2-3 sentence summary",
    "objectives": ["objective 1", "objective 2", ...],
    "functional_requirements": ["requirement 1", "requirement 2", ...],
    "non_functional_requirements": ["requirement 1", "requirement 2", ...],
    "technology_stack": {{
        "frontend": ["technology 1", ...],
        "backend": ["technology 1", ...],
        "database": ["technology 1", ...],
        "infrastructure": ["technology 1", ...]
    }},
    "team_structure": [
        {{"role": "Role Name", "count": 1, "responsibilities": "Description"}},
        ...
    ],
    "phases": [
        {{
            "phase_name": "Phase 1: Planning",
            "duration_weeks": 2,
            "effort_hours": 160,
            "tasks": [
                {{"task_name": "Task 1", "effort_hours": 40, "role": "Role"}},
                ...
            ]
        }},
        ...
    ],
    "assumptions": ["assumption 1", ...],
    "risks": ["risk 1", ...],
    "success_criteria": ["criteria 1", ...]
}}

Ensure the analysis is thorough, realistic, and based on industry best practices.
"""

        try:
            # Get LLM response
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                model=model_id,
                temperature=0.3  # Lower temperature for more consistent output
            )

            # Parse JSON from response
            import json
            analysis_text = response.get("content", "{}")

            # Extract JSON from markdown code blocks if present
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

            analysis = json.loads(analysis_text)
            logger.info(f"Successfully analyzed project: {analysis.get('project_name')}")

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing project scope: {e}")
            # Return default structure
            return {
                "project_name": "Project Estimation",
                "executive_summary": "Project analysis",
                "objectives": ["To be defined"],
                "functional_requirements": ["To be defined"],
                "non_functional_requirements": ["To be defined"],
                "technology_stack": {
                    "frontend": ["React"],
                    "backend": ["Python/FastAPI"],
                    "database": ["PostgreSQL"],
                    "infrastructure": ["Docker"]
                },
                "team_structure": [
                    {"role": "Developer", "count": 2, "responsibilities": "Development"}
                ],
                "phases": [
                    {
                        "phase_name": "Phase 1: Development",
                        "duration_weeks": 8,
                        "effort_hours": 320,
                        "tasks": [
                            {"task_name": "Development", "effort_hours": 320, "role": "Developer"}
                        ]
                    }
                ],
                "assumptions": ["Standard development practices"],
                "risks": ["Technical complexity"],
                "success_criteria": ["Project completion"]
            }

    async def _generate_brd(self, analysis: Dict[str, Any]) -> str:
        """
        Generate Business Requirement Document in Word format.
        """
        doc = Document()

        # Title
        title = doc.add_heading(f"Business Requirements Document", 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Subtitle
        subtitle = doc.add_heading(analysis.get("project_name", "Project"), 1)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Document info
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        doc.add_page_break()

        # Executive Summary
        doc.add_heading("1. Executive Summary", 1)
        doc.add_paragraph(analysis.get("executive_summary", ""))

        # Objectives
        doc.add_heading("2. Project Objectives", 1)
        for obj in analysis.get("objectives", []):
            doc.add_paragraph(obj, style='List Bullet')

        # Functional Requirements
        doc.add_heading("3. Functional Requirements", 1)
        for req in analysis.get("functional_requirements", []):
            doc.add_paragraph(req, style='List Bullet')

        # Non-Functional Requirements
        doc.add_heading("4. Non-Functional Requirements", 1)
        for req in analysis.get("non_functional_requirements", []):
            doc.add_paragraph(req, style='List Bullet')

        # Technology Stack
        doc.add_heading("5. Technology Stack", 1)
        tech_stack = analysis.get("technology_stack", {})
        for category, technologies in tech_stack.items():
            doc.add_heading(category.replace("_", " ").title(), 2)
            for tech in technologies:
                doc.add_paragraph(tech, style='List Bullet')

        # Team Structure
        doc.add_heading("6. Team Structure", 1)
        for member in analysis.get("team_structure", []):
            role_para = doc.add_paragraph()
            role_para.add_run(f"{member.get('role')} ({member.get('count')} person(s)): ").bold = True
            role_para.add_run(member.get('responsibilities', ''))

        # Project Timeline
        doc.add_heading("7. Project Timeline and Phases", 1)
        for phase in analysis.get("phases", []):
            doc.add_heading(phase.get("phase_name", "Phase"), 2)
            doc.add_paragraph(f"Duration: {phase.get('duration_weeks')} weeks")
            doc.add_paragraph(f"Estimated Effort: {phase.get('effort_hours')} hours")
            doc.add_paragraph("Tasks:")
            for task in phase.get("tasks", []):
                task_para = doc.add_paragraph(style='List Bullet')
                task_para.add_run(f"{task.get('task_name')} ").bold = True
                task_para.add_run(f"({task.get('effort_hours')} hrs, {task.get('role')})")

        # Assumptions
        doc.add_heading("8. Assumptions", 1)
        for assumption in analysis.get("assumptions", []):
            doc.add_paragraph(assumption, style='List Bullet')

        # Risks
        doc.add_heading("9. Risks", 1)
        for risk in analysis.get("risks", []):
            doc.add_paragraph(risk, style='List Bullet')

        # Success Criteria
        doc.add_heading("10. Success Criteria", 1)
        for criteria in analysis.get("success_criteria", []):
            doc.add_paragraph(criteria, style='List Bullet')

        # Save document
        filename = f"BRD_{analysis.get('project_name', 'Project').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = self.output_dir / filename
        doc.save(str(filepath))

        logger.info(f"BRD generated: {filepath}")
        return str(filepath)

    async def _generate_cost_estimation(
        self,
        analysis: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """
        Generate cost estimation Excel with multiple tabs and formulas.
        """
        wb = Workbook()

        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])

        # Create tabs
        self._create_lookup_tab(wb, config)
        self._create_unit_cost_tab(wb, config)
        self._create_aiml_cost_tab(wb, analysis, config)
        self._create_summary_tab(wb, analysis, config)
        self._create_resource_loading_tab(wb, analysis)

        # Save workbook
        filename = f"CostEstimation_{analysis.get('project_name', 'Project').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = self.output_dir / filename
        wb.save(str(filepath))

        logger.info(f"Cost estimation Excel generated: {filepath}")
        return str(filepath)

    def _create_lookup_tab(self, wb: Workbook, config: Dict[str, Any]):
        """Create lookup reference data tab with all configurable parameters."""
        ws = wb.create_sheet("lookup")

        # Headers
        headers = ["Parameter", "Value", "Unit"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

        # Data - ALL configurable parameters from config
        # Billing Rates (rows 2-7)
        data = [
            ["Planning Rate", config.get("planning_rate", config.get("hourly_rate", 25)), "$/hr"],
            ["Development Rate", config.get("development_rate", config.get("hourly_rate", 30)), "$/hr"],
            ["Testing Rate", config.get("testing_rate", config.get("hourly_rate", 25)), "$/hr"],
            ["UI Development Rate", config.get("ui_development_rate", config.get("hourly_rate", 22)), "$/hr"],
            ["Solution Architect Rate", config.get("solution_architect_rate", config.get("hourly_rate", 40)), "$/hr"],
            ["Scraping Development Rate", config.get("scraping_development_rate", config.get("hourly_rate", 22)), "$/hr"],

            # Overhead Percentages (rows 8-11)
            ["Solution Architect %", config.get("solution_architect_percentage", 10) / 100, "%"],
            ["Project Manager %", config.get("project_manager_percentage", config.get("project_manager_hours_percentage", 5)) / 100, "%"],
            ["Business Analyst %", config.get("business_analyst_percentage", 5) / 100, "%"],
            ["Contingency %", config.get("contingency_percentage", 10) / 100, "%"],

            # Testing Percentages (rows 12-14)
            ["Unit Testing %", config.get("unit_testing_percentage", 20) / 100, "%"],
            ["QA Testing %", config.get("qa_testing_percentage", config.get("qa_hours_percentage", 25)) / 100, "%"],
            ["Integration Testing %", config.get("integration_testing_percentage", 20) / 100, "%"],

            # Infrastructure Costs (rows 15-16)
            ["One-time Infrastructure", config.get("one_time_infrastructure", config.get("infrastructure_cost_percentage", 280)), "$"],
            ["Monthly BAU", config.get("monthly_bau", 1030), "$"],
        ]

        for row_idx, row_data in enumerate(data, 2):
            for col_idx, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # Auto-width columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = max_length + 2

    def _create_unit_cost_tab(self, wb: Workbook, config: Dict[str, Any]):
        """Create unit cost/rate card tab."""
        ws = wb.create_sheet("unit_cost")

        headers = ["Role", "Hourly Rate", "Daily Rate", "Monthly Rate"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

        # Standard rates based on development rate as base
        base_rate = config.get("development_rate", 30)  # Default to $30/hr if not found
        roles = [
            ("Senior Architect", base_rate * 1.5),
            ("Senior Developer", base_rate * 1.3),
            ("Developer", base_rate),
            ("Junior Developer", base_rate * 0.7),
            ("Project Manager", base_rate * 1.4),
            ("QA Engineer", base_rate * 0.9),
            ("DevOps Engineer", base_rate * 1.2),
            ("UI/UX Designer", base_rate * 1.1),
        ]

        for row_idx, (role, rate) in enumerate(roles, 2):
            ws.cell(row=row_idx, column=1, value=role)
            ws.cell(row=row_idx, column=2, value=rate)
            ws.cell(row=row_idx, column=3, value=f"=B{row_idx}*8")  # Daily = 8 hours
            ws.cell(row=row_idx, column=4, value=f"=B{row_idx}*160")  # Monthly = 160 hours

        # Format as currency
        for row in range(2, len(roles) + 2):
            for col in range(2, 5):
                ws.cell(row=row, column=col).number_format = '$#,##0.00'

        # Auto-width
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = max_length + 2

    def _get_rate_cell_reference(self, role: str) -> str:
        """
        Map role to appropriate rate cell reference in lookup tab.

        Lookup tab structure:
        Row 2: Planning Rate
        Row 3: Development Rate
        Row 4: Testing Rate
        Row 5: UI Development Rate
        Row 6: Solution Architect Rate
        Row 7: Scraping Development Rate
        """
        role_lower = role.lower() if role else ""

        # Planning-related roles
        if any(keyword in role_lower for keyword in ["planning", "analysis", "design", "assessment", "requirements", "architecture"]):
            return "lookup!$B$2"  # Planning Rate

        # Testing-related roles
        elif any(keyword in role_lower for keyword in ["test", "qa", "quality"]):
            return "lookup!$B$4"  # Testing Rate

        # UI-related roles
        elif any(keyword in role_lower for keyword in ["ui", "ux", "design", "frontend"]):
            return "lookup!$B$5"  # UI Development Rate

        # Solution Architect roles
        elif any(keyword in role_lower for keyword in ["architect", "solution", "technical lead"]):
            return "lookup!$B$6"  # Solution Architect Rate

        # Scraping-related roles
        elif any(keyword in role_lower for keyword in ["scraping", "scraper", "crawler", "extraction"]):
            return "lookup!$B$7"  # Scraping Development Rate

        # Integration-related roles (use development rate)
        elif any(keyword in role_lower for keyword in ["integration", "api", "connect"]):
            return "lookup!$B$3"  # Development Rate

        # Default to Development Rate for all other cases
        else:
            return "lookup!$B$3"  # Development Rate

    def _create_aiml_cost_tab(self, wb: Workbook, analysis: Dict[str, Any], config: Dict[str, Any]):
        """Create detailed task breakdown tab with formula-based rates."""
        ws = wb.create_sheet("AIML_cost")

        headers = ["Phase", "Task", "Role", "Hours", "Rate", "Cost"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

        row_idx = 2
        for phase in analysis.get("phases", []):
            for task in phase.get("tasks", []):
                ws.cell(row=row_idx, column=1, value=phase.get("phase_name"))
                ws.cell(row=row_idx, column=2, value=task.get("task_name"))
                role = task.get("role", "Development")
                ws.cell(row=row_idx, column=3, value=role)
                ws.cell(row=row_idx, column=4, value=task.get("effort_hours"))

                # Use formula reference to lookup tab instead of hardcoded value
                rate_reference = self._get_rate_cell_reference(role)
                ws.cell(row=row_idx, column=5, value=f"={rate_reference}")
                ws.cell(row=row_idx, column=6, value=f"=D{row_idx}*E{row_idx}")
                row_idx += 1

        # Total row
        total_row = row_idx
        ws.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True)
        ws.cell(row=total_row, column=4, value=f"=SUM(D2:D{total_row-1})").font = Font(bold=True)
        ws.cell(row=total_row, column=6, value=f"=SUM(F2:F{total_row-1})").font = Font(bold=True)

        # Format
        for row in range(2, total_row + 1):
            ws.cell(row=row, column=5).number_format = '$#,##0.00'
            ws.cell(row=row, column=6).number_format = '$#,##0.00'

        # Auto-width
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = max_length + 2

    def _create_summary_tab(self, wb: Workbook, analysis: Dict[str, Any], config: Dict[str, Any]):
        """Create cost summary tab."""
        ws = wb.create_sheet("AIML_COST_SUMMARY", 0)  # Make it first tab

        # Title
        ws.merge_cells('A1:C1')
        title_cell = ws['A1']
        title_cell.value = f"Cost Estimation Summary - {analysis.get('project_name')}"
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = Alignment(horizontal='center')

        # Summary data
        row = 3
        ws.cell(row, 1, "Category").font = Font(bold=True)
        ws.cell(row, 2, "Amount").font = Font(bold=True)

        row += 1
        ws.cell(row, 1, "Base Development Cost")
        ws.cell(row, 2, "=SUM(AIML_cost!F:F)")

        row += 1
        # Infrastructure: One-time + Annual BAU
        one_time_infra = config.get("one_time_infrastructure", 280)
        monthly_bau = config.get("monthly_bau", 1030)
        annual_infra = one_time_infra + (monthly_bau * 12)
        ws.cell(row, 1, "Infrastructure (One-time + Annual BAU)")
        ws.cell(row, 2, annual_infra)

        row += 1
        contingency_pct = config.get("contingency_percentage", 10)
        ws.cell(row, 1, f"Contingency ({contingency_pct}%)")
        ws.cell(row, 2, f"=B{row-2}*{contingency_pct/100}")

        row += 2
        ws.cell(row, 1, "TOTAL PROJECT COST").font = Font(bold=True, size=14)
        ws.cell(row, 2, f"=SUM(B4:B{row-1})").font = Font(bold=True, size=14)

        # Format currency
        for r in range(4, row + 1):
            ws.cell(r, 2).number_format = '$#,##0.00'

        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20

    def _create_resource_loading_tab(self, wb: Workbook, analysis: Dict[str, Any]):
        """Create resource allocation/loading tab."""
        ws = wb.create_sheet("Resource Loading")

        headers = ["Role", "Phase", "Allocation %", "Hours per Week", "Total Hours"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

        row_idx = 2
        for phase in analysis.get("phases", []):
            # Group tasks by role
            role_hours = {}
            for task in phase.get("tasks", []):
                role = task.get("role", "Unknown")
                hours = task.get("effort_hours", 0)
                role_hours[role] = role_hours.get(role, 0) + hours

            # Add rows for each role
            for role, hours in role_hours.items():
                duration_weeks = phase.get("duration_weeks", 1)
                ws.cell(row=row_idx, column=1, value=role)
                ws.cell(row=row_idx, column=2, value=phase.get("phase_name"))
                ws.cell(row=row_idx, column=3, value=100)  # 100% allocation
                ws.cell(row=row_idx, column=4, value=hours / duration_weeks if duration_weeks > 0 else hours)
                ws.cell(row=row_idx, column=5, value=hours)
                row_idx += 1

        # Auto-width
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = max_length + 2


# Singleton instance
project_estimator_service = ProjectEstimatorService()
