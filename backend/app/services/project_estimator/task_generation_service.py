"""
Task Generation Service

Generates 20-30 detailed project tasks using LLM with hierarchical numbering,
effort estimation, and complexity classification.

Based on analysis of real project cost estimates.

Author: AI Assistant
Date: 2025-11-21
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TaskGenerationService:
    """
    Generate detailed task breakdown using LLM.

    Creates 20-30 tasks with hierarchical numbering (1, 1.1, 1.2, 2, 2.1...),
    effort estimates, complexity classification, and categorization.
    """

    def __init__(self, llm_client):
        """
        Initialize task generation service.

        Args:
            llm_client: LLM client (OpenAI, Anthropic, or Ollama)
        """
        self.llm_client = llm_client
        logger.info("TaskGenerationService initialized")

    async def generate_tasks(
        self,
        project_scope: str,
        project_type: str,
        num_tasks: int = 25,
        project_name: str = "",
        industry: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate detailed task breakdown with effort estimates.

        Args:
            project_scope: Description of project scope
            project_type: POC, Staff Augmentation, or Full Service
            num_tasks: Target number of tasks (default: 25)
            project_name: Optional project name for context
            industry: Optional industry for context

        Returns:
            List of tasks with:
            - task_number: hierarchical numbering (1, 1.1, 1.2, 2, 2.1...)
            - task_name: specific task description
            - category: Planning, Development, Testing, Infrastructure, etc.
            - effort_hours: estimated hours
            - complexity: Easy, Medium, Hard
            - dependencies: list of prerequisite task numbers (optional)
        """
        logger.info(f"Generating {num_tasks} tasks for {project_type} project")

        try:
            prompt = self._build_task_generation_prompt(
                project_scope,
                project_type,
                num_tasks,
                project_name,
                industry
            )

            response = await self._call_llm(
                prompt,
                max_tokens=3000,
                temperature=0.7
            )

            # Parse response into structured tasks
            tasks = self._parse_task_response(response)

            # Validate and enhance task structure
            tasks = self._validate_and_enhance_tasks(tasks, num_tasks)

            logger.info(f"Generated {len(tasks)} tasks successfully")
            return tasks

        except Exception as e:
            logger.error(f"Error generating tasks: {e}")
            raise

    def _build_task_generation_prompt(
        self,
        project_scope: str,
        project_type: str,
        num_tasks: int,
        project_name: str,
        industry: str
    ) -> str:
        """Build comprehensive prompt for task generation"""

        prompt = f"""
Generate a detailed task breakdown for the following project:

**Project Type**: {project_type}
**Project Name**: {project_name if project_name else 'Data Extraction Solution'}
**Industry**: {industry if industry else 'General'}
**Number of Tasks**: {num_tasks}

**Project Scope**:
{project_scope}

---

Follow these patterns from real project estimates:

**Task Categories** (distribute tasks across these):

1. **Planning, Design and System Setup** (15-40 hours total, ~10-15% of tasks)
   - Solution approach and architecture
   - Database design and schema definition
   - Infrastructure setup and configuration
   Example: "1 | Planning, Design and System Setup | Planning | 40 | Medium"
   Example: "1.1 | Solution Approach (Architecture and Database Design) | Planning | 24 | Medium"

2. **Scraper Development/Configuration** (40-60% of total effort, largest section)
   - Specific source scrapers
   - Data extraction modules
   - API integrations
   - Data parsing and normalization
   Example: "2 | Data Extraction Development | Development | 2456 | Hard"
   Example: "2.1 | Website scraping (500 sources) | Development | 1200 | Hard"
   Example: "2.2 | Email attachment parser | Development | 40 | Medium"

3. **Data Transformation & Processing** (10-15% of effort)
   - Data cleaning and standardization
   - Deduplication logic
   - Logging and monitoring
   - File delivery and notifications
   Example: "3 | Data Processing Pipeline | Development | 180 | Medium"
   Example: "3.1 | Data cleaning and validation | Development | 80 | Medium"

4. **Data Quality & Validation** (5-10% of effort)
   - Automated quality checks
   - Validation rules implementation
   - Confidence scoring
   Example: "4 | Quality Assurance | QA | 120 | Medium"
   Example: "4.1 | Validation rules engine | Development | 60 | Medium"

5. **UAT Issue Fixes** (10-15% of effort)
   - Buffer for bug fixes
   - Performance optimization
   - User-reported issue resolution
   Example: "5 | UAT Issue Fixes | Support | 240 | Medium"
   Example: "5.1 | Bug fixes and corrections | Support | 120 | Easy"

6. **Integration and Deployment** (5-10% of effort)
   - System integration
   - Deployment automation
   - Documentation
   - Handoff and training
   Example: "6 | Integration and Deployment | Deployment | 80 | Medium"
   Example: "6.1 | CI/CD pipeline setup | Infrastructure | 40 | Easy"

---

**Task Numbering Rules**:
- Main phases: 1, 2, 3, 4, 5, 6
- Sub-tasks: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, etc.
- Use hierarchical format consistently
- Number of sub-tasks varies by phase complexity

**Effort Estimation Guidelines**:
- Easy tasks: 8-24 hours
- Medium tasks: 24-60 hours
- Hard tasks: 60-120 hours
- Very large phases (like scraper development): 200-2500+ hours

**Complexity Classification**:
- **Easy**: Straightforward implementation, clear requirements
- **Medium**: Moderate complexity, some unknowns
- **Hard**: High complexity, significant unknowns, requires extensive work

**Additional Guidelines for {project_type}**:
{"- Keep scope limited, focus on proof-of-concept items\n- Include PM and Documentation as FOC (Free of Charge)\n- Shorter timeline (6-8 weeks)" if project_type == "POC" else ""}
{"- Focus on resource allocation\n- Include skill categories\n- Emphasize team composition" if project_type == "Staff Augmentation" else ""}
{"- Include all phases comprehensively\n- Add ongoing support and maintenance tasks\n- Include BAU operational tasks" if project_type == "Full Service" else ""}

---

**Output Format** (IMPORTANT: Use pipe-separated format):

S.No | Task Description | Category | Effort (Hours) | Complexity

Example output:
1 | Planning, Design and System Setup | Planning | 40 | Medium
1.1 | Solution Approach (System Architecture and Database Design) | Planning | 24 | Medium
1.2 | Infrastructure Setup (VMs, DB, Storage) | Infrastructure | 16 | Easy
2 | Scraper Development/Configuration | Development | 2456 | Hard
2.1 | Media sites and registries scraping (2000 sources) | Development | 2400 | Hard
2.2 | Company press releases scraper | Development | 8 | Easy
2.3 | Real-time data API integration | Development | 48 | Medium
3 | Data Transformation & Processing | Development | 180 | Medium
3.1 | Data cleaning and deduplication | Development | 80 | Medium
3.2 | Logging and error handling | Development | 40 | Easy
3.3 | File delivery automation | Development | 60 | Medium
4 | Data Quality & Validation | QA | 120 | Medium
4.1 | Validation rules implementation | Development | 60 | Medium
4.2 | Confidence scoring algorithm | Development | 60 | Medium
5 | UAT Issue Fixes | Support | 240 | Medium
5.1 | Bug fixes and corrections | Support | 120 | Easy
5.2 | Performance optimization | Development | 80 | Medium
5.3 | User feedback incorporation | Support | 40 | Easy
6 | Integration and Deployment | Deployment | 80 | Medium
6.1 | CI/CD pipeline setup | Infrastructure | 40 | Easy
6.2 | Production deployment | Deployment | 24 | Medium
6.3 | Documentation and handoff | Documentation | 16 | Easy

---

**Generate exactly {num_tasks} tasks following this pattern**:
"""

        return prompt

    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Call LLM with prompt and return response"""
        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _parse_task_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured task list.

        Expected format:
        S.No | Task Description | Category | Effort (Hours) | Complexity
        """
        tasks = []
        lines = response.split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines and headers
            if not line or 'S.No' in line or '---' in line or line.startswith('#'):
                continue

            # Must contain pipe separator
            if '|' not in line:
                continue

            # Split by pipe
            parts = [p.strip() for p in line.split('|')]

            if len(parts) >= 5:
                try:
                    task_number = parts[0]
                    task_name = parts[1]
                    category = parts[2]
                    effort_str = parts[3]
                    complexity = parts[4]

                    # Parse effort hours
                    effort_hours = self._parse_effort(effort_str)

                    # Validate complexity
                    complexity = self._normalize_complexity(complexity)

                    task = {
                        "task_number": task_number,
                        "task_name": task_name,
                        "category": category,
                        "effort_hours": effort_hours,
                        "complexity": complexity
                    }

                    tasks.append(task)

                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse task line: {line} - {e}")
                    continue

        return tasks

    def _parse_effort(self, effort_str: str) -> float:
        """
        Parse effort string to float.

        Handles formats like:
        - "40"
        - "40 hours"
        - "2456"
        """
        # Extract numeric value
        match = re.search(r'(\d+(?:\.\d+)?)', effort_str)
        if match:
            return float(match.group(1))
        else:
            logger.warning(f"Could not parse effort: {effort_str}, defaulting to 24")
            return 24.0

    def _normalize_complexity(self, complexity: str) -> str:
        """Normalize complexity to Easy, Medium, or Hard"""
        complexity = complexity.lower().strip()

        if complexity in ['easy', 'simple', 'low']:
            return 'Easy'
        elif complexity in ['hard', 'difficult', 'high', 'complex']:
            return 'Hard'
        else:
            return 'Medium'

    def _validate_and_enhance_tasks(
        self,
        tasks: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """
        Validate task structure and enhance with additional metadata.

        Ensures:
        - Tasks have proper hierarchical numbering
        - Total hours are reasonable
        - Task count is close to target
        """
        if not tasks:
            logger.warning("No tasks generated, returning empty list")
            return []

        # Sort tasks by task number (hierarchical)
        tasks = self._sort_tasks_hierarchically(tasks)

        # Calculate total hours
        total_hours = sum(t['effort_hours'] for t in tasks)
        logger.info(f"Total effort: {total_hours} hours across {len(tasks)} tasks")

        # Add metadata
        for i, task in enumerate(tasks):
            task['task_index'] = i
            task['is_main_phase'] = '.' not in str(task['task_number'])

        return tasks

    def _sort_tasks_hierarchically(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sort tasks by hierarchical numbering.

        Order: 1, 1.1, 1.2, 2, 2.1, 2.2, 2.3, 3, 3.1, etc.
        """

        def parse_task_number(task_num: str) -> tuple:
            """Convert task number to sortable tuple"""
            try:
                # Handle formats like "1", "1.1", "1.2.3"
                parts = str(task_num).split('.')
                return tuple(int(p) for p in parts)
            except:
                # Fallback for malformed numbers
                return (999, 999)

        tasks.sort(key=lambda t: parse_task_number(t['task_number']))
        return tasks

    def calculate_effort_distribution(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate effort distribution across categories and complexity levels.

        Returns:
            Dictionary with effort breakdown by category and complexity
        """
        if not tasks:
            return {
                "total_hours": 0,
                "by_category": {},
                "by_complexity": {},
                "task_count": 0
            }

        total_hours = sum(t['effort_hours'] for t in tasks)

        # By category
        by_category = {}
        for task in tasks:
            category = task['category']
            if category not in by_category:
                by_category[category] = {
                    "hours": 0,
                    "task_count": 0,
                    "percentage": 0
                }
            by_category[category]["hours"] += task['effort_hours']
            by_category[category]["task_count"] += 1

        # Calculate percentages
        for category in by_category:
            if total_hours > 0:
                by_category[category]["percentage"] = round(
                    (by_category[category]["hours"] / total_hours) * 100,
                    1
                )

        # By complexity
        by_complexity = {}
        for task in tasks:
            complexity = task['complexity']
            if complexity not in by_complexity:
                by_complexity[complexity] = {
                    "hours": 0,
                    "task_count": 0,
                    "percentage": 0
                }
            by_complexity[complexity]["hours"] += task['effort_hours']
            by_complexity[complexity]["task_count"] += 1

        # Calculate percentages
        for complexity in by_complexity:
            if total_hours > 0:
                by_complexity[complexity]["percentage"] = round(
                    (by_complexity[complexity]["hours"] / total_hours) * 100,
                    1
                )

        return {
            "total_hours": total_hours,
            "by_category": by_category,
            "by_complexity": by_complexity,
            "task_count": len(tasks)
        }

    def generate_task_summary(
        self,
        tasks: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable task summary"""

        distribution = self.calculate_effort_distribution(tasks)

        summary = f"""
Task Breakdown Summary
======================

Total Tasks: {distribution['task_count']}
Total Effort: {distribution['total_hours']} hours

By Category:
"""
        for category, data in distribution['by_category'].items():
            summary += f"  - {category}: {data['hours']} hours ({data['percentage']}%) - {data['task_count']} tasks\n"

        summary += "\nBy Complexity:\n"
        for complexity, data in distribution['by_complexity'].items():
            summary += f"  - {complexity}: {data['hours']} hours ({data['percentage']}%) - {data['task_count']} tasks\n"

        return summary
