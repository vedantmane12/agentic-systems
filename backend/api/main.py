"""
Synchronous FastAPI Backend for Research Assistant
Direct request-response processing without background tasks
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging
import uuid
from datetime import datetime

# Add the backend directory to the path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from features.orchestration.research_crew import ResearchCrew

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Research Assistant API - Synchronous",
    description="AI-powered research assistant with synchronous processing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ResearchRequest(BaseModel):
    query: str
    config: Optional[Dict[str, Any]] = None

class ResearchResponse(BaseModel):
    success: bool
    query: str
    report: Dict[str, Any]
    sources: list
    metadata: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None

# Initialize research crew
research_crew = ResearchCrew()

# Store recent research for metrics
recent_research = []

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Research Assistant API - Synchronous Mode",
        "version": "1.0.0",
        "mode": "synchronous",
        "endpoints": {
            "POST /research/sync": "Execute research synchronously",
            "GET /health": "Health check",
            "GET /recent": "Get recent research"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "synchronous",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "serper_configured": bool(os.getenv("SERPER_API_KEY"))
        }
    }

@app.post("/research/sync", response_model=ResearchResponse)
async def execute_research_sync(request: ResearchRequest):
    """
    Execute research synchronously and return complete results
    
    Args:
        request: Research request with query and optional config
        
    Returns:
        Complete research results
    """
    # Validate request
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    logger.info(f"Starting synchronous research for: {request.query}")
    start_time = datetime.now()
    
    try:
        # Configure crew if needed
        if request.config:
            crew = ResearchCrew(request.config)
        else:
            crew = research_crew
        
        # Execute research synchronously
        result = crew.execute_research(request.query)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Ensure result has all required fields
        if not result.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=f"Research failed: {result.get('error', 'Unknown error')}"
            )
        
        # Add to recent research
        research_record = {
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "success": result.get('success', False)
        }
        recent_research.append(research_record)
        
        # Keep only last 10 records
        if len(recent_research) > 10:
            recent_research.pop(0)
        
        logger.info(f"Research completed successfully in {execution_time:.2f}s")
        
        return ResearchResponse(
            success=result['success'],
            query=result['query'],
            report=result['report'],
            sources=result['sources'],
            metadata=result['metadata'],
            execution_time=result['execution_time']
        )
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Research failed: {str(e)}")
        
        # Add failed research to records
        research_record = {
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "success": False,
            "error": str(e)
        }
        recent_research.append(research_record)
        
        raise HTTPException(
            status_code=500,
            detail=f"Research execution failed: {str(e)}"
        )

@app.get("/recent")
async def get_recent_research():
    """Get recent research history"""
    return {
        "count": len(recent_research),
        "research": recent_research
    }

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    if not recent_research:
        return {
            "total_research": 0,
            "success_rate": 0,
            "avg_execution_time": 0
        }
    
    successful = [r for r in recent_research if r.get('success')]
    total = len(recent_research)
    
    avg_time = sum(r.get('execution_time', 0) for r in recent_research) / total
    
    return {
        "total_research": total,
        "successful": len(successful),
        "failed": total - len(successful),
        "success_rate": (len(successful) / total) * 100,
        "avg_execution_time": round(avg_time, 2)
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    print("🚀 Starting Synchronous Research Assistant API...")
    print(f"📡 Server will run on: http://{host}:{port}")
    print("📝 Endpoint: POST /research/sync")
    
    # Run the server
    uvicorn.run(
        "main_sync:app",
        host=host,
        port=port,
        reload=True
    )