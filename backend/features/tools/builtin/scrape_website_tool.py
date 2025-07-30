"""
Scrape Website Tool Configuration
"""

from typing import Optional, Dict, Any
from crewai_tools import ScrapeWebsiteTool
import logging

logger = logging.getLogger(__name__)


class ScrapeWebsiteToolConfig:
    """Configuration and initialization for ScrapeWebsiteTool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Scrape Website tool configuration
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.tool = None
        self._initialized = False
    
    def initialize(self) -> Optional[ScrapeWebsiteTool]:
        """
        Initialize the ScrapeWebsiteTool
        
        Returns:
            Initialized ScrapeWebsiteTool or None if initialization fails
        """
        if self._initialized and self.tool:
            return self.tool
        
        try:
            # ScrapeWebsiteTool configuration
            # Can add timeout, user agent, etc.
            
            self.tool = ScrapeWebsiteTool()
            
            self._initialized = True
            logger.info("ScrapeWebsiteTool initialized successfully")
            
            return self.tool
            
        except Exception as e:
            logger.error(f"Failed to initialize ScrapeWebsiteTool: {str(e)}")
            return None
    
    def get_tool(self) -> Optional[ScrapeWebsiteTool]:
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
            'name': 'ScrapeWebsiteTool',
            'initialized': self._initialized,
            'available': self.is_available(),
            'config': {
                'timeout': self.config.get('timeout', 30),
                **self.config
            }
        }
    
    def validate(self) -> Dict[str, Any]:
        """Validate the tool configuration"""
        result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        if not self.is_available():
            result['warnings'].append(
                "ScrapeWebsiteTool is not available. Web scraping functionality will be limited."
            )
        
        return result