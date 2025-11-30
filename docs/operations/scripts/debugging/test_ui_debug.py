#!/usr/bin/env python3
"""
Standalone UI Test Script - No pytest required

This script will:
1. Open the UI in a browser
2. Select a local LLM model
3. Send a query
4. Capture what model_id is being sent to the backend
5. Show screenshots of the UI state

Run with: python3 test_ui_debug.py
"""

import asyncio
import sys
import re
from playwright.async_api import async_playwright


async def test_local_llm_from_ui():
    """Test the complete UI → Backend → Ollama flow"""

    print("="*80)
    print("🧪 UI DEBUGGING TEST - Local LLM Query Flow")
    print("="*80)

    async with async_playwright() as p:
        # Launch browser (headless=False to see what happens)
        print("\n📂 Launching Chromium browser...")
        browser = await p.chromium.launch(
            headless=False,  # Set to True if you don't want to see the browser
            slow_mo=500  # Slow down actions to see what's happening
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        # Track intercepted network requests
        intercepted_data = []

        async def intercept_query_request(route, request):
            """Intercept /query API calls to see what's being sent"""
            if '/api/v1/query' in request.url:
                body_data = request.post_data
                print(f"\n📤 INTERCEPTED /query REQUEST")
                print(f"   URL: {request.url}")
                print(f"   Method: {request.method}")

                # Parse multipart form data to extract model_id
                if body_data:
                    # Extract model_id from form data
                    if b'model_id' in body_data:
                        model_match = re.search(rb'name="model_id"[^\r\n]*\r\n\r\n([^\r\n]+)', body_data)
                        if model_match:
                            model_id = model_match.group(1).decode('utf-8')
                            print(f"   🎯 Model ID extracted: '{model_id}'")
                            intercepted_data.append({'model_id': model_id, 'url': request.url})

                    # Extract query text
                    query_match = re.search(rb'name="query"[^\r\n]*\r\n\r\n([^\r\n]+)', body_data)
                    if query_match:
                        query_text = query_match.group(1).decode('utf-8')
                        print(f"   💬 Query text: '{query_text}'")

            await route.continue_()

        # Setup request interception
        await page.route("**/api/v1/query*", intercept_query_request)

        try:
            # Step 1: Navigate to the application
            print("\n📍 Step 1: Navigating to http://localhost:3001")
            await page.goto("http://localhost:3001", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            print("   ✅ Page loaded")

            # Take screenshot
            await page.screenshot(path="/tmp/ui_step1_loaded.png")
            print("   📸 Screenshot: /tmp/ui_step1_loaded.png")

            # Step 2: Find and inspect model selector
            print("\n🔍 Step 2: Looking for model selector...")

            # Try multiple selectors
            selectors = [
                'select[name="model"]',
                'select#model',
                'select[id*="model"]',
                '[data-testid="model-selector"]',
                'select'  # Last resort - any select
            ]

            model_selector = None
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=2000):
                        model_selector = element
                        print(f"   ✅ Found model selector: {selector}")
                        break
                except:
                    continue

            if not model_selector:
                print("   ❌ Model selector not found!")
                await page.screenshot(path="/tmp/ui_error_no_selector.png")
                return

            # Get all available options
            options = await model_selector.locator('option').all_text_contents()
            print(f"\n📋 Available models in dropdown:")
            for i, opt in enumerate(options):
                print(f"   [{i}] {opt}")

            # Step 3: Select a local model
            print("\n🎯 Step 3: Selecting local LLM model...")

            # Priority order for local models
            local_model_patterns = [
                "qwen2.5:1.5b",
                "llama3.2:3b",
                "ollama",
                "qwen",
                "llama"
            ]

            selected_model = None
            for pattern in local_model_patterns:
                for opt in options:
                    if pattern.lower() in opt.lower():
                        selected_model = opt
                        print(f"   🎯 Selecting: {selected_model}")
                        await model_selector.select_option(label=selected_model)
                        await page.wait_for_timeout(1000)
                        break
                if selected_model:
                    break

            if not selected_model:
                print(f"   ⚠️  No local model found. Using first option: {options[0]}")
                await model_selector.select_option(index=0)
                selected_model = options[0]

            # Verify selection
            selected_value = await model_selector.input_value()
            print(f"   ✅ Selected value (HTML): {selected_value}")

            await page.screenshot(path="/tmp/ui_step3_model_selected.png")
            print("   📸 Screenshot: /tmp/ui_step3_model_selected.png")

            # Step 4: Find chat input and button
            print("\n💬 Step 4: Looking for chat input...")

            # Try multiple input selectors
            input_selectors = [
                'input[type="text"]',
                'textarea',
                'input[placeholder*="Ask"]',
                'textarea[placeholder*="Ask"]',
                'input[placeholder*="question"]',
                'textarea[placeholder*="question"]'
            ]

            chat_input = None
            for selector in input_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=2000):
                        chat_input = element
                        print(f"   ✅ Found chat input: {selector}")
                        break
                except:
                    continue

            if not chat_input:
                print("   ❌ Chat input not found!")
                await page.screenshot(path="/tmp/ui_error_no_input.png")
                return

            # Find send button
            button_selectors = [
                'button:has-text("Send")',
                'button[type="submit"]',
                'button:has-text("Ask")',
                'button:has-text("Query")'
            ]

            send_button = None
            for selector in button_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=2000):
                        send_button = element
                        print(f"   ✅ Found send button: {selector}")
                        break
                except:
                    continue

            if not send_button:
                print("   ❌ Send button not found!")
                await page.screenshot(path="/tmp/ui_error_no_button.png")
                return

            # Step 5: Type query and send
            query_text = "What is 2+2? Answer with just the number."
            print(f"\n🚀 Step 5: Sending query...")
            print(f"   Query: {query_text}")

            await chat_input.fill(query_text)
            await page.wait_for_timeout(500)

            await page.screenshot(path="/tmp/ui_step5_ready_to_send.png")
            print("   📸 Screenshot: /tmp/ui_step5_ready_to_send.png")

            print("   🔴 Clicking Send button...")
            await send_button.click()

            # Step 6: Wait for response
            print("\n⏳ Step 6: Waiting for response...")

            # Wait for new messages to appear
            await page.wait_for_timeout(5000)  # Wait 5 seconds for response

            await page.screenshot(path="/tmp/ui_step6_after_send.png")
            print("   📸 Screenshot: /tmp/ui_step6_after_send.png")

            # Look for response messages
            message_selectors = [
                '.message',
                '.response',
                '[class*="message"]',
                '[class*="response"]',
                '[data-testid="message"]'
            ]

            for selector in message_selectors:
                try:
                    messages = await page.locator(selector).all_text_contents()
                    if messages:
                        print(f"\n📨 Messages found ({selector}):")
                        for i, msg in enumerate(messages[-5:]):  # Last 5 messages
                            print(f"   [{i}] {msg[:200]}")
                        break
                except:
                    continue

            # Check for errors
            error_selectors = [
                '.error',
                '[class*="error"]',
                '[class*="Error"]'
            ]

            for selector in error_selectors:
                try:
                    errors = await page.locator(selector).all_text_contents()
                    if errors:
                        print(f"\n❌ Errors found ({selector}):")
                        for err in errors:
                            print(f"   {err}")
                except:
                    continue

            # Final screenshot
            await page.screenshot(path="/tmp/ui_final_state.png")
            print("\n📸 Final screenshot: /tmp/ui_final_state.png")

            # Print summary
            print("\n" + "="*80)
            print("📊 TEST SUMMARY")
            print("="*80)
            print(f"✅ Model selected in UI: {selected_model}")
            print(f"✅ Model value (HTML): {selected_value}")

            if intercepted_data:
                print("\n📤 Network requests intercepted:")
                for req in intercepted_data:
                    print(f"   🎯 Model ID sent to backend: '{req['model_id']}'")
                    print(f"   🔗 URL: {req['url']}")

                # Compare UI selection vs actual request
                print("\n🔍 VERIFICATION:")
                backend_model = intercepted_data[0]['model_id'] if intercepted_data else "NONE"
                if selected_value == backend_model or selected_model == backend_model:
                    print(f"   ✅ MATCH: UI and backend are using the same model")
                else:
                    print(f"   ❌ MISMATCH:")
                    print(f"      UI selected: '{selected_value}' / '{selected_model}'")
                    print(f"      Backend got: '{backend_model}'")
                    print(f"   🔧 This is the bug - UI not passing correct model to backend!")
            else:
                print("\n⚠️  No /query requests intercepted")
                print("   Possible reasons:")
                print("   1. Request failed before reaching backend")
                print("   2. Different endpoint being used")
                print("   3. Request blocked by CORS or other error")

            print("="*80)

            # Keep browser open for 5 seconds to see final state
            print("\n⏸️  Keeping browser open for 5 seconds...")
            await page.wait_for_timeout(5000)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path="/tmp/ui_error_exception.png")

        finally:
            await browser.close()
            print("\n✅ Browser closed")


if __name__ == "__main__":
    print("\n🚀 Starting UI Debug Test...")
    print("This will open a browser and test the local LLM query flow.\n")

    try:
        asyncio.run(test_local_llm_from_ui())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n✅ Test completed")
