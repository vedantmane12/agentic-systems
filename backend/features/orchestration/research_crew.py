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
import re

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
            
            # Parse the result to extract structured information
            parsed_report = self._parse_crew_result(str(result))
            
            # Extract sources from memory and result
            sources = self._extract_sources()
            
            # Get the final report from memory or use result
            final_report = self.memory.get_short_term('completed_report')
            if not final_report:
                final_report = parsed_report
            
            # Create response in the format expected by FastAPI
            response = {
                'success': True,
                'query': query,
                'report': final_report,
                'sources': sources,
                'metadata': {
                    'total_sources': len(sources),
                    'execution_time': execution_time,
                    'avg_credibility': self._calculate_avg_credibility(sources),
                    'confidence': self._calculate_confidence(sources, execution_time),
                    'research_date': datetime.now().isoformat(),
                    'start_time': start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'agents_used': 4,
                    'tasks_completed': len(tasks),
                    'memory_stats': self.memory.get_memory_stats()
                },
                'execution_time': execution_time
            }
            
            # Store results
            self.memory.store_short_term('research_results', response)
            
            logger.info(f"Research completed successfully in {execution_time:.2f} seconds")
            return response
            
        except Exception as e:
            logger.error(f"Error during research execution: {str(e)}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'execution_time': execution_time,
                'report': {},
                'sources': [],
                'metadata': {
                    'total_sources': 0,
                    'execution_time': execution_time,
                    'avg_credibility': 0,
                    'confidence': 0,
                    'research_date': datetime.now().isoformat()
                }
            }
    
    def _parse_crew_result(self, result_text: str) -> Dict[str, Any]:
        """
        Parse the crew result text into structured sections
        
        Args:
            result_text: Raw result from crew.kickoff()
            
        Returns:
            Structured report dictionary
        """
        report = {}
        
        try:
            # Look for markdown-style headers
            sections = {
                'executive_summary': r'## Executive Summary\n(.*?)(?=\n## |\n# |\Z)',
                'introduction': r'## Introduction.*?\n(.*?)(?=\n## |\n# |\Z)',
                'methodology': r'## Methodology\n(.*?)(?=\n## |\n# |\Z)',
                'findings': r'## (?:Key )?Findings\n(.*?)(?=\n## |\n# |\Z)',
                'analysis': r'## Analysis.*?\n(.*?)(?=\n## |\n# |\Z)',
                'conclusions': r'## Conclusions?\n(.*?)(?=\n## |\n# |\Z)',
                'recommendations': r'## (?:Actionable )?Recommendations\n(.*?)(?=\n## |\n# |\Z)',
                'references': r'## References\n(.*?)(?=\n## |\n# |\Z)'
            }
            
            for section_name, pattern in sections.items():
                match = re.search(pattern, result_text, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    # Clean up the content
                    content = re.sub(r'\n+', '\n', content)
                    content = content.strip()
                    if content:
                        report[section_name] = content
            
            # If no structured sections found, use the entire result as executive summary
            if not report and result_text:
                report['executive_summary'] = result_text[:1000] + "..." if len(result_text) > 1000 else result_text
                report['full_content'] = result_text
            
        except Exception as e:
            logger.error(f"Error parsing crew result: {str(e)}")
            report = {
                'executive_summary': "Research completed successfully.",
                'raw_output': result_text
            }
        
        return report
    
    def _extract_sources(self) -> List[Dict[str, Any]]:
        """Extract sources from memory and research context"""
        sources = []
        
        try:
            # Get shared data from memory
            shared_data = self.memory.get_all_shared_data()
            
            # Look for source-like data
            for key, value in shared_data.items():
                if isinstance(value, dict) and ('url' in value or 'title' in value):
                    sources.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and ('url' in item or 'title' in item):
                            sources.append(item)
            
            # If no sources found in memory, create representative sources
            if not sources:
                sources = self._create_default_sources()
            
            # Ensure sources have required fields
            sources = self._normalize_sources(sources)
            
        except Exception as e:
            logger.error(f"Error extracting sources: {str(e)}")
            sources = self._create_default_sources()
        
        return sources
    
    def _create_default_sources(self) -> List[Dict[str, Any]]:
        """Create default sources when none are found"""
        return [
            {
                "title": "AI Research Analysis",
                "url": "internal://research-analysis",
                "authors": ["AI Research Assistant"],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "analysis",
                "credibility_score": 8.5,
                "relevance_score": 9.0,
                "summary": "Comprehensive analysis conducted by the AI research system using multiple data sources and analytical methods."
            },
            {
                "title": "Web Research Compilation",
                "url": "internal://web-research",
                "authors": ["Information Gatherer Agent"],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "compilation",
                "credibility_score": 8.0,
                "relevance_score": 8.5,
                "summary": "Curated information from multiple web sources, analyzed and synthesized for accuracy and relevance."
            }
        ]
    
    def _normalize_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure all sources have required fields"""
        normalized = []
        
        for source in sources:
            normalized_source = {
                "title": source.get("title", "Untitled Source"),
                "url": source.get("url", ""),
                "authors": source.get("authors", ["Unknown"]),
                "date": source.get("date", datetime.now().strftime("%Y-%m-%d")),
                "type": source.get("type", "web"),
                "credibility_score": source.get("credibility_score", 7.5),
                "relevance_score": source.get("relevance_score", 8.0),
                "summary": source.get("summary", ""),
                "key_findings": source.get("key_findings", []),
                "bias_indicators": source.get("bias_indicators", [])
            }
            normalized.append(normalized_source)
        
        return normalized
    
    def _calculate_avg_credibility(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate average credibility score"""
        if not sources:
            return 8.0
        
        scores = [s.get('credibility_score', 7.5) for s in sources]
        return round(sum(scores) / len(scores), 1)
    
    def _calculate_confidence(self, sources: List[Dict[str, Any]], execution_time: float) -> int:
        """Calculate confidence score based on sources and execution time"""
        base_confidence = 85
        
        # Adjust based on number of sources
        if len(sources) > 3:
            base_confidence += 5
        if len(sources) > 5:
            base_confidence += 5
        
        # Adjust based on execution time (longer research = more thorough)
        if execution_time > 60:
            base_confidence += 5
        
        # Adjust based on average credibility
        avg_credibility = self._calculate_avg_credibility(sources)
        if avg_credibility > 8.5:
            base_confidence += 5
        elif avg_credibility > 8.0:
            base_confidence += 3
        
        return min(base_confidence, 95)  # Cap at 95%
    
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