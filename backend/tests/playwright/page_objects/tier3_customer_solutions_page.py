"""Page Object for Tier 3 Customer Solution POCs."""
from playwright.sync_api import Page, expect
from .base_page import BasePage
import time


class Tier3CustomerSolutionPage(BasePage):
    """Base class for all Tier 3 customer solution POC pages."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001", poc_id: str = ""):
        super().__init__(page, base_url)
        self.poc_id = poc_id

    def navigate_to_poc(self):
        """Navigate to specific Tier 3 POC."""
        self.navigate_to("/")
        time.sleep(1)
        # Click on Tier 3 / Customer Solutions
        tier3_selector = '[data-tier="3"], button:has-text("Customer Solutions"), button:has-text("Tier 3")'
        try:
            self.page.locator(tier3_selector).first.click()
            time.sleep(0.5)
        except:
            pass

        # Click on specific POC
        poc_selector = f'[data-poc-id="{self.poc_id}"]'
        if self.is_visible(poc_selector):
            self.click(poc_selector)
        else:
            # Try text-based selector
            self.page.get_by_text(self.poc_id.replace('-', ' '), exact=False).click()
        time.sleep(1)

    def upload_file(self, file_path: str):
        """Upload a file."""
        self.page.set_input_files('input[type="file"]', file_path)
        time.sleep(1)

    def wait_for_processing(self, timeout: int = 60000):
        """Wait for processing to complete."""
        # Wait for loading indicators to disappear
        loading_selectors = [
            '.loading',
            '[data-testid="loading"]',
            '.spinner',
            '[aria-busy="true"]'
        ]
        for selector in loading_selectors:
            try:
                self.page.wait_for_selector(selector, state="hidden", timeout=5000)
            except:
                pass

    def verify_results_available(self):
        """Verify results are available."""
        result_indicators = [
            '[data-testid="results"]',
            '.results',
            'table',
            '.extraction-results',
            'pre'
        ]
        for selector in result_indicators:
            if self.is_visible(selector):
                return True
        return False


class BritishCouncilPOCPage(Tier3CustomerSolutionPage):
    """Page object for British Council POC."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url, "british-council")

    def enter_learner_profile(self, skills: str, interests: str, education_level: str):
        """Enter learner profile information."""
        # Skills
        skills_input = 'input[placeholder*="skill"], textarea[placeholder*="skill"]'
        if self.is_visible(skills_input):
            self.fill(skills_input, skills)

        # Interests
        interests_input = 'input[placeholder*="interest"], textarea[placeholder*="interest"]'
        if self.is_visible(interests_input):
            self.fill(interests_input, interests)

        # Education level
        education_select = 'select[name*="education"]'
        if self.is_visible(education_select):
            self.page.select_option(education_select, education_level)

    def get_course_recommendations(self) -> list:
        """Get course recommendations."""
        # Look for course cards or list items
        courses_selector = '[data-testid="course-card"], .course-item, li'
        course_elements = self.page.locator(courses_selector).all()
        return [elem.text_content() for elem in course_elements[:10]]  # Top 10

    def verify_recommendations_shown(self):
        """Verify course recommendations are displayed."""
        assert len(self.get_course_recommendations()) > 0, "No course recommendations found"


class CRUPOCPage(Tier3CustomerSolutionPage):
    """Page object for CRU Mining Intelligence POC."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url, "cru")

    def upload_mining_report(self, file_path: str):
        """Upload mining report for analysis."""
        self.upload_file(file_path)

    def enter_mining_query(self, query: str):
        """Enter query about mining data."""
        query_input = 'textarea, input[type="text"]'
        self.page.locator(query_input).first.fill(query)

    def click_query_button(self):
        """Click query/search button."""
        self.page.locator('button:has-text("Query"), button:has-text("Search"), button:has-text("Analyze")').first.click()

    def get_extraction_results(self) -> dict:
        """Get mining data extraction results."""
        results_text = self.get_text('[data-testid="results"], .results-container, pre')
        import json
        try:
            return json.loads(results_text)
        except:
            return {"raw_results": results_text}

    def verify_mining_data_extracted(self):
        """Verify mining data was extracted."""
        assert self.verify_results_available(), "No mining data extraction results found"


class GrantThorntonPOCPage(Tier3CustomerSolutionPage):
    """Page object for Grant Thornton POC."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url, "grant-thornton")

    def upload_financial_report(self, file_path: str):
        """Upload annual report/financial document."""
        self.upload_file(file_path)

    def click_extract_button(self):
        """Click extract datapoints button."""
        extract_selectors = [
            'button:has-text("Extract")',
            'button:has-text("Analyze")',
            'button:has-text("Process")'
        ]
        for selector in extract_selectors:
            if self.is_visible(selector):
                self.click(selector)
                return

    def wait_for_extraction(self, timeout: int = 120000):
        """Wait for extraction to complete (can take 1-2 minutes)."""
        self.wait_for_processing(timeout)

    def verify_datapoints_extracted(self):
        """Verify financial datapoints were extracted."""
        # Check for table or results
        assert self.verify_results_available(), "No financial datapoints found"

    def download_excel_results(self):
        """Download Excel export."""
        download_button = 'button:has-text("Download"), button:has-text("Export Excel")'
        if self.is_visible(download_button):
            with self.page.expect_download() as download_info:
                self.click(download_button)
            download = download_info.value
            return download.path()
        return None


class GTMotivePOCPage(Tier3CustomerSolutionPage):
    """Page object for GT Motive POC."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url, "gt-motive")

    def upload_parts_catalog(self, file_path: str):
        """Upload parts catalog PDF."""
        self.upload_file(file_path)

    def upload_parts_diagram(self, image_path: str):
        """Upload parts diagram image."""
        self.page.set_input_files('input[accept*="image"]', image_path)

    def click_extract_parts_button(self):
        """Click extract part codes button."""
        self.click('button:has-text("Extract"), button:has-text("Analyze Parts")')

    def get_part_codes(self) -> list:
        """Get extracted part codes."""
        # Look for table rows or list items
        parts_selector = 'table tr, .part-code-item, li'
        part_elements = self.page.locator(parts_selector).all()
        return [elem.text_content() for elem in part_elements[:20]]

    def verify_parts_extracted(self):
        """Verify part codes were extracted."""
        parts = self.get_part_codes()
        assert len(parts) > 0, "No part codes extracted"


class SoleraPOCPage(Tier3CustomerSolutionPage):
    """Page object for Solera Claims Processing POC."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url, "solera")

    def upload_claims_photo(self, image_path: str):
        """Upload claims photo."""
        self.page.set_input_files('input[type="file"]', image_path)

    def click_process_claims_button(self):
        """Click process claims button."""
        self.click('button:has-text("Process"), button:has-text("Analyze")')

    def wait_for_ocr_processing(self, timeout: int = 30000):
        """Wait for OCR processing."""
        self.wait_for_processing(timeout)

    def get_vin_number(self) -> str:
        """Get extracted VIN number."""
        vin_selector = '[data-testid="vin"], .vin-number, [class*="vin"]'
        if self.is_visible(vin_selector):
            return self.get_text(vin_selector)
        return ""

    def get_damage_assessment(self) -> str:
        """Get damage assessment."""
        damage_selector = '[data-testid="damage"], .damage-assessment, [class*="damage"]'
        if self.is_visible(damage_selector):
            return self.get_text(damage_selector)
        return ""

    def verify_claims_processed(self):
        """Verify claims were processed."""
        assert self.verify_results_available(), "No claims processing results found"

    def download_claims_report(self):
        """Download claims report PDF."""
        download_button = 'button:has-text("Download Report")'
        if self.is_visible(download_button):
            with self.page.expect_download() as download_info:
                self.click(download_button)
            return download_info.value.path()
        return None


class ConstructionMonitorPOCPage(Tier3CustomerSolutionPage):
    """Page object for Construction Monitor POC."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url, "construction-monitor")

    def upload_construction_document(self, file_path: str):
        """Upload construction document."""
        self.upload_file(file_path)

    def click_extract_entities_button(self):
        """Click extract entities button."""
        self.click('button:has-text("Extract"), button:has-text("Analyze")')

    def get_extracted_entities(self) -> dict:
        """Get extracted entities (PROJECT, CONTRACTOR, MATERIAL, etc.)."""
        results_text = self.get_text('[data-testid="results"], .results-container, pre')
        import json
        try:
            return json.loads(results_text)
        except:
            return {"entities": [], "raw_results": results_text}

    def verify_entities_extracted(self):
        """Verify entities were extracted."""
        entities = self.get_extracted_entities()
        assert entities.get("entities") or entities.get("raw_results"), "No entities extracted"
