import time
import logging
from typing import List, Dict
from .data_cleaner import DataCleaner
from .data_normalizer import DataNormalizer
from .storage_handler import MongoDBStorage

logger = logging.getLogger(__name__)

class DataProcessingPipeline:
    """Complete data processing pipeline."""
    
    def __init__(self):
        self.cleaner = DataCleaner()
        self.normalizer = DataNormalizer()
        self.storage = MongoDBStorage()
        
    def process_batch(self, raw_data: List[Dict], test_mode: bool = False) -> Dict:
        """Process a batch of raw data through the entire pipeline."""
        start_time = time.time()
        
        logger.info(f"Starting pipeline processing for {len(raw_data)} records")
        
        # Step 1: Data Cleaning
        cleaning_start = time.time()
        cleaned_data = self.cleaner.batch_clean_data(raw_data)
        cleaning_time = time.time() - cleaning_start
        
        # Step 2: Data Storage (NoSQL)
        storage_start = time.time()
        if not test_mode:
            stored_ids = self.storage.store_processed_data(cleaned_data)
        storage_time = time.time() - storage_start
        
        # Step 3: Data Normalization
        normalization_start = time.time()
        structured_data = self.normalizer.to_structured_json(cleaned_data)
        
        # Generate multiple output formats
        json_output = self.normalizer.to_json(cleaned_data, "processed_data.json")
        sqlite_path = self.normalizer.to_sqlite(cleaned_data, "music_data.db")
        normalization_time = time.time() - normalization_start
        
        total_time = time.time() - start_time
        
        # Performance metrics
        metrics = {
            "total_records": len(raw_data),
            "successful_records": len(cleaned_data),
            "processing_time_total": total_time,
            "cleaning_time": cleaning_time,
            "storage_time": storage_time,
            "normalization_time": normalization_time,
            "records_per_second": len(cleaned_data) / total_time if total_time > 0 else 0,
            "success_rate": len(cleaned_data) / len(raw_data) if len(raw_data) > 0 else 0
        }
        
        logger.info(f"Pipeline completed: {metrics}")
        
        return {
            "metrics": metrics,
            "cleaned_data": cleaned_data,
            "structured_data": structured_data,
            "output_files": {
                "json": "processed_data.json",
                "sqlite": sqlite_path
            }
        }
    
    def test_efficiency(self, sample_sizes: List[int] = [10, 50, 100]):
        """Test processing efficiency with different sample sizes."""
        logger.info("Starting efficiency tests with different sample sizes")
        
        # Get some sample data
        sample_data = self.storage.get_processed_data(limit=max(sample_sizes))
        
        if not sample_data:
            logger.warning("No sample data available for testing")
            return
        
        results = {}
        
        for size in sample_sizes:
            if size > len(sample_data):
                logger.warning(f"Sample size {size} exceeds available data ({len(sample_data)})")
                continue
            
            test_batch = sample_data[:size]
            logger.info(f"Testing with sample size: {size}")
            
            result = self.process_batch(test_batch, test_mode=True)
            results[size] = result["metrics"]
        
        # Print efficiency report
        self._print_efficiency_report(results)
        return results
    
    def _print_efficiency_report(self, results: Dict):
        """Print a formatted efficiency report."""
        print("\n" + "="*50)
        print("DATA PROCESSING EFFICIENCY REPORT")
        print("="*50)
        
        for size, metrics in results.items():
            print(f"\nSample Size: {size} records")
            print(f"  Total Time: {metrics['processing_time_total']:.2f}s")
            print(f"  Cleaning Time: {metrics['cleaning_time']:.2f}s")
            print(f"  Storage Time: {metrics['storage_time']:.2f}s")
            print(f"  Normalization Time: {metrics['normalization_time']:.2f}s")
            print(f"  Records/Second: {metrics['records_per_second']:.2f}")
            print(f"  Success Rate: {metrics['success_rate']:.1%}")
        
        print("\n" + "="*50)