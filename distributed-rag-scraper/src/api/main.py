from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import verify_token
from .endpoints import raw_data, processed_data, search

app = FastAPI(
    title="Distributed RAG Web Scraper API",
    description="API for accessing scraped and processed web data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(raw_data.router, prefix="/api/v1", tags=["raw-data"])
app.include_router(processed_data.router, prefix="/api/v1", tags=["processed-data"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])

@app.get("/")
async def root():
    return {"message": "Distributed RAG Web Scraper API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}