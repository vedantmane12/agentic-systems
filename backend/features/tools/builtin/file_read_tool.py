"""
File Read Tool Configuration
"""

from typing import Optional, Dict, Any
from crewai_tools import FileReadTool
import logging

logger = logging.getLogger(__name__)


class FileReadToolConfig:
    """Configuration and initialization for FileReadTool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize File Read tool configuration
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.tool = None
        self._initialized = False
    
    def initialize(self) -> Optional[FileReadTool]:
        """
        Initialize the FileReadTool
        
        Returns:
            Initialized FileReadTool or None if initialization fails
        """
        if self._initialized and self.tool:
            return self.tool
        
        try:
            # FileReadTool configuration options
            # You can add file type restrictions, size limits, etc.
            
            self.tool = FileReadTool()
            
            self._initialized = True
            logger.info("FileReadTool initialized successfully")
            
            return self.tool
            
        except Exception as e:
            logger.error(f"Failed to initialize FileReadTool: {str(e)}")
            return None
    
    def get_tool(self) -> Optional[FileReadTool]:
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
            'name': 'FileReadTool',
            'initialized': self._initialized,
            'available': self.is_available(),
            'config': {
                'supported_formats': ['.txt', '.pdf', '.docx', '.csv', '.json'],
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
        
        # FileReadTool is critical for many operations
        if not self.is_available():
            result['errors'].append(
                "FileReadTool failed to initialize. File processing will be unavailable."
            )
            result['valid'] = False
        
        return result