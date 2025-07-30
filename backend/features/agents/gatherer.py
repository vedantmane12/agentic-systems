"""
Information Gatherer Agent
Specializes in collecting and retrieving information from various sources
"""

from typing import Optional, Dict, Any, List
from crewai import Agent
from ..memory.research_memory import ResearchMemory
from ..tools.tools_manager import get_tools_manager
import logging

logger = logging.getLogger(__name__)


class InformationGathererAgent:
    """Information Gatherer - collects data from multiple sources"""
    
    def __init__(self, memory: ResearchMemory, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Information Gatherer agent
        
        Args:
            memory: Shared memory system
            config: Optional configuration
        """
        self.memory = memory
        self.config = config or {}
        self.tools_manager = get_tools_manager()
        self.tools = self._get_tools()
        self.agent = self._create_agent()
        logger.info("Information Gatherer agent initialized")
    
    def _get_tools(self) -> List[Any]:
        """Get tools for information gathering"""
        tools = self.tools_manager.get_tools_for_agent('information_gatherer')
        logger.info(f"Information Gatherer loaded {len(tools)} tools")
        return tools
    
    def _create_agent(self) -> Agent:
        """Create and configure the information gatherer agent"""
        return Agent(
            role="Information Gatherer",
            goal="""Collect comprehensive and reliable information by:
            1. Searching multiple sources for relevant data
            2. Evaluating source credibility and reliability
            3. Extracting key information and insights
            4. Organizing findings in a structured format
            5. Identifying gaps that need further investigation""",
            backstory="""You are a skilled information specialist with expertise in research 
            and data collection. You have years of experience in finding relevant information 
            from diverse sources, evaluating credibility, and extracting key insights. You're 
            meticulous about accuracy and always verify information from multiple sources when 
            possible. You excel at crafting effective search queries and know how to dig deep 
            to find comprehensive information on any topic.""",
            tools=self.tools,
            verbose=self.config.get('verbose', True),
            max_iter=self.config.get('max_iterations', 5),
            memory=True,
            callbacks=[self._agent_callback]
        )
    
    def _agent_callback(self, event: Dict[str, Any]) -> None:
        """Callback for agent events"""
        event_type = event.get('type', 'unknown')
        logger.debug(f"Gatherer event: {event_type}")
        
        # Track important events
        if event_type == 'tool_use':
            tool_name = event.get('tool')
            self.memory.store_short_term(f"gatherer_tool_use_{tool_name}", event)
        
        if event_type == 'source_found':
            source = event.get('source')
            # Store reliable sources in long-term memory
            if self._is_reliable_source(source):
                self.memory.store_long_term('reliable_sources', source, 'append')
        
        # Share progress
        if event_type in ['search_completed', 'extraction_completed']:
            self.memory.share_data(
                'information_gatherer',
                {
                    'status': 'in_progress',
                    'last_action': event_type,
                    'timestamp': event.get('timestamp')
                }
            )
    
    def _is_reliable_source(self, source: Dict[str, Any]) -> bool:
        """Check if a source is reliable"""
        if not isinstance(source, dict):
            return False
        
        # Simple heuristic for reliability
        reliability_indicators = [
            '.edu' in source.get('url', ''),
            '.gov' in source.get('url', ''),
            'peer-reviewed' in source.get('description', '').lower(),
            'academic' in source.get('type', '').lower(),
            source.get('credibility_score', 0) > 0.7
        ]
        
        # More lenient: require at least 1 strong indicator
        return sum(reliability_indicators) >= 1
    
    def search_information(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for information based on query
        
        Args:
            query: Search query
            context: Optional context from coordinator
            
        Returns:
            Search results and metadata
        """
        logger.info(f"Searching information for: {query}")
        
        # Store query in memory
        self.memory.store_short_term('current_search_query', query)
        
        # Prepare search strategy
        search_strategy = self._prepare_search_strategy(query, context)
        
        # Store strategy in memory
        self.memory.store_short_term('search_strategy', search_strategy)
        
        # Share status
        self.memory.share_data(
            'information_gatherer',
            {
                'status': 'searching',
                'query': query,
                'strategy': search_strategy
            }
        )
        
        return {
            'query': query,
            'strategy': search_strategy,
            'status': 'ready'
        }
    
    def _prepare_search_strategy(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare search strategy based on query and context"""
        strategy = {
            'primary_searches': [],
            'fallback_searches': [],
            'source_types': [],
            'depth': 'standard'
        }
        
        # Analyze query
        query_lower = query.lower()
        
        # Determine search depth
        if context:
            complexity = context.get('complexity', 'medium')
            if complexity == 'high':
                strategy['depth'] = 'comprehensive'
            elif complexity == 'low':
                strategy['depth'] = 'quick'
        
        # Determine source types needed
        if 'research' in query_lower or 'study' in query_lower:
            strategy['source_types'].append('academic')
        if 'news' in query_lower or 'current' in query_lower or 'latest' in query_lower:
            strategy['source_types'].append('news')
        if 'how to' in query_lower or 'guide' in query_lower:
            strategy['source_types'].append('tutorial')
        
        # Default to general if no specific type
        if not strategy['source_types']:
            strategy['source_types'].append('general')
        
        # Create search variations
        strategy['primary_searches'] = self._create_search_queries(query)
        strategy['fallback_searches'] = self._create_fallback_queries(query)
        
        return strategy
    
    def _create_search_queries(self, query: str) -> List[str]:
        """Create variations of search queries"""
        queries = [query]  # Original query
        
        # Add quoted version for exact match
        if '"' not in query:
            queries.append(f'"{query}"')
        
        # Add academic version
        if 'research' not in query.lower():
            queries.append(f"{query} research study")
        
        # Add recent version - use current year
        import datetime
        current_year = datetime.datetime.now().year
        if not any(word in query.lower() for word in ['recent', 'latest', str(current_year), str(current_year-1)]):
            queries.append(f"{query} {current_year-1}")  # Use previous year for more results
        
        return queries[:3]  # Limit to 3 queries
    
    def _create_fallback_queries(self, query: str) -> List[str]:
        """Create fallback queries if primary searches fail"""
        # Simplify query by removing adjectives and keeping key nouns
        words = query.split()
        
        # Simple heuristic: keep words that are likely nouns (capitalized or long)
        key_words = [w for w in words if len(w) > 4 or w[0].isupper()]
        
        if len(key_words) >= 2:
            return [' '.join(key_words)]
        
        return []
    
    def evaluate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate and rank sources by reliability
        
        Args:
            sources: List of sources to evaluate
            
        Returns:
            Evaluated and ranked sources
        """
        evaluated_sources = []
        
        for source in sources:
            evaluation = {
                'source': source,
                'reliability_score': self._calculate_reliability_score(source),
                'relevance_score': source.get('relevance_score', 0.5),
                'recency_score': self._calculate_recency_score(source),
                'overall_score': 0.0
            }
            
            # Calculate overall score
            evaluation['overall_score'] = (
                evaluation['reliability_score'] * 0.4 +
                evaluation['relevance_score'] * 0.4 +
                evaluation['recency_score'] * 0.2
            )
            
            evaluated_sources.append(evaluation)
        
        # Sort by overall score
        evaluated_sources.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Store top sources in memory
        top_sources = [e['source'] for e in evaluated_sources[:5]]
        self.memory.store_short_term('top_sources', top_sources)
        
        return evaluated_sources
    
    def _calculate_reliability_score(self, source: Dict[str, Any]) -> float:
        """Calculate reliability score for a source"""
        score = 0.5  # Base score
        
        url = source.get('url', '')
        
        # Domain-based scoring
        if '.edu' in url:
            score += 0.3
        elif '.gov' in url:
            score += 0.3
        elif '.org' in url:
            score += 0.1
        
        # Source type scoring
        source_type = source.get('type', '').lower()
        if 'academic' in source_type:
            score += 0.2
        elif 'news' in source_type and any(domain in url for domain in ['reuters', 'bbc', 'nytimes']):
            score += 0.1
        
        # Has author
        if source.get('author'):
            score += 0.1
        
        # Has date
        if source.get('date'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_recency_score(self, source: Dict[str, Any]) -> float:
        """Calculate recency score for a source"""
        # Simple implementation - in production would parse dates
        date_str = source.get('date', '')
        
        if '2025' in date_str:
            return 1.0
        elif '2024' in date_str:
            return 0.9
        elif '2023' in date_str:
            return 0.7
        elif '2022' in date_str:
            return 0.5
        else:
            return 0.3
    
    def extract_key_information(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract key information from sources
        
        Args:
            sources: Evaluated sources
            
        Returns:
            Extracted information organized by topic
        """
        extracted_info = {
            'main_findings': [],
            'supporting_evidence': [],
            'contradictions': [],
            'gaps': [],
            'sources_used': []
        }
        
        # Process each source
        for source_eval in sources[:10]:  # Limit to top 10
            source = source_eval['source']
            content = source.get('content', '')
            
            # Extract findings (simplified - in production would use NLP)
            if content:
                # Add source reference
                source_ref = {
                    'url': source.get('url'),
                    'title': source.get('title'),
                    'reliability': source_eval['reliability_score']
                }
                extracted_info['sources_used'].append(source_ref)
                
                # Simple extraction based on keywords
                if any(word in content.lower() for word in ['found', 'discovered', 'revealed']):
                    extracted_info['main_findings'].append({
                        'finding': content[:200] + '...',
                        'source': source_ref
                    })
        
        # Store in memory
        self.memory.store_short_term('extracted_information', extracted_info)
        
        # Share completion status
        self.memory.share_data(
            'information_gatherer',
            {
                'status': 'completed',
                'sources_found': len(sources),
                'findings_extracted': len(extracted_info['main_findings'])
            }
        )
        
        return extracted_info
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent