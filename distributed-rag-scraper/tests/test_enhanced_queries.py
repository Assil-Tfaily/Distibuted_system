# tests/test_enhanced_queries.py
import os
import sys
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.rag.pipeline import RAGPipeline
import json
import time

def test_enhanced_queries():
    print("🎵 Testing Enhanced RAG Pipeline")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = RAGPipeline()
    setup_result = pipeline.setup(limit=100)
    
    if not setup_result['ready']:
        print("❌ Pipeline not ready. Check MongoDB data.")
        return
    
    print("✅ Pipeline ready! Starting enhanced query tests...\n")
    
    # Test queries covering different aspects
    test_queries = [
        # Genre-based queries
        {
            "query": "Find me some rock music",
            "type": "genre_exploration",
            "expected": "genre analysis, popular tracks"
        },
        {
            "query": "What jazz artists do you have?",
            "type": "artist_discovery", 
            "expected": "artist lists, recommendations"
        },
        
        # Mood/context queries
        {
            "query": "Recommend emotional songs",
            "type": "mood_based",
            "expected": "emotional tracks, artist variety"
        },
        {
            "query": "What are good driving songs?",
            "type": "context_based",
            "expected": "energetic tracks, popular choices"
        },
        
        # Popularity-based queries
        {
            "query": "Show me popular tracks",
            "type": "popularity_focused",
            "expected": "high listener counts, trending artists"
        },
        {
            "query": "What's trending in electronic music?",
            "type": "trend_analysis",
            "expected": "genre insights, popular subgenres"
        },
        
        # Specific artist queries
        {
            "query": "Tell me about Jeff Buckley",
            "type": "artist_specific",
            "expected": "track details, genre information"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {test_case['type'].upper()}")
        print(f"   Query: '{test_case['query']}'")
        print(f"   Expected: {test_case['expected']}")
        print("-" * 40)
        
        try:
            # Execute query
            start_time = time.time()
            result = pipeline.query(test_case['query'], n_results=5)
            response_time = time.time() - start_time
            
            # Display results
            print(f"   Status: {result['status']}")
            print(f"   Response time: {response_time:.2f}s")
            print(f"   Sources used: {result.get('sources_used', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            
            # Enhanced features check
            if 'enhancements' in result:
                print(f"   Enhancements: {result['enhancements']}")
            
            if 'quick_insights' in result:
                print(f"   Quick Insights: {result['quick_insights']}")
            
            # Display answer (truncated for readability)
            answer = result['answer']
            if len(answer) > 300:
                answer = answer[:300] + "..."
            print(f"   Answer: {answer}")
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test pipeline status
    print(f"\n📊 Final Pipeline Status:")
    status = pipeline.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    test_enhanced_queries()