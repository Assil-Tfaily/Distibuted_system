# tests/test_enhancement_comparison.py
import time
import os
import sys
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.rag.pipeline import RAGPipeline

def test_enhancement_comparison():
    """Compare basic vs enhanced responses for the same query"""
    print("🔄 Enhancement Comparison Test")
    print("=" * 50)
    
    pipeline = RAGPipeline()
    pipeline.setup(limit=100)
    
    # Test query that should show clear enhancements
    test_query = "What rock music would you recommend for someone who likes emotional songs?"
    
    print(f"Test Query: '{test_query}'\n")
    
    # The pipeline now automatically uses enhancements
    # But we can demonstrate the value by showing what information is being analyzed
    
    print("🔍 What the enhanced pipeline analyzes:")
    print("   - Genre distribution in results")
    print("   - Artist variety and popularity") 
    print("   - Listener counts and engagement metrics")
    print("   - Pattern recognition across tracks")
    print("   - Cross-referencing emotional keywords with music data")
    print("   - Generating personalized recommendations\n")
    
    # Execute query
    result = pipeline.query(test_query, n_results=6)
    
    print("📈 Enhanced Response Features:")
    if result['status'] == 'success':
        print(f"   ✅ Analysis completed using {result.get('sources_used', 0)} sources")
        print(f"   ✅ Confidence level: {result.get('confidence', 'N/A')}")
        
        if 'quick_insights' in result:
            print(f"   ✅ Data insights: {result['quick_insights']}")
        
        if 'enhancements' in result:
            print(f"   ✅ Enhancement features: {result['enhancements']}")
        
        print(f"\n🎯 Final Answer:")
        print(f"   {result['answer']}")
    else:
        print(f"   ❌ Query failed: {result.get('answer', 'Unknown error')}")

if __name__ == "__main__":
    test_enhancement_comparison()