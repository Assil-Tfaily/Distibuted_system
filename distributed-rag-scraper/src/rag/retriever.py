from typing import List, Dict
from src.rag.vector_store import VectorStore
from src.processing.storage_handler import MongoDBStorage
import logging

logger = logging.getLogger(__name__)

class DataRetriever:
    def __init__(self):
        self.mongo = MongoDBStorage()
        self.vector_store = VectorStore()
    
    def index_data(self, limit: int = None) -> Dict:
        """Index data from MongoDB."""
        try:
            # Use the correct collection name from your storage handler
            docs = list(self.mongo.raw_data_collection.find().limit(limit or 0))
            if not docs:
                return {"status": "no_data", "indexed": 0}
            
            indexed_count = self.vector_store.add_documents(docs)
            return {"status": "success", "indexed": indexed_count}
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant documents."""
        try:
            return self.vector_store.search(query, n_results)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get basic statistics."""
        try:
            return {
                "mongodb_docs": self.mongo.raw_data_collection.count_documents({}),
                "vector_docs": self.vector_store.get_collection_stats().get("total_documents", 0)
            }
        except Exception as e:
            logger.error(f"Stats failed: {e}")
            return {"mongodb_docs": 0, "vector_docs": 0}
