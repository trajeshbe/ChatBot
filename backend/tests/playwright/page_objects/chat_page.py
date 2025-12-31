"""Chat Page Object for Main Application."""
from playwright.sync_api import Page, expect
from .base_page import BasePage
import time
import json


class ChatPage(BasePage):
    """Page object for Chat Interface."""

    # Navigation Selectors
    CHAT_TAB = 'button:has-text("Chat"), a[href*="chat"], [role="tab"]:has-text("Chat")'
    NEW_CHAT_BUTTON = 'button:has-text("New Chat"), button:has-text("+ New")'

    # Project Selector (simple select dropdown)
    PROJECT_DROPDOWN = 'select'
    PROJECT_OPTION = 'option'

    # Model Selector (BUTTON showing current model, opens menu on click)
    MODEL_BUTTON = 'button:has-text("Ollama"), button:has-text("GPT"), button:has-text("Claude"), button:has-text("LLaMA")'
    MODEL_MENU = '[role="menu"], [role="listbox"]'
    MODEL_MENU_ITEM = '[role="menuitem"], [role="option"]'

    # Chat Input (textarea with placeholder)
    CHAT_INPUT = 'textarea'
    # Send button is icon-only (green button with SVG, no text)
    # Located next to textarea, has specific styling: p-3 + rounded-xl
    SEND_BUTTON = 'button.rounded-xl.bg-primary-600:has(svg)'

    # Messages
    # Be specific to avoid matching other flex containers
    MESSAGE_CONTAINER = 'div.flex.gap-3'  # All messages (user + assistant)
    USER_MESSAGE = 'div.flex.gap-3.justify-end'  # User messages align right
    ASSISTANT_MESSAGE = 'div.flex.gap-3.justify-start'  # Assistant messages align left
    MODEL_BADGE = '[class*="model-badge"], .model-badge, [data-model]'

    # File Upload
    FILE_UPLOAD_BUTTON = 'button:has-text("Upload"), button:has([data-icon="upload"])'
    FILE_INPUT = 'input[type="file"]'
    UPLOADED_FILES_LIST = '[class*="file-list"], [class*="uploaded-files"]'
    FILE_ITEM = '[class*="file-item"]'

    # RAG Settings
    RAG_SETTINGS_BUTTON = 'button:has-text("Settings"), button:has-text("RAG Settings")'
    RAG_TOP_K_SLIDER = 'input[type="range"], input[name*="top_k"]'
    RAG_ENABLE_CHECKBOX = 'input[type="checkbox"][name*="rag"], input[type="checkbox"][name*="enable"]'
    RAG_SAVE_BUTTON = 'button:has-text("Save"), button:has-text("Apply")'

    # Chat History
    CHAT_HISTORY_SIDEBAR = '[class*="sidebar"], [class*="history"]'
    CHAT_HISTORY_ITEM = '[class*="chat-item"], [class*="session-item"]'
    CHAT_TITLE = '[class*="chat-title"], [class*="session-title"]'

    # Prompt Library
    PROMPT_LIBRARY_BUTTON = 'button:has-text("Prompts"), button:has-text("Library")'
    PROMPT_ITEM = '[class*="prompt-item"]'
    PROMPT_USE_BUTTON = 'button:has-text("Use"), button:has-text("Apply")'

    # Export
    EXPORT_BUTTON = 'button:has-text("Export"), button[title*="Export"]'
    EXPORT_EXCEL = 'button:has-text("Excel"), [role="menuitem"]:has-text("Excel")'
    EXPORT_WORD = 'button:has-text("Word"), [role="menuitem"]:has-text("Word")'
    EXPORT_JSON = 'button:has-text("JSON"), [role="menuitem"]:has-text("JSON")'

    # Navigation Tabs
    SIDEBAR_MENU = '[class*="sidebar-menu"], nav'
    MENU_ITEM = '[class*="menu-item"], nav a'

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url)

    def navigate_to_chat(self):
        """Navigate to chat page."""
        self.navigate_to("/")
        time.sleep(2)
        self.wait_for_navigation()

    # === Project Management ===

    def select_project(self, project_name: str):
        """Select a project from dropdown."""
        if self.is_visible(self.PROJECT_DROPDOWN):
            self.click(self.PROJECT_DROPDOWN)
            time.sleep(0.5)
            # Try to select by text
            option = self.page.locator(f'{self.PROJECT_OPTION}:has-text("{project_name}")')
            if option.count() > 0:
                option.first.click()
                time.sleep(1)

    def get_selected_project(self) -> str:
        """Get currently selected project."""
        if self.is_visible(self.PROJECT_DROPDOWN):
            return self.page.locator(self.PROJECT_DROPDOWN).input_value()
        return ""

    # === Model Selection ===

    def select_model(self, model_name: str):
        """Select a model from button dropdown.

        Model selector is a BUTTON showing current model, not a <select>.
        Click button to open menu, then select model from menu.
        """
        # Find and click model button (shows current model)
        model_btn = self.page.locator(self.MODEL_BUTTON).first
        if model_btn.count() > 0:
            model_btn.click()
            time.sleep(1)  # Wait for menu to open

            # Select from menu - try different selector patterns
            selectors = [
                f'text="{model_name}"',
                f'button:has-text("{model_name}")',
                f'[role="menuitem"]:has-text("{model_name}")',
                f'[role="option"]:has-text("{model_name}")'
            ]

            for selector in selectors:
                option = self.page.locator(selector)
                if option.count() > 0:
                    option.first.click()
                    time.sleep(1)
                    return True
        return False

    def get_selected_model(self) -> str:
        """Get currently selected model from button text."""
        model_btn = self.page.locator(self.MODEL_BUTTON).first
        if model_btn.count() > 0:
            # Button text shows current model (e.g., "LLaMA 3.2 Vision 11B (Ollama GPU)")
            return model_btn.inner_text()
        return ""

    def verify_model_in_response(self, model_name: str) -> bool:
        """Verify the model name appears in the last assistant message.

        This checks if the backend actually used the selected model.
        """
        # Wait for assistant message
        time.sleep(2)

        # Get last assistant message
        messages = self.page.locator(self.ASSISTANT_MESSAGE).all()
        if len(messages) == 0:
            return False

        last_message = messages[-1]

        # Check for model badge/indicator in message
        model_badge = last_message.locator(self.MODEL_BADGE)
        if model_badge.count() > 0:
            badge_text = model_badge.inner_text().lower()
            return model_name.lower() in badge_text

        # Check in message metadata (data attributes)
        model_attr = last_message.get_attribute('data-model')
        if model_attr:
            return model_name.lower() in model_attr.lower()

        return False

    # === Chat Operations ===

    def send_message(self, message: str):
        """Send a chat message."""
        # Find and fill input
        input_field = self.page.locator(self.CHAT_INPUT).first
        input_field.fill(message)
        time.sleep(0.5)

        # Click send button
        send_btn = self.page.locator(self.SEND_BUTTON).first
        send_btn.click()
        # Don't wait here - let wait_for_response() handle detection

    def wait_for_response(self, timeout: int = 30000):
        """Wait for assistant response to complete.

        Strategy: Wait for the last assistant message text to change,
        indicating a new response has arrived.
        """
        # Get text of last assistant message before sending
        initial_text = self.get_last_assistant_message()
        print(f"[wait_for_response] Initial last message text: {initial_text[:100]}...")

        # Wait for the last message to change
        start_time = time.time()
        iteration = 0
        while time.time() - start_time < timeout / 1000:
            current_text = self.get_last_assistant_message()

            # Log every 10 iterations (5 seconds)
            if iteration % 10 == 0:
                elapsed = time.time() - start_time
                print(f"[wait_for_response] [{elapsed:5.1f}s] Checking if last message changed...")

            # Check if text changed (new response arrived)
            if current_text != initial_text and len(current_text) > 0:
                elapsed = time.time() - start_time
                print(f"[wait_for_response] ✓ New response detected after {elapsed:.1f}s")
                print(f"[wait_for_response] New text: {current_text[:100]}...")
                time.sleep(2)  # Wait for streaming to complete
                return True

            time.sleep(0.5)
            iteration += 1

        print(f"[wait_for_response] ✗ Timeout after {timeout/1000}s - no new response detected")
        return False

    def get_last_user_message(self) -> str:
        """Get text of last user message."""
        messages = self.page.locator(self.USER_MESSAGE).all()
        if len(messages) > 0:
            return messages[-1].inner_text()
        return ""

    def get_last_assistant_message(self) -> str:
        """Get text of last assistant message."""
        messages = self.page.locator(self.ASSISTANT_MESSAGE).all()
        if len(messages) > 0:
            return messages[-1].inner_text()
        return ""

    def get_message_count(self) -> int:
        """Get total message count."""
        return self.page.locator(self.MESSAGE_CONTAINER).count()

    def start_new_chat(self):
        """Start a new chat session."""
        new_chat_btn = self.page.locator(self.NEW_CHAT_BUTTON).first
        if new_chat_btn.count() > 0:
            new_chat_btn.click()
            time.sleep(1)

    # === File Upload ===

    def upload_file(self, file_path: str):
        """Upload a file to the chat."""
        # Click upload button to reveal file input
        upload_btn = self.page.locator(self.FILE_UPLOAD_BUTTON).first
        if upload_btn.count() > 0:
            upload_btn.click()
            time.sleep(0.5)

        # Find and use file input
        file_input = self.page.locator(self.FILE_INPUT).first
        file_input.set_input_files(file_path)
        time.sleep(2)  # Wait for upload to complete

    def get_uploaded_files(self) -> list:
        """Get list of uploaded file names."""
        files = []
        file_items = self.page.locator(self.FILE_ITEM).all()
        for item in file_items:
            files.append(item.inner_text())
        return files

    def verify_file_uploaded(self, filename: str) -> bool:
        """Verify a file was uploaded."""
        files = self.get_uploaded_files()
        return any(filename in f for f in files)

    # === RAG Settings ===

    def open_rag_settings(self):
        """Open RAG settings panel."""
        settings_btn = self.page.locator(self.RAG_SETTINGS_BUTTON).first
        if settings_btn.count() > 0:
            settings_btn.click()
            time.sleep(1)

    def set_rag_top_k(self, value: int):
        """Set RAG top_k value."""
        slider = self.page.locator(self.RAG_TOP_K_SLIDER).first
        if slider.count() > 0:
            slider.fill(str(value))
            time.sleep(0.5)

    def toggle_rag(self, enable: bool):
        """Enable or disable RAG."""
        checkbox = self.page.locator(self.RAG_ENABLE_CHECKBOX).first
        if checkbox.count() > 0:
            is_checked = checkbox.is_checked()
            if is_checked != enable:
                checkbox.click()
                time.sleep(0.5)

    def save_rag_settings(self):
        """Save RAG settings."""
        save_btn = self.page.locator(self.RAG_SAVE_BUTTON).first
        if save_btn.count() > 0:
            save_btn.click()
            time.sleep(1)

    # === Chat History ===

    def get_chat_history_items(self) -> list:
        """Get list of chat history items."""
        items = self.page.locator(self.CHAT_HISTORY_ITEM).all()
        return [item.inner_text() for item in items]

    def select_chat_from_history(self, index: int = 0):
        """Select a chat from history by index."""
        items = self.page.locator(self.CHAT_HISTORY_ITEM).all()
        if index < len(items):
            items[index].click()
            time.sleep(1)

    def get_current_chat_title(self) -> str:
        """Get current chat title."""
        title = self.page.locator(self.CHAT_TITLE).first
        if title.count() > 0:
            return title.inner_text()
        return ""

    # === Prompt Library ===

    def open_prompt_library(self):
        """Open prompt library."""
        library_btn = self.page.locator(self.PROMPT_LIBRARY_BUTTON).first
        if library_btn.count() > 0:
            library_btn.click()
            time.sleep(1)

    def use_prompt(self, prompt_name: str):
        """Use a prompt from library."""
        # Find prompt by name
        prompt = self.page.locator(f'{self.PROMPT_ITEM}:has-text("{prompt_name}")').first
        if prompt.count() > 0:
            # Click use button within the prompt item
            use_btn = prompt.locator(self.PROMPT_USE_BUTTON)
            if use_btn.count() > 0:
                use_btn.click()
                time.sleep(1)

    def get_prompt_library_items(self) -> list:
        """Get list of prompts in library."""
        items = self.page.locator(self.PROMPT_ITEM).all()
        return [item.inner_text() for item in items]

    # === Export ===

    def export_to_excel(self):
        """Export chat to Excel."""
        # Open export menu
        export_btn = self.page.locator(self.EXPORT_BUTTON).first
        if export_btn.count() > 0:
            export_btn.click()
            time.sleep(0.5)

        # Click Excel option
        excel_btn = self.page.locator(self.EXPORT_EXCEL).first
        if excel_btn.count() > 0:
            # Set up download handler
            with self.page.expect_download() as download_info:
                excel_btn.click()
            download = download_info.value
            return download.path()
        return None

    def export_to_word(self):
        """Export chat to Word."""
        export_btn = self.page.locator(self.EXPORT_BUTTON).first
        if export_btn.count() > 0:
            export_btn.click()
            time.sleep(0.5)

        word_btn = self.page.locator(self.EXPORT_WORD).first
        if word_btn.count() > 0:
            with self.page.expect_download() as download_info:
                word_btn.click()
            download = download_info.value
            return download.path()
        return None

    def export_to_json(self):
        """Export chat to JSON."""
        export_btn = self.page.locator(self.EXPORT_BUTTON).first
        if export_btn.count() > 0:
            export_btn.click()
            time.sleep(0.5)

        json_btn = self.page.locator(self.EXPORT_JSON).first
        if json_btn.count() > 0:
            with self.page.expect_download() as download_info:
                json_btn.click()
            download = download_info.value
            return download.path()
        return None

    # === Navigation ===

    def navigate_to_tab(self, tab_name: str):
        """Navigate to a specific tab."""
        tab = self.page.locator(f'button:has-text("{tab_name}"), a:has-text("{tab_name}")').first
        if tab.count() > 0:
            tab.click()
            time.sleep(1)

    def navigate_back(self):
        """Navigate back using browser back button."""
        self.page.go_back()
        time.sleep(1)

    def navigate_forward(self):
        """Navigate forward using browser forward button."""
        self.page.go_forward()
        time.sleep(1)

    def get_session_id_from_url(self) -> str:
        """Extract session ID from URL."""
        url = self.page.url
        # Try to extract session_id from URL params or path
        if "session_id=" in url:
            return url.split("session_id=")[1].split("&")[0]
        return ""

    def verify_session_retained(self, expected_message_count: int) -> bool:
        """Verify session is retained (message count matches)."""
        time.sleep(1)
        actual_count = self.get_message_count()
        return actual_count >= expected_message_count

    # === Backend Verification ===

    def get_last_response_metadata(self) -> dict:
        """Get metadata from last response (model used, tokens, etc)."""
        # This would need to inspect network responses or page data
        # For now, return empty dict - can be extended based on actual implementation
        return {}

    def verify_model_was_used(self, expected_model: str) -> bool:
        """Verify the backend actually used the expected model.

        This is critical for catching model selection bugs.
        """
        # Method 1: Check model badge in UI
        if self.verify_model_in_response(expected_model):
            return True

        # Method 2: Check network request/response
        # This would require listening to network traffic
        # Can be implemented using page.route() or CDP

        # Method 3: Check backend logs (not ideal for E2E tests)

        return False
