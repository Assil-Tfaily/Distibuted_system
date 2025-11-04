import requests
import json
import time
import os
import sys

# Add src to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

BASE_URL = "http://localhost:8000"
TOKEN = "your-test-token-here"

def test_health_check():
    """Test API health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ Health Check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_raw_data_endpoint():
    """Test raw data retrieval"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/api/v1/raw-data", headers=headers)
    print(f"📊 Raw Data Endpoint: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Retrieved {len(data)} documents")
        return True
    return False

def test_processed_data_endpoint():
    """Test processed data retrieval"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/api/v1/processed-data", headers=headers)
    print(f"🔧 Processed Data Endpoint: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Retrieved {len(data)} processed documents")
        return True
    return False

def test_search_endpoint():
    """Test search functionality"""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    search_data = {
        "query": "artificial intelligence",
        "limit": 5,
        "threshold": 0.7
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/search",
        headers=headers,
        json=search_data
    )
    print(f"🔍 Search Endpoint: {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        print(f"   Found {results['total_count']} results in {results['query_time']:.2f}s")
        return True
    return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    rate_limit_hit = False
    
    for i in range(65):  # Exceed rate limit (60 requests/min)
        response = requests.get(f"{BASE_URL}/api/v1/raw-data", headers=headers)
        if response.status_code == 429:
            print(f"🚫 Rate limit hit at request {i+1}")
            rate_limit_hit = True
            break
        time.sleep(0.1)
    
    return rate_limit_hit

def run_all_tests():
    """Run all API tests"""
    print("🚀 Starting API Tests...\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Raw Data Endpoint", test_raw_data_endpoint),
        ("Processed Data Endpoint", test_processed_data_endpoint),
        ("Search Endpoint", test_search_endpoint),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n📋 Test Summary:")
    print("-" * 40)
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    return all(success for _, success in results)

if __name__ == "__main__":
    run_all_tests()