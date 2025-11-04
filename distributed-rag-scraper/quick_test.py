from src.scraping.base_scraper import LastFMScraperBS
import logging

def quick_test():
    """Run a quick test with minimal data."""
    logging.basicConfig(level=logging.INFO)
    
    print("=== QUICK SCRAPER TEST ===")
    scraper = LastFMScraperBS(output_csv="quick_test_results.csv")
    
    # Test with just 1 genre and 2 tracks
    scraper.run(
        genre_names=["Rock"],      # Just one genre
        max_tracks_per_genre=3,    # Just 3 tracks
        pages=1                    # Just 1 page
    )
    
    # Check results
    import pandas as pd
    try:
        df = pd.read_csv("quick_test_results.csv")
        print(f"\n=== RESULTS ===")
        print(f"Total records: {len(df)}")
        good_records = df[(df['track_name'] != 'N/A') & (df['artist_name'] != 'N/A')]
        print(f"Good records: {len(good_records)}")
        
        if len(good_records) > 0:
            print("\nSample results:")
            for i, row in good_records.iterrows():
                print(f"  - {row['track_name']} by {row['artist_name']}")
        else:
            print("No good records found. Check the failed_urls.txt file for issues.")
            
    except Exception as e:
        print(f"Error reading results: {e}")

if __name__ == "__main__":
    quick_test()