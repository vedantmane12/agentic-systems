"""
Website Search Tool Configuration
"""

from typing import Optional, Dict, Any
from crewai_tools import WebsiteSearchTool
import logging

logger = logging.getLogger(__name__)


class WebsiteSearchToolConfig:
    """Configuration and initialization for WebsiteSearchTool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Website Search tool configuration
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.tool = None
        self._initialized = False
    
    def initialize(self) -> Optional[WebsiteSearchTool]:
        """
        Initialize the WebsiteSearchTool
        
        Returns:
            Initialized WebsiteSearchTool or None if initialization fails
        """
        if self._initialized and self.tool:
            return self.tool
        
        try:
            # WebsiteSearchTool doesn't require API keys
            # You can add custom configuration here if needed
            
            self.tool = WebsiteSearchTool()
            
            self._initialized = True
            logger.info("WebsiteSearchTool initialized successfully")
            
            return self.tool
            
        except Exception as e:
            logger.error(f"Failed to initialize WebsiteSearchTool: {str(e)}")
            return None
    
    def get_tool(self) -> Optional[WebsiteSearchTool]:
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
            'name': 'WebsiteSearchTool',
            'initialized': self._initialized,
            'available': self.is_available(),
            'config': self.config
        }
    
    def validate(self) -> Dict[str, Any]:
        """Validate the tool configuration"""
        result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # WebsiteSearchTool is generally always available
        if not self.is_available():
            result['errors'].append(
                "WebsiteSearchTool failed to initialize. This is a critical error."
            )
            result['valid'] = False
        
        return result