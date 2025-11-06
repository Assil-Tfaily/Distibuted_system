# tests/test_pipeline_setup.py
import sys
import os
import logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from src.rag.pipeline import RAGPipeline


logging.basicConfig(level=logging.INFO)

def test_pipeline_setup():
    print("🧪 Testing Pipeline Setup")
    print("=" * 40)
    
    pipeline = RAGPipeline()
    setup_result = pipeline.setup(limit=50)  # Use small limit for testing
    
    print(f"✅ Pipeline initialized: {setup_result['ready']}")
    print(f"📊 Documents indexed: {setup_result.get('indexed', 0)}")
    print(f"🤖 LLM ready: {setup_result.get('llm_ready', False)}")
    print(f"🗄️ MongoDB docs: {setup_result.get('mongodb_docs', 0)}")
    
    return setup_result['ready']

if __name__ == "__main__":
    test_pipeline_setup()