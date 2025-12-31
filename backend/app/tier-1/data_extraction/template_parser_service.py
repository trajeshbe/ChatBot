"""
Template Parser Service for Project Estimator

Parses uploaded reference templates to extract valuable patterns:
- Excel cost templates: rates, formulas, project metrics
- BRD templates: document structure and sections
- Sample data: complexity indicators
"""

import logging
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from docx import Document as DocxDocument
import io

logger = logging.getLogger(__name__)


class TemplateParserService:
    """Parse and analyze uploaded reference templates."""

    def __init__(self):
        self.logger = logger

    def parse_excel_cost_template(self, content: str) -> Dict[str, Any]:
        """
        Parse Excel cost template to extract rates, formulas, and patterns.

        Args:
            content: Raw Excel content extracted as text

        Returns:
            Dict containing extracted rates, formulas, and metrics
        """
        try:
            self.logger.info("Parsing Excel cost template")

            # Initialize result structure
            result = {
                "rates_found": {},
                "formulas_detected": [],
                "project_metrics": {},
                "phases_identified": [],
                "raw_patterns": []
            }

            # Split content into sheets
            sheets = content.split("=== Sheet:")

            for sheet in sheets:
                if not sheet.strip():
                    continue

                lines = sheet.split("\n")
                sheet_name = lines[0].strip() if lines else "Unknown"

                self.logger.info(f"Processing sheet: {sheet_name}")

                # Extract rates (looking for patterns like "$XX/hour", "XX per hour")
                rate_patterns = [
                    r'\$?(\d+\.?\d*)\s*(?:per\s+hour|/hour|hourly)',
                    r'rate[:\s]+\$?(\d+\.?\d*)',
                    r'(\d+\.?\d*)\s*(?:USD|dollars?)\s*(?:per\s+hour|/hour)'
                ]

                for line in lines[1:]:  # Skip sheet name
                    line_lower = line.lower()

                    # Find rates
                    for pattern in rate_patterns:
                        matches = re.findall(pattern, line_lower)
                        if matches:
                            for match in matches:
                                try:
                                    rate_value = float(match)
                                    # Try to identify role from context
                                    role = "unknown"
                                    if "developer" in line_lower or "dev" in line_lower:
                                        role = "developer"
                                    elif "architect" in line_lower or "tech lead" in line_lower:
                                        role = "architect"
                                    elif "pm" in line_lower or "project manager" in line_lower:
                                        role = "project_manager"
                                    elif "qa" in line_lower or "test" in line_lower:
                                        role = "qa"
                                    elif "design" in line_lower:
                                        role = "designer"

                                    if role not in result["rates_found"]:
                                        result["rates_found"][role] = []
                                    result["rates_found"][role].append(rate_value)
                                except ValueError:
                                    continue

                    # Detect formulas (look for formula keywords)
                    if any(keyword in line_lower for keyword in ['formula', 'calculation', '=', 'sum', 'total']):
                        result["formulas_detected"].append(line.strip())

                    # Extract project metrics
                    if "total hours" in line_lower or "effort" in line_lower:
                        numbers = re.findall(r'(\d+\.?\d*)', line)
                        if numbers:
                            result["project_metrics"]["total_hours"] = float(numbers[0])

                    if "total cost" in line_lower or "budget" in line_lower:
                        numbers = re.findall(r'\$?(\d+\.?\d*)', line)
                        if numbers:
                            result["project_metrics"]["total_cost"] = float(numbers[0])

                    # Identify phases
                    phase_keywords = ['planning', 'design', 'development', 'testing', 'deployment', 'phase']
                    if any(keyword in line_lower for keyword in phase_keywords):
                        phase_match = re.search(r'(planning|design|development|testing|deployment|phase\s+\d+)', line_lower)
                        if phase_match and phase_match.group(1) not in result["phases_identified"]:
                            result["phases_identified"].append(phase_match.group(1))

            # Calculate average rates per role
            averaged_rates = {}
            for role, rates in result["rates_found"].items():
                if rates:
                    averaged_rates[role] = sum(rates) / len(rates)

            result["averaged_rates"] = averaged_rates
            result["template_name"] = self._extract_template_name(content)

            self.logger.info(f"Extracted {len(averaged_rates)} role rates, "
                           f"{len(result['phases_identified'])} phases")

            return result

        except Exception as e:
            self.logger.error(f"Error parsing Excel cost template: {e}")
            return {
                "rates_found": {},
                "formulas_detected": [],
                "project_metrics": {},
                "phases_identified": [],
                "averaged_rates": {},
                "error": str(e)
            }

    def parse_brd_template(self, content: str) -> Dict[str, Any]:
        """
        Parse BRD template to extract document structure.

        Args:
            content: DOCX content extracted as text

        Returns:
            Dict containing BRD structure and sections
        """
        try:
            self.logger.info("Parsing BRD template structure")

            result = {
                "sections_found": [],
                "heading_levels": {},
                "section_patterns": [],
                "template_structure": {}
            }

            lines = content.split("\n")

            # Common BRD section patterns
            section_patterns = [
                r'^\s*(\d+\.?\d*)\s+(executive\s+summary|introduction|overview)',
                r'^\s*(\d+\.?\d*)\s+(project\s+objectives?|goals?)',
                r'^\s*(\d+\.?\d*)\s+(scope|scope\s+of\s+work)',
                r'^\s*(\d+\.?\d*)\s+(functional\s+requirements?)',
                r'^\s*(\d+\.?\d*)\s+(technical\s+requirements?)',
                r'^\s*(\d+\.?\d*)\s+(assumptions?|constraints?)',
                r'^\s*(\d+\.?\d*)\s+(timeline|schedule|milestones?)',
                r'^\s*(\d+\.?\d*)\s+(budget|cost|pricing)',
            ]

            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # Check for section headers
                for pattern in section_patterns:
                    match = re.search(pattern, line_stripped, re.IGNORECASE)
                    if match:
                        section_number = match.group(1)
                        section_name = match.group(2)
                        result["sections_found"].append({
                            "number": section_number,
                            "name": section_name,
                            "full_text": line_stripped
                        })

                # Detect heading levels (rough estimation)
                if line_stripped and (line_stripped[0].isdigit() or line_stripped.isupper()):
                    level = "main" if len(line_stripped.split()) <= 5 else "sub"
                    if level not in result["heading_levels"]:
                        result["heading_levels"][level] = 0
                    result["heading_levels"][level] += 1

            # Build template structure
            result["template_structure"] = {
                "total_sections": len(result["sections_found"]),
                "has_executive_summary": any("executive" in s["name"].lower() or "summary" in s["name"].lower()
                                            for s in result["sections_found"]),
                "has_objectives": any("objective" in s["name"].lower() or "goal" in s["name"].lower()
                                     for s in result["sections_found"]),
                "has_scope": any("scope" in s["name"].lower() for s in result["sections_found"]),
                "has_requirements": any("requirement" in s["name"].lower() for s in result["sections_found"]),
                "has_timeline": any("timeline" in s["name"].lower() or "schedule" in s["name"].lower()
                                   for s in result["sections_found"]),
            }

            self.logger.info(f"Extracted {len(result['sections_found'])} sections from BRD template")

            return result

        except Exception as e:
            self.logger.error(f"Error parsing BRD template: {e}")
            return {
                "sections_found": [],
                "heading_levels": {},
                "template_structure": {},
                "error": str(e)
            }

    def analyze_sample_data(self, content: str, file_count: int) -> Dict[str, Any]:
        """
        Analyze sample data files to determine project complexity.

        Args:
            content: Sample data content (combined from multiple files)
            file_count: Number of sample data files uploaded

        Returns:
            Dict containing complexity metrics
        """
        try:
            self.logger.info(f"Analyzing {file_count} sample data files")

            result = {
                "file_count": file_count,
                "total_content_length": len(content),
                "complexity_score": 0,
                "data_characteristics": {},
                "estimated_scope_adjustment": 1.0
            }

            # Calculate complexity based on file count and content volume
            if file_count == 0:
                result["complexity_score"] = 0
                result["complexity_level"] = "unknown"
            elif file_count <= 5:
                result["complexity_score"] = 30
                result["complexity_level"] = "low"
                result["estimated_scope_adjustment"] = 0.9
            elif file_count <= 15:
                result["complexity_score"] = 60
                result["complexity_level"] = "medium"
                result["estimated_scope_adjustment"] = 1.0
            else:
                result["complexity_score"] = 90
                result["complexity_level"] = "high"
                result["estimated_scope_adjustment"] = 1.2

            # Adjust based on content volume
            avg_file_size = len(content) / max(file_count, 1)
            if avg_file_size > 100000:  # Large files
                result["complexity_score"] = min(100, result["complexity_score"] + 10)
                result["estimated_scope_adjustment"] *= 1.1

            result["data_characteristics"] = {
                "average_file_size": avg_file_size,
                "total_characters": len(content),
                "estimated_pages": len(content) / 3000  # Rough estimate
            }

            self.logger.info(f"Complexity analysis: {result['complexity_level']} "
                           f"(score: {result['complexity_score']})")

            return result

        except Exception as e:
            self.logger.error(f"Error analyzing sample data: {e}")
            return {
                "file_count": 0,
                "complexity_score": 0,
                "complexity_level": "unknown",
                "error": str(e)
            }

    def match_templates(self, project_scope: str, parsed_templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Match current project to most similar historical template.

        Args:
            project_scope: Current project description
            parsed_templates: List of parsed cost templates

        Returns:
            Dict containing best match and similarity score
        """
        try:
            self.logger.info("Matching project to historical templates")

            if not parsed_templates:
                return {
                    "best_match": None,
                    "similarity_score": 0.0,
                    "match_reasons": []
                }

            # Simple keyword-based matching (can be enhanced with ML/embeddings)
            project_keywords = set(re.findall(r'\b\w+\b', project_scope.lower()))

            best_match = None
            best_score = 0.0
            best_reasons = []

            for template in parsed_templates:
                template_name = template.get("template_name", "Unknown")

                # Extract keywords from template name
                template_keywords = set(re.findall(r'\b\w+\b', template_name.lower()))

                # Calculate Jaccard similarity
                intersection = project_keywords & template_keywords
                union = project_keywords | template_keywords

                if union:
                    similarity = len(intersection) / len(union)

                    if similarity > best_score:
                        best_score = similarity
                        best_match = template_name
                        best_reasons = list(intersection)[:5]  # Top 5 common keywords

            return {
                "best_match": best_match,
                "similarity_score": best_score,
                "match_reasons": best_reasons,
                "confidence_level": "HIGH" if best_score > 0.3 else "MEDIUM" if best_score > 0.15 else "LOW"
            }

        except Exception as e:
            self.logger.error(f"Error matching templates: {e}")
            return {
                "best_match": None,
                "similarity_score": 0.0,
                "match_reasons": [],
                "error": str(e)
            }

    def _extract_template_name(self, content: str) -> str:
        """Extract template name from content."""
        # Look for first meaningful line or sheet name
        lines = content.split("\n")
        for line in lines[:10]:  # Check first 10 lines
            line_stripped = line.strip()
            if line_stripped and len(line_stripped) > 5 and not line_stripped.startswith("==="):
                # Remove common prefixes
                name = re.sub(r'^(Sheet:|File:|Template:)\s*', '', line_stripped, flags=re.IGNORECASE)
                return name[:50]  # Limit length
        return "Unknown Template"

    def generate_quality_metrics(
        self,
        scope_provided: bool,
        sample_data_count: int,
        brd_template_provided: bool,
        cost_templates_count: int
    ) -> Dict[str, Any]:
        """
        Generate quality metrics based on uploaded files.

        Args:
            scope_provided: Whether scope document was provided
            sample_data_count: Number of sample data files
            brd_template_provided: Whether BRD template was provided
            cost_templates_count: Number of cost templates provided

        Returns:
            Dict containing quality metrics and confidence scores
        """
        try:
            self.logger.info("Generating quality metrics")

            # Calculate completeness score (0-100)
            completeness_score = 0
            if scope_provided:
                completeness_score += 30
            if sample_data_count > 0:
                completeness_score += min(30, sample_data_count * 10)
            if brd_template_provided:
                completeness_score += 20
            if cost_templates_count > 0:
                completeness_score += min(20, cost_templates_count * 10)

            # Calculate data coverage score
            data_coverage = 0
            if sample_data_count == 0:
                data_coverage = 20  # Minimal
            elif sample_data_count <= 5:
                data_coverage = 50  # Basic
            elif sample_data_count <= 15:
                data_coverage = 80  # Good
            else:
                data_coverage = 95  # Excellent

            # Calculate template alignment score
            template_alignment = 0
            if cost_templates_count > 0:
                template_alignment += 50
            if brd_template_provided:
                template_alignment += 30
            if cost_templates_count > 1:  # Multiple templates for comparison
                template_alignment += 20

            # Determine overall confidence level
            avg_score = (completeness_score + data_coverage + template_alignment) / 3

            if avg_score >= 80:
                confidence_level = "HIGH"
            elif avg_score >= 60:
                confidence_level = "MEDIUM"
            else:
                confidence_level = "LOW"

            result = {
                "completeness_score": min(100, completeness_score),
                "data_coverage": min(100, data_coverage),
                "template_alignment": min(100, template_alignment),
                "overall_score": round(avg_score, 1),
                "confidence_level": confidence_level
            }

            self.logger.info(f"Quality metrics: {confidence_level} confidence "
                           f"(overall score: {result['overall_score']})")

            return result

        except Exception as e:
            self.logger.error(f"Error generating quality metrics: {e}")
            return {
                "completeness_score": 0,
                "data_coverage": 0,
                "template_alignment": 0,
                "overall_score": 0,
                "confidence_level": "LOW",
                "error": str(e)
            }


# Create singleton instance
template_parser_service = TemplateParserService()
