
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        try:
            self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection(
                name="music_tracks"
            )
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Vector store init failed: {e}")
            raise
    
    def add_documents(self, documents: List[Dict]) -> int:
        """Add documents to vector store."""
        try:
            ids, embeddings, texts, metadatas = [], [], [], []
            
            for i, doc in enumerate(documents):
                text = self._doc_to_text(doc)
                embedding = self.embedding_model.encode(text).tolist()
                
                ids.append(f"doc_{i}")
                embeddings.append(embedding)
                texts.append(text)
                # Store metadata for better retrieval
                metadatas.append({
                    'track_name': doc.get('track_name', 'Unknown'),
                    'artist_name': doc.get('artist_name', 'Unknown'),
                    'genre': doc.get('genre', 'Unknown'),
                    'listeners': doc.get('listeners', 'Unknown')
                })
            
            self.collection.add(
                ids=ids, 
                embeddings=embeddings, 
                documents=texts,
                metadatas=metadatas
            )
            logger.info(f"Added {len(ids)} documents to vector store")
            return len(ids)
        except Exception as e:
            logger.error(f"Add documents failed: {e}")
            return 0
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search similar documents."""
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['metadatas', 'documents', 'distances']
            )
            
            # Convert results to simple format
            docs = []
            for i in range(len(results['ids'][0])):
                docs.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'distance': results['distances'][0][i],
                    'track_name': results['metadatas'][0][i].get('track_name', 'Unknown'),
                    'artist_name': results['metadatas'][0][i].get('artist_name', 'Unknown'),
                    'genre': results['metadatas'][0][i].get('genre', 'Unknown'),
                    'listeners': results['metadatas'][0][i].get('listeners', 'Unknown')
                })
            
            return docs
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _doc_to_text(self, doc: Dict) -> str:
        """Convert document to text for embedding."""
        parts = []
        if doc.get('track_name'): parts.append(f"Track: {doc['track_name']}")
        if doc.get('artist_name'): parts.append(f"Artist: {doc['artist_name']}")
        if doc.get('genre'): parts.append(f"Genre: {doc['genre']}")
        if doc.get('listeners'): parts.append(f"Listeners: {doc['listeners']}")
        return ", ".join(parts)
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        try:
            return {"total_documents": self.collection.count()}
        except:
            return {"total_documents": 0}
