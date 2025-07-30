"""
Research Memory System
Handles short-term, long-term, and shared memory for agents
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory storage"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SHARED = "shared"


class ResearchMemory:
    """
    Shared memory system for research agents
    
    This class manages three types of memory:
    1. Short-term: Current task context and temporary data
    2. Long-term: Persistent knowledge and patterns
    3. Shared: Cross-agent communication data
    """
    
    def __init__(self):
        """Initialize memory storage"""
        self.short_term: Dict[str, Dict[str, Any]] = {}
        self.long_term: Dict[str, Any] = {
            "reliable_sources": [],
            "search_patterns": [],
            "topic_knowledge": {},
            "quality_scores": {}
        }
        self.shared_data: Dict[str, Dict[str, Any]] = {}
        self._init_timestamp = datetime.now()
        logger.info("Research memory system initialized")
    
    def store_short_term(self, key: str, value: Any, metadata: Optional[Dict] = None) -> None:
        """
        Store data in short-term memory with timestamp
        
        Args:
            key: Unique identifier for the data
            value: Data to store
            metadata: Optional metadata about the data
        """
        self.short_term[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        logger.debug(f"Stored short-term memory: {key}")
    
    def get_short_term(self, key: str) -> Optional[Any]:
        """
        Retrieve data from short-term memory
        
        Args:
            key: Identifier of the data to retrieve
            
        Returns:
            The stored value or None if not found
        """
        if key in self.short_term:
            return self.short_term[key]["value"]
        return None
    
    def store_long_term(self, category: str, data: Any, operation: str = "append") -> None:
        """
        Store data in long-term memory
        
        Args:
            category: Category of long-term memory (e.g., 'reliable_sources')
            data: Data to store
            operation: How to store - 'append' for lists, 'update' for dicts, 'set' to replace
        """
        if category not in self.long_term:
            logger.warning(f"Unknown long-term category: {category}. Creating new category.")
            self.long_term[category] = [] if operation == "append" else {}
        
        if operation == "append" and isinstance(self.long_term[category], list):
            self.long_term[category].append(data)
        elif operation == "update" and isinstance(self.long_term[category], dict):
            self.long_term[category].update(data)
        elif operation == "set":
            self.long_term[category] = data
        else:
            logger.error(f"Invalid operation {operation} for category {category}")
            raise ValueError(f"Invalid operation {operation} for category {category}")
        
        logger.debug(f"Updated long-term memory: {category}")
    
    def get_long_term(self, category: str) -> Optional[Any]:
        """
        Retrieve data from long-term memory
        
        Args:
            category: Category to retrieve
            
        Returns:
            The stored data or None if not found
        """
        return self.long_term.get(category)
    
    def share_data(self, agent_id: str, data: Any, priority: str = "normal") -> None:
        """
        Share data for cross-agent communication
        
        Args:
            agent_id: ID of the agent sharing the data
            data: Data to share
            priority: Priority level ('high', 'normal', 'low')
        """
        self.shared_data[agent_id] = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "priority": priority,
            "accessed_count": 0
        }
        logger.info(f"Agent {agent_id} shared data with priority: {priority}")
    
    def get_shared_data(self, agent_id: str) -> Optional[Any]:
        """
        Retrieve shared data from an agent
        
        Args:
            agent_id: ID of the agent whose data to retrieve
            
        Returns:
            The shared data or None if not found
        """
        if agent_id in self.shared_data:
            self.shared_data[agent_id]["accessed_count"] += 1
            return self.shared_data[agent_id]["data"]
        return None
    
    def get_all_shared_data(self, priority: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all shared data, optionally filtered by priority
        
        Args:
            priority: Filter by priority level
            
        Returns:
            Dictionary of all shared data
        """
        if priority:
            return {
                agent_id: data["data"] 
                for agent_id, data in self.shared_data.items() 
                if data["priority"] == priority
            }
        return {agent_id: data["data"] for agent_id, data in self.shared_data.items()}
    
    def clear_short_term(self) -> None:
        """Clear all short-term memory"""
        self.short_term.clear()
        logger.info("Short-term memory cleared")
    
    def clear_shared_data(self, agent_id: Optional[str] = None) -> None:
        """
        Clear shared data
        
        Args:
            agent_id: Specific agent's data to clear, or None to clear all
        """
        if agent_id:
            self.shared_data.pop(agent_id, None)
            logger.info(f"Cleared shared data for agent: {agent_id}")
        else:
            self.shared_data.clear()
            logger.info("All shared data cleared")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage"""
        return {
            "short_term_items": len(self.short_term),
            "long_term_categories": len(self.long_term),
            "shared_data_agents": len(self.shared_data),
            "uptime_seconds": (datetime.now() - self._init_timestamp).total_seconds(),
            "memory_breakdown": {
                "short_term": list(self.short_term.keys()),
                "long_term": list(self.long_term.keys()),
                "shared_agents": list(self.shared_data.keys())
            }
        }
    
    def export_memory(self) -> Dict[str, Any]:
        """Export all memory for persistence"""
        return {
            "short_term": self.short_term,
            "long_term": self.long_term,
            "shared_data": self.shared_data,
            "export_timestamp": datetime.now().isoformat()
        }
    
    def import_memory(self, memory_data: Dict[str, Any]) -> None:
        """Import memory from exported data"""
        if "short_term" in memory_data:
            self.short_term = memory_data["short_term"]
        if "long_term" in memory_data:
            self.long_term = memory_data["long_term"]
        if "shared_data" in memory_data:
            self.shared_data = memory_data["shared_data"]
        logger.info("Memory imported successfully")