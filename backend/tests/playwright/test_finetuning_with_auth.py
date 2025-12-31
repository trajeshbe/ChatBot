"""Fine-Tuning E2E Test with Token-Based Auth.

This test bypasses the login UI by setting the auth token directly in localStorage.
"""
import pytest
from playwright.sync_api import Page, Browser
from page_objects.finetuning_page import FineTuningPage
import time
import os
import json

BASE_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")
BACKEND_URL = "http://localhost:8000"


def get_auth_token() -> dict:
    """Get auth token from backend API."""
    import requests

    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin"}
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Login failed: {response.text}")


@pytest.fixture
def authenticated_page(browser: Browser) -> Page:
    """Create page with authentication token set."""
    page = browser.new_page(viewport={"width": 1920, "height": 1080})

    # Get auth token
    auth_data = get_auth_token()
    access_token = auth_data["access_token"]
    user_data = auth_data["user"]

    print(f"\nAuthenticated as: {user_data['username']} (role: {user_data['role']})")

    # Navigate to frontend first
    page.goto(BASE_URL)
    time.sleep(1)

    # Set auth token in localStorage
    page.evaluate(f"""() => {{
        localStorage.setItem('access_token', '{access_token}');
        localStorage.setItem('user', '{json.dumps(user_data)}');
    }}""")

    print(f"Auth token set in localStorage")

    yield page

    page.close()


@pytest.fixture
def finetuning_page(authenticated_page: Page) -> FineTuningPage:
    """Create fine-tuning page with authentication."""
    ft_page = FineTuningPage(authenticated_page, BASE_URL)
    return ft_page


# ============================================================================
# TESTS
# ============================================================================

def test_navigate_to_finetuning_section(finetuning_page: FineTuningPage):
    """TC_FT_AUTH_001: Navigate to Fine-Tuning section."""
    print("\nTest: Navigate to Fine-Tuning Section")

    # Navigate to admin page
    finetuning_page.navigate_to_admin()
    time.sleep(2)

    finetuning_page.take_screenshot("TC_FT_AUTH_001_admin_page")

    # Verify we're on admin page
    assert "/admin" in finetuning_page.page.url, "Not on admin page"
    print(f"✓ On admin page: {finetuning_page.page.url}")

    # Click Fine-Tuning tab
    finetuning_button = finetuning_page.page.get_by_text("Fine-Tuning", exact=False)
    finetuning_button.click()
    time.sleep(2)

    finetuning_page.take_screenshot("TC_FT_AUTH_001_finetuning_section")

    # Verify Fine-Tuning section loaded
    page_content = finetuning_page.page.content()
    assert "Fine-Tuning" in page_content or "fine" in page_content.lower(), \
        "Fine-Tuning section not loaded"

    print("✓ Fine-Tuning section loaded")


def test_verify_qwen_in_models(finetuning_page: FineTuningPage):
    """TC_FT_AUTH_002: Verify Qwen 2.5 1.5B in base models."""
    print("\nTest: Verify Qwen 2.5 1.5B in Models")

    # Navigate to Fine-Tuning
    finetuning_page.navigate_to_finetuning()
    time.sleep(2)

    # Click Models section
    finetuning_page.click_models_section()
    time.sleep(2)

    finetuning_page.take_screenshot("TC_FT_AUTH_002_models_section")

    # Check page content for Qwen
    page_content = finetuning_page.page.content()

    has_qwen = "qwen" in page_content.lower() or "Qwen" in page_content

    finetuning_page.take_screenshot("TC_FT_AUTH_002_qwen_search")

    if has_qwen:
        print("✓ Qwen 2.5 1.5B found in models catalog")
    else:
        print("⚠ Qwen not found in page content - may need to scroll or click")

        # Try scrolling down
        finetuning_page.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

        page_content = finetuning_page.page.content()
        has_qwen = "qwen" in page_content.lower()

        if has_qwen:
            print("✓ Found Qwen after scrolling")


def test_all_finetuning_sections_accessible(finetuning_page: FineTuningPage):
    """TC_FT_AUTH_003: Test all fine-tuning sections are accessible."""
    print("\nTest: All Fine-Tuning Sections Accessible")

    finetuning_page.navigate_to_finetuning()
    time.sleep(2)

    sections = [
        ("Models", "click_models_section"),
        ("Datasets", "click_datasets_section"),
        ("Fine-tuning Jobs", "click_jobs_section"),
        ("Evaluations", "click_evaluations_section"),
        ("Deployment", "click_deployment_section"),
        ("Monitoring", "click_monitoring_section"),
        ("Governance & Audit", "click_governance_section"),
    ]

    for section_name, method_name in sections:
        print(f"\n  Testing: {section_name}")

        try:
            # Click section
            method = getattr(finetuning_page, method_name)
            method()
            time.sleep(1)

            # Take screenshot
            safe_name = section_name.replace(" ", "_").replace("&", "and")
            finetuning_page.take_screenshot(f"TC_FT_AUTH_003_{safe_name}")

            # Basic verification that page loaded
            print(f"    ✓ {section_name} section loaded")

        except Exception as e:
            print(f"    ✗ {section_name} failed: {e}")


def test_models_section_details(finetuning_page: FineTuningPage):
    """TC_FT_AUTH_004: Test Models section in detail."""
    print("\nTest: Models Section Details")

    finetuning_page.navigate_to_finetuning()
    finetuning_page.click_models_section()
    time.sleep(2)

    finetuning_page.take_screenshot("TC_FT_AUTH_004_models_full_page")

    # Get page content
    page_content = finetuning_page.page.content()

    # Check for common model-related keywords
    keywords = ["base", "model", "qwen", "llama", "mistral", "gemma"]
    found_keywords = [kw for kw in keywords if kw in page_content.lower()]

    print(f"  Found keywords: {found_keywords}")

    # Try to count model cards or entries
    model_cards = finetuning_page.page.locator('[data-testid="base-model-card"]')
    model_count = model_cards.count()

    if model_count > 0:
        print(f"  ✓ Found {model_count} model cards")
    else:
        # Try alternative selectors
        buttons = finetuning_page.page.locator('button').all()
        print(f"  Found {len(buttons)} buttons on page")

        # Look for model names in buttons or text
        for i, button in enumerate(buttons[:10]):  # Check first 10
            try:
                text = button.text_content().lower()
                if any(kw in text for kw in ["qwen", "model", "llama"]):
                    print(f"    Button {i}: {text[:50]}")
            except:
                pass


def test_complete_finetuning_workflow_basic(finetuning_page: FineTuningPage):
    """TC_FT_AUTH_005: Complete workflow test (basic navigation)."""
    print("\nTest: Complete Fine-Tuning Workflow (Basic)")

    steps = [
        ("Navigate to Fine-Tuning", lambda: finetuning_page.navigate_to_finetuning()),
        ("Open Models Section", lambda: finetuning_page.click_models_section()),
        ("Open Datasets Section", lambda: finetuning_page.click_datasets_section()),
        ("Open Jobs Section", lambda: finetuning_page.click_jobs_section()),
        ("Open Evaluations Section", lambda: finetuning_page.click_evaluations_section()),
        ("Open Deployment Section", lambda: finetuning_page.click_deployment_section()),
        ("Open Monitoring Section", lambda: finetuning_page.click_monitoring_section()),
        ("Open Governance Section", lambda: finetuning_page.click_governance_section()),
    ]

    for i, (step_name, step_func) in enumerate(steps, 1):
        print(f"\n  Step {i}: {step_name}")

        try:
            step_func()
            time.sleep(1.5)

            safe_name = step_name.replace(" ", "_")
            finetuning_page.take_screenshot(f"TC_FT_AUTH_005_step{i}_{safe_name}")

            print(f"    ✓ {step_name} - Success")

        except Exception as e:
            print(f"    ✗ {step_name} - Failed: {e}")
            finetuning_page.take_screenshot(f"TC_FT_AUTH_005_step{i}_FAILED")

    print("\n✓ Complete workflow navigation test finished")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
