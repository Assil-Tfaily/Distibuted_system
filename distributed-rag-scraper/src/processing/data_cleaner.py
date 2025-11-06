import re
import json
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    """Clean and normalize scraped data."""
    
    def __init__(self):
        self.clean_patterns = [
            (r'\s+', ' '),  # Multiple whitespace to single space
            (r'\n+', ' '),  # Multiple newlines to space
            (r'\t+', ' '),  # Multiple tabs to space
            (r'[^\x00-\x7F]+', ' '),  # Remove non-ASCII characters
        ]
    
    def clean_html_content(self, raw_html: str) -> str:
        """Remove HTML tags, scripts, and styles from raw HTML."""
        if not raw_html or raw_html == "N/A":
            return ""
        
        try:
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()
            
            # Get clean text
            text = soup.get_text()
            
            # Apply cleaning patterns
            for pattern, replacement in self.clean_patterns:
                text = re.sub(pattern, replacement, text)
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            return ""
    
    def normalize_track_data(self, track_data: Dict) -> Dict:
        """Normalize track data structure and values."""
        normalized = track_data.copy()
        
        # Clean text fields
        text_fields = ['track_name', 'artist_name', 'album', 'genre']
        for field in text_fields:
            if field in normalized:
                normalized[field] = self.clean_text_field(normalized[field])
        
        # Normalize numeric fields
        if 'listeners' in normalized:
            normalized['listeners'] = self.normalize_number(normalized['listeners'])
        
        if 'playcount' in normalized:
            normalized['playcount'] = self.normalize_number(normalized['playcount'])
        
        # Normalize duration
        if 'duration' in normalized:
            normalized['duration_seconds'] = self.normalize_duration(normalized['duration'])
        
        # Add timestamp
        normalized['processed_at'] = self.get_current_timestamp()
        
        # Clean HTML content
        if 'raw_html' in normalized:
            normalized['cleaned_text'] = self.clean_html_content(normalized['raw_html'])
            # Remove raw HTML to save space (optional)
            # del normalized['raw_html']
        
        return normalized
    
    def clean_text_field(self, text: str) -> str:
        """Clean and normalize text fields."""
        if not text or text == "N/A":
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def normalize_number(self, number_str: str) -> int:
        """Convert number strings to integers."""
        if not number_str or number_str == "N/A":
            return 0
        
        try:
            # Remove commas and spaces
            cleaned = re.sub(r'[,\s]', '', number_str)
            return int(cleaned)
        except (ValueError, TypeError):
            logger.warning(f"Could not normalize number: {number_str}")
            return 0
    
    def normalize_duration(self, duration_str: str) -> int:
        """Convert duration string to seconds."""
        if not duration_str or duration_str == "N/A":
            return 0
        
        try:
            if ':' in duration_str:
                parts = duration_str.split(':')
                if len(parts) == 2:  # MM:SS
                    return int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:  # HH:MM:SS
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return 0
        except (ValueError, TypeError):
            logger.warning(f"Could not normalize duration: {duration_str}")
            return 0
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def batch_clean_data(self, data_batch: List[Dict]) -> List[Dict]:
        """Clean a batch of data records."""
        cleaned_batch = []
        
        for record in data_batch:
            try:
                cleaned_record = self.normalize_track_data(record)
                cleaned_batch.append(cleaned_record)
            except Exception as e:
                logger.error(f"Error cleaning record: {e}")
                continue
        
        logger.info(f"Cleaned {len(cleaned_batch)}/{len(data_batch)} records")
        return cleaned_batch