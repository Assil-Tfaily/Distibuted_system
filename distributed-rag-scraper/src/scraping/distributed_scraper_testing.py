import ray
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import List, Dict

# Initialize Ray
ray.init()

@ray.remote
class URLManager:
    def __init__(self):
        self.pending_urls = set()
        self.visited_urls = set()
        self.max_urls = 1000
    
    def add_urls(self, urls: List[str]):
        new_urls = [url for url in urls if url not in self.visited_urls and url not in self.pending_urls]
        self.pending_urls.update(new_urls[:self.max_urls - len(self.visited_urls)])
        return len(new_urls)
    
    def get_next_batch(self, batch_size: int = 10):
        batch = list(self.pending_urls)[:batch_size]
        for url in batch:
            self.pending_urls.remove(url)
            self.visited_urls.add(url)
        return batch
    
    def get_stats(self):
        return {
            "pending": len(self.pending_urls),
            "visited": len(self.visited_urls)
        }

@ray.remote
class WebScraper:
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_url(self, url: str) -> Dict:
        try:
            time.sleep(self.delay)  # Be polite
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text and links
            text = soup.get_text(separator=' ', strip=True)
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                if self.is_valid_url(absolute_url):
                    links.append(absolute_url)
            
            return {
                'url': url,
                'title': title_text,
                'content': text,
                'links': links,
                'status': 'success',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'url': url,
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

class DistributedScrapingManager:
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.url_manager = URLManager.remote()
        self.scrapers = [WebScraper.remote(delay=1.0) for _ in range(num_workers)]
    
    def start_scraping(self, seed_urls: List[str], max_pages: int = 100):
        # Add seed URLs
        ray.get(self.url_manager.add_urls.remote(seed_urls))
        
        results = []
        while len(results) < max_pages:
            # Get next batch of URLs
            batch = ray.get(self.url_manager.get_next_batch.remote(10))
            if not batch:
                break
            
            # Distribute scraping tasks
            scraping_tasks = []
            for url in batch:
                scraper = self.scrapers[len(scraping_tasks) % self.num_workers]
                scraping_tasks.append(scraper.scrape_url.remote(url))
            
            # Wait for results
            batch_results = ray.get(scraping_tasks)
            
            # Process results and extract new URLs
            for result in batch_results:
                if result['status'] == 'success':
                    results.append(result)
                    # Add new links to URL manager
                    if result['links']:
                        ray.get(self.url_manager.add_urls.remote(result['links']))
            
            # Print progress
            stats = ray.get(self.url_manager.get_stats.remote())
            print(f"Progress: {len(results)}/{max_pages} - Pending: {stats['pending']} - Visited: {stats['visited']}")
        
        return results

if __name__ == "__main__":
    manager = DistributedScrapingManager(num_workers=4)
    seed_urls = [
        "https://example.com",
        "https://httpbin.org/html"
    ]
    
    results = manager.start_scraping(seed_urls, max_pages=50)
    print(f"Scraped {len(results)} pages successfully!")