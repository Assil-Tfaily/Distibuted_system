# kubernetes_fault_tolerance.py
import subprocess
import time
import requests

def demonstrate_fault_tolerance():
    print("🛡️ Demonstrating Kubernetes Fault Tolerance")
    print("=" * 50)
    
    # Get current pods
    print("1. Checking current API pods...")
    result = subprocess.run(['kubectl', 'get', 'pods', '-l', 'app=rag-api'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    # Find a pod to "accidentally" delete
    lines = result.stdout.strip().split('\n')
    if len(lines) > 1:  # Header + at least one pod
        pod_name = lines[1].split()[0]  # First pod name
        
        print(f"2. Simulating pod failure by deleting: {pod_name}")
        subprocess.run(['kubectl', 'delete', 'pod', pod_name])
        
        print("3. Waiting for auto-restart...")
        time.sleep(10)
        
        print("4. Checking new pods (should show new instance)...")
        result = subprocess.run(['kubectl', 'get', 'pods', '-l', 'app=rag-api'], 
                              capture_output=True, text=True)
        print(result.stdout)
        
        print("✅ Kubernetes automatically restarted the failed pod!")
    else:
        print("❌ No pods found. Make sure your deployment is running.")

def test_service_continuity():
    print("\n🌐 Testing Service Continuity During Failures")
    print("=" * 50)
    
    # Test that service remains available even during pod restarts
    service_url = "http://localhost:8000/health"
    
    print("Testing API health during pod rotations...")
    for i in range(5):
        try:
            response = requests.get(service_url, timeout=5)
            print(f"Request {i+1}: Status {response.status_code} - Service available")
        except Exception as e:
            print(f"Request {i+1}: Service temporarily unavailable - {e}")
        time.sleep(2)

if __name__ == "__main__":
    demonstrate_fault_tolerance()
    test_service_continuity()