import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.database import db

def test_mongodb():
    print("🔗 Testing MongoDB connection...")
    
    if db.connect():
        # Test insert
        test_doc = {
            "url": "https://example.com",
            "title": "Test Document",
            "content": "This is a test document",
            "scraped_at": "2024-01-01T00:00:00Z"
        }
        
        result = db.db.raw_data.insert_one(test_doc)
        print(f"✅ Insert successful, ID: {result.inserted_id}")
        
        # Test read
        document = db.db.raw_data.find_one({"_id": result.inserted_id})
        print(f"✅ Read successful: {document['title']}")
        
        # Test delete
        db.db.raw_data.delete_one({"_id": result.inserted_id})
        print("✅ Delete successful")
        
        # List collections
        collections = db.db.list_collection_names()
        print(f"📁 Collections: {collections}")
        
        db.close()

if __name__ == "__main__":
    test_mongodb()