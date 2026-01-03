"""Page Object for Tier 2 Domain Vertical Modules."""
from playwright.sync_api import Page, expect
from .base_page import BasePage
import time


class Tier2ModulePage(BasePage):
    """Base class for all Tier 2 domain vertical module pages."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001", module_id: str = ""):
        super().__init__(page, base_url)
        self.module_id = module_id

    # Common navigation
    def navigate_to_module(self):
        """Navigate to specific Tier 2 module."""
        self.navigate_to("/")
        # Wait for page load
        time.sleep(1)
        # Click on the module in sidebar or module grid
        module_selector = f'[data-module-id="{self.module_id}"]'
        if self.is_visible(module_selector):
            self.click(module_selector)
            self.wait_for_navigation()
        else:
            # Try alternative selector
            self.page.get_by_text(self.module_id, exact=False).click()
            time.sleep(1)

    # Common file upload
    def upload_file(self, file_path: str):
        """Upload a file to the module."""
        file_input_selector = 'input[type="file"]'
        self.page.set_input_files(file_input_selector, file_path)
        time.sleep(1)  # Wait for file to be selected

    # Common text input
    def enter_text_input(self, text: str, selector: str = 'textarea'):
        """Enter text in text area or input."""
        self.fill(selector, text)

    # Common button clicks
    def click_submit_button(self):
        """Click the submit/analyze/process button."""
        submit_selectors = [
            'button:has-text("Submit")',
            'button:has-text("Analyze")',
            'button:has-text("Process")',
            'button:has-text("Extract")',
            'button[type="submit"]'
        ]
        for selector in submit_selectors:
            if self.is_visible(selector):
                self.click(selector)
                return
        raise Exception("No submit button found")

    # Common result verification
    def wait_for_results(self, timeout: int = 30000):
        """Wait for results to appear."""
        result_selectors = [
            '[data-testid="results"]',
            '.results-container',
            '[class*="result"]',
            'pre',
            'table'
        ]
        for selector in result_selectors:
            try:
                self.wait_for_element(selector, timeout=timeout)
                return True
            except:
                continue
        return False

    def verify_results_visible(self):
        """Verify that results are displayed."""
        assert self.wait_for_results(), "Results not visible after processing"

    def get_results_text(self) -> str:
        """Get the results text."""
        result_selectors = [
            '[data-testid="results"]',
            '.results-container',
            'pre',
            '.json-display'
        ]
        for selector in result_selectors:
            if self.is_visible(selector):
                return self.get_text(selector)
        return ""

    # Common error handling
    def check_for_errors(self) -> bool:
        """Check if there are any error messages."""
        error_selectors = [
            '.error',
            '[data-testid="error"]',
            '[class*="error"]',
            '.text-red'
        ]
        for selector in error_selectors:
            if self.is_visible(selector):
                return True
        return False

    def get_error_message(self) -> str:
        """Get error message if present."""
        error_selectors = [
            '.error',
            '[data-testid="error"]',
            '[class*="error"]'
        ]
        for selector in error_selectors:
            if self.is_visible(selector):
                return self.get_text(selector)
        return ""


class DocumentIntelligencePage(Tier2ModulePage):
    """Page object for Document Intelligence modules."""

    def __init__(self, page: Page, base_url: str, module_id: str):
        super().__init__(page, base_url, module_id)

    def upload_document(self, file_path: str):
        """Upload a document for intelligence extraction."""
        self.upload_file(file_path)

    def enter_query(self, query: str):
        """Enter a query for RAG (Generic RAG module)."""
        self.enter_text_input(query, 'textarea[placeholder*="question"], textarea[placeholder*="query"]')

    def get_extraction_results(self) -> dict:
        """Get structured extraction results."""
        results_text = self.get_results_text()
        # Try to parse as JSON
        import json
        try:
            return json.loads(results_text)
        except:
            return {"raw_text": results_text}


class ProcurementPage(Tier2ModulePage):
    """Page object for Procurement modules."""

    def __init__(self, page: Page, base_url: str, module_id: str):
        super().__init__(page, base_url, module_id)

    def upload_purchase_order(self, file_path: str):
        """Upload purchase order."""
        # Look for specific PO upload input
        po_selector = 'input[accept*="pdf"], input[accept*="csv"]'
        if self.is_visible(po_selector):
            self.page.set_input_files(po_selector, file_path)
        else:
            self.upload_file(file_path)

    def upload_invoice(self, file_path: str):
        """Upload invoice for matching."""
        self.upload_file(file_path)

    def get_match_results(self) -> dict:
        """Get matching results."""
        results_text = self.get_results_text()
        import json
        try:
            return json.loads(results_text)
        except:
            return {"match_percentage": 0, "raw_results": results_text}


class ConstructionPage(Tier2ModulePage):
    """Page object for Construction modules."""

    def __init__(self, page: Page, base_url: str, module_id: str):
        super().__init__(page, base_url, module_id)

    def upload_planning_document(self, file_path: str):
        """Upload planning document."""
        self.upload_file(file_path)

    def upload_image(self, file_path: str):
        """Upload image for vision-based classification."""
        self.page.set_input_files('input[accept*="image"]', file_path)

    def get_classification_results(self) -> dict:
        """Get classification results."""
        results_text = self.get_results_text()
        import json
        try:
            return json.loads(results_text)
        except:
            return {"classification": "unknown", "raw_results": results_text}


class HRTalentPage(Tier2ModulePage):
    """Page object for HR & Talent modules."""

    def __init__(self, page: Page, base_url: str, module_id: str):
        super().__init__(page, base_url, module_id)

    def upload_resume(self, file_path: str):
        """Upload resume/CV."""
        self.upload_file(file_path)

    def upload_job_description(self, file_path: str):
        """Upload job description."""
        self.upload_file(file_path)

    def enter_skill_query(self, skills: str):
        """Enter skills for matching."""
        self.enter_text_input(skills, 'input[placeholder*="skill"], textarea[placeholder*="skill"]')

    def get_talent_results(self) -> dict:
        """Get talent search/matching results."""
        results_text = self.get_results_text()
        import json
        try:
            return json.loads(results_text)
        except:
            return {"candidates": [], "raw_results": results_text}


class AgriculturePage(Tier2ModulePage):
    """Page object for Agriculture modules."""

    def __init__(self, page: Page, base_url: str, module_id: str):
        super().__init__(page, base_url, module_id)

    def enter_field_report(self, report_text: str):
        """Enter field inspection report."""
        self.enter_text_input(report_text, 'textarea')

    def upload_agricultural_data(self, file_path: str):
        """Upload agricultural data CSV."""
        self.upload_file(file_path)

    def get_taxonomy_results(self) -> dict:
        """Get taxonomy extraction results."""
        results_text = self.get_results_text()
        import json
        try:
            return json.loads(results_text)
        except:
            return {"taxonomy": {}, "raw_results": results_text}


class AnalyticsPage(Tier2ModulePage):
    """Page object for Analytics modules."""

    def __init__(self, page: Page, base_url: str, module_id: str):
        super().__init__(page, base_url, module_id)

    def upload_data_file(self, file_path: str):
        """Upload data file for analysis."""
        self.upload_file(file_path)

    def select_analysis_type(self, analysis_type: str):
        """Select type of analysis."""
        # Try dropdown selector
        select_selector = 'select'
        if self.is_visible(select_selector):
            self.page.select_option(select_selector, analysis_type)

    def get_analytics_results(self) -> dict:
        """Get analytics results."""
        results_text = self.get_results_text()
        import json
        try:
            return json.loads(results_text)
        except:
            return {"metrics": {}, "raw_results": results_text}
