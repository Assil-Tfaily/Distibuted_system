from kafka import KafkaProducer
import json

class TaskDistributor:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    
    def send_scraping_task(self, url, priority="normal"):
        task = {
            "url": url,
            "priority": priority,
            "timestamp": str(datetime.now())
        }
        self.producer.send('scraping-tasks', task)
        print(f"📨 Sent task: {url}")

# Usage example
if __name__ == "__main__":
    distributor = TaskDistributor()
    distributor.send_scraping_task("https://www.last.fm/music/rock")