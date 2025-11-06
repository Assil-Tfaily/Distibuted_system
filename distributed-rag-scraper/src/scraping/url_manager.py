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
        
    def submit_urls(self, urls: List[Dict], topic: str = 'scraping-urls'):
        """Submit URLs to Kafka topic for distributed processing."""
        successful = 0
        for url_data in urls:
            try:
                future = self.producer.send(topic, value=url_data)
                future.get(timeout=10)
                successful += 1
                logger.info(f"Submitted URL to {topic}: {url_data.get('url', 'Unknown')}")
            except Exception as e:
                logger.error(f"Failed to submit URL {url_data}: {e}")
        
        self.producer.flush()
        logger.info(f"Successfully submitted {successful}/{len(urls)} URLs to {topic}")
        return successful

    def get_url_batch(self, topic: str, batch_size: int = 10, timeout: int = 30):
        """Get a batch of URLs from Kafka for processing."""
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            group_id='dask-workers',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        urls = []
        start_time = time.time()
        
        for message in consumer:
            if len(urls) >= batch_size or (time.time() - start_time) > timeout:
                break
                
            urls.append(message.value)
            # Manually commit offset
            consumer.commit()
        
        consumer.close()
        return urls