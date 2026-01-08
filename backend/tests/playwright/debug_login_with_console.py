"""Debug script with console logging."""
import os
import time
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://frontend:3000"

def debug_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        # Capture network requests
        requests = []
        page.on("request", lambda request: requests.append(f"{request.method} {request.url}"))
        
        # Navigate to frontend
        print("\n=== Navigating to frontend ===")
        page.goto(FRONTEND_URL, timeout=30000, wait_until="domcontentloaded")
        time.sleep(2)
        
        # Fill login form
        print("\n=== Logging in ===")
        page.fill('#username', 'admin')
        page.fill('#password', 'admin')
        
        # Clear previous requests
        requests.clear()
        console_messages.clear()
        
        print("Clicking Sign In button...")
        page.click('button[type="submit"]')
        
        # Wait for login attempt
        time.sleep(5)
        
        print(f"\nAfter login URL: {page.url}")
        
        # Print console messages
        print("\n=== Console Messages ===")
        for msg in console_messages:
            print(msg)
        
        # Print network requests
        print("\n=== Network Requests ===")
        for req in requests:
            print(req)
        
        browser.close()

if __name__ == "__main__":
    debug_login()
