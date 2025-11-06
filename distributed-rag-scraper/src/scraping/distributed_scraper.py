from dask.distributed import Client, LocalCluster
import time
from typing import List, Dict
from .base_scraper import LastFMScraperBS
from .url_manager import KafkaURLManager
import logging
import csv

logger = logging.getLogger(__name__)

def kafka_worker_process(url_batch: List[Dict]) -> List[Dict]:
    """Dask worker function that processes URLs from Kafka."""
    scraper = LastFMScraperBS()
    results = []
    
    for url_data in url_batch:
        try:
            details = scraper.extract_track_details(
                url_data['url'], 
                url_data['genre']
            )
            results.append(details)
            time.sleep(0.5)  # Rate limiting
            logger.info(f"Processed: {details.get('track_name')}")
        except Exception as e:
            logger.error(f"Failed to process URL {url_data['url']}: {e}")
            # Create error record
            error_data = {
                "genre": url_data.get('genre', 'Unknown'),
                "track_url": url_data.get('url', 'Unknown'),
                "track_name": url_data.get('track_name', 'Unknown'),
                "artist_name": "N/A",
                "album": "N/A", 
                "duration": "N/A",
                "listeners": "N/A",
                "playcount": "N/A",
                "raw_html": "N/A",
                "scraping_status": f"error: {str(e)}"
            }
            results.append(error_data)
    
    return results

def scrape_genre_worker(genre_data: Dict, max_tracks: int = 50, pages: int = 2) -> List[Dict]:
    """Traditional Dask worker function (without Kafka)."""
    worker_id = id(genre_data) % 1000
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
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Worker {worker_id} failed to extract track: {e}")
                continue
        
        logger.info(f"Worker {worker_id} completed {genre_data['name']}: {len(results)} tracks")
        return results
    except Exception as e:
        logger.error(f"Worker {worker_id} failed on genre {genre_data['name']}: {e}")
        return []

class DistributedScraper:
    def __init__(self, n_workers: int = 4):
        self.n_workers = n_workers
        self.cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1)
        self.client = Client(self.cluster)
        self.kafka_manager = KafkaURLManager()
        logger.info(f"Initialized Dask cluster with {n_workers} workers")

    def scrape_genres_kafka(self, genre_names: List[str] = None, max_tracks_per_genre: int = 50, pages: int = 2) -> List[Dict]:
        """Distributed scraping using Kafka for URL management and Dask for processing."""
        base_scraper = LastFMScraperBS()
        all_genres = base_scraper.get_genres()
        
        if genre_names:
            all_genres = [g for g in all_genres if g["name"].lower() in [x.lower() for x in genre_names]]
        
        logger.info(f"Generating URLs for {len(all_genres)} genres")
        
        # Generate all URLs and push to Kafka
        all_urls = []
        for genre in all_genres:
            tracks = base_scraper.get_tracks_from_genre(genre['url'], pages=pages)
            if max_tracks_per_genre:
                tracks = tracks[:max_tracks_per_genre]
            
            for track in tracks:
                url_data = {
                    'url': track['url'],
                    'genre': genre['name'],
                    'track_name': track['name'],
                    'type': 'track_details'
                }
                all_urls.append(url_data)
        
        # Submit all URLs to Kafka
        total_urls = self.kafka_manager.submit_urls(all_urls)
        logger.info(f"Submitted {total_urls} URLs to Kafka topic")
        
        # Process URLs from Kafka using Dask workers
        all_results = []
        processed_urls = 0
        batch_size = 5  # URLs per batch per worker
        
        while processed_urls < total_urls:
            # Get URL batch from Kafka
            url_batch = self.kafka_manager.get_url_batch('scraping-urls', batch_size=batch_size)
            
            if not url_batch:
                logger.info("No more URLs to process")
                break
            
            # Submit batch to Dask workers
            futures = []
            for i in range(0, len(url_batch), batch_size):
                batch = url_batch[i:i + batch_size]
                future = self.client.submit(kafka_worker_process, batch)
                futures.append(future)
            
            # Collect results
            for future in futures:
                try:
                    batch_results = future.result(timeout=300)
                    all_results.extend(batch_results)
                    processed_urls += len(batch_results)
                    logger.info(f"Progress: {processed_urls}/{total_urls} URLs processed")
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")
        
        logger.info(f"Kafka+Dask scraping completed. Total tracks: {len(all_results)}")
        return all_results

    def scrape_genres_dask(self, genre_names: List[str] = None, max_tracks_per_genre: int = 50, pages: int = 2) -> List[Dict]:
        """Traditional Dask distributed scraping without Kafka."""
        base_scraper = LastFMScraperBS()
        all_genres = base_scraper.get_genres()
        
        if genre_names:
            all_genres = [g for g in all_genres if g["name"].lower() in [x.lower() for x in genre_names]]
        
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
        
        all_results = []
        completed = 0
        for future in futures:
            try:
                result = future.result(timeout=300)
                all_results.extend(result)
                completed += 1
                logger.info(f"Progress: {completed}/{len(all_genres)} genres completed")
            except Exception as e:
                logger.error(f"Error getting result from worker: {e}")
        
        logger.info(f"Dask scraping completed. Total tracks: {len(all_results)}")
        return all_results

    def save_results(self, results: List[Dict], filename: str = "distributed_scraping_results.csv"):
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
        """Close Dask client and cluster."""
        self.client.close()
        self.cluster.close()