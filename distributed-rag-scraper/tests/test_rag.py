import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.rag.pipeline import RAGPipeline
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Less verbose
logger = logging.getLogger(__name__)

def test_rag(provider: str = "ollama"):
    """
    Test RAG pipeline with different LLM providers.
    
    Args:
        provider: "ollama" (free, local) or "openai" (paid, cloud)
    """
    print("\n" + "=" * 60)
    print(f"🎵 RAG Pipeline Test - Using {provider.upper()}")
    print("=" * 60 + "\n")
    
    try:
        # Initialize with chosen provider
        print(f" Initializing RAG Pipeline with {provider.upper()}...")
        pipeline = RAGPipeline(llm_provider=provider)
        
        print(" Setting up (indexing 10 documents)...")
        setup_result = pipeline.setup(limit=10)
        print(f" Setup complete: {setup_result}\n")
        
        if not setup_result.get("llm_ready"):
            print("  Warning: LLM not ready, will use fallback responses\n")
        
        # Test queries
        test_queries = [
            "What are some popular rock songs?",
            "Tell me about Coldplay tracks",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print("-" * 60)
            print(f" Query {i}/{len(test_queries)}: {query}")
            print("-" * 60)
            
            result = pipeline.query(query, n_results=3)
            
            print(f"\n Status: {result.get('status', 'unknown')}")
            print(f" Model: {result.get('model', 'unknown')}")
            print(f"\n Answer:\n{result['answer']}\n")
        
        # Show final stats
        print("=" * 60)
        print(" Pipeline Statistics")
        print("=" * 60)
        status = pipeline.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        print()
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RAG Pipeline")
    parser.add_argument(
        "--provider",
        choices=["huggingface", "ollama", "openai"],
        default="huggingface",
        help="LLM provider: huggingface (free, no install), ollama (free, needs install), or openai (paid)"
    )
    
    args = parser.parse_args()
    
    print(f"\n💡 Using {args.provider.upper()} provider")
    
    test_rag(provider=args.provider)