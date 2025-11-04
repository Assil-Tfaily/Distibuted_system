from pymongo import MongoClient
from typing import Dict, List
import logging

class MongoDBClient:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "web_scraper"):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.raw_data_collection = self.db['raw_data']
    
    def insert_scraped_data(self, data: Dict):
        try:
            # Add unique index on URL to prevent duplicates
            self.raw_data_collection.create_index("url", unique=True)
            
            result = self.raw_data_collection.update_one(
                {"url": data['url']},
                {"$set": data},
                upsert=True
            )
            return result.upserted_id or data['url']
        except Exception as e:
            logging.error(f"Error inserting data: {e}")
            return None
    
    def get_scraped_data(self, filter_query: Dict = None, limit: int = 100):
        filter_query = filter_query or {}
        return list(self.raw_data_collection.find(filter_query).limit(limit))
    
    def get_data_count(self):
        return self.raw_data_collection.count_documents({})

if __name__ == "__main__":
    client = MongoDBClient()
    sample_data = {
        "url": "https://example.com",
        "title": "Example Domain",
        "content": "This domain is for use in illustrative examples...",
        "status": "success",
        "timestamp": 1698765432.123
    }
    
    client.insert_scraped_data(sample_data)
    print(f"Total documents: {client.get_data_count()}")