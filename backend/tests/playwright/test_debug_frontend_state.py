"""Debug frontend state to see what data it has."""
import pytest
from playwright.sync_api import Page, Browser
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


def test_debug_frontend_models_state(authenticated_page: Page):
    """Debug what models state the frontend has."""
    print("\n=== Debugging Frontend Models State ===")

    # Navigate to admin
    authenticated_page.goto(f"{BASE_URL}/admin")
    time.sleep(2)

    # Click Fine-Tuning tab
    authenticated_page.get_by_text("Fine-Tuning", exact=False).click()
    time.sleep(2)

    # Click Models section
    authenticated_page.get_by_text("Models", exact=True).first.click()
    time.sleep(5)  # Give it plenty of time to fetch

    # Inject script to access React state
    state_info = authenticated_page.evaluate("""() => {
        // Try to access window for debugging
        const debug = {
            localStorage: {
                access_token: localStorage.getItem('access_token') ? 'EXISTS' : 'MISSING',
                user: localStorage.getItem('user') ? 'EXISTS' : 'MISSING'
            },
            pageContent: {
                hasModelsText: document.body.textContent.includes('models'),
                hasQwenText: document.body.textContent.toLowerCase().includes('qwen'),
                hasLoRAText: document.body.textContent.toLowerCase().includes('lora')
            }
        };

        return debug;
    }""")

    print(f"\n  Frontend State:")
    print(json.dumps(state_info, indent=4))

    # Try to manually call the fetch and see the response
    fetch_result = authenticated_page.evaluate("""async () => {
        const token = localStorage.getItem('access_token');
        const url = 'http://localhost:8000/api/v1/finetuning/base-models';

        try {
            const response = await fetch(url, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            const data = await response.json();

            return {
                status: response.status,
                ok: response.ok,
                modelsCount: data.models ? data.models.length : 0,
                firstModel: data.models && data.models[0] ? {
                    id: data.models[0].id,
                    name: data.models[0].name,
                    family: data.models[0].family
                } : null,
                hasModels: !!data.models,
                error: null
            };
        } catch (error) {
            return {
                status: 'ERROR',
                error: error.toString()
            };
        }
    }""")

    print(f"\n  Frontend Fetch Result:")
    print(json.dumps(fetch_result, indent=4))

    # Get all network requests
    network_requests = []

    def log_request(request):
        if 'finetuning' in request.url or 'base-models' in request.url:
            network_requests.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers)
            })

    def log_response(response):
        if 'finetuning' in response.url or 'base-models' in response.url:
            print(f"\n  Response for {response.url}:")
            print(f"    Status: {response.status}")
            print(f"    OK: {response.ok}")

    authenticated_page.on("request", log_request)
    authenticated_page.on("response", log_response)

    # Reload to capture network requests
    print(f"\n  Reloading page to capture network...")
    authenticated_page.reload()
    time.sleep(5)

    print(f"\n  Network requests to finetuning endpoints:")
    for req in network_requests:
        print(f"    {req['method']} {req['url']}")
        auth_header = req['headers'].get('authorization', 'NO AUTH')
        print(f"      Auth: {auth_header[:50] if len(auth_header) > 10 else auth_header}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
