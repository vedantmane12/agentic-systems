"""
Research Crew Orchestration
Manages the CrewAI crew for research tasks
"""

from typing import Dict, Any, Optional, List
from crewai import Crew, Task, Process
from ..agents import (
    ResearchCoordinatorAgent,
    InformationGathererAgent,
    DataAnalystAgent,
    ContentSynthesizerAgent
)
from ..memory.research_memory import ResearchMemory
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ResearchCrew:
    """Orchestrates the research crew for executing research tasks"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the research crew
        
        Args:
            config: Optional configuration for the crew
        """
        self.config = config or {}
        self.memory = ResearchMemory()
        
        # Initialize agents
        self._initialize_agents()
        
        # Crew will be created when needed
        self.crew = None
        
        logger.info("Research crew initialized")
    
    def _initialize_agents(self) -> None:
        """Initialize all agents with shared memory"""
        agent_config = self.config.get('agents', {})
        
        # Create agent instances
        self.coordinator = ResearchCoordinatorAgent(
            self.memory,
            agent_config.get('coordinator', {})
        )
        
        self.gatherer = InformationGathererAgent(
            self.memory,
            agent_config.get('gatherer', {})
        )
        
        self.analyst = DataAnalystAgent(
            self.memory,
            agent_config.get('analyst', {})
        )
        
        self.synthesizer = ContentSynthesizerAgent(
            self.memory,
            agent_config.get('synthesizer', {})
        )
        
        logger.info("All agents initialized successfully")
    
    def create_research_tasks(self, query: str) -> List[Task]:
        """
        Create tasks for the research query
        
        Args:
            query: Research query
            
        Returns:
            List of tasks to execute
        """
        tasks = []
        
        # Task 1: Research Planning (Coordinator)
        planning_task = Task(
            description=f"""
            Create a comprehensive research plan for the following query:
            
            Query: {query}
            
            Your plan should include:
            1. Key research objectives
            2. Information gathering strategy
            3. Analysis approach
            4. Expected deliverables
            
            Provide a structured plan that will guide the research process.
            """,
            expected_output="A detailed research plan with clear objectives and strategies",
            agent=self.coordinator.get_agent()
        )
        tasks.append(planning_task)
        
        # Task 2: Information Gathering (Gatherer)
        gathering_task = Task(
            description=f"""
            Based on the research plan, gather comprehensive information for:
            
            Query: {query}
            
            Your tasks:
            1. Search for relevant and credible sources
            2. Extract key information from each source
            3. Evaluate source reliability
            4. Organize findings by relevance
            5. Identify any gaps in information
            
            Use all available tools to find high-quality, relevant information.
            """,
            expected_output="Comprehensive collection of relevant information with source citations",
            agent=self.gatherer.get_agent(),
            context=[planning_task]  # Depends on planning
        )
        tasks.append(gathering_task)
        
        # Task 3: Data Analysis (Analyst)
        analysis_task = Task(
            description=f"""
            Analyze the gathered information to extract meaningful insights:
            
            Original Query: {query}
            
            Your analysis should:
            1. Identify key patterns and trends
            2. Compare different sources and perspectives
            3. Find correlations and relationships
            4. Assess the quality and consistency of data
            5. Generate actionable insights
            
            Provide both quantitative and qualitative analysis.
            """,
            expected_output="Detailed analysis with patterns, insights, and confidence levels",
            agent=self.analyst.get_agent(),
            context=[gathering_task]  # Depends on gathering
        )
        tasks.append(analysis_task)
        
        # Task 4: Report Synthesis (Synthesizer)
        synthesis_task = Task(
            description=f"""
            Create a comprehensive research report that addresses:
            
            Query: {query}
            
            Your report should include:
            1. Executive summary
            2. Introduction and background
            3. Methodology
            4. Key findings with proper citations
            5. Analysis and insights
            6. Conclusions
            7. Actionable recommendations
            8. References
            
            Ensure the report is well-structured, clear, and provides value to the reader.
            """,
            expected_output="Complete research report with all sections properly formatted",
            agent=self.synthesizer.get_agent(),
            context=[planning_task, gathering_task, analysis_task]  # Depends on all previous
        )
        tasks.append(synthesis_task)
        
        return tasks
    
    def execute_research(self, query: str) -> Dict[str, Any]:
        """
        Execute the complete research process
        
        Args:
            query: Research query
            
        Returns:
            Research results including report and metadata
        """
        logger.info(f"Starting research for query: {query}")
        start_time = datetime.now()
        
        try:
            # Store query in memory
            self.memory.store_short_term('research_query', query)
            self.memory.store_short_term('start_time', start_time.isoformat())
            
            # Create tasks
            tasks = self.create_research_tasks(query)
            
            # Create crew
            self.crew = Crew(
                agents=[
                    self.coordinator.get_agent(),
                    self.gatherer.get_agent(),
                    self.analyst.get_agent(),
                    self.synthesizer.get_agent()
                ],
                tasks=tasks,
                process=Process.sequential,  # Tasks execute in order
                verbose=self.config.get('verbose', True),
                memory=True,
                embedder={
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small"
                    }
                } if self.config.get('use_embeddings', False) else None
            )
            
            # Execute crew
            result = self.crew.kickoff()
            
            # Process results
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Get the final report from memory
            final_report = self.memory.get_short_term('completed_report')
            
            # Create response
            response = {
                'success': True,
                'query': query,
                'report': final_report if final_report else str(result),
                'execution_time': execution_time,
                'metadata': {
                    'start_time': start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'agents_used': 4,
                    'tasks_completed': len(tasks),
                    'memory_stats': self.memory.get_memory_stats()
                }
            }
            
            # Store results
            self.memory.store_short_term('research_results', response)
            
            logger.info(f"Research completed in {execution_time:.2f} seconds")
            return response
            
        except Exception as e:
            logger.error(f"Error during research execution: {str(e)}")
            
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
    
    def get_memory_export(self) -> Dict[str, Any]:
        """Export the current memory state"""
        return self.memory.export_memory()
    
    def load_memory(self, memory_data: Dict[str, Any]) -> None:
        """Load a previous memory state"""
        self.memory.import_memory(memory_data)
    
    def clear_memory(self) -> None:
        """Clear all memory"""
        self.memory.clear_short_term()
        self.memory.clear_shared_data()
        logger.info("Memory cleared")
    
    def get_research_history(self) -> List[Dict[str, Any]]:
        """Get history of research queries"""
        # This would be implemented with persistent storage
        # For now, return current session data
        history = []
        
        if self.memory.get_short_term('research_query'):
            history.append({
                'query': self.memory.get_short_term('research_query'),
                'timestamp': self.memory.get_short_term('start_time'),
                'status': 'completed' if self.memory.get_short_term('research_results') else 'in_progress'
            })
        
        return history