"""
Tests for Research Crew Orchestration
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.features.orchestration.research_crew import ResearchCrew


class TestResearchCrew:
    """Test cases for Research Crew"""
    
    @pytest.fixture
    def crew(self):
        """Create research crew instance"""
        config = {
            'verbose': False,
            'use_embeddings': False
        }
        return ResearchCrew(config)
    
    def test_initialization(self, crew):
        """Test crew initialization"""
        assert crew is not None
        assert crew.memory is not None
        assert crew.coordinator is not None
        assert crew.gatherer is not None
        assert crew.analyst is not None
        assert crew.synthesizer is not None
        assert crew.crew is None  # Not created until needed
    
    def test_initialize_agents(self, crew):
        """Test agent initialization"""
        # Agents should be initialized
        assert hasattr(crew.coordinator, 'agent')
        assert hasattr(crew.gatherer, 'agent')
        assert hasattr(crew.analyst, 'agent')
        assert hasattr(crew.synthesizer, 'agent')
        
        # All should share the same memory
        assert crew.coordinator.memory is crew.memory
        assert crew.gatherer.memory is crew.memory
        assert crew.analyst.memory is crew.memory
        assert crew.synthesizer.memory is crew.memory
    
    def test_create_research_tasks(self, crew):
        """Test task creation"""
        query = "What is artificial intelligence?"
        tasks = crew.create_research_tasks(query)
        
        assert len(tasks) == 4
        
        # Check task order
        assert tasks[0].agent == crew.coordinator.get_agent()  # Planning
        assert tasks[1].agent == crew.gatherer.get_agent()     # Gathering
        assert tasks[2].agent == crew.analyst.get_agent()      # Analysis
        assert tasks[3].agent == crew.synthesizer.get_agent()  # Synthesis
        
        # Check dependencies
        assert tasks[1].context == [tasks[0]]  # Gathering depends on planning
        assert tasks[2].context == [tasks[1]]  # Analysis depends on gathering
        assert tasks[3].context == [tasks[0], tasks[1], tasks[2]]  # Synthesis depends on all
        
        # Check descriptions contain query
        for task in tasks:
            assert query in task.description
    
    @patch('backend.features.orchestration.research_crew.Crew')
    def test_execute_research_success(self, mock_crew_class, crew):
        """Test successful research execution"""
        query = "Test query"
        
        # Mock crew instance
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Research completed"
        mock_crew_class.return_value = mock_crew_instance
        
        # Mock memory to return a report
        crew.memory.store_short_term('completed_report', {
            'title': 'Test Report',
            'content': 'Test content'
        })
        
        # Execute
        result = crew.execute_research(query)
        
        # Verify results
        assert result['success'] is True
        assert result['query'] == query
        assert 'report' in result
        assert 'execution_time' in result
        assert 'metadata' in result
        
        # Verify crew was created and executed
        mock_crew_class.assert_called_once()
        mock_crew_instance.kickoff.assert_called_once()
        
        # Verify memory storage
        assert crew.memory.get_short_term('research_query') == query
        assert crew.memory.get_short_term('start_time') is not None
    
    @patch('backend.features.orchestration.research_crew.Crew')
    def test_execute_research_failure(self, mock_crew_class, crew):
        """Test research execution with error"""
        query = "Test query"
        
        # Mock crew to raise exception
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.side_effect = Exception("Test error")
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute
        result = crew.execute_research(query)
        
        # Verify error handling
        assert result['success'] is False
        assert result['query'] == query
        assert 'error' in result
        assert result['error'] == "Test error"
        assert 'execution_time' in result
    
    def test_memory_operations(self, crew):
        """Test memory operations"""
        # Test memory export
        crew.memory.store_short_term('test_key', 'test_value')
        export = crew.get_memory_export()
        
        assert 'short_term' in export
        assert 'long_term' in export
        assert 'shared_data' in export
        
        # Test memory load
        new_data = {
            'short_term': {'new_key': {'value': 'new_value'}},
            'long_term': {},
            'shared_data': {}
        }
        crew.load_memory(new_data)
        assert crew.memory.get_short_term('new_key') == 'new_value'
        
        # Test memory clear
        crew.clear_memory()
        assert len(crew.memory.short_term) == 0
        assert len(crew.memory.shared_data) == 0
    
    def test_get_research_history(self, crew):
        """Test research history retrieval"""
        # No history initially
        history = crew.get_research_history()
        assert len(history) == 0
        
        # Add some data
        crew.memory.store_short_term('research_query', 'Test query')
        crew.memory.store_short_term('start_time', '2024-01-01T00:00:00')
        crew.memory.store_short_term('research_results', {'success': True})
        
        # Get history
        history = crew.get_research_history()
        assert len(history) == 1
        assert history[0]['query'] == 'Test query'
        assert history[0]['status'] == 'completed'
    
    def test_crew_configuration(self):
        """Test crew with different configurations"""
        config = {
            'verbose': True,
            'use_embeddings': True,
            'agents': {
                'coordinator': {'max_iterations': 10},
                'gatherer': {'verbose': False}
            }
        }
        
        crew = ResearchCrew(config)
        
        # Verify configuration is passed
        assert crew.config == config
        assert crew.coordinator.config.get('max_iterations') == 10
        assert crew.gatherer.config.get('verbose') is False
    
    @patch('backend.features.orchestration.research_crew.Crew')
    def test_crew_creation_with_embeddings(self, mock_crew_class, crew):
        """Test crew creation with embeddings enabled"""
        crew.config['use_embeddings'] = True
        query = "Test query"
        
        # Mock crew
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Done"
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute to trigger crew creation
        crew.execute_research(query)
        
        # Verify embedder configuration was passed
        call_args = mock_crew_class.call_args[1]
        assert 'embedder' in call_args
        assert call_args['embedder']['provider'] == 'openai'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])