import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.scraper_service import scraper_service

async def test():
    print("="*80)
    print("🧪 TESTING SCRAPER TEXT EXTRACTION")
    print("="*80)
    
    url = "https://books.toscrape.com/catalogue/sharp-objects_997/index.html"
    print(f"\n📡 Fetching: {url}")
    
    # Scrape without DB (returns dict with html and text)
    result = await scraper_service.scrape_url(url, db=None)
    
    print(f"\n✅ Scrape completed")
    print(f"📊 Result keys: {list(result.keys())}")
    
    html = result.get('html', '')
    text = result.get('text', '')
    
    print(f"\n📄 HTML length: {len(html):,} chars")
    print(f"📝 Text length: {len(text):,} chars")
    
    print(f"\n🔍 HTML preview (first 500 chars):")
    print("-"*80)
    print(html[:500])
    print("-"*80)
    
    print(f"\n🔍 TEXT preview (first 500 chars):")
    print("-"*80)
    print(text[:500])
    print("-"*80)
    
    print(f"\n🔍 TEXT type: {type(text)}")
    print(f"🔍 TEXT encoding info:")
    try:
        print(f"   - Can encode to UTF-8: {text.encode('utf-8')[:50]}")
    except Exception as e:
        print(f"   - ❌ UTF-8 encode failed: {e}")
    
    # Check for binary data markers
    if any(ord(c) < 32 and c not in '\n\r\t' for c in text[:1000]):
        print("\n❌ TEXT CONTAINS BINARY DATA (non-printable characters detected)")
    else:
        print("\n✅ TEXT appears to be clean readable text")

asyncio.run(test())
