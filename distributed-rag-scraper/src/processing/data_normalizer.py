import json
import sqlite3
from typing import Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataNormalizer:
    """Convert data to structured formats (JSON/SQL)."""
    
    def __init__(self):
        self.schema = {
            'tracks': {
                'genre': 'TEXT',
                'track_name': 'TEXT',
                'artist_name': 'TEXT', 
                'album': 'TEXT',
                'duration': 'TEXT',
                'duration_seconds': 'INTEGER',
                'listeners': 'INTEGER',
                'playcount': 'INTEGER',
                'track_url': 'TEXT',
                'scraping_status': 'TEXT',
                'processed_at': 'TEXT',
                'cleaned_text': 'TEXT'
            }
        }
    
    def to_json(self, data: List[Dict], output_file: str = None) -> str:
        """Convert data to JSON format."""
        try:
            # Remove MongoDB ObjectId and other non-serializable objects
            serializable_data = []
            for record in data:
                serializable_record = {}
                for key, value in record.items():
                    # Skip MongoDB ObjectId and other non-serializable types
                    if key == '_id':
                        continue
                    try:
                        json.dumps(value)  # Test if serializable
                        serializable_record[key] = value
                    except (TypeError, OverflowError):
                        # Convert non-serializable values to string
                        serializable_record[key] = str(value)
                serializable_data.append(serializable_record)
            
            json_data = json.dumps(serializable_data, indent=2, ensure_ascii=False)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                logger.info(f"JSON data saved to {output_file}")
            
            return json_data
        
        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            return ""
    
    def to_sqlite(self, data: List[Dict], db_path: str = "music_data.db") -> str:
        """Store data in SQLite database."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create table
            table_name = 'tracks'
            columns = self.schema[table_name]
            column_defs = ', '.join([f"{col} {dtype}" for col, dtype in columns.items()])
            
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(f"CREATE TABLE {table_name} ({column_defs})")
            
            # Insert data
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns.keys())
            
            for record in data:
                values = [record.get(col) for col in columns.keys()]
                cursor.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", values)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Data stored in SQLite database: {db_path}")
            return db_path
        
        except Exception as e:
            logger.error(f"Error storing in SQLite: {e}")
            return ""
    
    def to_structured_json(self, data: List[Dict]) -> Dict[str, Any]:
        """Create structured JSON with metadata."""
        structured_data = {
            "metadata": {
                "total_records": len(data),
                "processed_at": datetime.utcnow().isoformat(),
                "source": "LastFM Scraper",
                "version": "1.0"
            },
            "statistics": {
                "unique_genres": len(set(record.get('genre', '') for record in data)),
                "unique_artists": len(set(record.get('artist_name', '') for record in data)),
                "total_listeners": sum(record.get('listeners', 0) for record in data),
                "total_playcount": sum(record.get('playcount', 0) for record in data)
            },
            "records": data
        }
        
        return structured_data