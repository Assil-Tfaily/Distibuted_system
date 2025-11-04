from kafka import KafkaProducer, KafkaConsumer
import json
import logging
from typing import List, Dict, Callable
import time
from threading import Thread

logger = logging.getLogger(__name__)

class KafkaURLManager:
    def __init__(self, bootstrap_servers: List[str] = ['localhost:9092']):
        self.bootstrap_servers = bootstrap_servers
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5
        )
        self.is_running = False
        
    def submit_urls(self, urls: List[Dict], topic: str = 'scraping-urls'):
        """Submit URLs to Kafka topic for distributed processing."""
        successful = 0
        for url_data in urls:
            try:
                future = self.producer.send(topic, value=url_data)
                future.get(timeout=10)  # Wait for confirmation
                successful += 1
                logger.info(f"Submitted URL to {topic}: {url_data.get('url', 'Unknown')}")
            except Exception as e:
                logger.error(f"Failed to submit URL {url_data}: {e}")
        
        self.producer.flush()
        logger.info(f"Successfully submitted {successful}/{len(urls)} URLs to {topic}")

    def start_url_consumer(self, topic: str, group_id: str, processor_callback: Callable):
        """Start a URL consumer in a separate thread."""
        self.is_running = True
        
        def consume_loop():
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=group_id,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            
            logger.info(f"Started URL consumer for topic {topic} in group {group_id}")
            
            for message in consumer:
                if not self.is_running:
                    break
                    
                try:
                    url_data = message.value
                    logger.info(f"Processing URL: {url_data.get('url', 'Unknown')}")
                    processor_callback(url_data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
            
            consumer.close()
        
        self.consumer_thread = Thread(target=consume_loop)
        self.consumer_thread.start()

    def stop_consumer(self):
        """Stop the URL consumer."""
        self.is_running = False
        if hasattr(self, 'consumer_thread'):
            self.consumer_thread.join(timeout=10)

class KafkaScraperCoordinator:
    def __init__(self, bootstrap_servers: List[str] = ['localhost:9092']):
        self.url_manager = KafkaURLManager(bootstrap_servers)
        self.results_producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
    def generate_urls_from_genres(self, genres: List[Dict], pages_per_genre: int = 2):
        """Generate URLs from genres and submit to Kafka."""
        from .base_scraper import LastFMScraperBS
        
        scraper = LastFMScraperBS()
        all_urls = []
        
        for genre in genres:
            logger.info(f"Generating URLs for genre: {genre['name']}")
            tracks = scraper.get_tracks_from_genre(genre['url'], pages=pages_per_genre)
            
            for track in tracks:
                url_data = {
                    'url': track['url'],
                    'genre': genre['name'],
                    'track_name': track['name'],
                    'type': 'track_details'
                }
                all_urls.append(url_data)
        
        self.url_manager.submit_urls(all_urls)
        return len(all_urls)
    
    def process_url_message(self, url_data: Dict):
        """Process a single URL message from Kafka."""
        from .base_scraper import LastFMScraperBS
        
        scraper = LastFMScraperBS()
        
        try:
            # Extract track details
            details = scraper.extract_track_details(
                url_data['url'], 
                url_data['genre']
            )
            
            # Send result to results topic
            self.results_producer.send('scraping-results', value=details)
            logger.info(f"Processed and sent results for: {details.get('track_name')}")
            
        except Exception as e:
            logger.error(f"Failed to process URL {url_data['url']}: {e}")
            
            # Send error to dead letter queue
            error_data = {
                'original_message': url_data,
                'error': str(e),
                'timestamp': time.time()
            }
            self.results_producer.send('scraping-errors', value=error_data)