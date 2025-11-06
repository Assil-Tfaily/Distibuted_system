# tests/test_error_handling.py
import os
import sys
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.rag.pipeline import RAGPipeline

def test_error_handling():
    print("🚨 Testing Error Handling")
    print("=" * 40)
    
    pipeline = RAGPipeline()
    
    # Test 1: Query without setup
    print("1. Testing query without setup...")
    result = pipeline.query("test query")
    print(f"   Result: {result['status']} - {result['answer']}\n")
    
    # Test 2: Setup pipeline properly
    print("2. Setting up pipeline...")
    setup_result = pipeline.setup(limit=50)
    if setup_result['ready']:
        print("   ✅ Setup successful")
        
        # Test 3: Empty query
        print("3. Testing empty query...")
        result = pipeline.query("")
        print(f"   Result: {result['status']} - {result['answer']}\n")
        
        # Test 4: Query with no results
        print("4. Testing query with no results...")
        result = pipeline.query("xyz123 nonexistent track")
        print(f"   Result: {result['status']} - {result['answer']}\n")
        
        # Test 5: Normal query
        print("5. Testing normal query...")
        result = pipeline.query("rock music")
        print(f"   Result: {result['status']} - Sources: {result.get('sources_used', 0)}")
    
    else:
        print("   ❌ Setup failed")

if __name__ == "__main__":
    test_error_handling()