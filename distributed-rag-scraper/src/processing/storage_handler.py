from pymongo import MongoClient
from typing import List, Dict
import logging
import time

logger = logging.getLogger(__name__)        #WHAT IS COMMENTED IS CODE FROM TASK2  COLLECTING RAW DATA

class MongoDBStorage:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "rag_scraper"):
        # self.client = MongoClient(connection_string)
        # self.db = self.client[db_name]
        # self.raw_data_collection = self.db["raw_scraped_data"]
        # logger.info(f"Connected to MongoDB database: {db_name}")
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ismaster')  # Test connection
            self.db = self.client[db_name]
            self.raw_data_collection = self.db["raw_scraped_data"]
            self.processed_data_collection = self.db["processed_tracks"]
            self.stats_collection = self.db["processing_stats"]
            logger.info(f"Connected to MongoDB database: {db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def store_raw_data(self, data: List[Dict]):
        """Store raw scraped data in MongoDB."""
        if not data:
            logger.warning("No data to store")
            return
        
        # try:
        #     result = self.raw_data_collection.insert_many(data)
        #     logger.info(f"Stored {len(result.inserted_ids)} documents in MongoDB")
        #     return result.inserted_ids
        # except Exception as e:
        #     logger.error(f"Failed to store data in MongoDB: {e}")
        #     return []
        try:
            # Add timestamp to each document
            for doc in data:
                doc['stored_at'] = time.time()
            
            result = self.raw_data_collection.insert_many(data)
            logger.info(f"Stored {len(result.inserted_ids)} raw documents in MongoDB")
            return result.inserted_ids
        except Exception as e:
            logger.error(f"Failed to store raw data in MongoDB: {e}")
            return []

    # def get_raw_data(self, query: Dict = None, limit: int = 100):
    #     """Retrieve raw data from MongoDB."""
    #     query = query or {}
    #     try:
    #         cursor = self.raw_data_collection.find(query).limit(limit)
    #         return list(cursor)
    #     except Exception as e:
    #         logger.error(f"Failed to retrieve data from MongoDB: {e}")
    #         return []
    def store_processed_data(self, data: List[Dict]):
        """Store processed and cleaned data in MongoDB."""
        if not data:
            logger.warning("No processed data to store")
            return
        
        try:
            # Add processing metadata
            for doc in data:
                doc['processed_at'] = time.time()
                doc['collection_type'] = 'processed_tracks'
            
            result = self.processed_data_collection.insert_many(data)
            
            # Update statistics
            self._update_processing_stats(len(result.inserted_ids))
            
            logger.info(f"Stored {len(result.inserted_ids)} processed documents in MongoDB")
            return result.inserted_ids
        except Exception as e:
            logger.error(f"Failed to store processed data in MongoDB: {e}")
            return []
    
    def _update_processing_stats(self, processed_count: int):
        """Update processing statistics."""
        try:
            stats_doc = {
                'timestamp': time.time(),
                'processed_count': processed_count,
                'type': 'batch_processing'
            }
            self.stats_collection.insert_one(stats_doc)
        except Exception as e:
            logger.error(f"Failed to update stats: {e}")
    
    def get_processed_data(self, query: Dict = None, limit: int = 100):
        """Retrieve processed data from MongoDB."""
        query = query or {}
        try:
            cursor = self.processed_data_collection.find(query).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to retrieve processed data: {e}")
            return []
    
    def get_processing_stats(self):
        """Get processing statistics."""
        try:
            stats = self.stats_collection.find().sort('timestamp', -1).limit(10)
            return list(stats)
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return []
    
    def create_indexes(self):
        """Create indexes for better query performance."""
        try:
            self.processed_data_collection.create_index([("genre", 1)])
            self.processed_data_collection.create_index([("artist_name", 1)])
            self.processed_data_collection.create_index([("listeners", -1)])
            self.processed_data_collection.create_index([("processed_at", -1)])
            logger.info("Created MongoDB indexes for better performance")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def close(self):
        """Close MongoDB connection."""
        self.client.close()