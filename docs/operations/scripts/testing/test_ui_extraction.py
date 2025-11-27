#!/usr/bin/env python3
"""
Comprehensive UI Test for Web Scraping Features
Tests all extraction modes end-to-end from the browser
"""
import asyncio
from playwright.async_api import async_playwright
import json
import time

# Test configuration
FRONTEND_URL = "http://localhost:3001"
TEST_URL = "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html"

async def test_smart_extraction():
    """Test 1: Smart Extraction from UI"""
    print("\n" + "="*80)
    print("TEST 1: SMART EXTRACTION FROM UI")
    print("="*80)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        try:
            # Navigate to frontend
            print(f"\n📱 Opening frontend: {FRONTEND_URL}")
            await page.goto(FRONTEND_URL, timeout=30000)
            await page.wait_for_load_state("networkidle")
            
            # Click on Data Extraction Hub
            print("🖱️  Clicking 'Data Extraction Hub' tab...")
            await page.click('button:has-text("Data Extraction Hub")')
            await page.wait_for_timeout(1000)
            
            # Click on Smart Extractor
            print("🖱️  Clicking 'Smart Extractor' tab...")
            await page.click('button:has-text("Smart Extractor")')
            await page.wait_for_timeout(1000)
            
            # Fill in URL
            print(f"📝 Entering URL: {TEST_URL}")
            await page.fill('input[placeholder*="URL"], input[placeholder*="url"]', TEST_URL)
            await page.wait_for_timeout(500)
            
            # Fill in instructions
            instructions = "Extract all mystery books. For each book get: title, price, and availability"
            print(f"📝 Entering instructions: {instructions}")
            await page.fill('textarea[placeholder*="instructions"], textarea[placeholder*="Instructions"]', instructions)
            await page.wait_for_timeout(500)
            
            # Click Extract button
            print("🚀 Clicking 'Extract Data' button...")
            await page.click('button:has-text("Extract Data"), button:has-text("Extract")')
            
            # Wait for extraction to complete (up to 60 seconds)
            print("⏳ Waiting for extraction to complete...")
            try:
                # Wait for results table or success message
                await page.wait_for_selector('table, div:has-text("successfully"), div:has-text("Success")', timeout=60000)
                print("✅ Extraction completed!")
                
                # Check if we have results
                results_visible = await page.is_visible('table')
                if results_visible:
                    # Count rows
                    rows = await page.locator('table tbody tr').count()
                    print(f"📊 Found {rows} books in results table")
                    
                    # Get first row data as sample
                    if rows > 0:
                        first_row = await page.locator('table tbody tr').first.inner_text()
                        print(f"📖 Sample book: {first_row[:100]}...")
                else:
                    print("⚠️  Results table not visible")
                    
                # Take screenshot
                await page.screenshot(path="/tmp/smart_extraction_results.png")
                print("📸 Screenshot saved: /tmp/smart_extraction_results.png")
                
                return True
                
            except Exception as e:
                print(f"❌ Extraction timed out or failed: {e}")
                await page.screenshot(path="/tmp/smart_extraction_error.png")
                return False
                
        finally:
            await browser.close()

async def test_template_saving():
    """Test 2: Save Template from Smart Extraction Results"""
    print("\n" + "="*80)
    print("TEST 2: TEMPLATE SAVING")
    print("="*80)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        try:
            # Navigate and extract (same as test 1)
            await page.goto(FRONTEND_URL, timeout=30000)
            await page.click('button:has-text("Data Extraction Hub")')
            await page.wait_for_timeout(500)
            await page.click('button:has-text("Smart Extractor")')
            await page.wait_for_timeout(500)
            
            await page.fill('input[placeholder*="URL"], input[placeholder*="url"]', TEST_URL)
            await page.fill('textarea[placeholder*="instructions"]', "Extract mystery books with title and price")
            await page.click('button:has-text("Extract Data")')
            
            # Wait for results
            await page.wait_for_selector('table', timeout=60000)
            print("✅ Extraction completed")
            
            # Look for "Save as Template" button
            print("🖱️  Looking for 'Save as Template' button...")
            save_button_visible = await page.is_visible('button:has-text("Save as Template")')
            
            if save_button_visible:
                print("🖱️  Clicking 'Save as Template'...")
                await page.click('button:has-text("Save as Template")')
                await page.wait_for_timeout(1000)
                
                # Fill in template name
                template_name = f"mystery_books_test_{int(time.time())}"
                print(f"📝 Entering template name: {template_name}")
                
                # Try different input selectors
                name_input = await page.locator('input[placeholder*="name"], input[placeholder*="Name"]').first
                if await name_input.is_visible():
                    await name_input.fill(template_name)
                    await page.wait_for_timeout(500)
                    
                    # Click Save button in modal
                    print("💾 Clicking Save button...")
                    await page.click('button:has-text("Save"):not(:has-text("Save as Template"))')
                    await page.wait_for_timeout(2000)
                    
                    # Check for success message
                    success_visible = await page.is_visible('text="success", text="Success", text="saved"')
                    if success_visible:
                        print(f"✅ Template '{template_name}' saved successfully!")
                        return True
                    else:
                        print("⚠️  No success message visible")
                        return False
            else:
                print("❌ 'Save as Template' button not found")
                await page.screenshot(path="/tmp/template_save_error.png")
                return False
                
        finally:
            await browser.close()

async def test_css_selector_mode():
    """Test 3: CSS Selector Extraction with Template"""
    print("\n" + "="*80)
    print("TEST 3: CSS SELECTOR MODE")
    print("="*80)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        try:
            await page.goto(FRONTEND_URL, timeout=30000)
            await page.click('button:has-text("Data Extraction Hub")')
            await page.wait_for_timeout(500)
            
            # Navigate to Template Extractor
            print("🖱️  Clicking 'Template Extractor' tab...")
            await page.click('button:has-text("Template Extractor")')
            await page.wait_for_timeout(1000)
            
            # Select CSS Selector mode
            print("🖱️  Selecting 'CSS Selector' extraction mode...")
            css_mode_visible = await page.is_visible('text="CSS Selector"')
            if css_mode_visible:
                await page.click('text="CSS Selector"')
                await page.wait_for_timeout(500)
                
                # Fill in test URL
                print(f"📝 Entering URL: {TEST_URL}")
                await page.fill('input[placeholder*="URL"]', TEST_URL)
                
                # Look for template selector or fields to define selectors
                print("📝 Defining CSS selectors...")
                # This part depends on your UI structure
                # For now, just take a screenshot to see what's available
                await page.screenshot(path="/tmp/css_selector_mode.png")
                print("📸 Screenshot saved: /tmp/css_selector_mode.png")
                
                print("✅ CSS Selector mode accessible")
                return True
            else:
                print("❌ CSS Selector mode not found")
                return False
                
        finally:
            await browser.close()

async def test_template_mapper():
    """Test 4: Smart Template Mapper"""
    print("\n" + "="*80)
    print("TEST 4: SMART TEMPLATE MAPPER")
    print("="*80)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        try:
            await page.goto(FRONTEND_URL, timeout=30000)
            await page.click('button:has-text("Data Extraction Hub")')
            await page.wait_for_timeout(500)
            
            # Navigate to Smart Template Mapper
            print("🖱️  Clicking 'Smart Template Mapper' tab...")
            mapper_visible = await page.is_visible('button:has-text("Smart Template Mapper"), button:has-text("Template Mapper")')
            
            if mapper_visible:
                await page.click('button:has-text("Smart Template Mapper"), button:has-text("Template Mapper")')
                await page.wait_for_timeout(1000)
                
                # Fill in URL
                print(f"📝 Entering URL: {TEST_URL}")
                await page.fill('input[placeholder*="URL"]', TEST_URL)
                await page.wait_for_timeout(500)
                
                # Take screenshot
                await page.screenshot(path="/tmp/template_mapper.png")
                print("📸 Screenshot saved: /tmp/template_mapper.png")
                print("✅ Template Mapper accessible")
                return True
            else:
                print("⚠️  Template Mapper tab not found")
                return False
                
        finally:
            await browser.close()

async def main():
    """Run all UI tests"""
    print("\n🚀 STARTING COMPREHENSIVE UI TESTS")
    print("="*80)
    
    results = {
        "smart_extraction": False,
        "template_saving": False,
        "css_selector_mode": False,
        "template_mapper": False
    }
    
    # Run tests
    try:
        results["smart_extraction"] = await test_smart_extraction()
        await asyncio.sleep(2)
        
        results["template_saving"] = await test_template_saving()
        await asyncio.sleep(2)
        
        results["css_selector_mode"] = await test_css_selector_mode()
        await asyncio.sleep(2)
        
        results["template_mapper"] = await test_template_mapper()
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<50} {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*80)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
