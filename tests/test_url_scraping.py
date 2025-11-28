"""
Test URL Scraping Functionality
Quick test to verify web scraping for knowledge base
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.url_scraper import URLScraper, scrape_url_for_knowledge


async def test_basic_scraping():
    """Test basic URL scraping"""
    print("=" * 60)
    print("Testing URL Scraping for Knowledge Base")
    print("=" * 60)
    
    scraper = URLScraper()
    
    # Test URLs
    test_urls = [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://www.python.org/about/",
        "https://example.com"
    ]
    
    for url in test_urls:
        print(f"\n🌐 Scraping: {url}")
        print("-" * 60)
        
        result = await scraper.scrape_url(url)
        
        if result["success"]:
            print(f"✅ SUCCESS")
            print(f"   Title: {result['title']}")
            print(f"   Domain: {result['metadata']['domain']}")
            print(f"   Word Count: {result['metadata']['word_count']:,}")
            print(f"   Content Length: {result['metadata']['content_length']:,} chars")
            print(f"   Preview: {result['content'][:200]}...")
        else:
            print(f"❌ FAILED: {result['error']}")


async def test_convenience_function():
    """Test convenience function for knowledge base"""
    print("\n" + "=" * 60)
    print("Testing Convenience Function")
    print("=" * 60)
    
    url = "https://www.python.org/about/"
    print(f"\n🌐 Testing: {url}")
    
    success, title, content, metadata = await scrape_url_for_knowledge(url)
    
    if success:
        print(f"✅ SUCCESS")
        print(f"   Title: {title}")
        print(f"   Content: {len(content)} chars")
        print(f"   Metadata: {metadata}")
    else:
        print(f"❌ FAILED: {metadata}")


async def test_multiple_urls():
    """Test scraping multiple URLs concurrently"""
    print("\n" + "=" * 60)
    print("Testing Concurrent Scraping")
    print("=" * 60)
    
    scraper = URLScraper()
    
    urls = [
        "https://example.com",
        "https://www.python.org",
        "https://en.wikipedia.org/wiki/Python_(programming_language)"
    ]
    
    print(f"\n🌐 Scraping {len(urls)} URLs concurrently...")
    results = await scraper.scrape_multiple(urls, max_concurrent=3)
    
    for i, result in enumerate(results):
        if result["success"]:
            print(f"✅ {urls[i]}: {result['metadata']['word_count']:,} words")
        else:
            print(f"❌ {urls[i]}: {result['error']}")


async def main():
    try:
        await test_basic_scraping()
        await test_convenience_function()
        await test_multiple_urls()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
