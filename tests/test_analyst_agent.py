"""
Tests for Data Analyst Agent
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

from backend.features.agents.analyst import DataAnalystAgent
from backend.features.memory.research_memory import ResearchMemory


class TestDataAnalystAgent:
    """Test cases for Data Analyst Agent"""
    
    @pytest.fixture
    def memory(self):
        """Create memory instance"""
        return ResearchMemory()
    
    @pytest.fixture
    def analyst(self, memory):
        """Create analyst agent"""
        return DataAnalystAgent(memory)
    
    def test_initialization(self, analyst):
        """Test agent initialization"""
        assert analyst is not None
        assert analyst.agent is not None
        assert analyst.memory is not None
        assert analyst.tools is not None
        assert len(analyst.tools) >= 1  # Should have at least FileReadTool
        
        # Check agent properties
        agent = analyst.get_agent()
        assert agent.role == "Data Analyst"
        assert len(agent.tools) >= 1
    
    def test_analyze_information(self, analyst):
        """Test information analysis"""
        gathered_data = {
            'sources_used': [
                {'url': 'https://example.edu', 'title': 'Study 1', 'reliability': 0.9},
                {'url': 'https://example.gov', 'title': 'Report 2', 'reliability': 0.8}
            ],
            'main_findings': [
                {
                    'finding': 'AI technology shows significant improvement in healthcare',
                    'source': {'title': 'Study 1'}
                },
                {
                    'finding': 'Machine learning demonstrates growth in adoption',
                    'source': {'title': 'Report 2'}
                }
            ]
        }
        
        results = analyst.analyze_information(gathered_data)
        
        assert 'patterns' in results
        assert 'insights' in results
        assert 'comparisons' in results
        assert 'contradictions' in results
        assert 'confidence_levels' in results
        assert 'summary' in results
        
        # Check memory storage
        stored = analyst.memory.get_short_term('analysis_results')
        assert stored == results
        
        # Check shared data
        shared = analyst.memory.get_shared_data('data_analyst')
        assert shared['status'] == 'completed'
    
    def test_identify_patterns(self, analyst):
        """Test pattern identification"""
        findings = [
            {'finding': 'Sales show increase over time'},
            {'finding': 'Revenue demonstrates growth pattern'},
            {'finding': 'Market share increase observed'},
            {'finding': 'Customer satisfaction shows improvement'}
        ]
        
        patterns = analyst._identify_patterns(findings)
        
        assert len(patterns) > 0
        # Should identify 'increase' and 'improvement' patterns
        themes = [p['theme'] for p in patterns]
        assert 'increase' in themes or 'growth' in themes or 'improvement' in themes
        
        # Check pattern strength
        strong_patterns = [p for p in patterns if p['strength'] == 'strong']
        assert len(strong_patterns) >= 0  # May or may not have strong patterns
    
    def test_generate_insights(self, analyst):
        """Test insight generation"""
        patterns = [
            {'theme': 'growth', 'frequency': 3, 'strength': 'strong'},
            {'theme': 'improvement', 'frequency': 2, 'strength': 'moderate'}
        ]
        findings = [
            {'finding': 'Finding 1'},
            {'finding': 'Finding 2'},
            {'finding': 'Finding 3'},
            {'finding': 'Finding 4'},
            {'finding': 'Finding 5'},
            {'finding': 'Finding 6'}
        ]
        
        insights = analyst._generate_insights(patterns, findings)
        
        assert len(insights) > 0
        
        # Should have pattern-based insight
        pattern_insights = [i for i in insights if i['type'] == 'pattern-based']
        assert len(pattern_insights) > 0
        
        # Should have coverage insight
        coverage_insights = [i for i in insights if i['type'] == 'coverage']
        assert len(coverage_insights) > 0
    
    def test_compare_sources(self, analyst):
        """Test source comparison"""
        sources = [
            {'url': 'https://university.edu/paper', 'reliability': 0.9},
            {'url': 'https://college.edu/study', 'reliability': 0.85},
            {'url': 'https://news.com/article', 'reliability': 0.6},
            {'url': 'https://data.gov/report', 'reliability': 0.95}
        ]
        
        comparisons = analyst._compare_sources(sources)
        
        assert len(comparisons) > 0
        
        # Check structure
        for comp in comparisons:
            assert 'source_type' in comp
            assert 'count' in comp
            assert 'avg_reliability' in comp
            assert 'assessment' in comp
        
        # Academic sources should have high assessment
        academic_comp = next((c for c in comparisons if c['source_type'] == 'academic'), None)
        if academic_comp:
            assert academic_comp['assessment'] == 'high'
    
    def test_categorize_source(self, analyst):
        """Test source categorization"""
        assert analyst._categorize_source('https://harvard.edu/research') == 'academic'
        assert analyst._categorize_source('https://cdc.gov/data') == 'government'
        assert analyst._categorize_source('https://nytimes.com/article') == 'news'
        assert analyst._categorize_source('https://example.com') == 'other'
    
    def test_find_contradictions(self, analyst):
        """Test contradiction detection"""
        findings = [
            {
                'finding': 'Stock prices show significant increase',
                'source': {'title': 'Report A'}
            },
            {
                'finding': 'Market analysis reveals decrease in values',
                'source': {'title': 'Report B'}
            },
            {
                'finding': 'Positive growth observed',
                'source': {'title': 'Report C'}
            },
            {
                'finding': 'Negative trends in sector',
                'source': {'title': 'Report D'}
            }
        ]
        
        contradictions = analyst._find_contradictions(findings)
        
        assert len(contradictions) > 0
        
        # Should find increase/decrease contradiction
        conflicts = [c['conflict'] for c in contradictions]
        assert any('increase vs decrease' in c or 'decrease vs increase' in c for c in conflicts)
    
    def test_calculate_confidence(self, analyst):
        """Test confidence calculation"""
        sources = [
            {'reliability': 0.9},
            {'reliability': 0.8},
            {'reliability': 0.85}
        ]
        findings = ['finding1', 'finding2', 'finding3', 'finding4']
        
        confidence = analyst._calculate_confidence(sources, findings)
        
        assert 'source_reliability' in confidence
        assert 'data_completeness' in confidence
        assert 'consistency' in confidence
        assert 'overall' in confidence
        
        # Check values
        assert 0 <= confidence['source_reliability'] <= 1
        assert 0 <= confidence['data_completeness'] <= 1
        assert 0 <= confidence['overall'] <= 1
        
        # With high reliability sources, should have good confidence
        assert confidence['source_reliability'] > 0.8
    
    def test_generate_summary(self, analyst):
        """Test summary generation"""
        analysis_results = {
            'patterns': [
                {'theme': 'growth', 'strength': 'strong'},
                {'theme': 'improvement', 'strength': 'moderate'}
            ],
            'insights': [
                {'confidence': 0.9},
                {'confidence': 0.8},
                {'confidence': 0.5}
            ],
            'confidence_levels': {
                'overall': 0.75
            }
        }
        
        summary = analyst._generate_summary(analysis_results)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'patterns' in summary.lower() or 'insights' in summary.lower()
        assert 'confidence' in summary.lower()
    
    def test_agent_callback(self, analyst):
        """Test agent callback functionality"""
        # Test analysis started event
        event = {
            'type': 'analysis_started',
            'task': 'Analyzing data',
            'timestamp': '2024-01-01T00:00:00'
        }
        analyst._agent_callback(event)
        
        stored = analyst.memory.get_short_term('analyst_current_task')
        assert stored == event
        
        # Test insight generated event
        insight_event = {
            'type': 'insight_generated',
            'insight': 'Important finding',
            'confidence': 0.85
        }
        analyst._agent_callback(insight_event)
        
        shared = analyst.memory.get_shared_data('data_analyst')
        assert shared['type'] == 'insight'
        assert shared['content'] == 'Important finding'
        assert shared['confidence'] == 0.85
    
    def test_perform_comparative_analysis(self, analyst):
        """Test comparative analysis method"""
        datasets = [
            {'name': 'Dataset 1', 'data': [1, 2, 3]},
            {'name': 'Dataset 2', 'data': [4, 5, 6]}
        ]
        
        results = analyst.perform_comparative_analysis(datasets)
        
        assert 'similarities' in results
        assert 'differences' in results
        assert 'trends' in results
        assert 'recommendations' in results
        
        # Check memory storage
        stored = analyst.memory.get_short_term('comparative_analysis_input')
        assert stored == datasets


if __name__ == "__main__":
    pytest.main([__file__, "-v"])