"""Test Reporter for Playwright tests with detailed screenshots and results."""
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


class TestStep:
    """Represents a single test step with expected and actual results."""

    def __init__(self, step_number: int, description: str, expected_result: str):
        self.step_number = step_number
        self.description = description
        self.expected_result = expected_result
        self.actual_result = ""
        self.status = "pending"  # pending, passed, failed
        self.screenshot_before = ""
        self.screenshot_after = ""
        self.error_message = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_number": self.step_number,
            "description": self.description,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "status": self.status,
            "screenshot_before": self.screenshot_before,
            "screenshot_after": self.screenshot_after,
            "error_message": self.error_message
        }


class TestCase:
    """Represents a complete test case with multiple steps."""

    def __init__(self, test_id: str, test_name: str, test_description: str):
        self.test_id = test_id
        self.test_name = test_name
        self.test_description = test_description
        self.status = "pending"  # pending, passed, failed
        self.start_time = None
        self.end_time = None
        self.steps: List[TestStep] = []
        self.overall_error = ""

    def add_step(self, step: TestStep):
        """Add a test step."""
        self.steps.append(step)

    def start(self):
        """Mark test case as started."""
        self.start_time = datetime.now()
        self.status = "running"

    def complete(self, status: str, error: str = ""):
        """Mark test case as completed."""
        self.end_time = datetime.now()
        self.status = status
        self.overall_error = error

    def duration(self) -> float:
        """Get test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert test case to dictionary."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_description": self.test_description,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration(),
            "steps": [step.to_dict() for step in self.steps],
            "overall_error": self.overall_error
        }


class TestReporter:
    """Generates comprehensive test reports with screenshots."""

    def __init__(self, output_dir: str = "backend/tests/playwright/test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_cases: List[TestCase] = []
        self.session_start = datetime.now()

    def add_test_case(self, test_case: TestCase):
        """Add a test case to the report."""
        self.test_cases.append(test_case)

    def generate_html_report(self, filename: str = "test_report.html"):
        """Generate comprehensive HTML report with screenshots."""
        report_path = self.output_dir / filename

        # Calculate summary statistics
        total_tests = len(self.test_cases)
        passed_tests = sum(1 for tc in self.test_cases if tc.status == "passed")
        failed_tests = sum(1 for tc in self.test_cases if tc.status == "failed")
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            color: white;
        }}
        .summary-card.total {{ background-color: #3498db; }}
        .summary-card.passed {{ background-color: #27ae60; }}
        .summary-card.failed {{ background-color: #e74c3c; }}
        .summary-card.rate {{ background-color: #9b59b6; }}
        .summary-card h3 {{ margin: 0; font-size: 36px; }}
        .summary-card p {{ margin: 10px 0 0; font-size: 14px; }}
        .test-case {{
            margin: 30px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }}
        .test-case-header {{
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-case-header:hover {{
            background-color: #f8f9fa;
        }}
        .test-case-header.passed {{
            background-color: #d4edda;
            border-left: 5px solid #28a745;
        }}
        .test-case-header.failed {{
            background-color: #f8d7da;
            border-left: 5px solid #dc3545;
        }}
        .test-case-body {{
            padding: 20px;
            display: none;
        }}
        .test-case-body.active {{
            display: block;
        }}
        .test-step {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }}
        .test-step.passed {{
            background-color: #f0f9ff;
            border-left: 4px solid #28a745;
        }}
        .test-step.failed {{
            background-color: #fff5f5;
            border-left: 4px solid #dc3545;
        }}
        .step-header {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        .result-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 15px 0;
        }}
        .result-box {{
            padding: 10px;
            border-radius: 5px;
        }}
        .expected {{
            background-color: #e8f4fd;
            border: 1px solid #b3d9f2;
        }}
        .actual {{
            background-color: #f0f9ff;
            border: 1px solid #c3e6ff;
        }}
        .screenshot-container {{
            margin: 15px 0;
            text-align: center;
        }}
        .screenshot-container img {{
            max-width: 100%;
            border: 2px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .status-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-badge.passed {{
            background-color: #28a745;
            color: white;
        }}
        .status-badge.failed {{
            background-color: #dc3545;
            color: white;
        }}
        .error-message {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            color: #856404;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 14px;
        }}
    </style>
    <script>
        function toggleTestCase(id) {{
            const body = document.getElementById('test-body-' + id);
            body.classList.toggle('active');
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>Admin Dashboard RBAC Test Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <div class="summary-card total">
                <h3>{total_tests}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h3>{passed_tests}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h3>{failed_tests}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card rate">
                <h3>{pass_rate:.1f}%</h3>
                <p>Pass Rate</p>
            </div>
        </div>

        <h2>Test Cases</h2>
"""

        # Add each test case
        for tc in self.test_cases:
            status_class = tc.status
            duration = tc.duration()

            html_content += f"""
        <div class="test-case">
            <div class="test-case-header {status_class}" onclick="toggleTestCase('{tc.test_id}')">
                <div>
                    <strong>{tc.test_name}</strong>
                    <p style="margin: 5px 0 0; color: #6c757d;">{tc.test_description}</p>
                    <p style="margin: 5px 0 0; color: #6c757d; font-size: 12px;">Duration: {duration:.2f}s</p>
                </div>
                <span class="status-badge {status_class}">{status_class}</span>
            </div>
            <div id="test-body-{tc.test_id}" class="test-case-body">
"""

            if tc.overall_error:
                html_content += f"""
                <div class="error-message">
                    <strong>Error:</strong> {tc.overall_error}
                </div>
"""

            # Add each step
            for step in tc.steps:
                html_content += f"""
                <div class="test-step {step.status}">
                    <div class="step-header">
                        Step {step.step_number}: {step.description}
                        <span class="status-badge {step.status}">{step.status}</span>
                    </div>

                    <div class="result-row">
                        <div class="result-box expected">
                            <strong>Expected Result:</strong>
                            <p>{step.expected_result}</p>
                        </div>
                        <div class="result-box actual">
                            <strong>Actual Result:</strong>
                            <p>{step.actual_result or 'N/A'}</p>
                        </div>
                    </div>
"""

                # Add screenshots if available
                if step.screenshot_before:
                    html_content += f"""
                    <div class="screenshot-container">
                        <p><strong>Before Action:</strong></p>
                        <img src="{step.screenshot_before}" alt="Before screenshot">
                    </div>
"""

                if step.screenshot_after:
                    html_content += f"""
                    <div class="screenshot-container">
                        <p><strong>After Action:</strong></p>
                        <img src="{step.screenshot_after}" alt="After screenshot">
                    </div>
"""

                if step.error_message:
                    html_content += f"""
                    <div class="error-message">
                        <strong>Error:</strong> {step.error_message}
                    </div>
"""

                html_content += """
                </div>
"""

            html_content += """
            </div>
        </div>
"""

        html_content += """
    </div>
</body>
</html>
"""

        # Write HTML report
        with open(report_path, 'w') as f:
            f.write(html_content)

        print(f"\nHTML Test Report generated: {report_path}")
        return str(report_path)

    def generate_json_report(self, filename: str = "test_report.json"):
        """Generate JSON report for machine processing."""
        report_path = self.output_dir / filename

        report_data = {
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "total_tests": len(self.test_cases),
            "passed_tests": sum(1 for tc in self.test_cases if tc.status == "passed"),
            "failed_tests": sum(1 for tc in self.test_cases if tc.status == "failed"),
            "test_cases": [tc.to_dict() for tc in self.test_cases]
        }

        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"JSON Test Report generated: {report_path}")
        return str(report_path)
