"""
Form Handler - Intelligent Form Automation with Playwright

Provides smart form field detection, filling, and submission capabilities.

Features:
- Auto-detect form fields
- Smart field matching (name, id, label, fuzzy)
- Multi-step form navigation
- CAPTCHA detection
- Error handling and retry
- File upload support
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class FormHandler:
    """
    Intelligent form automation using Playwright.

    Integrates seamlessly with existing scraper workflows.
    Zero new dependencies - uses Playwright already installed.
    """

    # Timeout constants (milliseconds)
    DEFAULT_TIMEOUT = 5000
    SUBMIT_TIMEOUT = 10000
    NAVIGATION_TIMEOUT = 30000

    def __init__(self, page: Page):
        """
        Initialize form handler.

        Args:
            page: Playwright Page object (from scraper)
        """
        self.page = page
        logger.info("FormHandler initialized")

    async def fill_and_submit_form(
        self,
        form_data: Dict[str, Any],
        submit_button_selector: Optional[str] = None,
        wait_after_submit: int = 3000,
        check_for_captcha: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fill form fields and submit.

        Args:
            form_data: Dictionary mapping field names to values
                      {"field_name": "value", "email": "user@example.com"}
            submit_button_selector: CSS selector for submit button
                                   (auto-detected if None)
            wait_after_submit: Time to wait after submission (ms)
            check_for_captcha: Whether to check for CAPTCHA
            **kwargs: Additional options (timeout, retry_count, etc.)

        Returns:
            {
                "success": bool,
                "fields_filled": int,
                "fields_failed": List[str],
                "submit_successful": bool,
                "response_url": str,
                "errors": List[str],
                "metadata": dict
            }

        Raises:
            RuntimeError: If form submission fails critically
        """
        logger.info(f"Filling form with {len(form_data)} fields")

        result = {
            "success": False,
            "fields_filled": 0,
            "fields_failed": [],
            "submit_successful": False,
            "response_url": "",
            "errors": [],
            "metadata": {}
        }

        try:
            # Check for CAPTCHA first
            if check_for_captcha:
                has_captcha = await self._detect_captcha()
                if has_captcha:
                    logger.warning("CAPTCHA detected on page")
                    result["errors"].append("CAPTCHA detected - manual intervention required")
                    result["metadata"]["captcha_detected"] = True
                    # Optionally pause for manual solving
                    if kwargs.get("pause_for_captcha", False):
                        logger.info("Pausing for manual CAPTCHA solving...")
                        await self.page.pause()

            # Fill form fields
            fill_results = await self._fill_fields(form_data, **kwargs)
            result["fields_filled"] = fill_results["filled_count"]
            result["fields_failed"] = fill_results["failed_fields"]
            result["errors"].extend(fill_results["errors"])

            # Check if enough fields were filled
            min_fields = kwargs.get("min_fields_required", len(form_data) // 2)
            if result["fields_filled"] < min_fields:
                logger.warning(
                    f"Only {result['fields_filled']}/{len(form_data)} fields filled "
                    f"(minimum: {min_fields})"
                )
                result["errors"].append(
                    f"Insufficient fields filled: {result['fields_filled']}/{len(form_data)}"
                )

            # Submit form
            if kwargs.get("auto_submit", True):
                submit_result = await self._submit_form(
                    submit_button_selector,
                    wait_after_submit,
                    **kwargs
                )
                result["submit_successful"] = submit_result["success"]
                result["response_url"] = submit_result.get("url", "")
                if not submit_result["success"]:
                    result["errors"].append(submit_result.get("error", "Submit failed"))

            # Overall success
            result["success"] = (
                result["fields_filled"] > 0 and
                (result["submit_successful"] or not kwargs.get("auto_submit", True))
            )

            logger.info(
                f"Form handling completed - "
                f"Success: {result['success']}, "
                f"Fields filled: {result['fields_filled']}/{len(form_data)}, "
                f"Submitted: {result['submit_successful']}"
            )

            return result

        except Exception as e:
            logger.error(f"Form handling failed: {e}", exc_info=True)
            result["errors"].append(str(e))
            return result

    async def _fill_fields(
        self,
        form_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fill form fields using intelligent field matching.

        Args:
            form_data: Field name to value mapping
            **kwargs: Additional options

        Returns:
            Fill results with counts and errors
        """
        filled_count = 0
        failed_fields = []
        errors = []

        for field_name, field_value in form_data.items():
            try:
                # Find field
                field_selector = await self._find_field_selector(field_name)

                if field_selector is None:
                    logger.warning(f"Could not find field: {field_name}")
                    failed_fields.append(field_name)
                    errors.append(f"Field not found: {field_name}")
                    continue

                # Fill field based on type
                fill_success = await self._fill_field(
                    field_selector,
                    field_value,
                    **kwargs
                )

                if fill_success:
                    filled_count += 1
                    logger.debug(f"Filled field: {field_name} = {field_value}")
                else:
                    failed_fields.append(field_name)
                    errors.append(f"Failed to fill: {field_name}")

            except Exception as e:
                logger.error(f"Error filling field {field_name}: {e}")
                failed_fields.append(field_name)
                errors.append(f"{field_name}: {str(e)}")

        return {
            "filled_count": filled_count,
            "failed_fields": failed_fields,
            "errors": errors
        }

    async def _find_field_selector(self, field_name: str) -> Optional[str]:
        """
        Find form field using intelligent matching strategies.

        Tries multiple strategies:
        1. Exact match by name attribute
        2. Exact match by id attribute
        3. Label text match
        4. Fuzzy match on label/placeholder

        Args:
            field_name: Field name to search for

        Returns:
            CSS selector string or None if not found
        """
        # Strategy 1: Match by name attribute
        selector = f'input[name="{field_name}"], select[name="{field_name}"], textarea[name="{field_name}"]'
        if await self._element_exists(selector):
            return selector

        # Strategy 2: Match by id attribute
        selector = f'#{field_name}'
        if await self._element_exists(selector):
            return selector

        # Strategy 3: Match by label text (exact)
        try:
            # Try to find label containing the field name
            label_selector = f'label:has-text("{field_name}")'
            if await self._element_exists(label_selector):
                # Get the for attribute or find input within label
                for_attr = await self.page.eval_on_selector(
                    label_selector,
                    'el => el.getAttribute("for")'
                )
                if for_attr:
                    return f'#{for_attr}'
                else:
                    # Input might be within label
                    return f'{label_selector} >> input, {label_selector} >> select, {label_selector} >> textarea'
        except:
            pass

        # Strategy 4: Fuzzy match on label/placeholder
        try:
            # Case-insensitive match
            field_name_lower = field_name.lower().replace('_', ' ').replace('-', ' ')
            selector = (
                f'input[placeholder*="{field_name_lower}" i], '
                f'textarea[placeholder*="{field_name_lower}" i], '
                f'input[aria-label*="{field_name_lower}" i]'
            )
            if await self._element_exists(selector):
                return selector
        except:
            pass

        # Strategy 5: Try common variations
        variations = [
            field_name.replace('_', '-'),  # username → user-name
            field_name.replace('_', ''),   # username → username
            field_name.replace('-', '_'),  # user-name → user_name
        ]

        for variation in variations:
            selector = f'input[name="{variation}"], select[name="{variation}"], textarea[name="{variation}"]'
            if await self._element_exists(selector):
                return selector

        return None

    async def _fill_field(
        self,
        selector: str,
        value: Any,
        **kwargs
    ) -> bool:
        """
        Fill a form field based on its type.

        Args:
            selector: CSS selector for field
            value: Value to fill
            **kwargs: Additional options

        Returns:
            True if filled successfully
        """
        try:
            # Get field type
            field_type = await self.page.eval_on_selector(
                selector,
                'el => el.tagName + ":" + (el.type || "text")'
            )
            field_type = field_type.lower()

            timeout = kwargs.get("field_timeout", self.DEFAULT_TIMEOUT)

            # Handle different field types
            if "select:" in field_type:
                # Dropdown/select
                await self.page.select_option(selector, str(value), timeout=timeout)

            elif "textarea:" in field_type:
                # Textarea
                await self.page.fill(selector, str(value), timeout=timeout)

            elif "checkbox" in field_type or "radio" in field_type:
                # Checkbox or radio button
                if value:
                    await self.page.check(selector, timeout=timeout)
                else:
                    await self.page.uncheck(selector, timeout=timeout)

            elif "file" in field_type:
                # File input
                if isinstance(value, str):
                    await self.page.set_input_files(selector, value, timeout=timeout)
                elif isinstance(value, list):
                    await self.page.set_input_files(selector, value, timeout=timeout)

            else:
                # Text input (default)
                await self.page.fill(selector, str(value), timeout=timeout)

            return True

        except Exception as e:
            logger.error(f"Failed to fill field {selector}: {e}")
            return False

    async def _submit_form(
        self,
        submit_selector: Optional[str],
        wait_after_submit: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Submit form and wait for response.

        Args:
            submit_selector: CSS selector for submit button
            wait_after_submit: Time to wait after submission (ms)
            **kwargs: Additional options

        Returns:
            Submit result dictionary
        """
        try:
            # Auto-detect submit button if not provided
            if submit_selector is None:
                submit_selector = await self._find_submit_button()

            if submit_selector is None:
                logger.error("Could not find submit button")
                return {
                    "success": False,
                    "error": "Submit button not found"
                }

            # Get current URL
            current_url = self.page.url

            # Click submit button
            async with self.page.expect_navigation(
                timeout=kwargs.get("navigation_timeout", self.NAVIGATION_TIMEOUT),
                wait_until="networkidle"
            ):
                await self.page.click(submit_selector, timeout=self.SUBMIT_TIMEOUT)

            # Wait additional time if specified
            if wait_after_submit > 0:
                await asyncio.sleep(wait_after_submit / 1000.0)

            # Get new URL
            new_url = self.page.url

            logger.info(f"Form submitted - {current_url} → {new_url}")

            return {
                "success": True,
                "url": new_url,
                "redirected": current_url != new_url
            }

        except PlaywrightTimeout:
            logger.warning("Form submission timed out")
            return {
                "success": False,
                "error": "Submit timeout",
                "url": self.page.url
            }
        except Exception as e:
            logger.error(f"Form submission failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": self.page.url
            }

    async def _find_submit_button(self) -> Optional[str]:
        """
        Auto-detect submit button.

        Returns:
            CSS selector for submit button or None
        """
        # Try common selectors in order of specificity
        selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Send")',
            'button:has-text("Continue")',
            'button:has-text("Next")',
            'input[value*="Submit" i]',
            'input[value*="Send" i]',
            'form button:last-child',  # Last button in form (common pattern)
        ]

        for selector in selectors:
            if await self._element_exists(selector):
                return selector

        return None

    async def _detect_captcha(self) -> bool:
        """
        Detect if page contains CAPTCHA.

        Returns:
            True if CAPTCHA detected
        """
        # Common CAPTCHA indicators
        captcha_selectors = [
            '[class*="captcha" i]',
            '[id*="captcha" i]',
            '[class*="recaptcha" i]',
            '[id*="recaptcha" i]',
            'iframe[src*="recaptcha"]',
            'iframe[src*="hcaptcha"]',
            '[class*="hcaptcha" i]',
        ]

        for selector in captcha_selectors:
            if await self._element_exists(selector):
                logger.info(f"CAPTCHA detected: {selector}")
                return True

        return False

    async def _element_exists(self, selector: str) -> bool:
        """
        Check if element exists on page.

        Args:
            selector: CSS selector

        Returns:
            True if element exists
        """
        try:
            await self.page.wait_for_selector(
                selector,
                timeout=1000,
                state="attached"
            )
            return True
        except:
            return False

    async def get_form_fields(self) -> List[Dict[str, Any]]:
        """
        Get all form fields on the page.

        Returns:
            List of field information dictionaries
        """
        try:
            fields = await self.page.evaluate('''
                () => {
                    const fields = [];
                    const inputs = document.querySelectorAll('input, select, textarea');

                    inputs.forEach(input => {
                        fields.push({
                            tag: input.tagName.toLowerCase(),
                            type: input.type || 'text',
                            name: input.name || '',
                            id: input.id || '',
                            placeholder: input.placeholder || '',
                            required: input.required || false,
                            value: input.value || ''
                        });
                    });

                    return fields;
                }
            ''')

            logger.info(f"Found {len(fields)} form fields")
            return fields

        except Exception as e:
            logger.error(f"Failed to get form fields: {e}")
            return []

    async def get_form_status(self) -> Dict[str, Any]:
        """
        Get form status and validation state.

        Returns:
            Form status dictionary
        """
        try:
            status = await self.page.evaluate('''
                () => {
                    const form = document.querySelector('form');
                    if (!form) return {has_form: false};

                    const inputs = form.querySelectorAll('input, select, textarea');
                    let filled = 0;
                    let required = 0;
                    let total = inputs.length;

                    inputs.forEach(input => {
                        if (input.required) required++;
                        if (input.value) filled++;
                    });

                    return {
                        has_form: true,
                        total_fields: total,
                        required_fields: required,
                        filled_fields: filled,
                        is_valid: form.checkValidity ? form.checkValidity() : null
                    };
                }
            ''')

            return status

        except Exception as e:
            logger.error(f"Failed to get form status: {e}")
            return {"has_form": False, "error": str(e)}
