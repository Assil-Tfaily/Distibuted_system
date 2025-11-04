from dask.distributed import Client, LocalCluster
import time
from typing import List, Dict
from .base_scraper import LastFMScraperBS
from .url_manager import KafkaScraperCoordinator
import logging
import csv

logger = logging.getLogger(__name__)

def scrape_genre_worker(genre_data: Dict, max_tracks: int = 50, pages: int = 2) -> List[Dict]:
    """Worker function to scrape a single genre."""
    worker_id = id(genre_data) % 1000  # Simple worker ID
    scraper = LastFMScraperBS()
    
    logger.info(f"Worker {worker_id} scraping genre: {genre_data['name']}")
    
    try:
        tracks = scraper.get_tracks_from_genre(genre_data["url"], pages=pages)
        if max_tracks:
            tracks = tracks[:max_tracks]
        
        results = []
        for track in tracks:
            try:
                details = scraper.extract_track_details(track["url"], genre_data["name"])
                results.append(details)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Worker {worker_id} failed to extract track: {e}")
                continue
        
        logger.info(f"Worker {worker_id} completed {genre_data['name']}: {len(results)} tracks")
        return results
    except Exception as e:
        logger.error(f"Worker {worker_id} failed on genre {genre_data['name']}: {e}")
        return []

class DistributedScraper:
    def __init__(self, n_workers: int = 4, use_kafka: bool = False):
        self.n_workers = n_workers
        self.use_kafka = use_kafka
        
        if use_kafka:
            self.kafka_coordinator = KafkaScraperCoordinator()
            logger.info("Initialized with Kafka URL management")
        else:
            self.cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1)
            self.client = Client(self.cluster)
            logger.info(f"Initialized Dask cluster with {n_workers} workers")

    def scrape_genres(self, genre_names: List[str] = None, max_tracks_per_genre: int = 50, pages: int = 2) -> List[Dict]:
        """Distribute scraping tasks across Dask workers."""
        base_scraper = LastFMScraperBS()
        all_genres = base_scraper.get_genres()
        
        if genre_names:
            all_genres = [g for g in all_genres if g["name"].lower() in [x.lower() for x in genre_names]]
        
        logger.info(f"Distributing {len(all_genres)} genres across {self.n_workers} workers")
        if self.use_kafka:
            return self._scrape_with_kafka(all_genres, max_tracks_per_genre, pages)
        else:
            return self._scrape_with_dask(all_genres, max_tracks_per_genre, pages)
        
        # Submit tasks to Dask
    def _scrape_with_dask(self, all_genres: List[Dict], max_tracks_per_genre: int, pages: int) -> List[Dict]:
        """Use Dask for distributed scraping."""
        logger.info(f"Distributing {len(all_genres)} genres across {self.n_workers} Dask workers")
        
        futures = []
        for genre in all_genres:
            future = self.client.submit(
                scrape_genre_worker,
                genre,
                max_tracks_per_genre,
                pages
            )
            futures.append(future)
        
        # Collect results
        all_results = []
        completed = 0
        for future in futures:
            try:
                result = future.result(timeout=300)  # 5 minute timeout
                all_results.extend(result)
                completed += 1
                logger.info(f"Progress: {completed}/{len(all_genres)} genres completed")
            except Exception as e:
                logger.error(f"Error getting result from worker: {e}")
        
        logger.info(f"Scraping completed. Total tracks: {len(all_results)}")
        return all_results
    
    def _scrape_with_kafka(self, all_genres: List[Dict], max_tracks_per_genre: int, pages: int) -> List[Dict]:
        """Use Kafka for URL management and distributed scraping."""
        from kafka import KafkaConsumer
        import json
        
        logger.info("Starting Kafka-based distributed scraping")
        
        # Generate and submit URLs to Kafka
        total_urls = self.kafka_coordinator.generate_urls_from_genres(all_genres, pages)
        logger.info(f"Generated {total_urls} URLs in Kafka topic")
        
        # Start multiple workers to process URLs
        results = []
        results_consumer = KafkaConsumer(
            'scraping-results',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='earliest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        # For demo purposes, we'll process URLs directly
        # In production, you'd have separate worker processes
        consumer = KafkaConsumer(
            'scraping-urls',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='earliest',
            group_id='demo-scraper-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        logger.info("Starting to process URLs from Kafka...")
        processed = 0
        
        for message in consumer:
            if processed >= total_urls:
                break
                
            url_data = message.value
            try:
                result = self.kafka_coordinator.process_url_message(url_data)
                processed += 1
                logger.info(f"Processed {processed}/{total_urls} URLs")
            except Exception as e:
                logger.error(f"Failed to process URL: {e}")
        
        consumer.close()
        results_consumer.close()
        
        # For this demo, return empty list since results go to Kafka topics
        # In real implementation, you'd collect from scraping-results topic
        return []

    def save_results(self, results: List[Dict], filename: str = "dask_scraping_results.csv"):
        """Save results to CSV."""
        if not results:
            logger.info("No results to save")
            return
        
        keys = ["genre", "track_name", "artist_name", "album", "duration", "listeners", "playcount", "track_url", "raw_html", "scraping_status"]
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Saved {len(results)} tracks to {filename}")

    def close(self):
        """Close resources."""
        if hasattr(self, 'client'):
            self.client.close()
        if hasattr(self, 'cluster'):
            self.cluster.close()
        if hasattr(self, 'kafka_coordinator'):
            self.kafka_coordinator.url_manager.stop_consumer()