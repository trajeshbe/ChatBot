"""Export Wizard Page Object for Playwright tests."""
from playwright.sync_api import Page, expect
from typing import Optional, List
import time
from .base_page import BasePage


class ExportWizardPage(BasePage):
    """Page object for Export Wizard functionality."""

    # Selectors
    TRIGGER_BUTTON = 'button:has-text("Export POC Package")'
    MODAL_CONTAINER = '[class*="fixed inset-0"]'
    MODAL_HEADER = 'h2:has-text("Export Wizard")'
    CLOSE_BUTTON = 'button[class*="hover:bg-gray"]'

    # Step 1: Tier Selection
    TIER_2_BUTTON = 'button:has-text("Tier 2")'
    TIER_3_BUTTON = 'button:has-text("Tier 3")'

    # Step 2: Module Selection
    MODULE_CARD = 'button[class*="border-2"]'
    SELECTED_MODULE_INDICATOR = 'svg[class*="text-purple"]'

    # Step 3: Export Progress
    PROGRESS_BAR = 'div[class*="bg-gradient-to-r from-purple"]'
    PROGRESS_TEXT = 'span:has-text("%")'
    CURRENT_STEP_TEXT = 'span[class*="text-gray-700"]'

    # Step 4: Complete
    SUCCESS_ICON = 'svg[class*="text-green"]'
    DOWNLOAD_BUTTON = 'button:has-text("Download ZIP Package")'

    # Footer
    BACK_BUTTON = 'button:has-text("Back")'
    CREATE_EXPORT_BUTTON = 'button:has-text("Create Export Package")'

    # Error
    ERROR_ALERT = '[class*="bg-red"]'
    ERROR_MESSAGE = '[class*="text-red-700"]'

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url)

    def navigate_to_page_with_button(self):
        """Navigate to a page that has the Export Wizard button (e.g., admin page)."""
        self.navigate_to("/admin")
        time.sleep(2)

    def click_export_wizard_button(self):
        """Click the Export POC Package trigger button."""
        self.page.click(self.TRIGGER_BUTTON)
        self.wait_for_modal_visible()

    def wait_for_modal_visible(self):
        """Wait for the Export Wizard modal to appear."""
        self.page.wait_for_selector(self.MODAL_CONTAINER, state="visible", timeout=10000)
        self.page.wait_for_selector(self.MODAL_HEADER, state="visible", timeout=10000)

    def is_modal_visible(self) -> bool:
        """Check if the Export Wizard modal is visible."""
        return self.page.is_visible(self.MODAL_CONTAINER)

    def close_modal(self):
        """Close the Export Wizard modal."""
        self.page.click(self.CLOSE_BUTTON)
        time.sleep(0.5)

    # Step 1: Tier Selection

    def select_tier_2(self):
        """Select Tier 2 (Domain Verticals)."""
        self.page.click(self.TIER_2_BUTTON)
        time.sleep(1)

    def select_tier_3(self):
        """Select Tier 3 (Customer Solutions)."""
        self.page.click(self.TIER_3_BUTTON)
        time.sleep(1)

    def is_on_tier_selection_step(self) -> bool:
        """Check if currently on tier selection step."""
        return self.page.is_visible('h3:has-text("Step 1: Select Module Tier")')

    # Step 2: Module Selection

    def is_on_module_selection_step(self) -> bool:
        """Check if currently on module selection step."""
        return self.page.is_visible('h3:has-text("Step 2: Select Module to Export")')

    def get_available_modules(self) -> List[str]:
        """Get list of available module names."""
        module_cards = self.page.locator(self.MODULE_CARD).all()
        module_names = []

        for card in module_cards:
            # Extract module name from card (first h4 element)
            name_element = card.locator('h4').first
            if name_element.is_visible():
                module_names.append(name_element.text_content())

        return module_names

    def select_module_by_name(self, module_name: str):
        """Select a module by its name."""
        # Find and click the module card containing the module name
        module_card = self.page.locator(f'{self.MODULE_CARD}:has(h4:has-text("{module_name}"))').first
        module_card.click()
        time.sleep(0.5)

    def is_module_selected(self, module_name: str) -> bool:
        """Check if a specific module is selected."""
        module_card = self.page.locator(f'{self.MODULE_CARD}:has(h4:has-text("{module_name}"))').first

        # Check if the card has the selected state (purple border)
        has_selected_border = 'border-purple' in module_card.get_attribute('class')

        return has_selected_border

    def click_create_export_button(self):
        """Click the 'Create Export Package' button."""
        self.page.click(self.CREATE_EXPORT_BUTTON)
        time.sleep(1)

    def is_create_export_button_enabled(self) -> bool:
        """Check if the create export button is enabled."""
        button = self.page.locator(self.CREATE_EXPORT_BUTTON).first
        is_disabled = 'cursor-not-allowed' in button.get_attribute('class')
        return not is_disabled

    # Step 3: Export Progress

    def is_on_export_progress_step(self) -> bool:
        """Check if currently on export progress step."""
        return self.page.is_visible('h3:has-text("Creating Export Package")')

    def get_export_progress(self) -> int:
        """Get current export progress percentage."""
        try:
            progress_text = self.page.locator(self.PROGRESS_TEXT).first.text_content()
            # Extract number from "75%" format
            return int(progress_text.strip('%'))
        except:
            return 0

    def get_current_step_text(self) -> str:
        """Get current step description text."""
        try:
            return self.page.locator(self.CURRENT_STEP_TEXT).first.text_content()
        except:
            return ""

    def wait_for_export_completion(self, timeout: int = 300000):
        """
        Wait for export to complete (up to 5 minutes).

        Args:
            timeout: Maximum wait time in milliseconds (default 300000 = 5 minutes)
        """
        start_time = time.time()

        while (time.time() - start_time) * 1000 < timeout:
            if self.is_on_export_complete_step():
                return True

            if self.has_error():
                raise Exception(f"Export failed: {self.get_error_message()}")

            time.sleep(2)  # Poll every 2 seconds

        raise TimeoutError(f"Export did not complete within {timeout/1000} seconds")

    # Step 4: Export Complete

    def is_on_export_complete_step(self) -> bool:
        """Check if currently on export complete step."""
        return self.page.is_visible('h3:has-text("Export Package Ready!")')

    def is_success_icon_visible(self) -> bool:
        """Check if success icon is visible."""
        return self.page.is_visible(self.SUCCESS_ICON)

    def click_download_button(self):
        """Click the 'Download ZIP Package' button."""
        # Set up download handler before clicking
        with self.page.expect_download() as download_info:
            self.page.click(self.DOWNLOAD_BUTTON)

        download = download_info.value
        return download

    def get_export_summary_info(self) -> dict:
        """Get export summary information from the complete screen."""
        summary = {}

        try:
            # Extract module name, tier, export ID from summary section
            summary_section = self.page.locator('[class*="bg-gray-50"]').first

            text_content = summary_section.text_content()

            # Parse the text (this is simplified - you might need more robust parsing)
            if "Module:" in text_content:
                summary['module'] = text_content.split("Module:")[1].split("Tier:")[0].strip()

            if "Tier:" in text_content:
                summary['tier'] = text_content.split("Tier:")[1].split("Export ID:")[0].strip()

            if "Export ID:" in text_content:
                summary['export_id'] = text_content.split("Export ID:")[1].strip()

        except Exception as e:
            print(f"Failed to parse export summary: {e}")

        return summary

    # Error Handling

    def has_error(self) -> bool:
        """Check if there is an error message displayed."""
        return self.page.is_visible(self.ERROR_ALERT)

    def get_error_message(self) -> str:
        """Get the error message text."""
        if self.has_error():
            return self.page.locator(self.ERROR_MESSAGE).first.text_content()
        return ""

    def close_error_alert(self):
        """Close the error alert."""
        close_button = self.page.locator(f'{self.ERROR_ALERT} button').first
        close_button.click()
        time.sleep(0.5)

    # Navigation

    def click_back_button(self):
        """Click the Back button."""
        self.page.click(self.BACK_BUTTON)
        time.sleep(0.5)

    # Complete Workflow Helpers

    def complete_export_workflow(self, tier: int, module_name: str, wait_for_completion: bool = True):
        """
        Complete full export workflow from start to download.

        Args:
            tier: 2 or 3
            module_name: Name of module to export
            wait_for_completion: Whether to wait for export to complete

        Returns:
            Download object if wait_for_completion=True, None otherwise
        """
        # Step 1: Select tier
        if tier == 2:
            self.select_tier_2()
        elif tier == 3:
            self.select_tier_3()
        else:
            raise ValueError("Tier must be 2 or 3")

        assert self.is_on_module_selection_step(), "Failed to advance to module selection"

        # Step 2: Select module
        modules = self.get_available_modules()
        assert module_name in modules, f"Module '{module_name}' not found in available modules: {modules}"

        self.select_module_by_name(module_name)
        assert self.is_module_selected(module_name), f"Failed to select module '{module_name}'"

        # Step 3: Create export
        assert self.is_create_export_button_enabled(), "Create export button is disabled"
        self.click_create_export_button()

        assert self.is_on_export_progress_step(), "Failed to start export"

        # Step 4: Wait for completion (optional)
        if wait_for_completion:
            self.wait_for_export_completion()
            assert self.is_on_export_complete_step(), "Export did not complete successfully"

            # Download
            download = self.click_download_button()
            return download

        return None

    # Validation Helpers

    def validate_modal_structure(self) -> bool:
        """Validate that the modal has all required elements."""
        checks = {
            "Modal container visible": self.is_modal_visible(),
            "Modal header visible": self.page.is_visible(self.MODAL_HEADER),
            "Close button visible": self.page.is_visible(self.CLOSE_BUTTON),
        }

        all_passed = all(checks.values())

        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")

        return all_passed

    def validate_tier_selection_step(self) -> bool:
        """Validate Step 1 - Tier Selection."""
        checks = {
            "On tier selection step": self.is_on_tier_selection_step(),
            "Tier 2 button visible": self.page.is_visible(self.TIER_2_BUTTON),
            "Tier 3 button visible": self.page.is_visible(self.TIER_3_BUTTON),
        }

        all_passed = all(checks.values())

        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")

        return all_passed

    def validate_module_selection_step(self) -> bool:
        """Validate Step 2 - Module Selection."""
        checks = {
            "On module selection step": self.is_on_module_selection_step(),
            "Modules loaded": len(self.get_available_modules()) > 0,
            "Back button visible": self.page.is_visible(self.BACK_BUTTON),
        }

        all_passed = all(checks.values())

        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")

        return all_passed
