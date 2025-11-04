from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..models import RawDataResponse
from ..auth import security, rate_limiter
from ..database import db

router = APIRouter()

@router.get("/raw-data", response_model=List[RawDataResponse])
async def get_raw_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    url_filter: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Rate limiting
    client_id = credentials.credentials
    if rate_limiter.is_rate_limited(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Build query
    query = {}
    if url_filter:
        query["url"] = {"$regex": url_filter, "$options": "i"}
    
    # Fetch data from MongoDB
    cursor = db.db.raw_data.find(query).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    
    return [RawDataResponse(**doc) for doc in results]

@router.get("/raw-data/{data_id}", response_model=RawDataResponse)
async def get_raw_data_by_id(
    data_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    document = await db.db.raw_data.find_one({"_id": data_id})
    if not document:
        raise HTTPException(status_code=404, detail="Data not found")
    
    return RawDataResponse(**document)