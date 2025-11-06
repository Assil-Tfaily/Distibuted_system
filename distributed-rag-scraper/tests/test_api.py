# tests/test_api.py
import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_KEY = "music-api-key-2024"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_api():
    print("🚀 Testing Music RAG API")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
    
    # Test 2: Get raw data
    print("2. Testing raw data endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/data/raw?limit=3", 
            headers=headers
        )
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   Count: {data.get('count')}")
        if data.get('data'):
            print(f"   Sample track: {data['data'][0].get('track_name', 'N/A')}\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
    
    # Test 3: Enhanced query
    print("3. Testing enhanced query...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/data/enhanced?query=rock music&n_results=3",
            headers=headers
        )
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   Sources used: {data.get('sources_used')}")
        print(f"   Confidence: {data.get('confidence')}")
        answer = data.get('answer', '')[:100] + "..." if data.get('answer') else "N/A"
        print(f"   Answer preview: {answer}\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
    
    # Test 4: Search
    print("4. Testing search...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/search?q=jazz&limit=3",
            headers=headers
        )
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   Results: {data.get('results_count')}")
        if data.get('results'):
            print(f"   Top result: {data['results'][0].get('track_name', 'N/A')}\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
    
    # Test 5: Stats
    print("5. Testing stats endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/stats", headers=headers)
        data = response.json()
        print(f"   Pipeline ready: {data.get('pipeline', {}).get('ready', 'N/A')}")
        print(f"   MongoDB docs: {data.get('mongodb', {}).get('total_documents', 'N/A')}\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")

if __name__ == "__main__":
    test_api()