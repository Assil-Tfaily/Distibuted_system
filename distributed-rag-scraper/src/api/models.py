from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RawDataResponse(BaseModel):
    id: str
    url: str
    title: str
    content: str
    scraped_at: datetime
    metadata: Dict[str, Any]

class ProcessedDataResponse(BaseModel):
    id: str
    raw_data_id: str
    cleaned_content: str
    structured_data: Dict[str, Any]
    processed_at: datetime
    summary: Optional[str] = None

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.7, ge=0.0, le=1.0)

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_count: int
    query_time: float

class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str]