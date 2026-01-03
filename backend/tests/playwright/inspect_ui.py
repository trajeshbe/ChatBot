#!/usr/bin/env python3
"""
UI Inspection Script - Identify actual module selectors in the frontend
"""
from playwright.sync_api import sync_playwright
import time

def inspect_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("=" * 80)
        print("UI INSPECTION - Module Selector Analysis")
        print("=" * 80)
        print()

        # Navigate to frontend
        print("[1] Navigating to http://frontend:3000...")
        page.goto('http://frontend:3000', wait_until='networkidle', timeout=60000)
        time.sleep(5)  # Extra buffer for React hydration

        # Take screenshot
        screenshot_path = '/app/tests/playwright/test_results/ui_inspection.png'
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"✓ Screenshot saved: {screenshot_path}")
        print()

        # Get page HTML
        print("[2] Capturing page HTML structure...")
        html_content = page.content()
        with open('/app/tests/playwright/test_results/ui_structure.html', 'w') as f:
            f.write(html_content)
        print(f"✓ HTML saved: /app/tests/playwright/test_results/ui_structure.html")
        print()

        # Get visible text
        print("[3] Extracting visible text from page...")
        body_text = page.inner_text('body')
        print("First 2000 characters of visible text:")
        print("-" * 80)
        print(body_text[:2000])
        print("-" * 80)
        print()

        # Try to find module-related elements
        print("[4] Searching for module elements...")

        # Search for common module selector patterns
        selectors_to_try = [
            'div[data-testid*="module"]',
            'div[class*="module"]',
            'div[class*="Module"]',
            'button[class*="module"]',
            '[data-module-id]',
            'h1, h2, h3, h4',
            '.card',
            '[role="button"]',
        ]

        for selector in selectors_to_try:
            try:
                elements = page.locator(selector).all()
                if elements:
                    print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
                    # Print first 3 elements' text content
                    for i, elem in enumerate(elements[:3]):
                        text = elem.inner_text()
                        if text.strip():
                            print(f"   [{i+1}] {text[:100]}")
            except Exception as e:
                continue

        print()
        print("[5] Searching for specific module keywords...")
        keywords = [
            "talent", "search", "taxonomy", "skill",
            "planning", "classifier", "procurement", "matcher",
            "module", "vertical", "domain"
        ]

        for keyword in keywords:
            try:
                # Case insensitive search
                elements = page.locator(f"text=/{keyword}/i").all()
                if elements:
                    print(f"\n✓ Found '{keyword}' in {len(elements)} elements")
                    for i, elem in enumerate(elements[:2]):
                        text = elem.inner_text()
                        if text.strip():
                            print(f"   [{i+1}] {text[:150]}")
            except Exception as e:
                continue

        print()
        print("[6] Attempting to locate module list/grid...")

        # Try to find a container with multiple modules
        potential_containers = page.locator('div[class*="grid"], div[class*="Grid"], div[class*="list"]').all()
        print(f"Found {len(potential_containers)} potential grid/list containers")

        for i, container in enumerate(potential_containers[:3]):
            try:
                text = container.inner_text()
                if len(text) > 100:  # Likely contains multiple modules
                    print(f"\nContainer {i+1} content (first 500 chars):")
                    print("-" * 80)
                    print(text[:500])
                    print("-" * 80)
            except:
                continue

        print()
        print("=" * 80)
        print("UI INSPECTION COMPLETE")
        print("=" * 80)

        browser.close()

if __name__ == "__main__":
    inspect_ui()
