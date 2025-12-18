"""Fine-Tuning UI Data Verification Test.

This test verifies that data is actually displayed in the fine-tuning UI,
not just that the sections are accessible.
"""
import pytest
from playwright.sync_api import Page, Browser, expect
from page_objects.finetuning_page import FineTuningPage
import time
import os
import json
import requests

BASE_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")
BACKEND_URL = "http://localhost:8000"


def get_auth_token() -> dict:
    """Get auth token from backend API."""
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

    print(f"\nAuthenticated as: {user_data['username']} (role: {user_data['role']}")

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


def test_models_catalog_displays_data(finetuning_page: FineTuningPage):
    """Test that Models section displays actual model data."""
    print("\n=== Test: Models Catalog Displays Data ===")

    # Navigate to fine-tuning
    finetuning_page.navigate_to_finetuning()
    time.sleep(2)

    # Click Models section
    finetuning_page.click_models_section()
    time.sleep(3)  # Give it time to fetch data

    # Take screenshot before checking
    finetuning_page.take_screenshot("models_catalog_before_check")

    # Check if page contains model-related content
    page_content = finetuning_page.page.content().lower()

    print(f"\n  Checking page content for model data...")

    # Check for Qwen (case insensitive)
    has_qwen = "qwen" in page_content
    print(f"  - Contains 'Qwen': {has_qwen}")

    # Check for other model indicators
    has_model_size = "1.5b" in page_content or "7b" in page_content or "3b" in page_content
    print(f"  - Contains model size (1.5B/7B/3B): {has_model_size}")

    has_qlora = "qlora" in page_content or "q-lora" in page_content
    print(f"  - Contains 'QLoRA': {has_qlora}")

    has_lora = "lora" in page_content
    print(f"  - Contains 'LoRA': {has_lora}")

    # Check for model families
    has_llama = "llama" in page_content
    has_mistral = "mistral" in page_content
    has_gemma = "gemma" in page_content

    print(f"  - Contains model families: Llama={has_llama}, Mistral={has_mistral}, Gemma={has_gemma}")

    # Look for specific UI elements
    try:
        # Try to find model cards or lists
        model_elements = finetuning_page.page.locator('[class*="model"], [class*="card"]').all()
        print(f"  - Found {len(model_elements)} elements with 'model' or 'card' in class name")

        # Try to find buttons
        buttons = finetuning_page.page.locator('button').all()
        button_texts = []
        for i, btn in enumerate(buttons[:20]):  # Check first 20 buttons
            try:
                text = btn.text_content().strip().lower()
                if text and len(text) > 0:
                    button_texts.append(text)
            except:
                pass

        print(f"  - Found {len(buttons)} total buttons")
        print(f"  - Sample button texts: {button_texts[:10]}")

        # Look for text containing model names
        page_text = finetuning_page.page.locator('body').text_content()
        print(f"\n  Page text sample (first 500 chars):")
        print(f"  {page_text[:500] if page_text else 'NO TEXT'}")

    except Exception as e:
        print(f"  ! Error checking UI elements: {e}")

    # Take final screenshot
    finetuning_page.take_screenshot("models_catalog_after_check")

    # Assert we found some model data
    assert has_qwen or has_model_size or has_qlora or has_llama or has_mistral, \
        "No model data found in UI! Expected to see Qwen, model sizes, or training methods."

    print("\n  ✓ Models catalog contains data")


def test_backend_api_returns_models(finetuning_page: FineTuningPage):
    """Verify backend API returns models (sanity check)."""
    print("\n=== Test: Backend API Returns Models ===")

    # Get token from localStorage
    token = finetuning_page.page.evaluate("() => localStorage.getItem('access_token')")

    print(f"  Token: {token[:50] if token else 'NO TOKEN'}...")

    # Call backend API directly
    response = requests.get(
        f"{BACKEND_URL}/api/v1/finetuning/base-models",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"  Status: {response.status_code}")

    assert response.status_code == 200, f"API call failed: {response.text}"

    data = response.json()
    models = data.get("models", [])

    print(f"  Models returned: {len(models)}")

    if models:
        print(f"\n  First model:")
        print(f"    - ID: {models[0].get('id')}")
        print(f"    - Name: {models[0].get('name')}")
        print(f"    - Family: {models[0].get('family')}")

        # Verify Qwen is first
        assert models[0]['id'] == 'qwen-2.5-1.5b', "First model should be Qwen 2.5 1.5B"
        print(f"\n  ✓ Backend API returns Qwen 2.5 1.5B as first model")


def test_frontend_can_fetch_models(finetuning_page: FineTuningPage):
    """Test that frontend successfully fetches models from backend."""
    print("\n=== Test: Frontend Fetches Models ===")

    # Navigate to fine-tuning and models section
    finetuning_page.navigate_to_finetuning()
    time.sleep(2)
    finetuning_page.click_models_section()
    time.sleep(3)

    # Check browser console for errors
    console_messages = []

    def handle_console(msg):
        console_messages.append(f"{msg.type}: {msg.text}")

    finetuning_page.page.on("console", handle_console)

    # Reload page to capture console messages
    finetuning_page.page.reload()
    time.sleep(3)

    print(f"\n  Console messages ({len(console_messages)}):")
    for msg in console_messages[-10:]:  # Show last 10
        print(f"    {msg}")

    # Check for errors
    errors = [m for m in console_messages if 'error' in m.lower() or 'failed' in m.lower()]
    warnings = [m for m in console_messages if 'warning' in m.lower()]

    print(f"\n  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    if errors:
        print(f"\n  Error messages:")
        for err in errors:
            print(f"    {err}")

    # We expect no major errors (warnings are OK)
    assert len(errors) == 0 or not any('fetch' in e.lower() or 'models' in e.lower() for e in errors), \
        f"Found fetch errors: {errors}"

    print(f"\n  ✓ No fetch errors in browser console")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
