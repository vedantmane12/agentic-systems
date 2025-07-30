"""
CrewAI Tool Wrapper
Wraps LangChain tools to be compatible with CrewAI
"""

from crewai_tools import BaseTool
from typing import Any, Type, Optional
from pydantic import BaseModel, Field
import json


class AcademicAnalyzerInput(BaseModel):
    """Input schema for Academic Analyzer"""
    url: str = Field(description="URL of the source")
    title: str = Field(description="Title of the source")
    content: str = Field(description="Content to analyze")


class AcademicAnalyzerTool(BaseTool):
    """CrewAI-compatible Academic Analyzer Tool"""
    
    name: str = "Academic Source Analyzer"
    description: str = """Analyze an academic or research source for credibility, bias, and quality.
    Use this tool to evaluate sources found during research."""
    args_schema: Type[BaseModel] = AcademicAnalyzerInput
    
    def _run(self, url: str, title: str, content: str) -> str:
        """Execute the academic analyzer"""
        # Import here to avoid circular imports
        from .academic_analyzer import analyze_academic_source
        
        # Create JSON input as expected by the original tool
        query_json = json.dumps({
            'url': url,
            'title': title,
            'content': content
        })
        
        # Call the original tool
        return analyze_academic_source(query_json)