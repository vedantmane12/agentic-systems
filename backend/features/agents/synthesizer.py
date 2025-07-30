"""
Content Synthesizer Agent
Specializes in creating comprehensive research reports
"""

from typing import Optional, Dict, Any, List
from crewai import Agent
from ..memory.research_memory import ResearchMemory
from ..tools.tools_manager import get_tools_manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContentSynthesizerAgent:
    """Content Synthesizer - creates final research reports and summaries"""
    
    def __init__(self, memory: ResearchMemory, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Content Synthesizer agent
        
        Args:
            memory: Shared memory system
            config: Optional configuration
        """
        self.memory = memory
        self.config = config or {}
        self.tools_manager = get_tools_manager()
        self.tools = self._get_tools()
        self.agent = self._create_agent()
        logger.info("Content Synthesizer agent initialized")
    
    def _get_tools(self) -> List[Any]:
        """Get tools for content synthesis"""
        tools = self.tools_manager.get_tools_for_agent('content_synthesizer')
        logger.info(f"Content Synthesizer loaded {len(tools)} tools")
        return tools
    
    def _create_agent(self) -> Agent:
        """Create and configure the content synthesizer agent"""
        return Agent(
            role="Content Synthesizer",
            goal="""Create comprehensive and well-structured research reports by:
            1. Synthesizing findings from multiple sources into coherent narratives
            2. Organizing information in logical, easy-to-follow structures
            3. Writing clear, concise, and engaging content
            4. Ensuring proper citations and references
            5. Creating executive summaries and actionable recommendations""",
            backstory="""You are a skilled writer and research synthesizer with expertise in 
            creating comprehensive reports and documentation. You excel at taking complex 
            information from multiple sources and transforming it into clear, accessible, and 
            actionable content. You have experience in academic writing, business reporting, 
            and technical documentation. You understand how to structure information for maximum 
            impact and clarity, and you always ensure proper attribution and citations.""",
            tools=self.tools,
            verbose=self.config.get('verbose', True),
            max_iter=self.config.get('max_iterations', 5),
            memory=True,
            callbacks=[self._agent_callback]
        )
    
    def _agent_callback(self, event: Dict[str, Any]) -> None:
        """Callback for agent events"""
        event_type = event.get('type', 'unknown')
        logger.debug(f"Synthesizer event: {event_type}")
        
        # Track synthesis events
        if event_type == 'synthesis_started':
            self.memory.store_short_term('synthesizer_current_task', event)
        
        if event_type == 'section_completed':
            section = event.get('section')
            self.memory.store_short_term(f'completed_section_{section}', event)
        
        if event_type == 'report_completed':
            self.memory.share_data(
                'content_synthesizer',
                {
                    'status': 'completed',
                    'report_type': event.get('report_type', 'research'),
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    def synthesize_report(self, 
                         query: str,
                         gathered_info: Dict[str, Any],
                         analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize a comprehensive research report
        
        Args:
            query: Original research query
            gathered_info: Information from gatherer agent
            analysis_results: Results from analyst agent
            
        Returns:
            Complete research report
        """
        logger.info(f"Synthesizing report for query: {query}")
        
        # Store inputs
        self.memory.store_short_term('synthesis_inputs', {
            'query': query,
            'gathered_info': gathered_info,
            'analysis_results': analysis_results
        })
        
        # Create report structure
        report = {
            'title': self._generate_title(query),
            'executive_summary': '',
            'introduction': '',
            'methodology': '',
            'findings': [],
            'analysis': {},
            'conclusions': [],
            'recommendations': [],
            'references': [],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'query': query,
                'confidence_score': analysis_results.get('confidence_levels', {}).get('overall', 0.5)
            }
        }
        
        # Generate each section
        report['executive_summary'] = self._create_executive_summary(
            query, gathered_info, analysis_results
        )
        
        report['introduction'] = self._create_introduction(query, gathered_info)
        
        report['methodology'] = self._create_methodology(gathered_info)
        
        report['findings'] = self._organize_findings(gathered_info, analysis_results)
        
        report['analysis'] = self._create_analysis_section(analysis_results)
        
        report['conclusions'] = self._create_conclusions(analysis_results)
        
        report['recommendations'] = self._create_recommendations(
            query, analysis_results
        )
        
        report['references'] = self._compile_references(gathered_info)
        
        # Store completed report
        self.memory.store_short_term('completed_report', report)
        self.memory.share_data(
            'content_synthesizer',
            {
                'status': 'completed',
                'report_sections': len([k for k, v in report.items() if v]),
                'word_count': self._estimate_word_count(report)
            }
        )
        
        return report
    
    def _generate_title(self, query: str) -> str:
        """Generate a title for the report"""
        # Simple title generation - preserve certain acronyms
        words = query.strip('?').split()
        
        # Preserve common acronyms
        acronyms = ['AI', 'ML', 'NLP', 'API', 'URL', 'PDF', 'CSV']
        
        titled_words = []
        for word in words:
            if word.upper() in acronyms:
                titled_words.append(word.upper())
            else:
                titled_words.append(word.capitalize())
        
        base_title = ' '.join(titled_words)
        return f"Research Report: {base_title}"
    
    def _create_executive_summary(self, 
                                 query: str,
                                 gathered_info: Dict[str, Any],
                                 analysis_results: Dict[str, Any]) -> str:
        """Create executive summary"""
        summary_parts = []
        
        # Opening
        summary_parts.append(f"This report addresses the research query: '{query}'")
        
        # Key findings count
        findings_count = len(gathered_info.get('main_findings', []))
        sources_count = len(gathered_info.get('sources_used', []))
        summary_parts.append(
            f"Based on analysis of {sources_count} sources and {findings_count} key findings:"
        )
        
        # Main insights
        insights = analysis_results.get('insights', [])
        if insights:
            high_conf = [i for i in insights if i.get('confidence', 0) > 0.7]
            if high_conf:
                summary_parts.append(
                    f"The analysis revealed {len(high_conf)} high-confidence insights."
                )
        
        # Patterns
        patterns = analysis_results.get('patterns', [])
        if patterns:
            strong_patterns = [p for p in patterns if p.get('strength') == 'strong']
            if strong_patterns:
                themes = [p['theme'] for p in strong_patterns]
                summary_parts.append(
                    f"Strong patterns identified in: {', '.join(themes)}."
                )
        
        # Confidence
        confidence = analysis_results.get('confidence_levels', {}).get('overall', 0)
        if confidence > 0.7:
            summary_parts.append("The findings demonstrate high reliability and consistency.")
        elif confidence > 0.5:
            summary_parts.append("The findings show moderate reliability with some variations.")
        else:
            summary_parts.append("Additional research is recommended to strengthen conclusions.")
        
        return " ".join(summary_parts)
    
    def _create_introduction(self, query: str, gathered_info: Dict[str, Any]) -> str:
        """Create introduction section"""
        intro_parts = []
        
        # Context
        intro_parts.append(f"This research report explores: {query}")
        
        # Scope
        sources = gathered_info.get('sources_used', [])
        if sources:
            source_types = set()
            for source in sources:
                if 'url' in source:
                    if '.edu' in source['url']:
                        source_types.add('academic')
                    elif '.gov' in source['url']:
                        source_types.add('government')
                    else:
                        source_types.add('general')
            
            if source_types:
                intro_parts.append(
                    f"The research encompasses {', '.join(source_types)} sources "
                    f"to provide a comprehensive perspective."
                )
        
        # Objectives
        intro_parts.append(
            "The objectives of this report are to: "
            "1) Gather relevant information, "
            "2) Analyze key patterns and insights, "
            "3) Provide actionable conclusions and recommendations."
        )
        
        return " ".join(intro_parts)
    
    def _create_methodology(self, gathered_info: Dict[str, Any]) -> str:
        """Create methodology section"""
        method_parts = []
        
        method_parts.append("This research employed a systematic approach:")
        
        # Search strategy
        method_parts.append(
            "1. Information Gathering: Comprehensive search across multiple sources "
            "using targeted queries and academic databases."
        )
        
        # Source evaluation
        sources_count = len(gathered_info.get('sources_used', []))
        method_parts.append(
            f"2. Source Evaluation: {sources_count} sources were evaluated for "
            "credibility, relevance, and recency."
        )
        
        # Analysis
        method_parts.append(
            "3. Data Analysis: Pattern identification, comparative analysis, "
            "and insight generation using systematic analytical methods."
        )
        
        # Synthesis
        method_parts.append(
            "4. Synthesis: Integration of findings into coherent conclusions "
            "and actionable recommendations."
        )
        
        return " ".join(method_parts)
    
    def _organize_findings(self, 
                          gathered_info: Dict[str, Any],
                          analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Organize findings into structured format"""
        organized_findings = []
        
        # Get raw findings
        raw_findings = gathered_info.get('main_findings', [])
        patterns = analysis_results.get('patterns', [])
        
        # Group by pattern themes if available
        if patterns:
            for pattern in patterns:
                theme = pattern['theme']
                related_findings = [
                    f for f in raw_findings 
                    if theme.lower() in f.get('finding', '').lower()
                ]
                
                if related_findings:
                    organized_findings.append({
                        'theme': theme.title(),
                        'findings': related_findings,
                        'pattern_strength': pattern.get('strength', 'moderate')
                    })
        
        # Add ungrouped findings
        grouped_findings = set()
        for of in organized_findings:
            for f in of['findings']:
                grouped_findings.add(f.get('finding', ''))
        
        ungrouped = [
            f for f in raw_findings 
            if f.get('finding', '') not in grouped_findings
        ]
        
        if ungrouped:
            organized_findings.append({
                'theme': 'Additional Findings',
                'findings': ungrouped,
                'pattern_strength': 'individual'
            })
        
        return organized_findings
    
    def _create_analysis_section(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create analysis section"""
        analysis_section = {}
        
        # Patterns
        patterns = analysis_results.get('patterns', [])
        if patterns:
            analysis_section['patterns'] = {
                'description': 'The following patterns emerged from the data:',
                'items': [
                    f"{p['theme'].title()} trend ({p['strength']} strength)"
                    for p in patterns
                ]
            }
        
        # Insights
        insights = analysis_results.get('insights', [])
        if insights:
            analysis_section['insights'] = {
                'description': 'Key insights from the analysis:',
                'items': [
                    {
                        'content': i['content'],
                        'confidence': i.get('confidence', 0.5),
                        'type': i.get('type', 'general')
                    }
                    for i in insights
                ]
            }
        
        # Contradictions
        contradictions = analysis_results.get('contradictions', [])
        if contradictions:
            analysis_section['contradictions'] = {
                'description': 'Conflicting information was identified:',
                'items': [
                    f"{c['source1']} vs {c['source2']}: {c['conflict']}"
                    for c in contradictions
                ]
            }
        
        # Confidence assessment
        confidence = analysis_results.get('confidence_levels', {})
        analysis_section['confidence'] = {
            'overall': confidence.get('overall', 0.5),
            'source_reliability': confidence.get('source_reliability', 0.5),
            'data_completeness': confidence.get('data_completeness', 0.5)
        }
        
        return analysis_section
    
    def _create_conclusions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Create conclusions based on analysis"""
        conclusions = []
        
        # Based on patterns
        patterns = analysis_results.get('patterns', [])
        strong_patterns = [p for p in patterns if p.get('strength') == 'strong']
        
        if strong_patterns:
            conclusions.append(
                f"The research identifies {len(strong_patterns)} strong patterns, "
                f"indicating clear trends in the data."
            )
        
        # Based on insights
        insights = analysis_results.get('insights', [])
        high_conf_insights = [i for i in insights if i.get('confidence', 0) > 0.7]
        
        if high_conf_insights:
            conclusions.append(
                f"Analysis reveals {len(high_conf_insights)} high-confidence insights "
                f"that provide actionable understanding."
            )
        
        # Based on overall confidence
        overall_conf = analysis_results.get('confidence_levels', {}).get('overall', 0.5)
        if overall_conf > 0.7:
            conclusions.append(
                "The findings are well-supported by reliable sources and consistent data."
            )
        elif overall_conf < 0.5:
            conclusions.append(
                "The current evidence base is limited; additional research is recommended."
            )
        
        # Summary conclusion
        conclusions.append(
            "This research provides valuable insights into the topic, "
            "though continued monitoring and analysis are advised."
        )
        
        return conclusions
    
    def _create_recommendations(self, 
                               query: str,
                               analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create actionable recommendations"""
        recommendations = []
        
        # Based on insights
        insights = analysis_results.get('insights', [])
        
        for i, insight in enumerate(insights[:3]):  # Top 3 insights
            if insight.get('confidence', 0) > 0.6:
                recommendations.append({
                    'priority': 'high' if insight.get('confidence', 0) > 0.8 else 'medium',
                    'recommendation': f"Based on {insight['type']} analysis: {insight['content']}",
                    'rationale': f"Confidence level: {insight.get('confidence', 0):.0%}"
                })
        
        # Based on gaps or limitations
        if analysis_results.get('confidence_levels', {}).get('data_completeness', 1) < 0.5:
            recommendations.append({
                'priority': 'medium',
                'recommendation': "Conduct additional research to address data gaps",
                'rationale': "Current data completeness is below optimal levels"
            })
        
        # Based on contradictions
        if analysis_results.get('contradictions'):
            recommendations.append({
                'priority': 'medium',
                'recommendation': "Investigate and resolve conflicting information",
                'rationale': "Multiple contradictions identified in sources"
            })
        
        return recommendations
    
    def _compile_references(self, gathered_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """Compile references from sources"""
        references = []
        
        sources = gathered_info.get('sources_used', [])
        
        for i, source in enumerate(sources):
            reference = {
                'id': f"[{i+1}]",
                'title': source.get('title', 'Untitled'),
                'url': source.get('url', ''),
                'reliability': f"{source.get('reliability', 0):.0%}"
            }
            references.append(reference)
        
        return references
    
    def _estimate_word_count(self, report: Dict[str, Any]) -> int:
        """Estimate word count of the report"""
        total_words = 0
        
        # Count words in string fields
        for key, value in report.items():
            if isinstance(value, str):
                total_words += len(value.split())
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        total_words += len(item.split())
                    elif isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, str):
                                total_words += len(v.split())
        
        return total_words
    
    def create_summary(self, report: Dict[str, Any], max_length: int = 500) -> str:
        """
        Create a brief summary of the report
        
        Args:
            report: Complete report
            max_length: Maximum summary length in words
            
        Returns:
            Brief summary
        """
        summary_parts = []
        
        # Title
        summary_parts.append(report.get('title', 'Research Report'))
        
        # Executive summary (if short enough)
        exec_summary = report.get('executive_summary', '')
        if exec_summary and len(exec_summary.split()) < max_length / 2:
            summary_parts.append(exec_summary)
        
        # Key conclusions
        conclusions = report.get('conclusions', [])
        if conclusions:
            summary_parts.append("Key conclusions: " + conclusions[0])
        
        # Top recommendation
        recommendations = report.get('recommendations', [])
        if recommendations:
            top_rec = next(
                (r for r in recommendations if r.get('priority') == 'high'),
                recommendations[0] if recommendations else None
            )
            if top_rec:
                summary_parts.append(
                    f"Primary recommendation: {top_rec['recommendation']}"
                )
        
        # Join and trim
        summary = " ".join(summary_parts)
        words = summary.split()
        
        if len(words) > max_length:
            summary = " ".join(words[:max_length]) + "..."
        
        return summary
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent