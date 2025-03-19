#  content_fetcher.py


import requests
from bs4 import BeautifulSoup
import trafilatura
import logging
import time
import random
from urllib.parse import urlparse
import cloudscraper  
from requests.exceptions import RequestException
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentFetcher:
    """Fetches content from URLs using multiple methods for reliability."""
    
    def __init__(self):
        # Initialize with a rotating set of user agents for better disguise
        try:
            self.user_agent = UserAgent()
        except:
            # Fallback if fake_useragent fails
            self.user_agent = None
            logger.warning("Failed to initialize UserAgent, using default fallback")
    
    def get_random_headers(self, url=None):
        """Generate random headers to avoid detection"""
        if self.user_agent:
            user_agent = self.user_agent.random
        else:
            # Fallback user agent options
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/121.0'
            ]
            user_agent = random.choice(user_agents)
            
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',  # Do Not Track
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # Add a referer that makes sense
        if url:
            parsed_url = urlparse(url)
            potential_referers = [
                f"{parsed_url.scheme}://{parsed_url.netloc}",
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://duckduckgo.com/"
            ]
            headers['Referer'] = random.choice(potential_referers)
            
        return headers
        
    def fetch_with_regular_requests(self, url, max_retries=3):
        """Attempt to fetch content using regular requests with retries and backoff"""
        for attempt in range(max_retries):
            try:
                # Add small random delay between retries to avoid detection patterns
                if attempt > 0:
                    time.sleep(2 + random.random() * 3)
                    
                headers = self.get_random_headers(url)
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    print("\n\nResponse: ", response.text, "\n\n")
                    return response.text
                elif response.status_code == 403 or response.status_code == 429:
                    logger.warning(f"Access denied (status {response.status_code}), retrying with different headers")
                    continue
                else:
                    logger.warning(f"Request failed with status code: {response.status_code}")
                    
            except RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{max_retries}): {e}")
                
        return None
        
    def fetch_with_cloudscraper(self, url):
        """Use cloudscraper to bypass Cloudflare protection"""
        try:
            scraper = cloudscraper.create_scraper(browser='chrome')
            response = scraper.get(url, timeout=20)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Cloudscraper request failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Cloudscraper extraction failed: {e}")
            return None
    
    def extract_content_from_html(self, html_content, url=""):
        """Extract the main content from HTML"""
        if not html_content:
            return {"title": "", "content": ""}
            
        # Method 1: Try using Trafilatura (handles most modern websites well)
        try:
            result = trafilatura.extract(html_content, 
                                         include_tables=False, 
                                         include_images=False, 
                                         include_links=False,
                                         output_format='txt')
            if result:
                # Extract title from HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                title = soup.title.string if soup.title else ""
                
                return {
                    "title": title.strip(),
                    "content": result.strip()
                }
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {e}")
        
        # Method 2: Fallback to Beautiful Soup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else ""
            
            # Extract content - searching for common content containers
            content = ""
            containers = [
                'article', 'main', 
                '.content', '#content', 
                '.post', '.entry', '.article', '.blog-post',
                '[itemprop="articleBody"]', '[itemprop="mainEntityOfPage"]'
            ]
            
            for container in containers:
                if content:
                    break
                    
                elements = soup.select(container)
                if elements:
                    # For each found element, remove nav, ads, etc.
                    for element in elements:
                        for unwanted in element.select('nav, aside, footer, .ads, .ad-container, .related-posts, .comments, .social-share'):
                            unwanted.extract()
                        
                    content = elements[0].get_text(separator='\n\n')
            
            # If no content found in common containers, get the body text with filtering
            if not content:
                # Remove unwanted elements
                for unwanted in soup.select('script, style, header, footer, nav, aside, .ads, .ad-container, .comments'):
                    unwanted.extract()
                
                # Try to find most content-dense element (paragraph density heuristic)
                p_tags = soup.find_all('p')
                if p_tags:
                    # Group p tags by parent to find the densest container
                    parents = {}
                    for p in p_tags:
                        parent = p.parent
                        if parent not in parents:
                            parents[parent] = []
                        parents[parent].append(p)
                    
                    # Find parent with most paragraphs
                    max_parent = max(parents.items(), key=lambda x: len(x[1]))[0]
                    content = max_parent.get_text(separator='\n\n')
                else:
                    # Fallback to body text
                    content = soup.body.get_text(separator='\n\n') if soup.body else ""
            
            return {
                "title": title.strip(),
                "content": content.strip()
            }
        except Exception as e:
            logger.error(f"BeautifulSoup extraction failed: {e}")
            return {
                "title": "",
                "content": ""
            }
    
    def fetch_content(self, url):
        """
        Attempts to extract content from a URL using multiple methods.
        
        Args:
            url (str): The URL to fetch content from
            
        Returns:
            dict: A dictionary containing the extracted title and content
        """
        logger.info(f"Fetching content from: {url}")
        
        # Method 1: Try fetching with trafilatura directly first (handles most cases)
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, 
                                          include_tables=False, 
                                          include_images=False, 
                                          include_links=False,
                                          output_format='txt')
                if result:
                    # Try to get the title separately
                    title = ""
                    soup = BeautifulSoup(downloaded, 'html.parser')
                    title = soup.title.string if soup.title else ""
                    
                    return {
                        "title": title.strip(),
                        "content": result.strip()
                    }
        except Exception as e:
            logger.warning(f"Direct trafilatura extraction failed: {e}")
        
        # Method 2: Try with regular requests
        html_content = self.fetch_with_regular_requests(url)
        if html_content:
            result = self.extract_content_from_html(html_content, url)
            if result["content"]:
                return result
        
        # Method 3: Try with cloudscraper (bypasses Cloudflare protection)
        html_content = self.fetch_with_cloudscraper(url)
        if html_content:
            result = self.extract_content_from_html(html_content, url)
            if result["content"]:
                return result
        
        # If all methods fail, return empty result
        logger.error(f"All content extraction methods failed for URL: {url}")
        return {
            "title": "",
            "content": ""
        }