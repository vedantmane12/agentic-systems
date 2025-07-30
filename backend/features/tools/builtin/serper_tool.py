"""
Serper Web Search Tool Configuration
"""

import os
from typing import Optional, Dict, Any
from crewai_tools import SerperDevTool
import logging

logger = logging.getLogger(__name__)


class SerperToolConfig:
    """Configuration and initialization for SerperDevTool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Serper tool configuration
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.tool = None
        self._initialized = False
    
    def initialize(self) -> Optional[SerperDevTool]:
        """
        Initialize the SerperDevTool
        
        Returns:
            Initialized SerperDevTool or None if initialization fails
        """
        if self._initialized and self.tool:
            return self.tool
        
        try:
            # Get API key from config or environment
            api_key = self.config.get('api_key') or os.getenv('SERPER_API_KEY')
            
            if not api_key:
                logger.warning(
                    "SERPER_API_KEY not found. SerperDevTool will not be initialized. "
                    "Please set the SERPER_API_KEY environment variable or provide it in config."
                )
                return None
            
            # Get configuration parameters
            n_results = self.config.get('n_results', 10)
            
            # Initialize the tool
            self.tool = SerperDevTool(
                api_key=api_key,
                n_results=n_results
            )
            
            self._initialized = True
            logger.info(f"SerperDevTool initialized successfully with {n_results} max results")
            
            return self.tool
            
        except Exception as e:
            logger.error(f"Failed to initialize SerperDevTool: {str(e)}")
            return None
    
    def get_tool(self) -> Optional[SerperDevTool]:
        """
        Get the initialized tool
        
        Returns:
            The tool instance or None if not initialized
        """
        if not self._initialized:
            return self.initialize()
        return self.tool
    
    def is_available(self) -> bool:
        """Check if the tool is available and properly initialized"""
        return self.tool is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the tool"""
        return {
            'name': 'SerperDevTool',
            'initialized': self._initialized,
            'available': self.is_available(),
            'config': {
                'n_results': self.config.get('n_results', 10),
                'has_api_key': bool(self.config.get('api_key') or os.getenv('SERPER_API_KEY'))
            }
        }
    
    def validate(self) -> Dict[str, Any]:
        """Validate the tool configuration"""
        result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check API key
        if not (self.config.get('api_key') or os.getenv('SERPER_API_KEY')):
            result['warnings'].append(
                "SERPER_API_KEY not configured. Web search functionality will be unavailable."
            )
        
        # Check if tool is initialized
        if not self.is_available():
            result['warnings'].append(
                "SerperDevTool is not initialized. This may limit research capabilities."
            )
        
        return result