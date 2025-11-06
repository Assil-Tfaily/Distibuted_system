from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'scraping-urls',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    group_id=None  # 👈 no group means stateless consumer (always reads from start)
)

for message in consumer:
    print(f"Received message: {message.value.decode('utf-8')}")
