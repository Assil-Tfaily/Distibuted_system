import argparse
from src.scraping.base_scraper import LastFMScraperBS
from src.scraping.distributed_scraper import DistributedScraper  # Ray version
from src.processing.storage_handler import MongoDBStorage
import logging

logger = logging.getLogger(__name__)

def run_local_scraping():
    """Run the original local scraper."""
    scraper = LastFMScraperBS(output_csv="local_scraping_results.csv")
    scraper.run(
        genre_names=["Rock", "Jazz", "Hip-Hop", "Indie"],
        max_tracks_per_genre=50,
        pages=2
    )

def run_dask_scraping():
    """Run distributed scraping with Dask."""
    scraper = DistributedScraper(n_workers=2)  # Dask uses n_workers
    results = scraper.scrape_genres_dask(
        genre_names=["Rock", "Jazz", "Hip-Hop", "Indie"],
        max_tracks_per_genre=25,
        pages=2
    )
    scraper.save_results(results, "dask_scraping_results.csv")
    scraper.close()
    
    # Store in MongoDB
    try:
        storage = MongoDBStorage()
        storage.store_raw_data(results)
    except Exception as e:
        logger.warning(f"Could not store in MongoDB: {e}")

def run_kafka_dask_scraping():
    """Run distributed scraping with Kafka + Dask integration."""
    scraper = DistributedScraper(n_workers=2)
    results = scraper.scrape_genres_kafka(
        genre_names=["Rock", "Jazz", "Hip-Hop"],
        max_tracks_per_genre=20,
        pages=1
    )
    scraper.save_results(results, "kafka_dask_scraping_results.csv")
    scraper.close()
    
    # Store in MongoDB
    try:
        storage = MongoDBStorage()
        storage.store_raw_data(results)
    except Exception as e:
        logger.warning(f"Could not store in MongoDB: {e}")

def run_scrapy_spider():
    """Run Scrapy spider."""
    print("To run Scrapy spider, use: scrapy crawl lastfm -o scrapy_results.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run web scraping in different modes")
    parser.add_argument("--mode", choices=["local", "dask", "kafka_dask", "scrapy"], 
                       default="local", help="Scraping mode")
    
    args = parser.parse_args()
    
    if args.mode == "local":
        run_local_scraping()
    elif args.mode == "dask":
        run_dask_scraping()
    elif args.mode == "kafka_dask":
        run_kafka_dask_scraping()
    elif args.mode == "scrapy":
        run_scrapy_spider()