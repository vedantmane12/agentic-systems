"""
Research Coordinator Agent
Main orchestrator for the research assistant system
"""

from typing import Optional, Dict, Any, List
from crewai import Agent
from ..memory.research_memory import ResearchMemory
import logging

logger = logging.getLogger(__name__)


class ResearchCoordinatorAgent:
    """Research Coordinator - orchestrates the entire research workflow"""
    
    def __init__(self, memory: ResearchMemory, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Research Coordinator agent
        
        Args:
            memory: Shared memory system
            config: Optional configuration
        """
        self.memory = memory
        self.config = config or {}
        self.agent = self._create_agent()
        logger.info("Research Coordinator agent initialized")
    
    def _create_agent(self) -> Agent:
        """Create and configure the coordinator agent"""
        return Agent(
            role="Research Coordinator",
            goal="""Orchestrate research tasks efficiently by:
            1. Analyzing research queries to identify key objectives
            2. Breaking down complex queries into manageable sub-tasks
            3. Delegating tasks to appropriate specialized agents
            4. Monitoring progress and ensuring quality standards
            5. Synthesizing results into comprehensive insights""",
            backstory="""You are an experienced research coordinator with years of expertise in 
            managing complex research projects. You excel at understanding research requirements, 
            breaking them down into actionable tasks, and ensuring all aspects of a query are 
            thoroughly investigated. You have a keen eye for quality and ensure that all research 
            meets high standards of accuracy and completeness. Your strength lies in strategic 
            thinking and efficient resource allocation.""",
            verbose=self.config.get('verbose', True),
            allow_delegation=True,
            max_iter=self.config.get('max_iterations', 5),
            memory=True,
            callbacks=[self._agent_callback]
        )
    
    def _agent_callback(self, event: Dict[str, Any]) -> None:
        """Callback for agent events"""
        event_type = event.get('type', 'unknown')
        logger.debug(f"Coordinator event: {event_type}")
        
        # Store important events in memory
        if event_type in ['task_started', 'task_completed', 'delegation']:
            self.memory.store_short_term(f"coordinator_event_{event_type}", event)
        
        # Track delegations
        if event_type == 'delegation':
            delegated_to = event.get('delegated_to')
            task = event.get('task')
            self.memory.share_data(
                'coordinator',
                {
                    'action': 'delegated',
                    'to': delegated_to,
                    'task': task
                },
                priority='high'
            )
    
    def plan_research(self, query: str) -> Dict[str, Any]:
        """
        Create a research plan for the given query
        
        Args:
            query: Research query
            
        Returns:
            Research plan with objectives and sub-tasks
        """
        logger.info(f"Planning research for query: {query}")
        
        # Store query in memory
        self.memory.store_short_term('current_query', query)
        
        # Create research plan structure
        plan = {
            'query': query,
            'objectives': [],
            'sub_tasks': [],
            'required_agents': [],
            'estimated_complexity': 'medium',
            'priority_order': []
        }
        
        # Analyze query complexity
        complexity = self._analyze_complexity(query)
        plan['estimated_complexity'] = complexity
        
        # Identify key objectives
        objectives = self._identify_objectives(query)
        plan['objectives'] = objectives
        
        # Break down into sub-tasks
        sub_tasks = self._create_sub_tasks(objectives)
        plan['sub_tasks'] = sub_tasks
        
        # Determine required agents
        required_agents = self._identify_required_agents(sub_tasks)
        plan['required_agents'] = required_agents
        
        # Set priority order
        priority_order = self._prioritize_tasks(sub_tasks)
        plan['priority_order'] = priority_order
        
        # Store plan in memory
        self.memory.store_short_term('research_plan', plan)
        self.memory.share_data('coordinator', plan, priority='high')
        
        logger.info(f"Research plan created with {len(sub_tasks)} sub-tasks")
        return plan
    
    def _analyze_complexity(self, query: str) -> str:
        """Analyze query complexity"""
        # Simple heuristic based on query characteristics
        query_lower = query.lower()
        
        # High complexity indicators
        high_complexity_keywords = [
            'comprehensive', 'detailed', 'in-depth', 'analyze', 
            'compare', 'evaluate', 'assess', 'investigate'
        ]
        
        # Check for multiple questions or topics
        question_marks = query.count('?')
        and_count = query_lower.count(' and ')
        
        complexity_score = 0
        
        # Add points for complexity indicators
        for keyword in high_complexity_keywords:
            if keyword in query_lower:
                complexity_score += 1
        
        complexity_score += question_marks
        complexity_score += and_count
        
        # Determine complexity level
        if complexity_score >= 4:
            return 'high'
        elif complexity_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _identify_objectives(self, query: str) -> List[str]:
        """Identify key objectives from the query"""
        objectives = []
        
        # Extract main research goals
        query_lower = query.lower()
        
        # Common research patterns
        if 'what' in query_lower:
            objectives.append("Identify and explain key concepts")
        if 'how' in query_lower:
            objectives.append("Explain processes or mechanisms")
        if 'why' in query_lower:
            objectives.append("Analyze causes and reasons")
        if 'compare' in query_lower or 'difference' in query_lower:
            objectives.append("Compare and contrast different aspects")
        if 'impact' in query_lower or 'effect' in query_lower:
            objectives.append("Analyze impacts and effects")
        if 'future' in query_lower or 'trend' in query_lower:
            objectives.append("Identify future trends and projections")
        if 'current' in query_lower or 'latest' in query_lower:
            objectives.append("Find current/latest information")
        
        # Default objective if none identified
        if not objectives:
            objectives.append("Gather comprehensive information on the topic")
        
        return objectives
    
    def _create_sub_tasks(self, objectives: List[str]) -> List[Dict[str, Any]]:
        """Create sub-tasks based on objectives"""
        sub_tasks = []
        
        for i, objective in enumerate(objectives):
            # Information gathering task
            if "information" in objective.lower() or "identify" in objective.lower():
                sub_tasks.append({
                    'id': f'task_{i}_gather',
                    'type': 'information_gathering',
                    'description': f"Gather relevant information for: {objective}",
                    'objective': objective,
                    'agent': 'information_gatherer'
                })
            
            # Analysis task
            if "analyze" in objective.lower() or "compare" in objective.lower():
                sub_tasks.append({
                    'id': f'task_{i}_analyze',
                    'type': 'analysis',
                    'description': f"Analyze data for: {objective}",
                    'objective': objective,
                    'agent': 'data_analyst'
                })
            
            # Synthesis task (always needed for final output)
            if i == len(objectives) - 1:  # Last objective
                sub_tasks.append({
                    'id': f'task_{i}_synthesize',
                    'type': 'synthesis',
                    'description': "Synthesize all findings into comprehensive report",
                    'objective': "Create final research output",
                    'agent': 'content_synthesizer'
                })
        
        return sub_tasks
    
    def _identify_required_agents(self, sub_tasks: List[Dict[str, Any]]) -> List[str]:
        """Identify which agents are needed"""
        required_agents = set()
        
        for task in sub_tasks:
            agent = task.get('agent')
            if agent:
                required_agents.add(agent)
        
        return list(required_agents)
    
    def _prioritize_tasks(self, sub_tasks: List[Dict[str, Any]]) -> List[str]:
        """Determine task execution order"""
        # Simple priority: gathering -> analysis -> synthesis
        priority_order = []
        
        # First: all gathering tasks
        for task in sub_tasks:
            if task['type'] == 'information_gathering':
                priority_order.append(task['id'])
        
        # Second: all analysis tasks
        for task in sub_tasks:
            if task['type'] == 'analysis':
                priority_order.append(task['id'])
        
        # Last: synthesis tasks
        for task in sub_tasks:
            if task['type'] == 'synthesis':
                priority_order.append(task['id'])
        
        return priority_order
    
    def monitor_progress(self) -> Dict[str, Any]:
        """Monitor research progress"""
        # Get shared data from all agents
        all_shared_data = self.memory.get_all_shared_data()
        
        progress = {
            'total_agents': len(all_shared_data),
            'agent_status': {},
            'completed_tasks': [],
            'pending_tasks': [],
            'errors': []
        }
        
        # Check each agent's status
        for agent_id, data in all_shared_data.items():
            if isinstance(data, dict):
                status = data.get('status', 'unknown')
                progress['agent_status'][agent_id] = status
                
                if status == 'completed':
                    progress['completed_tasks'].append(agent_id)
                elif status == 'error':
                    progress['errors'].append({
                        'agent': agent_id,
                        'error': data.get('error', 'Unknown error')
                    })
        
        return progress
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent