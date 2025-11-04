from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..models import ProcessedDataResponse
from ..auth import security, rate_limiter
from ..database import db

router = APIRouter()

@router.get("/processed-data", response_model=List[ProcessedDataResponse])
async def get_processed_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    raw_data_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Rate limiting
    client_id = credentials.credentials
    if rate_limiter.is_rate_limited(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Build query
    query = {}
    if raw_data_id:
        query["raw_data_id"] = raw_data_id
    
    # Fetch data from MongoDB
    cursor = db.db.processed_data.find(query).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    
    return [ProcessedDataResponse(**doc) for doc in results]

@router.get("/processed-data/{data_id}", response_model=ProcessedDataResponse)
async def get_processed_data_by_id(
    data_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    document = await db.db.processed_data.find_one({"_id": data_id})
    if not document:
        raise HTTPException(status_code=404, detail="Processed data not found")
    
    return ProcessedDataResponse(**document)