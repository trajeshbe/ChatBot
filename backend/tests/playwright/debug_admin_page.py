"""Debug script to check admin page state."""
import os
import time
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://frontend:3000"

def debug_admin_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        print("\n=== Navigating to frontend ===")
        page.goto(FRONTEND_URL, timeout=30000, wait_until="domcontentloaded")
        time.sleep(2)
        
        print(f"Current URL: {page.url}")
        print(f"Page title: {page.title()}")
        
        # Check if login is needed
        print("\n=== Checking for login ===")
        has_logout = page.is_visible('button:has-text("Logout")', timeout=1000)
        print(f"Logout button visible: {has_logout}")
        
        has_username = page.is_visible('#username', timeout=1000)
        print(f"Username input (#username) visible: {has_username}")
        
        if not has_logout and has_username:
            print("\n=== Logging in ===")
            print("Filling username field...")
            page.fill('#username', 'admin')
            print("Filling password field...")
            page.fill('#password', 'admin')  # Corrected password
            
            print("Clicking Sign In button...")
            page.click('button[type="submit"]')
            
            print("Waiting 5 seconds for login to complete...")
            time.sleep(5)
            
            print(f"After login URL: {page.url}")
            print(f"After login title: {page.title()}")
            
            # Check if we're logged in now
            has_logout_after = page.is_visible('button:has-text("Logout")', timeout=2000)
            print(f"Logout button visible after login: {has_logout_after}")
        
        # Navigate to admin
        print("\n=== Navigating to /admin ===")
        page.goto(f"{FRONTEND_URL}/admin", timeout=30000, wait_until="domcontentloaded")
        time.sleep(5)  # Wait longer for React to hydrate
        
        print(f"Admin page URL: {page.url}")
        print(f"Admin page title: {page.title()}")
        
        # Check page content
        print("\n=== Checking page content ===")
        page_content = page.content()
        if "Export POC Package" in page_content:
            print("✅ 'Export POC Package' text found in page HTML")
        else:
            print("❌ 'Export POC Package' text NOT found in page HTML")
        
        # Check for button with different selectors
        print("\n=== Testing different selectors ===")
        selectors = [
            'button:has-text("Export POC Package")',
            'button:has-text("Export")',
            'button:has-text("Back to Chat")',
            'button:has-text("Logout")',
            'button',
        ]
        
        for selector in selectors:
            try:
                count = page.locator(selector).count()
                print(f"Selector '{selector}': {count} elements found")
                if count > 0 and selector == 'button':
                    # List all buttons
                    buttons = page.locator('button').all()
                    print("  All button texts:")
                    for i, btn in enumerate(buttons):
                        text = btn.text_content()
                        print(f"    {i+1}. '{text}'")
            except Exception as e:
                print(f"Selector '{selector}': Error - {e}")
        
        # Save screenshot
        print("\n=== Saving screenshot ===")
        page.screenshot(path="test_results/debug_admin_page.png")
        print("Screenshot saved to: test_results/debug_admin_page.png")
        
        # Save HTML
        with open("test_results/debug_admin_page.html", "w") as f:
            f.write(page_content)
        print("HTML saved to: test_results/debug_admin_page.html")
        
        browser.close()

if __name__ == "__main__":
    debug_admin_page()
