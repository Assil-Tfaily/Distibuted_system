import redis
import json
import os

class URLQueue:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.queue_name = 'scraping_urls'
    
    def add_url(self, url, priority=1):
        """Add URL to queue with priority"""
        item = json.dumps({'url': url, 'priority': priority})
        self.redis_client.zadd(self.queue_name, {item: priority})
    
    def get_url(self):
        """Get highest priority URL from queue"""
        items = self.redis_client.zrange(self.queue_name, 0, 0)
        if items:
            item = json.loads(items[0])
            self.redis_client.zrem(self.queue_name, items[0])
            return item['url']
        return None
    
    def get_queue_size(self):
        """Get number of URLs in queue"""
        return self.redis_client.zcard(self.queue_name)

# Simple in-memory fallback queue
class SimpleURLQueue:
    def __init__(self):
        self.urls = []
    
    def add_url(self, url, priority=1):
        self.urls.append(url)
    
    def get_url(self):
        return self.urls.pop(0) if self.urls else None
    
    def get_queue_size(self):
        return len(self.urls)