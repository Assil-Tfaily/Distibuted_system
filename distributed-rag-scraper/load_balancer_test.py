import requests
import time

# Simulate multiple API instances
endpoints = [
    "http://localhost:8000",
    "http://localhost:8001", 
    "http://localhost:8002"
]

def test_load_balancing():
    print("🧪 Testing Load Balancing Concept")
    print("=" * 40)
    
    current = 0
    for i in range(10):
        # Round-robin load balancing
        endpoint = endpoints[current]
        current = (current + 1) % len(endpoints)
        
        try:
            response = requests.get(f"{endpoint}/health", timeout=5)
            print(f"Request {i+1}: {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"Request {i+1}: {endpoint} - Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_load_balancing()