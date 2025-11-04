import pandas as pd
import json
from typing import Dict, List

def analyze_data_quality(filename: str) -> Dict:
    """Analyze the quality of scraped data."""
    print(f"\n=== ANALYZING {filename} ===")
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filename)
        elif filename.endswith('.json'):
            with open(filename, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        else:
            print(f"Unsupported file format: {filename}")
            return {}
        
        print(f"Total records: {len(df)}")
        
        # Data completeness analysis
        completeness = {}
        for column in df.columns:
            non_na_count = df[column].notna().sum()
            na_count = len(df) - non_na_count
            completeness[column] = {
                'non_na': non_na_count,
                'na': na_count,
                'completeness_percent': (non_na_count / len(df)) * 100
            }
            print(f"{column}: {non_na_count}/{len(df)} ({completeness[column]['completeness_percent']:.1f}%) complete")
        
        # Check for "N/A" values
        na_values_count = {}
        for column in df.columns:
            if df[column].dtype == 'object':
                na_count = (df[column] == 'N/A').sum()
                na_values_count[column] = na_count
                if na_count > 0:
                    print(f"  - {na_count} 'N/A' values in {column}")
        
        # Sample of good records
        good_records = df[(df['track_name'] != 'N/A') & (df['artist_name'] != 'N/A')]
        print(f"\nGood records (has track and artist): {len(good_records)}")
        
        if len(good_records) > 0:
            print("\nSample of good records:")
            for i, (idx, row) in enumerate(good_records.head(3).iterrows()):
                print(f"  {i+1}. {row['track_name']} - {row['artist_name']} ({row['genre']})")
        
        return {
            'total_records': len(df),
            'good_records': len(good_records),
            'completeness': completeness,
            'na_values': na_values_count
        }
    
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")
        return {}

def check_all_results():
    """Check all result files."""
    files_to_check = [
        'local_scraping_results.csv',
        'dask_scraping_results.csv',
        'multiprocessing_scraping_results.csv',
        'test_scraping_results.csv'
    ]
    
    summary = {}
    for file in files_to_check:
        try:
            result = analyze_data_quality(file)
            summary[file] = result
        except FileNotFoundError:
            print(f"\n{file} not found (skipping)")
        except Exception as e:
            print(f"\nError processing {file}: {e}")
    
    # Summary
    print("\n=== OVERALL SUMMARY ===")
    for file, stats in summary.items():
        if stats:
            good_pct = (stats['good_records'] / stats['total_records'] * 100) if stats['total_records'] > 0 else 0
            print(f"{file}: {stats['good_records']}/{stats['total_records']} good records ({good_pct:.1f}%)")

if __name__ == "__main__":
    check_all_results()