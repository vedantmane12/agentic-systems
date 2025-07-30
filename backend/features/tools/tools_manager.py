"""
Tools Manager
Central management for all tools (built-in and custom)
"""

from typing import Dict, Any, Optional, List
from .builtin import (
    SerperToolConfig,
    WebsiteSearchToolConfig,
    FileReadToolConfig,
    ScrapeWebsiteToolConfig
)
import logging

logger = logging.getLogger(__name__)


class ToolsManager:
    """Centralized manager for all tools"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tools manager
        
        Args:
            config: Optional configuration dictionary with tool-specific configs
        """
        self.config = config or {}
        self._builtin_configs = {}
        self._builtin_tools = {}
        self._custom_tools = {}
        self._initialize_builtin_tools()
        self._initialize_custom_tools()
    
    def _initialize_builtin_tools(self) -> None:
        """Initialize all built-in tool configurations"""
        try:
            # Initialize Serper tool
            serper_config = self.config.get('serper', {})
            self._builtin_configs['serper'] = SerperToolConfig(serper_config)
            
            # Initialize Website Search tool
            website_search_config = self.config.get('website_search', {})
            self._builtin_configs['website_search'] = WebsiteSearchToolConfig(website_search_config)
            
            # Initialize File Read tool
            file_read_config = self.config.get('file_read', {})
            self._builtin_configs['file_read'] = FileReadToolConfig(file_read_config)
            
            # Initialize Scrape Website tool
            scrape_website_config = self.config.get('scrape_website', {})
            self._builtin_configs['scrape_website'] = ScrapeWebsiteToolConfig(scrape_website_config)
            
            # Actually initialize the tools
            for name, config in self._builtin_configs.items():
                tool = config.initialize()
                if tool:
                    self._builtin_tools[name] = tool
                    
            logger.info(f"Initialized {len(self._builtin_tools)} built-in tools")
            
        except Exception as e:
            logger.error(f"Error initializing built-in tools: {str(e)}")
            raise
    
    def _initialize_custom_tools(self) -> None:
        """Initialize custom tools"""
        try:
            # Import the CrewAI-compatible version
            from .crewai_wrapper import AcademicAnalyzerTool
            
            # Add academic analyzer tool
            self._custom_tools['academic_analyzer'] = AcademicAnalyzerTool()
            
            logger.info(f"Initialized {len(self._custom_tools)} custom tools")
            
        except Exception as e:
            logger.error(f"Error initializing custom tools: {str(e)}")
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Get a specific tool by name
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            The tool instance or None if not found
        """
        # Check built-in tools first
        if tool_name in self._builtin_tools:
            return self._builtin_tools[tool_name]
        
        # Check custom tools
        if tool_name in self._custom_tools:
            return self._custom_tools[tool_name]
        
        return None
    
    def get_all_tools(self) -> Dict[str, Any]:
        """
        Get all available tools
        
        Returns:
            Dictionary of all tools (built-in and custom)
        """
        all_tools = {}
        all_tools.update(self._builtin_tools)
        all_tools.update(self._custom_tools)
        return all_tools
    
    def get_builtin_tools(self) -> Dict[str, Any]:
        """Get only built-in tools"""
        return self._builtin_tools.copy()
    
    def get_custom_tools(self) -> Dict[str, Any]:
        """Get only custom tools"""
        return self._custom_tools.copy()
    
    def get_tools_for_agent(self, agent_role: str) -> List[Any]:
        """
        Get appropriate tools for a specific agent role
        
        Args:
            agent_role: The role of the agent
            
        Returns:
            List of tools appropriate for the agent
        """
        # Define tool mappings for different agent roles
        role_tool_mapping = {
            'information_gatherer': [
                'serper', 
                'website_search', 
                'scrape_website',
                'academic_analyzer'
            ],
            'data_analyst': [
                'file_read',
                'academic_analyzer'
            ],
            'content_synthesizer': [
                'file_read'
            ],
            'research_coordinator': []  # Coordinator doesn't need tools directly
        }
        
        # Get tool names for the role
        tool_names = role_tool_mapping.get(agent_role.lower(), [])
        
        # Return the actual tool instances
        tools = []
        for name in tool_names:
            tool = self.get_tool(name)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"Tool '{name}' not available for agent role '{agent_role}'")
        
        return tools
    
    def get_tools_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed status of all tools
        
        Returns:
            Dictionary with status information for each tool
        """
        status = {}
        
        # Get built-in tools status
        for name, config in self._builtin_configs.items():
            status[name] = config.get_status()
        
        # Add custom tools status
        for name in self._custom_tools:
            status[name] = {
                'name': name,
                'type': 'custom',
                'available': True,
                'initialized': True
            }
        
        return status
    
    def validate_all_tools(self) -> Dict[str, Any]:
        """
        Validate all tools and their configurations
        
        Returns:
            Comprehensive validation results
        """
        results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'tool_validations': {}
        }
        
        # Validate each built-in tool
        for name, config in self._builtin_configs.items():
            validation = config.validate()
            results['tool_validations'][name] = validation
            
            if validation.get('warnings'):
                results['warnings'].extend(
                    [f"{name}: {w}" for w in validation['warnings']]
                )
            
            if validation.get('errors'):
                results['errors'].extend(
                    [f"{name}: {e}" for e in validation['errors']]
                )
                results['valid'] = False
        
        # Check if we have minimum required tools
        if len(self._builtin_tools) + len(self._custom_tools) == 0:
            results['errors'].append("No tools available. System cannot function.")
            results['valid'] = False
        
        # Check for critical tools
        critical_tools = ['website_search', 'file_read']
        for tool in critical_tools:
            if tool not in self._builtin_tools:
                results['warnings'].append(
                    f"Critical tool '{tool}' is not available. Some features may not work."
                )
        
        return results
    
    def get_tool_config(self, tool_name: str) -> Optional[Any]:
        """
        Get the configuration object for a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool configuration object or None
        """
        return self._builtin_configs.get(tool_name)
    
    def reload_tool(self, tool_name: str) -> bool:
        """
        Reload a specific tool
        
        Args:
            tool_name: Name of the tool to reload
            
        Returns:
            True if successful, False otherwise
        """
        if tool_name in self._builtin_configs:
            config = self._builtin_configs[tool_name]
            tool = config.initialize()
            if tool:
                self._builtin_tools[tool_name] = tool
                logger.info(f"Successfully reloaded tool: {tool_name}")
                return True
            else:
                logger.error(f"Failed to reload tool: {tool_name}")
                return False
        
        logger.warning(f"Tool '{tool_name}' not found for reload")
        return False


# Singleton instance
_tools_manager = None


def get_tools_manager(config: Optional[Dict[str, Any]] = None) -> ToolsManager:
    """
    Get or create the tools manager singleton
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        ToolsManager instance
    """
    global _tools_manager
    
    if _tools_manager is None:
        _tools_manager = ToolsManager(config)
    
    return _tools_manager


def reset_tools_manager() -> None:
    """Reset the tools manager singleton (mainly for testing)"""
    global _tools_manager
    _tools_manager = None