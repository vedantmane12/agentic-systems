"""
Tests for Content Synthesizer Agent
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

from backend.features.agents.synthesizer import ContentSynthesizerAgent
from backend.features.memory.research_memory import ResearchMemory


class TestContentSynthesizerAgent:
    """Test cases for Content Synthesizer Agent"""
    
    @pytest.fixture
    def memory(self):
        """Create memory instance"""
        return ResearchMemory()
    
    @pytest.fixture
    def synthesizer(self, memory):
        """Create synthesizer agent"""
        return ContentSynthesizerAgent(memory)
    
    @pytest.fixture
    def sample_gathered_info(self):
        """Sample gathered information"""
        return {
            'main_findings': [
                {
                    'finding': 'AI adoption is increasing in healthcare',
                    'source': {'title': 'Medical AI Study', 'url': 'https://med.edu/study'}
                },
                {
                    'finding': 'Machine learning improves diagnostic accuracy',
                    'source': {'title': 'Healthcare Report', 'url': 'https://health.gov/report'}
                }
            ],
            'sources_used': [
                {
                    'title': 'Medical AI Study',
                    'url': 'https://med.edu/study',
                    'reliability': 0.9
                },
                {
                    'title': 'Healthcare Report',
                    'url': 'https://health.gov/report',
                    'reliability': 0.85
                }
            ]
        }
    
    @pytest.fixture
    def sample_analysis_results(self):
        """Sample analysis results"""
        return {
            'patterns': [
                {'theme': 'improvement', 'strength': 'strong', 'frequency': 3},
                {'theme': 'adoption', 'strength': 'moderate', 'frequency': 2}
            ],
            'insights': [
                {
                    'type': 'trend',
                    'content': 'Healthcare AI shows consistent growth',
                    'confidence': 0.85
                },
                {
                    'type': 'impact',
                    'content': 'Diagnostic accuracy improvements are significant',
                    'confidence': 0.75
                }
            ],
            'contradictions': [],
            'confidence_levels': {
                'overall': 0.8,
                'source_reliability': 0.875,
                'data_completeness': 0.7
            }
        }
    
    def test_initialization(self, synthesizer):
        """Test agent initialization"""
        assert synthesizer is not None
        assert synthesizer.agent is not None
        assert synthesizer.memory is not None
        assert synthesizer.tools is not None
        
        # Check agent properties
        agent = synthesizer.get_agent()
        assert agent.role == "Content Synthesizer"
    
    def test_synthesize_report(self, synthesizer, sample_gathered_info, sample_analysis_results):
        """Test report synthesis"""
        query = "What is the impact of AI on healthcare?"
        
        report = synthesizer.synthesize_report(
            query,
            sample_gathered_info,
            sample_analysis_results
        )
        
        # Check report structure
        assert 'title' in report
        assert 'executive_summary' in report
        assert 'introduction' in report
        assert 'methodology' in report
        assert 'findings' in report
        assert 'analysis' in report
        assert 'conclusions' in report
        assert 'recommendations' in report
        assert 'references' in report
        assert 'metadata' in report
        
        # Check content
        assert report['title'].startswith('Research Report:')
        assert len(report['executive_summary']) > 0
        assert len(report['conclusions']) > 0
        assert len(report['recommendations']) > 0
        assert len(report['references']) == len(sample_gathered_info['sources_used'])
        
        # Check metadata
        assert report['metadata']['query'] == query
        assert report['metadata']['confidence_score'] == 0.8
        
        # Check memory
        stored = synthesizer.memory.get_short_term('completed_report')
        assert stored == report
    
    def test_generate_title(self, synthesizer):
        """Test title generation"""
        queries = [
            ("What is machine learning?", "Research Report: What Is Machine Learning"),
            ("How does AI work?", "Research Report: How Does AI Work"),
            ("impact of climate change", "Research Report: Impact Of Climate Change")
        ]
        
        for query, expected in queries:
            title = synthesizer._generate_title(query)
            assert title == expected
    
    def test_create_executive_summary(self, synthesizer, sample_gathered_info, sample_analysis_results):
        """Test executive summary creation"""
        query = "AI in healthcare"
        
        summary = synthesizer._create_executive_summary(
            query,
            sample_gathered_info,
            sample_analysis_results
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert query in summary
        assert "2 sources" in summary
        assert "2 key findings" in summary
        assert "high reliability" in summary.lower()
    
    def test_create_methodology(self, synthesizer, sample_gathered_info):
        """Test methodology section creation"""
        methodology = synthesizer._create_methodology(sample_gathered_info)
        
        assert isinstance(methodology, str)
        assert "systematic approach" in methodology
        assert "2 sources" in methodology
        assert "Information Gathering" in methodology
        assert "Source Evaluation" in methodology
        assert "Data Analysis" in methodology
        assert "Synthesis" in methodology
    
    def test_organize_findings(self, synthesizer, sample_gathered_info, sample_analysis_results):
        """Test findings organization"""
        organized = synthesizer._organize_findings(
            sample_gathered_info,
            sample_analysis_results
        )
        
        assert isinstance(organized, list)
        assert len(organized) > 0
        
        # Check structure
        for finding_group in organized:
            assert 'theme' in finding_group
            assert 'findings' in finding_group
            assert 'pattern_strength' in finding_group
        
        # Should have grouped by patterns
        themes = [f['theme'] for f in organized]
        # Themes might be lowercase or title case
        assert any('improvement' in t.lower() for t in themes) or any('adoption' in t.lower() for t in themes)
    
    def test_create_analysis_section(self, synthesizer, sample_analysis_results):
        """Test analysis section creation"""
        analysis = synthesizer._create_analysis_section(sample_analysis_results)
        
        assert isinstance(analysis, dict)
        assert 'patterns' in analysis
        assert 'insights' in analysis
        assert 'confidence' in analysis
        
        # Check patterns
        assert len(analysis['patterns']['items']) == 2
        
        # Check insights
        assert len(analysis['insights']['items']) == 2
        assert all('confidence' in i for i in analysis['insights']['items'])
        
        # Check confidence
        assert analysis['confidence']['overall'] == 0.8
    
    def test_create_conclusions(self, synthesizer, sample_analysis_results):
        """Test conclusions creation"""
        conclusions = synthesizer._create_conclusions(sample_analysis_results)
        
        assert isinstance(conclusions, list)
        assert len(conclusions) > 0
        
        # Should mention patterns
        assert any('pattern' in c.lower() for c in conclusions)
        
        # Should mention confidence
        assert any('well-supported' in c or 'reliable' in c for c in conclusions)
    
    def test_create_recommendations(self, synthesizer, sample_analysis_results):
        """Test recommendations creation"""
        query = "AI healthcare impact"
        
        recommendations = synthesizer._create_recommendations(
            query,
            sample_analysis_results
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check structure
        for rec in recommendations:
            assert 'priority' in rec
            assert 'recommendation' in rec
            assert 'rationale' in rec
        
        # Should have high priority items
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        assert len(high_priority) > 0
    
    def test_compile_references(self, synthesizer, sample_gathered_info):
        """Test reference compilation"""
        references = synthesizer._compile_references(sample_gathered_info)
        
        assert isinstance(references, list)
        assert len(references) == len(sample_gathered_info['sources_used'])
        
        # Check structure
        for i, ref in enumerate(references):
            assert ref['id'] == f"[{i+1}]"
            assert 'title' in ref
            assert 'url' in ref
            assert 'reliability' in ref
        
        # Check content
        assert references[0]['title'] == 'Medical AI Study'
        assert references[0]['reliability'] == '90%'
    
    def test_estimate_word_count(self, synthesizer):
        """Test word count estimation"""
        report = {
            'title': 'Test Report',
            'summary': 'This is a test summary with several words',
            'sections': [
                'First section content',
                'Second section with more content'
            ],
            'nested': {
                'content': 'Nested content here'
            }
        }
        
        count = synthesizer._estimate_word_count(report)
        assert count > 0
        assert count >= 15  # Minimum expected words
    
    def test_create_summary(self, synthesizer):
        """Test summary creation from report"""
        report = {
            'title': 'AI Research Report',
            'executive_summary': 'This report explores AI impact on healthcare.',
            'conclusions': [
                'AI improves diagnostic accuracy',
                'Implementation challenges remain'
            ],
            'recommendations': [
                {
                    'priority': 'high',
                    'recommendation': 'Invest in AI training'
                }
            ]
        }
        
        summary = synthesizer.create_summary(report, max_length=50)
        
        assert isinstance(summary, str)
        assert 'AI Research Report' in summary
        assert len(summary.split()) <= 50
    
    def test_agent_callback(self, synthesizer):
        """Test agent callback functionality"""
        # Test synthesis started
        event = {
            'type': 'synthesis_started',
            'task': 'Creating report'
        }
        synthesizer._agent_callback(event)
        
        stored = synthesizer.memory.get_short_term('synthesizer_current_task')
        assert stored == event
        
        # Test section completed
        section_event = {
            'type': 'section_completed',
            'section': 'introduction'
        }
        synthesizer._agent_callback(section_event)
        
        stored = synthesizer.memory.get_short_term('completed_section_introduction')
        assert stored == section_event
        
        # Test report completed
        complete_event = {
            'type': 'report_completed',
            'report_type': 'research'
        }
        synthesizer._agent_callback(complete_event)
        
        shared = synthesizer.memory.get_shared_data('content_synthesizer')
        assert shared['status'] == 'completed'
        assert shared['report_type'] == 'research'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])