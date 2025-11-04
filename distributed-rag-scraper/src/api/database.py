import os
import pymongo

class MongoDB:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/rag_scraper")
        self.db_name = os.getenv("DB_NAME", "rag_scraper")
        self.client = None
        self.db = None
    
    def connect(self):
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            print("✅ MongoDB connection successful")
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def close(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

# Database instance
db = MongoDB()