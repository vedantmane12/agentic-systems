"""
Data Analyst Agent
Specializes in analyzing and processing collected information
"""

from typing import Optional, Dict, Any, List
from crewai import Agent
from ..memory.research_memory import ResearchMemory
from ..tools.tools_manager import get_tools_manager
import logging

logger = logging.getLogger(__name__)


class DataAnalystAgent:
    """Data Analyst - analyzes collected information and generates insights"""
    
    def __init__(self, memory: ResearchMemory, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Data Analyst agent
        
        Args:
            memory: Shared memory system
            config: Optional configuration
        """
        self.memory = memory
        self.config = config or {}
        self.tools_manager = get_tools_manager()
        self.tools = self._get_tools()
        self.agent = self._create_agent()
        logger.info("Data Analyst agent initialized")
    
    def _get_tools(self) -> List[Any]:
        """Get tools for data analysis"""
        tools = self.tools_manager.get_tools_for_agent('data_analyst')
        logger.info(f"Data Analyst loaded {len(tools)} tools")
        return tools
    
    def _create_agent(self) -> Agent:
        """Create and configure the data analyst agent"""
        return Agent(
            role="Data Analyst",
            goal="""Analyze collected information to generate meaningful insights by:
            1. Processing and organizing raw data from multiple sources
            2. Identifying patterns, trends, and correlations
            3. Performing comparative analysis across different sources
            4. Evaluating evidence quality and consistency
            5. Generating data-driven conclusions and recommendations""",
            backstory="""You are an expert data analyst with strong analytical and critical 
            thinking skills. You excel at finding patterns in complex information, identifying 
            key insights, and drawing meaningful conclusions from diverse data sources. You have 
            experience in both quantitative and qualitative analysis, and you're skilled at 
            synthesizing information to provide clear, actionable insights. You maintain 
            objectivity and always base your conclusions on evidence.""",
            tools=self.tools,
            verbose=self.config.get('verbose', True),
            max_iter=self.config.get('max_iterations', 5),
            memory=True,
            callbacks=[self._agent_callback]
        )
    
    def _agent_callback(self, event: Dict[str, Any]) -> None:
        """Callback for agent events"""
        event_type = event.get('type', 'unknown')
        logger.debug(f"Analyst event: {event_type}")
        
        # Track analysis events
        if event_type == 'analysis_started':
            self.memory.store_short_term('analyst_current_task', event)
        
        if event_type == 'pattern_found':
            pattern = event.get('pattern')
            self.memory.store_long_term('identified_patterns', pattern, 'append')
        
        if event_type == 'insight_generated':
            insight = event.get('insight')
            self.memory.share_data(
                'data_analyst',
                {
                    'type': 'insight',
                    'content': insight,
                    'confidence': event.get('confidence', 0.5)
                },
                priority='high'
            )
    
    def analyze_information(self, gathered_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze gathered information to extract insights
        
        Args:
            gathered_data: Data collected by information gatherer
            
        Returns:
            Analysis results with insights and patterns
        """
        logger.info("Starting information analysis")
        
        # Store input data
        self.memory.store_short_term('analysis_input', gathered_data)
        
        # Initialize analysis results
        analysis_results = {
            'patterns': [],
            'insights': [],
            'comparisons': [],
            'contradictions': [],
            'confidence_levels': {},
            'summary': ''
        }
        
        # Extract sources for analysis
        sources = gathered_data.get('sources_used', [])
        findings = gathered_data.get('main_findings', [])
        
        # Analyze patterns
        patterns = self._identify_patterns(findings)
        analysis_results['patterns'] = patterns
        
        # Generate insights
        insights = self._generate_insights(patterns, findings)
        analysis_results['insights'] = insights
        
        # Compare sources
        comparisons = self._compare_sources(sources)
        analysis_results['comparisons'] = comparisons
        
        # Identify contradictions
        contradictions = self._find_contradictions(findings)
        analysis_results['contradictions'] = contradictions
        
        # Calculate confidence levels
        confidence = self._calculate_confidence(sources, findings)
        analysis_results['confidence_levels'] = confidence
        
        # Generate summary
        analysis_results['summary'] = self._generate_summary(analysis_results)
        
        # Store results
        self.memory.store_short_term('analysis_results', analysis_results)
        self.memory.share_data(
            'data_analyst',
            {
                'status': 'completed',
                'patterns_found': len(patterns),
                'insights_generated': len(insights)
            }
        )
        
        return analysis_results
    
    def _identify_patterns(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify patterns in the findings"""
        patterns = []
        
        # Group findings by common themes (simplified)
        theme_counts = {}
        for finding in findings:
            content = finding.get('finding', '').lower()
            
            # Simple keyword-based pattern detection
            keywords = ['increase', 'decrease', 'growth', 'decline', 'improvement', 'impact']
            for keyword in keywords:
                if keyword in content:
                    theme_counts[keyword] = theme_counts.get(keyword, 0) + 1
        
        # Convert to patterns
        for theme, count in theme_counts.items():
            if count >= 2:  # Pattern threshold
                patterns.append({
                    'type': 'trend',
                    'theme': theme,
                    'frequency': count,
                    'strength': 'strong' if count >= 3 else 'moderate'
                })
        
        return patterns
    
    def _generate_insights(self, patterns: List[Dict[str, Any]], 
                          findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights from patterns and findings"""
        insights = []
        
        # Insight from patterns
        for pattern in patterns:
            if pattern['strength'] == 'strong':
                insights.append({
                    'type': 'pattern-based',
                    'content': f"Strong {pattern['theme']} trend observed across multiple sources",
                    'confidence': 0.8,
                    'supporting_evidence': pattern['frequency']
                })
        
        # Insight from finding count
        if len(findings) > 5:
            insights.append({
                'type': 'coverage',
                'content': "Comprehensive coverage with multiple corroborating sources",
                'confidence': 0.9,
                'supporting_evidence': len(findings)
            })
        elif len(findings) < 2:
            insights.append({
                'type': 'limitation',
                'content': "Limited data available, additional research recommended",
                'confidence': 0.5,
                'supporting_evidence': len(findings)
            })
        
        return insights
    
    def _compare_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compare different sources"""
        comparisons = []
        
        # Group sources by type
        source_types = {}
        for source in sources:
            s_type = self._categorize_source(source.get('url', ''))
            if s_type not in source_types:
                source_types[s_type] = []
            source_types[s_type].append(source)
        
        # Compare reliability across types
        for s_type, type_sources in source_types.items():
            avg_reliability = sum(s.get('reliability', 0.5) for s in type_sources) / len(type_sources)
            comparisons.append({
                'source_type': s_type,
                'count': len(type_sources),
                'avg_reliability': avg_reliability,
                'assessment': 'high' if avg_reliability > 0.7 else 'moderate'
            })
        
        return comparisons
    
    def _categorize_source(self, url: str) -> str:
        """Categorize source by URL"""
        if '.edu' in url:
            return 'academic'
        elif '.gov' in url:
            return 'government'
        elif any(news in url for news in ['news', 'times', 'post']):
            return 'news'
        else:
            return 'other'
    
    def _find_contradictions(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify contradictions in findings"""
        contradictions = []
        
        # Simple contradiction detection based on opposing keywords
        opposing_pairs = [
            ('increase', 'decrease'),
            ('positive', 'negative'),
            ('growth', 'decline'),
            ('improvement', 'deterioration')
        ]
        
        for i, finding1 in enumerate(findings):
            content1 = finding1.get('finding', '').lower()
            
            for j, finding2 in enumerate(findings[i+1:], i+1):
                content2 = finding2.get('finding', '').lower()
                
                # Check for opposing terms
                for term1, term2 in opposing_pairs:
                    if (term1 in content1 and term2 in content2) or \
                       (term2 in content1 and term1 in content2):
                        contradictions.append({
                            'type': 'opposing_claims',
                            'source1': finding1.get('source', {}).get('title', 'Unknown'),
                            'source2': finding2.get('source', {}).get('title', 'Unknown'),
                            'conflict': f"{term1} vs {term2}"
                        })
        
        return contradictions
    
    def _calculate_confidence(self, sources: List[Dict[str, Any]], 
                            findings: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate confidence levels for different aspects"""
        confidence = {}
        
        # Source reliability confidence
        if sources:
            avg_reliability = sum(s.get('reliability', 0.5) for s in sources) / len(sources)
            confidence['source_reliability'] = avg_reliability
        else:
            confidence['source_reliability'] = 0.0
        
        # Data completeness confidence
        confidence['data_completeness'] = min(len(findings) / 10.0, 1.0)
        
        # Consistency confidence (based on contradictions)
        # This would be calculated after contradiction analysis
        confidence['consistency'] = 0.8  # Default high consistency
        
        # Overall confidence
        confidence['overall'] = sum(confidence.values()) / len(confidence)
        
        return confidence
    
    def _generate_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a summary of the analysis"""
        patterns = analysis_results.get('patterns', [])
        insights = analysis_results.get('insights', [])
        confidence = analysis_results.get('confidence_levels', {})
        
        summary_parts = []
        
        # Pattern summary
        if patterns:
            summary_parts.append(f"Identified {len(patterns)} significant patterns")
        
        # Insight summary
        if insights:
            high_conf_insights = [i for i in insights if i.get('confidence', 0) > 0.7]
            if high_conf_insights:
                summary_parts.append(f"{len(high_conf_insights)} high-confidence insights generated")
        
        # Confidence summary
        overall_conf = confidence.get('overall', 0)
        if overall_conf > 0.7:
            summary_parts.append("High overall confidence in analysis")
        elif overall_conf > 0.5:
            summary_parts.append("Moderate confidence in analysis")
        else:
            summary_parts.append("Low confidence - additional data recommended")
        
        return ". ".join(summary_parts)
    
    def perform_comparative_analysis(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comparative analysis across multiple datasets
        
        Args:
            datasets: List of datasets to compare
            
        Returns:
            Comparative analysis results
        """
        logger.info(f"Performing comparative analysis on {len(datasets)} datasets")
        
        comparative_results = {
            'similarities': [],
            'differences': [],
            'trends': [],
            'recommendations': []
        }
        
        # Store in memory
        self.memory.store_short_term('comparative_analysis_input', datasets)
        
        # Analysis logic would go here
        # For now, return structured results
        
        return comparative_results
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent