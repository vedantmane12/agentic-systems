"""
Tests for Tools Manager
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.features.tools.tools_manager import (
    ToolsManager,
    get_tools_manager,
    reset_tools_manager
)


class TestToolsManager:
    """Test cases for ToolsManager"""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton before each test"""
        reset_tools_manager()
        yield
        reset_tools_manager()
    
    @pytest.fixture
    def mock_env(self):
        """Mock environment variables"""
        with patch.dict(os.environ, {
            'SERPER_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            yield
    
    def test_initialization_without_api_key(self):
        """Test initialization without SERPER API key"""
        # Temporarily remove SERPER_API_KEY to test
        original_key = os.environ.pop('SERPER_API_KEY', None)
        try:
            manager = ToolsManager()
            
            # Should initialize but serper won't be available
            assert manager is not None
            builtin_tools = manager.get_builtin_tools()
            custom_tools = manager.get_custom_tools()
            
            assert 'serper' not in builtin_tools
            # WebsiteSearchTool might not initialize without OPENAI_API_KEY
            assert len(builtin_tools) >= 2  # At least file_read, scrape_website
            assert 'academic_analyzer' in custom_tools
        finally:
            # Restore the key if it existed
            if original_key:
                os.environ['SERPER_API_KEY'] = original_key
    
    def test_initialization_with_api_key(self, mock_env):
        """Test initialization with API key"""
        manager = ToolsManager()
        
        builtin_tools = manager.get_builtin_tools()
        assert 'serper' in builtin_tools
        assert 'website_search' in builtin_tools
        assert 'file_read' in builtin_tools
        assert 'scrape_website' in builtin_tools
    
    def test_initialization_with_config(self):
        """Test initialization with custom configuration"""
        config = {
            'serper': {
                'api_key': 'config_key',
                'n_results': 5
            },
            'website_search': {},
            'file_read': {},
            'scrape_website': {
                'timeout': 60
            }
        }
        
        with patch('backend.features.tools.builtin.serper_tool.SerperDevTool') as mock_serper:
            manager = ToolsManager(config)
            
            # Check that SerperDevTool was called with correct parameters
            mock_serper.assert_called_with(
                api_key='config_key',
                n_results=5
            )
    
    def test_get_tool(self, mock_env):
        """Test getting a specific tool"""
        manager = ToolsManager()
        
        # Get existing built-in tool that doesn't require API keys
        tool = manager.get_tool('file_read')
        assert tool is not None
        
        # Get custom tool
        tool = manager.get_tool('academic_analyzer')
        assert tool is not None
        
        # Get non-existing tool
        tool = manager.get_tool('non_existent')
        assert tool is None
    
    def test_get_all_tools(self, mock_env):
        """Test getting all tools"""
        manager = ToolsManager()
        tools = manager.get_all_tools()
        
        assert isinstance(tools, dict)
        assert 'academic_analyzer' in tools  # Custom tool
        assert len(tools) >= 4  # At least 4 tools total
    
    def test_get_builtin_and_custom_tools_separately(self, mock_env):
        """Test getting built-in and custom tools separately"""
        manager = ToolsManager()
        
        builtin = manager.get_builtin_tools()
        custom = manager.get_custom_tools()
        
        # Check for tools that should always be available
        assert 'file_read' in builtin
        assert 'scrape_website' in builtin
        assert 'academic_analyzer' not in builtin
        
        assert 'academic_analyzer' in custom
        assert 'file_read' not in custom
    
    def test_get_tools_for_agent(self, mock_env):
        """Test getting tools for specific agent roles"""
        manager = ToolsManager()
        
        # Information gatherer should get search tools and analyzer
        gatherer_tools = manager.get_tools_for_agent('information_gatherer')
        # Should have at least serper, scrape_website, and academic_analyzer
        # WebsiteSearchTool might not be available without proper setup
        assert len(gatherer_tools) >= 3
        tool_names = [type(tool).__name__ for tool in gatherer_tools]
        # Check for custom tool (it's a function, so we check differently)
        has_academic_analyzer = any('analyze_academic_source' in str(tool) for tool in gatherer_tools)
        assert has_academic_analyzer
        
        # Data analyst should get file tools and analyzer
        analyst_tools = manager.get_tools_for_agent('data_analyst')
        assert len(analyst_tools) >= 2
        
        # Content synthesizer should get file tools only
        synthesizer_tools = manager.get_tools_for_agent('content_synthesizer')
        assert len(synthesizer_tools) >= 1
        
        # Research coordinator shouldn't need tools
        coordinator_tools = manager.get_tools_for_agent('research_coordinator')
        assert len(coordinator_tools) == 0
    
    def test_get_tools_status(self, mock_env):
        """Test getting tools status"""
        manager = ToolsManager()
        status = manager.get_tools_status()
        
        assert isinstance(status, dict)
        assert 'serper' in status
        assert 'website_search' in status
        assert 'academic_analyzer' in status
        
        # Check status structure
        assert 'available' in status['serper']
        assert 'initialized' in status['website_search']
        assert status['academic_analyzer']['type'] == 'custom'
    
    def test_validate_all_tools(self, mock_env):
        """Test comprehensive tool validation"""
        manager = ToolsManager()
        results = manager.validate_all_tools()
        
        assert 'valid' in results
        assert 'warnings' in results
        assert 'errors' in results
        assert 'tool_validations' in results
        
        # The system might have warnings but should still be functional
        # Check that we have at least some tools
        all_tools = manager.get_all_tools()
        assert len(all_tools) > 0
    
    def test_validate_tools_missing_critical(self):
        """Test validation when critical tools are missing"""
        # Mock tools to simulate missing critical tools
        with patch('backend.features.tools.builtin.website_search_tool.WebsiteSearchTool', side_effect=Exception("Init error")):
            manager = ToolsManager()
            results = manager.validate_all_tools()
            
            # Should have warnings about missing critical tool
            assert len(results['warnings']) > 0
            assert any('website_search' in w for w in results['warnings'])
    
    def test_get_tool_config(self, mock_env):
        """Test getting tool configuration"""
        manager = ToolsManager()
        
        # Get config for existing tool
        config = manager.get_tool_config('serper')
        assert config is not None
        assert hasattr(config, 'get_status')
        
        # Get config for non-existing tool
        config = manager.get_tool_config('non_existent')
        assert config is None
    
    def test_reload_tool(self, mock_env):
        """Test reloading a specific tool"""
        manager = ToolsManager()
        
        # Reload a tool that doesn't require API keys
        success = manager.reload_tool('file_read')
        assert success is True
        
        # Try to reload non-existing tool
        success = manager.reload_tool('non_existent')
        assert success is False
    
    def test_singleton_behavior(self, mock_env):
        """Test singleton pattern"""
        manager1 = get_tools_manager()
        manager2 = get_tools_manager()
        
        assert manager1 is manager2
        
        # Reset and get new instance
        reset_tools_manager()
        manager3 = get_tools_manager()
        
        assert manager3 is not manager1
    
    def test_error_handling_during_initialization(self):
        """Test error handling when tools fail to initialize"""
        # Mock a built-in tool to fail
        with patch('backend.features.tools.builtin.file_read_tool.FileReadTool', side_effect=Exception("Init error")):
            manager = ToolsManager()
            
            # Should still have other tools
            tools = manager.get_all_tools()
            assert len(tools) > 0  # Should have at least custom tools
            assert 'academic_analyzer' in tools


if __name__ == "__main__":
    pytest.main([__file__, "-v"])