import logging
from src.processing.processing_pipeline import DataProcessingPipeline
from src.scraping.base_scraper import LastFMScraperBS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_data_processing():
    """Test the complete data processing pipeline."""
    print("🚀 Testing Data Processing Pipeline (Task 3)")
    
    # Step 1: Scrape some sample data
    print("\n1. Scraping sample data...")
    scraper = LastFMScraperBS()
    sample_genres = scraper.get_genres()[:2]  # Just 2 genres for testing
    
    raw_data = []
    for genre in sample_genres:
        tracks = scraper.get_tracks_from_genre(genre['url'], pages=1)
        for track in tracks[:5]:  # 5 tracks per genre
            details = scraper.extract_track_details(track['url'], genre['name'])
            raw_data.append(details)
    
    print(f"Scraped {len(raw_data)} raw records")
    
    # Step 2: Process through pipeline
    print("\n2. Running data processing pipeline...")
    pipeline = DataProcessingPipeline()
    
    result = pipeline.process_batch(raw_data)
    
    # Step 3: Test efficiency
    print("\n3. Testing processing efficiency...")
    pipeline.test_efficiency(sample_sizes=[5, 10, 20])
    
    # Step 4: Show results
    print("\n4. Processing Results:")
    print(f"   Input records: {result['metrics']['total_records']}")
    print(f"   Output records: {result['metrics']['successful_records']}")
    print(f"   Success rate: {result['metrics']['success_rate']:.1%}")
    print(f"   Output files created:")
    print(f"     - {result['output_files']['json']}")
    print(f"     - {result['output_files']['sqlite']}")
    
    print("\n✅ Task 3 - Data Processing Module completed successfully!")

if __name__ == "__main__":
    test_data_processing()