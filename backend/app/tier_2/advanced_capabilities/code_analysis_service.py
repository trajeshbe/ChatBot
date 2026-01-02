"""Code Analysis & Review AI - Business Logic Service"""
import logging
import re
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .code_analysis_schemas import *

logger = logging.getLogger(__name__)

class CodeAnalysisService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService()

    async def analyze_code(self, request: AnalyzeCodeRequest) -> AnalyzeCodeResponse:
        """Perform comprehensive code analysis with AI insights"""
        try:
            # Calculate metrics
            metrics = self._calculate_code_metrics(request.code, request.language)

            # Detect issues
            issues = []
            if request.check_security:
                issues.extend(self._check_security_issues(request.code, request.language))
            if request.check_performance:
                issues.extend(self._check_performance_issues(request.code, request.language))
            if request.check_style:
                issues.extend(self._check_style_issues(request.code, request.language))

            # Calculate overall quality score
            quality_score = self._calculate_quality_score(issues, metrics)

            # Generate recommendations
            recommendations = self._generate_recommendations(issues, metrics, request.language)

            # Get AI insights
            prompt = f"""Review {request.language.value} code with {len(issues)} issues found.
Quality score: {quality_score:.1f}/100. Complexity: {metrics.complexity_score:.1f}.
Provide 2-3 sentences on key improvement areas."""

            insights = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.3
            )

            return AnalyzeCodeResponse(
                success=True,
                code_id=request.code_id,
                language=request.language,
                issues=sorted(issues, key=lambda x: (x.severity.value, x.line_number)),
                metrics=metrics,
                overall_quality_score=round(quality_score, 2),
                recommendations=recommendations,
                ai_insights=insights.strip()
            )

        except Exception as e:
            logger.error(f"Code analysis error: {e}", exc_info=True)
            raise

    def _calculate_code_metrics(self, code: str, language: ProgrammingLanguage) -> CodeMetrics:
        """Calculate code metrics"""
        lines = code.split('\n')
        total_lines = len(lines)

        # Count different line types
        code_lines = 0
        comment_lines = 0
        blank_lines = 0

        comment_patterns = {
            ProgrammingLanguage.PYTHON: [r'^\s*#', r'^\s*"""', r"^\s*'''"],
            ProgrammingLanguage.JAVASCRIPT: [r'^\s*//', r'^\s*/\*'],
            ProgrammingLanguage.TYPESCRIPT: [r'^\s*//', r'^\s*/\*'],
            ProgrammingLanguage.JAVA: [r'^\s*//', r'^\s*/\*'],
            ProgrammingLanguage.CSHARP: [r'^\s*//', r'^\s*/\*'],
            ProgrammingLanguage.GO: [r'^\s*//', r'^\s*/\*'],
            ProgrammingLanguage.RUST: [r'^\s*//', r'^\s*/\*'],
            ProgrammingLanguage.CPP: [r'^\s*//', r'^\s*/\*'],
        }

        patterns = comment_patterns.get(language, [r'^\s*#', r'^\s*//'])

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif any(re.match(pattern, stripped) for pattern in patterns):
                comment_lines += 1
            else:
                code_lines += 1

        # Calculate complexity (simple heuristic based on control structures)
        complexity_keywords = ['if', 'else', 'elif', 'for', 'while', 'switch', 'case', 'try', 'catch', 'except']
        complexity_count = sum(code.lower().count(keyword) for keyword in complexity_keywords)
        complexity_score = min(100.0, max(0.0, 100 - (complexity_count / max(code_lines, 1)) * 50))

        # Calculate maintainability index (simplified)
        comment_ratio = comment_lines / max(total_lines, 1)
        avg_line_length = sum(len(line) for line in lines) / max(total_lines, 1)

        maintainability = 100.0
        if comment_ratio < 0.1:  # Less than 10% comments
            maintainability -= 20
        if avg_line_length > 100:  # Long lines
            maintainability -= 15
        if code_lines > 500:  # Very long file
            maintainability -= 10

        maintainability = max(0.0, maintainability)

        # Estimate technical debt
        issue_estimate = complexity_count * 0.5  # 30 min per complex structure
        length_estimate = max(0, code_lines - 300) / 50  # Extra hour per 50 lines over 300
        tech_debt = issue_estimate + length_estimate

        return CodeMetrics(
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            complexity_score=round(complexity_score, 2),
            maintainability_index=round(maintainability, 2),
            estimated_technical_debt_hours=round(tech_debt, 2)
        )

    def _check_security_issues(self, code: str, language: ProgrammingLanguage) -> List[CodeIssue]:
        """Check for security vulnerabilities"""
        issues = []
        lines = code.split('\n')

        # Common security patterns
        security_checks = [
            (r'eval\s*\(', 'Avoid using eval() - potential code injection risk', IssueSeverity.CRITICAL),
            (r'exec\s*\(', 'Avoid using exec() - potential code injection risk', IssueSeverity.CRITICAL),
            (r'password\s*=\s*["\']', 'Hardcoded password detected', IssueSeverity.HIGH),
            (r'api[_-]?key\s*=\s*["\']', 'Hardcoded API key detected', IssueSeverity.HIGH),
            (r'\.format\s*\(.*sql', 'Potential SQL injection via string formatting', IssueSeverity.HIGH),
            (r'subprocess\.call\(.*shell=True', 'Avoid shell=True in subprocess - command injection risk', IssueSeverity.HIGH),
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, message, severity in security_checks:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        line_number=line_num,
                        severity=severity,
                        category=IssueCategory.SECURITY,
                        message=message,
                        suggested_fix="Use parameterized queries or environment variables" if "password" in message.lower() or "key" in message.lower() else None,
                        explanation=f"Security vulnerability detected on line {line_num}"
                    ))

        return issues

    def _check_performance_issues(self, code: str, language: ProgrammingLanguage) -> List[CodeIssue]:
        """Check for performance anti-patterns"""
        issues = []
        lines = code.split('\n')

        # Performance patterns
        perf_checks = [
            (r'for\s+\w+\s+in\s+range\(len\(', 'Use enumerate() instead of range(len())', IssueSeverity.LOW),
            (r'\w+\s*\+=\s*\w+\s*\+\s*', 'Use join() for string concatenation in loops', IssueSeverity.MEDIUM),
            (r'\.append\(.+\)\s*$', 'Consider list comprehension for better performance', IssueSeverity.LOW),
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, message, severity in perf_checks:
                if re.search(pattern, line):
                    issues.append(CodeIssue(
                        line_number=line_num,
                        severity=severity,
                        category=IssueCategory.PERFORMANCE,
                        message=message,
                        suggested_fix=None,
                        explanation=f"Performance optimization opportunity on line {line_num}"
                    ))

        return issues

    def _check_style_issues(self, code: str, language: ProgrammingLanguage) -> List[CodeIssue]:
        """Check for style and best practice violations"""
        issues = []
        lines = code.split('\n')

        # Style checks (simplified)
        for line_num, line in enumerate(lines, 1):
            # Line too long
            if len(line) > 120:
                issues.append(CodeIssue(
                    line_number=line_num,
                    severity=IssueSeverity.INFO,
                    category=IssueCategory.BEST_PRACTICE,
                    message=f"Line exceeds 120 characters ({len(line)} chars)",
                    suggested_fix="Break into multiple lines",
                    explanation="Long lines reduce readability"
                ))

            # Multiple statements on one line (Python)
            if language == ProgrammingLanguage.PYTHON and line.count(';') > 0:
                issues.append(CodeIssue(
                    line_number=line_num,
                    severity=IssueSeverity.LOW,
                    category=IssueCategory.CODE_SMELL,
                    message="Multiple statements on one line",
                    suggested_fix="Split into separate lines",
                    explanation="Reduces code clarity"
                ))

        return issues

    def _calculate_quality_score(self, issues: List[CodeIssue], metrics: CodeMetrics) -> float:
        """Calculate overall quality score"""
        base_score = 100.0

        # Deduct points for issues
        severity_weights = {
            IssueSeverity.CRITICAL: 20,
            IssueSeverity.HIGH: 10,
            IssueSeverity.MEDIUM: 5,
            IssueSeverity.LOW: 2,
            IssueSeverity.INFO: 0.5
        }

        for issue in issues:
            base_score -= severity_weights.get(issue.severity, 1)

        # Factor in metrics
        base_score = (base_score + metrics.complexity_score + metrics.maintainability_index) / 3

        return max(0.0, min(100.0, base_score))

    def _generate_recommendations(
        self,
        issues: List[CodeIssue],
        metrics: CodeMetrics,
        language: ProgrammingLanguage
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Critical issues first
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical security issues immediately")

        # Complexity
        if metrics.complexity_score < 50:
            recommendations.append("Refactor complex functions into smaller, testable units")

        # Maintainability
        if metrics.maintainability_index < 60:
            recommendations.append("Improve code documentation and reduce file size")

        # Comments
        comment_ratio = metrics.comment_lines / max(metrics.total_lines, 1)
        if comment_ratio < 0.1:
            recommendations.append("Add more inline comments to explain complex logic")

        # Generic best practices
        if not recommendations:
            recommendations.append(f"Code quality is good! Consider adding unit tests for {language.value} code")

        return recommendations[:5]  # Top 5 recommendations

    async def search_analyses(self, request: SearchAnalysesRequest) -> SearchAnalysesResponse:
        """Search historical code analyses"""
        # Placeholder implementation
        return SearchAnalysesResponse(
            success=True,
            analyses=[],
            total_count=0
        )

    async def export_analyses(self, request: ExportAnalysesRequest) -> ExportAnalysesResponse:
        """Export code analyses in specified format"""
        # Placeholder implementation
        export_data = {
            "format": request.format,
            "code_ids": request.code_ids,
            "exported_at": "2026-01-01T00:00:00Z"
        }

        return ExportAnalysesResponse(
            success=True,
            export_data=export_data,
            format=request.format
        )

    async def get_stats(self) -> CodeAnalysisStatsResponse:
        """Get code analysis statistics"""
        # Placeholder implementation
        return CodeAnalysisStatsResponse(
            success=True,
            total_analyses=0,
            most_common_language="python",
            average_quality_score=0.0,
            total_issues_found=0
        )

    async def get_status(self) -> StatusResponse:
        """Get service status and capabilities"""
        return StatusResponse(
            success=True,
            status="operational",
            capabilities=[
                "Security Vulnerability Detection",
                "Performance Analysis",
                "Code Style Checking",
                "Complexity Metrics",
                "AI-Powered Insights",
                "8+ Languages Supported"
            ]
        )
