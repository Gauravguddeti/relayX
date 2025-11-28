"""
URL Scraper for Knowledge Base
Scrapes websites and extracts clean text content for AI agent knowledge
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class URLScraper:
    """Web scraper for extracting clean text content from URLs"""
    
    def __init__(self, timeout: int = 30, max_content_length: int = 500000):
        """
        Initialize URL scraper
        
        Args:
            timeout: Request timeout in seconds
            max_content_length: Max content size in bytes (500KB default)
        """
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    async def scrape_url(self, url: str) -> Dict[str, any]:
        """
        Scrape a single URL and extract clean text content
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dict with:
                - success: bool
                - url: original URL
                - title: page title
                - content: cleaned text content
                - metadata: dict with domain, word_count, etc.
                - error: error message if failed
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    "success": False,
                    "url": url,
                    "error": "Invalid URL format"
                }
            
            # Fetch content with retries
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Add Referer header to look more legitimate
            headers = self.headers.copy()
            headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            # Try with different approaches if first fails
            attempts = [
                {'headers': headers},
                {'headers': {**headers, 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}},
                {'headers': {**headers, 'Accept-Encoding': 'gzip, deflate'}}  # Without brotli
            ]
            
            last_error = None
            html = None
            
            for attempt_num, attempt_config in enumerate(attempts):
                try:
                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                        async with session.get(
                            url, 
                            headers=attempt_config['headers'],
                            timeout=aiohttp.ClientTimeout(total=self.timeout),
                            allow_redirects=True
                        ) as response:
                            
                            # Check status
                            if response.status == 403:
                                if attempt_num < len(attempts) - 1:
                                    logger.info(f"Got 403, trying alternative approach {attempt_num + 2}...")
                                    last_error = "Access denied (403)"
                                    await asyncio.sleep(0.5)  # Small delay between attempts
                                    continue
                                return {
                                    "success": False,
                                    "url": url,
                                    "error": "Website blocking: This site prevents automated scraping. Solution: Visit the page in your browser, copy the text content, and paste it manually into the knowledge base using 'Add Knowledge' instead."
                                }
                            elif response.status == 404:
                                return {
                                    "success": False,
                                    "url": url,
                                    "error": "Page not found (404)"
                                }
                            elif response.status != 200:
                                if attempt_num < len(attempts) - 1:
                                    last_error = f"HTTP {response.status}"
                                    await asyncio.sleep(0.5)
                                    continue
                                return {
                                    "success": False,
                                    "url": url,
                                    "error": f"HTTP {response.status} - Unable to access page"
                                }
                            
                            # Check content type
                            content_type = response.headers.get('Content-Type', '')
                            if 'text/html' not in content_type:
                                return {
                                    "success": False,
                                    "url": url,
                                    "error": f"Not HTML content: {content_type}"
                                }
                            
                            # Read content with size limit
                            html = await response.text()
                            if len(html) > self.max_content_length:
                                html = html[:self.max_content_length]
                            
                            # Success! Break out of retry loop
                            break
                            
                except aiohttp.ClientError as e:
                    if attempt_num < len(attempts) - 1:
                        logger.info(f"Network error on attempt {attempt_num + 1}, retrying: {e}")
                        last_error = str(e)
                        await asyncio.sleep(0.5)
                        continue
                    raise
            
            if html is None:
                return {
                    "success": False,
                    "url": url,
                    "error": f"Failed after {len(attempts)} attempts: {last_error}"
                }
            
            # Parse and extract text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                script.decompose()
            
            # Get title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else urlparse(url).netloc
            
            # Extract main content
            # Try to find main content areas first
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_=re.compile(r'content|main|body', re.I)) or
                soup.body
            )
            
            if main_content:
                # Get text
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Clean up text
            cleaned_text = self._clean_text(text)
            
            # Calculate metadata
            word_count = len(cleaned_text.split())
            domain = parsed.netloc
            
            return {
                "success": True,
                "url": url,
                "title": title_text,
                "content": cleaned_text,
                "metadata": {
                    "domain": domain,
                    "word_count": word_count,
                    "scraped_at": asyncio.get_event_loop().time(),
                    "content_length": len(cleaned_text)
                }
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "url": url,
                "error": f"Timeout after {self.timeout}s"
            }
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "url": url,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize scraped text"""
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        # Remove empty lines
        lines = [line for line in lines if line]
        # Remove duplicate consecutive lines
        cleaned_lines = []
        prev_line = None
        for line in lines:
            if line != prev_line:
                cleaned_lines.append(line)
                prev_line = line
        
        # Join with newlines
        cleaned = '\n'.join(cleaned_lines)
        
        # Normalize whitespace
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    async def scrape_multiple(self, urls: List[str], max_concurrent: int = 3) -> List[Dict]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of scrape results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_limit(url):
            async with semaphore:
                return await self.scrape_url(url)
        
        tasks = [scrape_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "url": urls[i],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def scrape_sitemap(self, url: str, max_pages: int = 10) -> List[Dict]:
        """
        Scrape pages from a sitemap or automatically discover pages
        
        Args:
            url: Base URL or sitemap URL
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of scraped page results
        """
        # TODO: Implement sitemap parsing and page discovery
        # For now, just scrape the single URL
        result = await self.scrape_url(url)
        return [result]


# Convenience function
async def scrape_url_for_knowledge(url: str) -> Tuple[bool, str, str, Dict]:
    """
    Scrape URL and return data ready for knowledge base
    
    Returns:
        (success, title, content, metadata)
    """
    scraper = URLScraper()
    result = await scraper.scrape_url(url)
    
    if result["success"]:
        return (
            True,
            result["title"],
            result["content"],
            result["metadata"]
        )
    else:
        return (False, "", "", {"error": result.get("error", "Unknown error")})
