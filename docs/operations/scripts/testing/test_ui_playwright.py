#!/usr/bin/env python3
"""
Playwright UI Test: Project Estimator with Meta-Validation
Runs from host to test the UI at localhost:3001
"""
import sys
import time

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("❌ Playwright not installed on host")
    print("Installing playwright...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

print("=" * 80)
print("🎭 PLAYWRIGHT UI TEST: Project Estimator Meta-Validation")
print("=" * 80)
print()

def test_project_estimator():
    with sync_playwright() as p:
        print("🌐 Launching Chromium browser...")
        browser = p.chromium.launch(
            headless=False,  # Show browser for debugging
            slow_mo=1000      # Slow down by 1 second per action
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            # Navigate to app
            print("📍 Navigating to http://localhost:3001...")
            page.goto("http://localhost:3001", timeout=30000)
            page.wait_for_load_state("networkidle")
            print("✅ Page loaded")
            print()
            
            # Take screenshot of initial page
            page.screenshot(path="/tmp/screenshot_1_homepage.png")
            print("📸 Screenshot saved: screenshot_1_homepage.png")
            
            # Click Project Estimator in sidebar
            print("🖱️  Clicking 'Project Estimator' in sidebar...")
            try:
                # Try multiple selectors
                project_estimator_btn = page.locator('text="Project Estimator"').first
                if project_estimator_btn.is_visible():
                    project_estimator_btn.click()
                    print("✅ Clicked Project Estimator button")
                else:
                    print("⚠️  Button not visible, trying alternative selector...")
                    page.locator('button:has-text("Project Estimator")').click()
            except Exception as e:
                print(f"⚠️  Error clicking: {e}")
                print("Trying to find by Calculator icon...")
                page.locator('svg.lucide-calculator').click()
            
            page.wait_for_timeout(2000)
            page.screenshot(path="/tmp/screenshot_2_project_estimator.png")
            print("📸 Screenshot saved: screenshot_2_project_estimator.png")
            print()
            
            # Fill in project scope
            test_scope = """Build a web dashboard to visualize our company's internal sales data from PostgreSQL.

Key Features:
- Display sales data in interactive charts (bar, line, pie charts)
- Filter by date range, product category, and sales rep
- Show summary statistics (total sales, top products, trends)
- Export reports to Excel
- User authentication and role-based access (Admin, Manager, Viewer)

Technical Requirements:
- Backend: RESTful API to query PostgreSQL database
- Frontend: Responsive web application with modern UI
- Database: Already exists with sales data (products, orders, customers)
- Scale: 5000 customers, ~15K transactions/month
- Users: ~50 concurrent users expected

The data is already in our PostgreSQL database. We need a responsive web application that non-technical users can easily navigate."""
            
            print("📝 Looking for project scope textarea...")
            # Find textarea (look for placeholder or label)
            textarea = page.locator('textarea').first
            if textarea.is_visible():
                print("✅ Found textarea")
                textarea.fill(test_scope)
                print("✅ Filled project scope")
            else:
                print("❌ Textarea not found")
                page.screenshot(path="/tmp/screenshot_error_no_textarea.png")
                return False
            
            page.wait_for_timeout(1000)
            print()
            
            # Select project type: Full Service
            print("⚙️  Selecting project type...")
            try:
                select = page.locator('select').first
                if select.is_visible():
                    select.select_option("full_service")
                    print("✅ Selected 'Full Service'")
                else:
                    print("⚠️  Dropdown not found, using default")
            except Exception as e:
                print(f"⚠️  Could not select project type: {e}")
            
            page.wait_for_timeout(1000)
            page.screenshot(path="/tmp/screenshot_3_form_filled.png")
            print("📸 Screenshot saved: screenshot_3_form_filled.png")
            print()
            
            # Submit the form
            print("🚀 Looking for Generate/Submit button...")
            try:
                # Try multiple button selectors
                submit_btn = None
                for selector in [
                    'button:has-text("Generate")',
                    'button:has-text("Submit")',
                    'button:has-text("Estimate")',
                    'button[type="submit"]'
                ]:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible():
                            submit_btn = btn
                            print(f"✅ Found button with selector: {selector}")
                            break
                    except:
                        continue
                
                if submit_btn:
                    submit_btn.click()
                    print("✅ Clicked submit button")
                else:
                    print("❌ Submit button not found")
                    page.screenshot(path="/tmp/screenshot_error_no_button.png")
                    return False
                    
            except Exception as e:
                print(f"❌ Error clicking submit: {e}")
                return False
            
            print()
            print("⏳ Waiting for workflow to complete...")
            print("   (This may take 2-5 minutes - workflow runs 7 agents)")
            print()
            
            page.screenshot(path="/tmp/screenshot_4_submitted.png")
            
            # Wait for completion with periodic screenshots
            start_time = time.time()
            max_wait = 300  # 5 minutes
            
            while time.time() - start_time < max_wait:
                elapsed = int(time.time() - start_time)
                print(f"⏱️  Elapsed: {elapsed}s / {max_wait}s", end='\r')
                
                # Check for download buttons or completion
                try:
                    if (page.locator('text=/Download.*BRD/i').is_visible() or 
                        page.locator('text=/Download.*Excel/i').is_visible() or
                        page.locator('text=/Completed/i').is_visible()):
                        print()
                        print("✅ Workflow completed!")
                        break
                except:
                    pass
                
                # Take periodic screenshots
                if elapsed % 30 == 0 and elapsed > 0:
                    page.screenshot(path=f"/tmp/screenshot_progress_{elapsed}s.png")
                
                time.sleep(2)
            else:
                print()
                print("❌ Timeout waiting for completion")
                page.screenshot(path="/tmp/screenshot_timeout.png")
                return False
            
            print()
            page.screenshot(path="/tmp/screenshot_5_completed.png")
            print("📸 Screenshot saved: screenshot_5_completed.png")
            print()
            
            # Check results
            print("=" * 80)
            print("📊 CHECKING RESULTS")
            print("=" * 80)
            print()
            
            brd_visible = page.locator('text=/Download.*BRD/i').is_visible()
            excel_visible = page.locator('text=/Download.*Excel/i').is_visible()
            
            if brd_visible:
                print("✅ BRD download button is visible")
            else:
                print("❌ BRD download button not found")
            
            if excel_visible:
                print("✅ Excel download button is visible")
            else:
                print("❌ Excel download button not found")
            
            print()
            print("=" * 80)
            print("📄 FINAL SCREENSHOT")
            print("=" * 80)
            page.screenshot(path="/tmp/screenshot_final.png", full_page=True)
            print("📸 Full page screenshot saved: screenshot_final.png")
            print()
            
            # Keep browser open for inspection
            print("🔍 Browser will stay open for 10 seconds for inspection...")
            time.sleep(10)
            
            return brd_visible and excel_visible
            
        except PlaywrightTimeout as e:
            print(f"❌ Timeout error: {e}")
            page.screenshot(path="/tmp/screenshot_error_timeout.png")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="/tmp/screenshot_error.png")
            return False
        finally:
            print()
            print("📸 All screenshots saved to /tmp/")
            context.close()
            browser.close()

# Run test
print()
success = test_project_estimator()

print()
print("=" * 80)
if success:
    print("✅ PLAYWRIGHT UI TEST PASSED")
    print()
    print("Next steps:")
    print("1. Check backend logs for validation output:")
    print("   docker-compose logs backend | grep -E '(Validator|alignment_score)'")
    print()
    print("2. Review screenshots in /tmp/screenshot_*.png")
else:
    print("❌ PLAYWRIGHT UI TEST FAILED")
    print()
    print("Check screenshots in /tmp/ for debugging")
print("=" * 80)

sys.exit(0 if success else 1)

