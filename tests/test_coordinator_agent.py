"""
Tests for Research Coordinator Agent
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.features.agents.coordinator import ResearchCoordinatorAgent
from backend.features.memory.research_memory import ResearchMemory


class TestResearchCoordinatorAgent:
    """Test cases for Research Coordinator Agent"""
    
    @pytest.fixture
    def memory(self):
        """Create memory instance"""
        return ResearchMemory()
    
    @pytest.fixture
    def coordinator(self, memory):
        """Create coordinator agent"""
        return ResearchCoordinatorAgent(memory)
    
    def test_initialization(self, coordinator):
        """Test agent initialization"""
        assert coordinator is not None
        assert coordinator.agent is not None
        assert coordinator.memory is not None
        
        # Check agent properties
        agent = coordinator.get_agent()
        assert agent.role == "Research Coordinator"
        assert agent.allow_delegation is True
        # Memory is enabled during creation but not accessible as an attribute
    
    def test_plan_research_simple_query(self, coordinator):
        """Test research planning for simple query"""
        query = "What is machine learning?"
        plan = coordinator.plan_research(query)
        
        assert plan['query'] == query
        assert len(plan['objectives']) > 0
        assert len(plan['sub_tasks']) > 0
        assert plan['estimated_complexity'] in ['low', 'medium', 'high']
        
        # Check memory storage
        stored_query = coordinator.memory.get_short_term('current_query')
        assert stored_query == query
        
        stored_plan = coordinator.memory.get_short_term('research_plan')
        assert stored_plan == plan
    
    def test_plan_research_complex_query(self, coordinator):
        """Test research planning for complex query"""
        query = "Compare and analyze the environmental impacts of electric vehicles versus traditional vehicles, including future trends and current developments"
        plan = coordinator.plan_research(query)
        
        assert plan['estimated_complexity'] == 'high'
        assert len(plan['objectives']) >= 3
        assert 'Compare and contrast different aspects' in plan['objectives']
        assert 'Analyze impacts and effects' in plan['objectives']
    
    def test_analyze_complexity(self, coordinator):
        """Test query complexity analysis"""
        # Low complexity
        simple_query = "What is Python?"
        assert coordinator._analyze_complexity(simple_query) == 'low'
        
        # Medium complexity
        medium_query = "How does machine learning work and what are its applications?"
        assert coordinator._analyze_complexity(medium_query) == 'medium'
        
        # High complexity
        complex_query = "Analyze and compare different machine learning algorithms, evaluate their performance, and investigate future trends in AI"
        assert coordinator._analyze_complexity(complex_query) == 'high'
    
    def test_identify_objectives(self, coordinator):
        """Test objective identification"""
        # Test various query types
        queries_and_expected = [
            ("What is AI?", ["Identify and explain key concepts"]),
            ("How does blockchain work?", ["Explain processes or mechanisms"]),
            ("Why is climate change happening?", ["Analyze causes and reasons"]),
            ("Compare Python and Java", ["Compare and contrast different aspects"]),
            ("What is the impact of social media?", ["Analyze impacts and effects"]),
            ("What are future trends in technology?", ["Identify future trends and projections"]),
            ("What are the latest developments in quantum computing?", ["Find current/latest information"])
        ]
        
        for query, expected_objectives in queries_and_expected:
            objectives = coordinator._identify_objectives(query)
            for expected in expected_objectives:
                assert expected in objectives
    
    def test_create_sub_tasks(self, coordinator):
        """Test sub-task creation"""
        objectives = [
            "Identify and explain key concepts",
            "Analyze impacts and effects",
            "Create final output"
        ]
        
        sub_tasks = coordinator._create_sub_tasks(objectives)
        
        # Should have at least one task per objective
        assert len(sub_tasks) >= len(objectives)
        
        # Check task structure
        for task in sub_tasks:
            assert 'id' in task
            assert 'type' in task
            assert 'description' in task
            assert 'objective' in task
            assert 'agent' in task
        
        # Should have synthesis task
        synthesis_tasks = [t for t in sub_tasks if t['type'] == 'synthesis']
        assert len(synthesis_tasks) >= 1
    
    def test_identify_required_agents(self, coordinator):
        """Test required agent identification"""
        sub_tasks = [
            {'agent': 'information_gatherer'},
            {'agent': 'data_analyst'},
            {'agent': 'information_gatherer'},  # Duplicate
            {'agent': 'content_synthesizer'}
        ]
        
        required = coordinator._identify_required_agents(sub_tasks)
        
        assert len(required) == 3  # Should deduplicate
        assert 'information_gatherer' in required
        assert 'data_analyst' in required
        assert 'content_synthesizer' in required
    
    def test_prioritize_tasks(self, coordinator):
        """Test task prioritization"""
        sub_tasks = [
            {'id': 'task_1', 'type': 'synthesis'},
            {'id': 'task_2', 'type': 'information_gathering'},
            {'id': 'task_3', 'type': 'analysis'},
            {'id': 'task_4', 'type': 'information_gathering'}
        ]
        
        priority = coordinator._prioritize_tasks(sub_tasks)
        
        # Gathering tasks should come first
        assert priority[0] == 'task_2'
        assert priority[1] == 'task_4'
        # Analysis next
        assert priority[2] == 'task_3'
        # Synthesis last
        assert priority[3] == 'task_1'
    
    def test_monitor_progress(self, coordinator):
        """Test progress monitoring"""
        # Add some shared data
        coordinator.memory.share_data('agent1', {'status': 'completed'})
        coordinator.memory.share_data('agent2', {'status': 'in_progress'})
        coordinator.memory.share_data('agent3', {'status': 'error', 'error': 'Test error'})
        
        progress = coordinator.monitor_progress()
        
        assert progress['total_agents'] == 3
        assert progress['agent_status']['agent1'] == 'completed'
        assert progress['agent_status']['agent2'] == 'in_progress'
        assert progress['agent_status']['agent3'] == 'error'
        
        assert 'agent1' in progress['completed_tasks']
        assert len(progress['errors']) == 1
        assert progress['errors'][0]['agent'] == 'agent3'
    
    def test_agent_callback(self, coordinator):
        """Test agent callback functionality"""
        # Test task started event
        event = {
            'type': 'task_started',
            'task': 'Test task',
            'timestamp': '2024-01-01T00:00:00'
        }
        
        coordinator._agent_callback(event)
        
        # Check if event was stored in memory
        stored = coordinator.memory.get_short_term('coordinator_event_task_started')
        assert stored == event
        
        # Test delegation event
        delegation_event = {
            'type': 'delegation',
            'delegated_to': 'information_gatherer',
            'task': 'Gather data'
        }
        
        coordinator._agent_callback(delegation_event)
        
        # Check shared data
        shared = coordinator.memory.get_shared_data('coordinator')
        assert shared['action'] == 'delegated'
        assert shared['to'] == 'information_gatherer'
    
    def test_configuration(self):
        """Test agent configuration options"""
        memory = ResearchMemory()
        config = {
            'verbose': False,
            'max_iterations': 10
        }
        
        coordinator = ResearchCoordinatorAgent(memory, config)
        agent = coordinator.get_agent()
        
        assert agent.verbose == False
        assert agent.max_iter == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])