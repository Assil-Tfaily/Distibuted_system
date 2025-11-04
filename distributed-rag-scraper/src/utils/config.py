import os
from typing import Dict, Any

class Config:
    # Scraping Configuration
    BASE_URL = "https://www.last.fm"
    DEFAULT_GENRES = ["Rock", "Jazz", "Hip-Hop", "Indie", "80s", "Dance", "Classical"]
    MAX_TRACKS_PER_GENRE = 100
    PAGES_PER_GENRE = 2
    
    # Distributed Computing
    RAY_NUM_WORKERS = int(os.getenv("RAY_NUM_WORKERS", "4"))
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    
    # MongoDB Configuration
    MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "rag_scraper")
    
    # Rate Limiting
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.5"))