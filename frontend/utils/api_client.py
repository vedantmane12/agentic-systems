import httpx
import asyncio
from typing import Dict, Any, Optional

class SyncAPIClient:
    """Synchronous API client for direct research execution"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 600  # 10 minutes for synchronous research
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def execute_research_sync(self, query: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute research synchronously and return complete results
        
        Args:
            query: Research query
            config: Optional configuration
            
        Returns:
            Complete research results or error
        """
        try:
            payload = {"query": query}
            if config:
                payload["config"] = config
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/research/sync",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "data": result
                    }
                else:
                    error_detail = response.text
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {error_detail}"
                    }
                    
        except httpx.TimeoutException:
            return {
                "status": "error", 
                "error": "Research timeout - the query was too complex. Try a simpler query."
            }
        except httpx.HTTPError as e:
            return {"status": "error", "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "error": f"Unexpected error: {str(e)}"}
    
    async def get_recent_research(self) -> Dict[str, Any]:
        """Get recent research history"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/recent")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/metrics")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}