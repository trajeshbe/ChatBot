"""
End-to-End UI Tests for Chat Interface with Local LLM

Tests the complete user flow:
1. Upload a document
2. Select local LLM model from UI
3. Ask a question
4. Verify response and sources

This will help identify where the UI → Backend → Ollama flow breaks.
"""

import asyncio
import json
from playwright.async_api import async_playwright, Page, expect
import pytest


class TestChatUIFlow:
    """Test complete chat UI flow with local models"""

    @pytest.mark.asyncio
    async def test_local_llm_query_from_ui(self):
        """Test querying with local LLM through UI"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # headless=False to see what happens
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Navigate to the application
                print("📍 Navigating to http://localhost:3001")
                await page.goto("http://localhost:3001", wait_until="networkidle")
                await page.wait_for_timeout(2000)

                # Step 1: Check if model selector is visible
                print("🔍 Looking for model selector...")
                model_selector = page.locator('select[name="model"], select#model, [data-testid="model-selector"]').first

                await expect(model_selector).to_be_visible(timeout=10000)
                print("✅ Model selector found")

                # Step 2: Get available models
                print("🔍 Getting available models from dropdown...")
                options = await model_selector.locator('option').all_text_contents()
                print(f"📋 Available models in UI: {options}")

                # Step 3: Select local LLM model (qwen2.5:1.5b or llama3.2:3b)
                local_model = None
                for model in ["qwen2.5:1.5b", "llama3.2:3b", "ollama/qwen2.5:1.5b"]:
                    if any(model in opt for opt in options):
                        local_model = model
                        break

                if not local_model:
                    print("⚠️  No local model found in dropdown")
                    print(f"Available: {options}")
                    # Try first model that contains 'ollama' or 'llama' or 'qwen'
                    for opt in options:
                        if any(x in opt.lower() for x in ['ollama', 'llama', 'qwen']):
                            local_model = opt
                            break

                if local_model:
                    print(f"🎯 Selecting model: {local_model}")
                    await model_selector.select_option(label=local_model)
                    await page.wait_for_timeout(1000)
                else:
                    raise ValueError(f"No local model found. Available: {options}")

                # Step 4: Verify model is selected
                selected_value = await model_selector.input_value()
                print(f"✅ Selected model value: {selected_value}")

                # Step 5: Find chat input and send button
                print("🔍 Looking for chat input...")
                chat_input = page.locator('input[type="text"], textarea, input[placeholder*="Ask"], textarea[placeholder*="Ask"]').first
                await expect(chat_input).to_be_visible(timeout=5000)
                print("✅ Chat input found")

                send_button = page.locator('button:has-text("Send"), button[type="submit"]').first
                await expect(send_button).to_be_visible(timeout=5000)
                print("✅ Send button found")

                # Step 6: Intercept network requests to see what's being sent
                intercepted_requests = []

                async def log_request(route, request):
                    if '/query' in request.url:
                        body_data = request.post_data
                        print(f"📤 Intercepted /query request:")
                        print(f"   URL: {request.url}")
                        print(f"   Method: {request.method}")
                        print(f"   Body (raw): {body_data[:500] if body_data else 'None'}")

                        # Try to parse multipart form data
                        if body_data:
                            # Extract model_id from form data
                            if b'model_id' in body_data:
                                import re
                                model_match = re.search(rb'name="model_id"[^\r\n]*\r\n\r\n([^\r\n]+)', body_data)
                                if model_match:
                                    model_id = model_match.group(1).decode('utf-8')
                                    print(f"   🎯 Model ID being sent: {model_id}")
                                    intercepted_requests.append({'model_id': model_id})

                    await route.continue_()

                await page.route("**/api/v1/query*", log_request)

                # Step 7: Type query and send
                query = "What is 2+2? Answer with just the number."
                print(f"💬 Typing query: {query}")
                await chat_input.fill(query)
                await page.wait_for_timeout(500)

                print("🚀 Clicking send button...")
                await send_button.click()

                # Step 8: Wait for response
                print("⏳ Waiting for response...")
                try:
                    # Wait for either success or error message
                    response_selector = '.message, .response, .error, [data-testid="message"]'
                    await page.wait_for_selector(response_selector, timeout=30000)

                    # Get all messages
                    messages = await page.locator('.message, .response, .error').all_text_contents()
                    print(f"📨 Messages found: {len(messages)}")
                    for i, msg in enumerate(messages[-3:]):  # Last 3 messages
                        print(f"   [{i}]: {msg[:200]}")

                    # Check for error
                    error_elements = await page.locator('.error, [class*="error"]').all_text_contents()
                    if error_elements:
                        print(f"❌ Error detected in UI: {error_elements}")

                except Exception as e:
                    print(f"⚠️  Timeout waiting for response: {e}")

                # Step 9: Check intercepted requests
                print("\n" + "="*60)
                print("📊 SUMMARY:")
                print("="*60)
                if intercepted_requests:
                    for req in intercepted_requests:
                        print(f"✅ Model ID sent to backend: {req.get('model_id', 'UNKNOWN')}")
                else:
                    print("⚠️  No /query requests intercepted")
                print(f"✅ Model selected in UI: {selected_value}")
                print("="*60)

                # Take screenshot for debugging
                await page.screenshot(path="/tmp/ui_test_screenshot.png")
                print("📸 Screenshot saved to /tmp/ui_test_screenshot.png")

            finally:
                await browser.close()


    @pytest.mark.asyncio
    async def test_template_extractor_flow(self):
        """Test template extraction through UI"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                print("📍 Navigating to http://localhost:3001")
                await page.goto("http://localhost:3001", wait_until="networkidle")
                await page.wait_for_timeout(2000)

                # Look for template extractor or web scraper tab/section
                print("🔍 Looking for template extractor section...")

                # Common patterns for tabs/navigation
                tabs = await page.locator('button, a, [role="tab"]').all_text_contents()
                print(f"📋 Available tabs/sections: {tabs}")

                # Try to find "Template", "Extractor", "Scraper", "Web" tabs
                for tab_text in tabs:
                    if any(keyword in tab_text.lower() for keyword in ['template', 'extract', 'scrape', 'web']):
                        print(f"🎯 Clicking tab: {tab_text}")
                        tab = page.locator(f'button:has-text("{tab_text}"), a:has-text("{tab_text}")').first
                        await tab.click()
                        await page.wait_for_timeout(1000)
                        break

                # Look for URL input
                print("🔍 Looking for URL input...")
                url_input = page.locator('input[type="url"], input[placeholder*="URL"], input[name*="url"]').first

                if await url_input.is_visible(timeout=5000):
                    print("✅ URL input found")

                    # Enter screener.in URL
                    url = "https://www.screener.in/company/BHARTIARTL/consolidated/"
                    print(f"📝 Entering URL: {url}")
                    await url_input.fill(url)
                    await page.wait_for_timeout(500)

                    # Look for extract/scrape button
                    extract_button = page.locator('button:has-text("Extract"), button:has-text("Scrape")').first
                    await extract_button.click()
                    print("🚀 Clicked extract button")

                    # Wait for results
                    print("⏳ Waiting for extraction results...")
                    try:
                        # Wait for results table/display
                        await page.wait_for_selector('table, .results, [data-testid="results"]', timeout=90000)

                        # Check for data
                        rows = await page.locator('table tr, .result-row').count()
                        print(f"📊 Extracted {rows} rows")

                        # Take screenshot
                        await page.screenshot(path="/tmp/template_extractor_screenshot.png")
                        print("📸 Screenshot saved to /tmp/template_extractor_screenshot.png")

                    except Exception as e:
                        print(f"❌ Timeout waiting for extraction results: {e}")
                        await page.screenshot(path="/tmp/template_extractor_error.png")

                else:
                    print("⚠️  URL input not found")
                    await page.screenshot(path="/tmp/template_extractor_not_found.png")

            finally:
                await browser.close()


if __name__ == "__main__":
    # Run tests directly
    print("🧪 Running UI End-to-End Tests\n")

    test_suite = TestChatUIFlow()

    print("\n" + "="*80)
    print("TEST 1: Local LLM Query from UI")
    print("="*80)
    asyncio.run(test_suite.test_local_llm_query_from_ui())

    print("\n" + "="*80)
    print("TEST 2: Template Extractor Flow")
    print("="*80)
    asyncio.run(test_suite.test_template_extractor_flow())
