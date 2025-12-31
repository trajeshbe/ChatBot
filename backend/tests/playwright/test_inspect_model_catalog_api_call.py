"""Inspect what the ModelCatalog component actually receives from the API."""
import pytest
from playwright.sync_api import Page, Browser
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
    return response.json()


@pytest.fixture
def authenticated_page(browser: Browser) -> Page:
    """Create page with authentication token set."""
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    auth_data = get_auth_token()
    access_token = auth_data["access_token"]
    user_data = auth_data["user"]

    page.goto(BASE_URL)
    time.sleep(1)

    page.evaluate(f"""() => {{
        localStorage.setItem('access_token', '{access_token}');
        localStorage.setItem('user', '{json.dumps(user_data)}');
    }}""")

    yield page
    page.close()


def test_inspect_api_responses(authenticated_page: Page):
    """Intercept and log all API responses to see what the frontend receives."""
    print("\n=== Inspecting API Responses ===")

    api_responses = []

    def handle_response(response):
        """Log all responses to finetuning endpoints."""
        if 'fine' in response.url.lower() or 'base-models' in response.url:
            try:
                response_data = {
                    'url': response.url,
                    'status': response.status,
                    'ok': response.ok,
                    'body': None
                }

                # Try to get response body
                try:
                    body = response.json()
                    response_data['body'] = body
                    if 'models' in body:
                        response_data['models_count'] = len(body.get('models', []))
                except Exception as e:
                    response_data['body_error'] = str(e)

                api_responses.append(response_data)
                print(f"\n  API Response:")
                print(f"    URL: {response_data['url']}")
                print(f"    Status: {response_data['status']}")
                print(f"    OK: {response_data['ok']}")
                if 'models_count' in response_data:
                    print(f"    Models Count: {response_data['models_count']}")
                if response_data['body']:
                    print(f"    Body (truncated): {json.dumps(response_data['body'])[:200]}...")
                if 'body_error' in response_data:
                    print(f"    Body Error: {response_data['body_error']}")

            except Exception as e:
                print(f"\n  Error handling response: {e}")

    # Attach response listener
    authenticated_page.on("response", handle_response)

    # Navigate to fine-tuning page
    authenticated_page.goto(f"{BASE_URL}/admin")
    time.sleep(2)

    print(f"\n  Navigated to admin page")

    # Click Fine-Tuning
    authenticated_page.get_by_text("Fine-Tuning", exact=False).click()
    time.sleep(2)

    print(f"\n  Clicked Fine-Tuning tab")

    # Click Models section
    authenticated_page.get_by_text("Models", exact=True).first.click()
    time.sleep(5)  # Give plenty of time for API call

    print(f"\n  Clicked Models section, waiting for API calls...")

    # Check page content
    page_content = authenticated_page.content()
    print(f"\n  Checking page content...")
    print(f"    Contains 'All Families': {'All Families' in page_content}")
    print(f"    Contains '0 models': {'0 models' in page_content}")
    print(f"    Contains '7 models': {'7 models' in page_content}")

    # Summary
    print(f"\n  Total API responses captured: {len(api_responses)}")
    for i, resp in enumerate(api_responses):
        print(f"\n  Response {i+1}:")
        print(f"    URL: {resp['url']}")
        print(f"    Status: {resp['status']}")
        if 'models_count' in resp:
            print(f"    Models: {resp['models_count']}")

    # Assert we got a response
    assert len(api_responses) > 0, "No API responses captured!"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
