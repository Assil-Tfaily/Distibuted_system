# kafka_task_demo.py
from kafka import KafkaProducer, KafkaConsumer
import json
import threading
import time
from datetime import datetime

class TaskDistributor:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
    def send_scraping_task(self, task_type, data):
        task = {
            "task_id": f"task_{int(time.time())}",
            "type": task_type,
            "data": data,
            "timestamp": str(datetime.now()),
            "status": "pending"
        }
        self.producer.send('scraping-tasks', task)
        print(f"📨 Sent task: {task['task_id']} - {task_type}")
        return task['task_id']

class TaskWorker:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.consumer = KafkaConsumer(
            'scraping-tasks',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='scraper-workers'
        )
        
    def start_consuming(self):
        print(f"👷 Worker {self.worker_id} started listening for tasks...")
        for message in self.consumer:
            task = message.value
            print(f"🔧 Worker {self.worker_id} processing: {task['task_id']}")
            
            # Simulate task processing
            time.sleep(2)
            
            # Mark task as completed
            task['status'] = 'completed'
            task['processed_by'] = f'worker_{self.worker_id}'
            task['completed_at'] = str(datetime.now())
            
            print(f"✅ Worker {self.worker_id} completed: {task['task_id']}")

def demonstrate_kafka_distribution():
    print("🚀 Demonstrating Kafka Task Distribution")
    print("=" * 50)
    
    # Start worker in background thread
    worker = TaskWorker(1)
    worker_thread = threading.Thread(target=worker.start_consuming, daemon=True)
    worker_thread.start()
    
    time.sleep(2)  # Let worker start
    
    # Create distributor and send tasks
    distributor = TaskDistributor()
    
    tasks = [
        ("scrape_artist", {"artist": "Jeff Buckley", "genre": "rock"}),
        ("scrape_genre", {"genre": "jazz", "limit": 50}),
        ("scrape_popular", {"timeframe": "weekly", "limit": 10}),
        ("update_metadata", {"action": "refresh_listeners"}),
        ("analyze_trends", {"metric": "genre_popularity"})
    ]
    
    print("Sending tasks to Kafka...")
    for task_type, data in tasks:
        distributor.send_scraping_task(task_type, data)
        time.sleep(1)
    
    print("\n🎯 Tasks distributed via Kafka! Check worker logs above.")
    print("This demonstrates dynamic task distribution across multiple workers.")

if __name__ == "__main__":
    demonstrate_kafka_distribution()