from pymongo import MongoClient
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class MongoDBStorage:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "rag_scraper"):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.raw_data_collection = self.db["raw_scraped_data"]
        logger.info(f"Connected to MongoDB database: {db_name}")

    def store_raw_data(self, data: List[Dict]):
        """Store raw scraped data in MongoDB."""
        if not data:
            logger.warning("No data to store")
            return
        
        try:
            result = self.raw_data_collection.insert_many(data)
            logger.info(f"Stored {len(result.inserted_ids)} documents in MongoDB")
            return result.inserted_ids
        except Exception as e:
            logger.error(f"Failed to store data in MongoDB: {e}")
            return []

    def get_raw_data(self, query: Dict = None, limit: int = 100):
        """Retrieve raw data from MongoDB."""
        query = query or {}
        try:
            cursor = self.raw_data_collection.find(query).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to retrieve data from MongoDB: {e}")
            return []

    def close(self):
        """Close MongoDB connection."""
        self.client.close()