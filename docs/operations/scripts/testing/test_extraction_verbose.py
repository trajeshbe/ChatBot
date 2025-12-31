#!/usr/bin/env python3
"""
Test extraction with verbose output showing:
1. The scraped data from the URL
2. The final prompt sent to OpenAI
"""
import sys
sys.path.insert(0, '/app')

import asyncio
from bs4 import BeautifulSoup
import httpx

async def test_extraction():
    print("="*80)
    print("🔍 EXTRACTION TEST: Sharp Objects Page")
    print("="*80)

    url = "https://books.toscrape.com/catalogue/sharp-objects_997/index.html"

    # Step 1: Scrape the page (same as scraper_service does)
    print("\n📡 Step 1: Fetching HTML...")
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        html = response.text

    print(f"✅ Fetched {len(html)} characters of HTML")

    # Step 2: Extract text using BeautifulSoup (same as scraper_service)
    print("\n📄 Step 2: Extracting text with BeautifulSoup...")
    soup = BeautifulSoup(html, 'lxml')

    # Remove navigation, scripts, styles (like scraper_service does)
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    scraped_data = soup.get_text(separator='\n', strip=True)

    print(f"✅ Extracted {len(scraped_data)} characters of text")

    # Step 3: Show the scraped data
    print("\n" + "="*80)
    print("📄 SCRAPED DATA (what OpenAI will receive):")
    print("="*80)
    print(scraped_data)
    print("="*80)

    # Step 4: Build the prompt (same as llm_extractor does)
    print("\n📝 Step 4: Building the prompt...")

    # Fields to extract
    fields = ["Product Type", "Availability"]

    # System prompt
    system_prompt = """You are a professional data extraction and mapping assistant specialized in extracting structured data from webpages.

Your task: Extract data from scraped webpage content and map it to template columns.

CRITICAL RULES:
1. Extract ONLY values that actually exist in the scraped data
2. NEVER make up, infer, or hallucinate values
3. If a field is not found in the scraped data, use: "—"
4. Return VALID JSON ONLY - no markdown, no code blocks, no explanations
5. Extract exact values as they appear (preserve numbers, text, formatting)

OUTPUT FORMAT - You MUST return a JSON object exactly like this:
{
  "mapped_data": {
    "Column1": "value found in data",
    "Column2": "another value",
    "Column3": "—"
  },
  "missing_fields": ["Column3"]
}

IMPORTANT: Return ONLY the JSON object. No markdown formatting. No code blocks. No explanations."""

    # Template info
    template_info = "TEMPLATE COLUMNS TO EXTRACT:\n"
    for i, field in enumerate(fields, 1):
        template_info += f"{i}. {field}\n"

    # User prompt with scraped data
    extraction_prompt = f"""SCRAPED WEBPAGE CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{scraped_data}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{template_info}

EXTRACTION INSTRUCTIONS:
1. Read the scraped content thoroughly - check ALL sections
2. For EACH template column:
   a. Search for exact matches or close variations of the column name
   b. Look in common locations: headers, tables, lists, key-value pairs
   c. Extract the value exactly as it appears
   d. If the column has multiple possible matches, choose the most relevant one
3. For missing fields: If you cannot find ANY relevant data for a column, use "—"
4. Return a valid JSON object with "mapped_data" and "missing_fields"

Return your response as PURE JSON (no markdown, no code blocks):"""

    # Step 5: Show the complete prompt
    print("\n" + "="*80)
    print("📋 PROMPT SENT TO OPENAI:")
    print("="*80)
    print("\n🎯 SYSTEM MESSAGE:")
    print("-"*80)
    print(system_prompt)
    print("-"*80)

    print("\n💬 USER MESSAGE (INSTRUCTIONS + SCRAPED DATA):")
    print("-"*80)
    print(extraction_prompt)
    print("-"*80)
    print("="*80)

    print("\n✅ This is exactly what OpenAI receives!")
    print(f"   - Scraped data length: {len(scraped_data)} chars")
    print(f"   - Fields to extract: {fields}")
    print(f"   - System prompt length: {len(system_prompt)} chars")
    print(f"   - Extraction prompt length: {len(extraction_prompt)} chars")

asyncio.run(test_extraction())
