import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scraper.distributed_lastfm_scraper import DistributedLastFMScraper
from database.mongodb_client import MongoDBClient
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Initialize components
    scraper = DistributedLastFMScraper(num_workers=4)
    db_client = MongoDBClient()
    
    # Define genres to scrape
    target_genres = ["Rock", "Jazz", "Hip-Hop", "Indie", "80s", "Dance", "Classical"]
    
    print("Starting distributed LastFM music scraping...")
    print(f"Target genres: {target_genres}")
    print(f"Workers: 4")
    
    if db_client.use_fallback:
        print("⚠️  MongoDB not available, using file-based storage")
    else:
        print("✅ Connected to MongoDB")
    
    try:
        # Start distributed scraping
        results = scraper.scrape_music_data(
            genres=target_genres,
            max_tracks_per_genre=30,  # Reduced for testing
            pages_per_genre=2
        )
        
        # Store results
        successful_scrapes = 0
        for result in results:
            if result.get('status') == 'success':
                db_client.insert_scraped_data(result)
                successful_scrapes += 1
        
        print(f"\nScraping completed!")
        print(f"Successfully scraped: {successful_scrapes} tracks")
        print(f"Total in storage: {db_client.get_data_count()} documents")
        
        # Save results to file for inspection
        with open('music_scraping_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print("Results saved to 'music_scraping_results.json'")
        
        # Show sample of scraped data
        sample_data = db_client.get_scraped_data(limit=5)
        print("\nSample of scraped music data:")
        for i, item in enumerate(sample_data):
            print(f"{i+1}. {item.get('track_name', 'N/A')} - {item.get('artist_name', 'N/A')}")
            print(f"   Genre: {item.get('genre', 'N/A')}, Album: {item.get('album', 'N/A')}")
            print(f"   Duration: {item.get('duration', 'N/A')}, Listeners: {item.get('listeners', 'N/A')}")
            print()
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()