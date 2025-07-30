"""
Tests for Research Memory System
"""

import pytest
import json
from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.features.memory.research_memory import ResearchMemory, MemoryType


class TestResearchMemory:
    """Test cases for ResearchMemory class"""
    
    @pytest.fixture
    def memory(self):
        """Create a fresh memory instance for each test"""
        return ResearchMemory()
    
    def test_initialization(self, memory):
        """Test memory system initialization"""
        assert memory.short_term == {}
        assert "reliable_sources" in memory.long_term
        assert "search_patterns" in memory.long_term
        assert "topic_knowledge" in memory.long_term
        assert "quality_scores" in memory.long_term
        assert memory.shared_data == {}
    
    def test_store_and_retrieve_short_term(self, memory):
        """Test short-term memory storage and retrieval"""
        # Store data
        memory.store_short_term("test_key", "test_value", {"type": "test"})
        
        # Retrieve data
        value = memory.get_short_term("test_key")
        assert value == "test_value"
        
        # Check metadata and timestamp
        assert "timestamp" in memory.short_term["test_key"]
        assert memory.short_term["test_key"]["metadata"]["type"] == "test"
        
        # Test non-existent key
        assert memory.get_short_term("non_existent") is None
    
    def test_store_and_retrieve_long_term_list(self, memory):
        """Test long-term memory with list operations"""
        # Append to list
        memory.store_long_term("reliable_sources", "source1", "append")
        memory.store_long_term("reliable_sources", "source2", "append")
        
        sources = memory.get_long_term("reliable_sources")
        assert len(sources) == 2
        assert "source1" in sources
        assert "source2" in sources
    
    def test_store_and_retrieve_long_term_dict(self, memory):
        """Test long-term memory with dict operations"""
        # Update dictionary
        memory.store_long_term("topic_knowledge", {"AI": "artificial intelligence"}, "update")
        memory.store_long_term("topic_knowledge", {"ML": "machine learning"}, "update")
        
        knowledge = memory.get_long_term("topic_knowledge")
        assert knowledge["AI"] == "artificial intelligence"
        assert knowledge["ML"] == "machine learning"
    
    def test_store_long_term_set_operation(self, memory):
        """Test long-term memory set operation"""
        # Set replaces entire content
        memory.store_long_term("quality_scores", {"test": 0.9}, "set")
        assert memory.get_long_term("quality_scores") == {"test": 0.9}
        
        memory.store_long_term("quality_scores", {"new": 0.8}, "set")
        assert memory.get_long_term("quality_scores") == {"new": 0.8}
        assert "test" not in memory.get_long_term("quality_scores")
    
    def test_invalid_long_term_operation(self, memory):
        """Test error handling for invalid operations"""
        with pytest.raises(ValueError):
            memory.store_long_term("reliable_sources", {"data": "value"}, "update")
    
    def test_share_and_retrieve_data(self, memory):
        """Test cross-agent data sharing"""
        # Share data
        memory.share_data("agent1", {"findings": ["result1", "result2"]}, "high")
        memory.share_data("agent2", {"analysis": "complete"}, "normal")
        
        # Retrieve data
        data1 = memory.get_shared_data("agent1")
        assert data1 == {"findings": ["result1", "result2"]}
        
        data2 = memory.get_shared_data("agent2")
        assert data2 == {"analysis": "complete"}
        
        # Check access count increases
        assert memory.shared_data["agent1"]["accessed_count"] == 1
        memory.get_shared_data("agent1")
        assert memory.shared_data["agent1"]["accessed_count"] == 2
        
        # Test non-existent agent
        assert memory.get_shared_data("non_existent") is None
    
    def test_get_all_shared_data(self, memory):
        """Test retrieving all shared data with filters"""
        # Share data with different priorities
        memory.share_data("agent1", "data1", "high")
        memory.share_data("agent2", "data2", "normal")
        memory.share_data("agent3", "data3", "high")
        
        # Get all data
        all_data = memory.get_all_shared_data()
        assert len(all_data) == 3
        assert all_data["agent1"] == "data1"
        
        # Get filtered data
        high_priority = memory.get_all_shared_data(priority="high")
        assert len(high_priority) == 2
        assert "agent1" in high_priority
        assert "agent3" in high_priority
        assert "agent2" not in high_priority
    
    def test_clear_operations(self, memory):
        """Test memory clearing operations"""
        # Add data
        memory.store_short_term("key1", "value1")
        memory.share_data("agent1", "data1")
        memory.share_data("agent2", "data2")
        
        # Clear short-term
        memory.clear_short_term()
        assert len(memory.short_term) == 0
        
        # Clear specific agent's shared data
        memory.clear_shared_data("agent1")
        assert "agent1" not in memory.shared_data
        assert "agent2" in memory.shared_data
        
        # Clear all shared data
        memory.clear_shared_data()
        assert len(memory.shared_data) == 0
    
    def test_memory_stats(self, memory):
        """Test memory statistics"""
        # Add some data
        memory.store_short_term("key1", "value1")
        memory.store_short_term("key2", "value2")
        memory.share_data("agent1", "data1")
        
        stats = memory.get_memory_stats()
        assert stats["short_term_items"] == 2
        assert stats["long_term_categories"] == 4  # Initial categories
        assert stats["shared_data_agents"] == 1
        assert "uptime_seconds" in stats
        assert stats["uptime_seconds"] >= 0
        
        # Check breakdown
        assert "key1" in stats["memory_breakdown"]["short_term"]
        assert "key2" in stats["memory_breakdown"]["short_term"]
        assert "agent1" in stats["memory_breakdown"]["shared_agents"]
    
    def test_export_import_memory(self, memory):
        """Test memory export and import"""
        # Add data
        memory.store_short_term("key1", "value1")
        memory.store_long_term("reliable_sources", "source1", "append")
        memory.share_data("agent1", "data1")
        
        # Export
        exported = memory.export_memory()
        assert "short_term" in exported
        assert "long_term" in exported
        assert "shared_data" in exported
        assert "export_timestamp" in exported
        
        # Create new memory and import
        new_memory = ResearchMemory()
        new_memory.import_memory(exported)
        
        # Verify imported data
        assert new_memory.get_short_term("key1") == "value1"
        assert "source1" in new_memory.get_long_term("reliable_sources")
        assert new_memory.get_shared_data("agent1") == "data1"
    
    def test_new_category_creation(self, memory):
        """Test automatic creation of new long-term categories"""
        # Store in non-existent category
        memory.store_long_term("new_category", "item1", "append")
        assert "new_category" in memory.long_term
        assert memory.get_long_term("new_category") == ["item1"]
        
        # Store dict in new category
        memory.store_long_term("dict_category", {"key": "value"}, "update")
        assert memory.get_long_term("dict_category") == {"key": "value"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])