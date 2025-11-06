import logging
from typing import Dict, List
from src.rag.retriever import DataRetriever
from src.rag.llm_processor import LLMProcessor

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, llm_provider: str = "huggingface"):
        """
        Initialize RAG Pipeline.
        
        Args:
            llm_provider: "huggingface" (free, no install), "ollama" (free, needs install), or "openai" (paid)
        """
        self.retriever = DataRetriever()
        self.llm = LLMProcessor(provider=llm_provider)
        self.is_setup = False
        self.provider = llm_provider
        
        logger.info(f" RAG Pipeline initialized with {llm_provider.upper()} provider")

    def setup(self, limit: int = None) -> Dict:
        """Setup the RAG pipeline with data indexing."""
        try:
            print(f" Setting up RAG pipeline with {self.provider.upper()}...")
            
            # Index data
            index_result = self.retriever.index_data(limit)
            print(f" Indexing result: {index_result}")
            
            # Test LLM connection
            llm_ready = self.llm.test_connection()
            print(f" LLM Ready: {llm_ready}")
            
            if not llm_ready and self.provider == "ollama":
                print("\n⚠️  Ollama not ready. Quick setup:")
                print("   1. Download Ollama: https://ollama.ai")
                print("   2. Run: ollama pull llama3.2")
                print("   3. Ollama starts automatically\n")
            
            self.is_setup = True
            
            stats = self.retriever.get_stats()
            return {
                "status": "success",
                "indexed": index_result.get("indexed", 0),
                "llm_ready": llm_ready,
                "provider": self.provider,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return {"status": "error", "error": str(e)}

    def query(self, query: str, n_results: int = 5) -> Dict:
        """Process a query through the RAG pipeline."""
        if not self.is_setup:
            return {"error": "Pipeline not setup. Call setup() first."}
        
        try:
            # Step 1: Retrieve relevant documents
            print(f" Retrieving {n_results} relevant documents...")
            context_docs = self.retriever.search(query, n_results)
            print(f" Retrieved {len(context_docs)} documents")
            
            # Step 2: Generate AI-enhanced answer
            print(f" Generating AI response with {self.provider.upper()}...")
            result = self.llm.generate_answer(query, context_docs)
            
            # Add retrieval info to result
            result["retrieved_docs"] = len(context_docs)
            result["query"] = query
            result["provider"] = self.provider
            
            return result
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"error": str(e), "answer": f"Error processing query: {e}"}

    def get_status(self) -> Dict:
        """Get pipeline status."""
        stats = self.retriever.get_stats()
        llm_ready = self.llm.test_connection()
        
        return {
            "setup_complete": self.is_setup,
            "llm_provider": self.provider,
            "llm_ready": llm_ready,
            "stats": stats
        }