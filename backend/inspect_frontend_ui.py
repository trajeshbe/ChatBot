#!/usr/bin/env python3
"""
Inspect Frontend UI Elements
Fetches frontend pages and identifies actual selectors for E2E tests
"""

import requests
from bs4 import BeautifulSoup
import json

FRONTEND_URL = "http://localhost:3001"

def inspect_page(url, page_name):
    """Fetch and inspect a page"""
    print(f"\n{'='*80}")
    print(f"Inspecting: {page_name}")
    print(f"URL: {url}")
    print(f"{'='*80}")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to fetch {url}: HTTP {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for key elements
        print("\n📋 Key Elements Found:")

        # Headers
        headers = soup.find_all(['h1', 'h2', 'h3'])
        if headers:
            print(f"\n  Headers ({len(headers)}):")
            for h in headers[:5]:  # First 5
                text = h.get_text(strip=True)[:60]
                print(f"    - {h.name}: {text}")

        # Forms/Inputs
        inputs = soup.find_all('input')
        if inputs:
            print(f"\n  Input Fields ({len(inputs)}):")
            for inp in inputs[:10]:  # First 10
                input_type = inp.get('type', 'text')
                placeholder = inp.get('placeholder', '')
                input_id = inp.get('id', '')
                input_name = inp.get('name', '')
                data_testid = inp.get('data-testid', '')
                print(f"    - type={input_type}, placeholder='{placeholder}', id='{input_id}', name='{input_name}', data-testid='{data_testid}'")

        # Textareas
        textareas = soup.find_all('textarea')
        if textareas:
            print(f"\n  Textareas ({len(textareas)}):")
            for ta in textareas:
                placeholder = ta.get('placeholder', '')
                ta_id = ta.get('id', '')
                ta_name = ta.get('name', '')
                data_testid = ta.get('data-testid', '')
                print(f"    - placeholder='{placeholder}', id='{ta_id}', name='{ta_name}', data-testid='{data_testid}'")

        # Select dropdowns
        selects = soup.find_all('select')
        if selects:
            print(f"\n  Select Dropdowns ({len(selects)}):")
            for sel in selects:
                sel_id = sel.get('id', '')
                sel_name = sel.get('name', '')
                data_testid = sel.get('data-testid', '')
                options = sel.find_all('option')
                option_texts = [opt.get_text(strip=True) for opt in options[:5]]
                print(f"    - id='{sel_id}', name='{sel_name}', data-testid='{data_testid}'")
                if option_texts:
                    print(f"      Options: {option_texts}")

        # Buttons
        buttons = soup.find_all('button')
        if buttons:
            print(f"\n  Buttons ({len(buttons)}):")
            for btn in buttons[:10]:  # First 10
                text = btn.get_text(strip=True)[:40]
                btn_type = btn.get('type', '')
                data_testid = btn.get('data-testid', '')
                print(f"    - '{text}', type='{btn_type}', data-testid='{data_testid}'")

        # Links
        links = soup.find_all('a')
        if links:
            print(f"\n  Links ({len(links)}):")
            for link in links[:10]:  # First 10
                href = link.get('href', '')
                text = link.get_text(strip=True)[:40]
                if href and not href.startswith('#'):
                    print(f"    - {text} → {href}")

        # Check for React hydration
        scripts = soup.find_all('script')
        has_nextjs = any('next' in str(s).lower() for s in scripts)
        has_react = any('react' in str(s).lower() for s in scripts)

        print(f"\n  Frontend Framework:")
        print(f"    - Next.js detected: {has_nextjs}")
        print(f"    - React detected: {has_react}")

        # Check for specific keywords
        content = soup.get_text().lower()
        keywords = ['chat', 'message', 'project', 'upload', 'scrape', 'model', 'query']
        print(f"\n  Keywords found in content:")
        for keyword in keywords:
            count = content.count(keyword)
            if count > 0:
                print(f"    - '{keyword}': {count} occurrences")

        # Save raw HTML for manual inspection
        filename = f"/tmp/{page_name.replace('/', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n  💾 Saved HTML to: {filename}")

    except requests.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
    except Exception as e:
        print(f"❌ Error inspecting page: {e}")

def main():
    """Inspect all key pages"""
    pages = [
        (f"{FRONTEND_URL}/", "home"),
        (f"{FRONTEND_URL}/library", "library"),
        (f"{FRONTEND_URL}/scrape", "scrape"),
        (f"{FRONTEND_URL}/models", "models"),
        (f"{FRONTEND_URL}/settings", "settings"),
    ]

    print("🔍 Frontend UI Inspector")
    print("="*80)

    for url, name in pages:
        inspect_page(url, name)

    print("\n" + "="*80)
    print("✅ Inspection complete!")
    print("="*80)

if __name__ == "__main__":
    main()
