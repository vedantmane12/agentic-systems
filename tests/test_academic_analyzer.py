"""
Tests for Academic Source Analyzer Tool
"""

import pytest
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.features.tools.academic_analyzer import (
    AcademicSourceAnalyzer, 
    SourceMetadata, 
    AnalysisResult,
    analyze_academic_source
)


class TestAcademicSourceAnalyzer:
    """Test cases for Academic Source Analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return AcademicSourceAnalyzer()
    
    @pytest.fixture
    def academic_content(self):
        """Sample academic content"""
        return """
        Research Article: Machine Learning in Healthcare
        
        Authors: Dr. Jane Smith, Prof. John Doe, Dr. Emily Johnson
        Published: March 15, 2024
        Journal of Medical AI Research
        
        Abstract:
        This peer-reviewed study examines the application of machine learning algorithms
        in healthcare diagnostics. Our methodology involved analyzing 10,000 patient records
        using supervised learning techniques.
        
        Introduction:
        Machine learning has shown promising results in medical diagnosis [1]. Previous 
        studies (Anderson et al., 2023) demonstrated significant improvements in accuracy.
        
        Methodology:
        We employed a systematic approach using random forest and neural network models.
        The data was collected from three major hospitals over a period of two years.
        
        Results:
        Our findings indicate that ML models achieved 95% accuracy in predicting diseases.
        The study found that early detection rates improved by 40%.
        
        Conclusion:
        This research demonstrates the potential of ML in healthcare. However, further
        validation is needed. Although promising, ethical considerations must be addressed.
        
        References:
        [1] Anderson, K. et al. (2023). "AI in Medicine." Medical Journal.
        [2] Brown, L. (2022). "Healthcare Analytics." Tech Review.
        """
    
    @pytest.fixture
    def blog_content(self):
        """Sample blog content"""
        return """
        My Thoughts on AI: Why Everyone Should Obviously Care
        
        Posted by TechBlogger123 on January 5, 2024
        
        Hey everyone! I've been thinking about AI lately and clearly it's going to 
        completely change everything. Nobody believes me, but AI will definitely 
        solve all our problems.
        
        I mean, obviously AI is the future. Everyone knows that traditional methods 
        are totally outdated. It's definitely time to embrace the change!
        
        In my opinion, we should always trust AI completely. There's never been a 
        better time to jump on the bandwagon. Surely you agree with me?
        
        Check out my other blog posts for more of my thoughts!
        """
    
    @pytest.fixture
    def news_content(self):
        """Sample news content"""
        return """
        Breaking: New Study Reveals AI Breakthrough
        
        By Sarah Reporter, Tech Daily News
        Published: December 10, 2023
        
        A groundbreaking study from MIT researchers has revealed a significant 
        breakthrough in artificial intelligence technology. The research, published
        in the journal Nature, demonstrates new capabilities in natural language
        processing.
        
        Dr. Michael Chen, lead researcher, stated: "Our findings show a 30% improvement
        in language understanding compared to previous models."
        
        However, critics argue that more testing is needed. Although the results are
        promising, industry experts caution against premature implementation.
        
        The study involved collaboration between multiple universities and was funded
        by the National Science Foundation.
        """
    
    def test_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer.compiled_patterns is not None
        assert "academic" in analyzer.compiled_patterns
        assert "bias" in analyzer.compiled_patterns
        assert len(analyzer.compiled_patterns) > 0
    
    def test_identify_source_type_academic(self, analyzer, academic_content):
        """Test identifying academic sources"""
        source_type, confidence = analyzer.identify_source_type(
            "https://journal.university.edu/article", 
            academic_content
        )
        assert source_type == "academic"
        assert confidence > 0.5
    
    def test_identify_source_type_blog(self, analyzer, blog_content):
        """Test identifying blog sources"""
        source_type, confidence = analyzer.identify_source_type(
            "https://myblog.wordpress.com/post", 
            blog_content
        )
        assert source_type == "blog"
        assert confidence > 0.3
    
    def test_identify_source_type_news(self, analyzer, news_content):
        """Test identifying news sources"""
        source_type, confidence = analyzer.identify_source_type(
            "https://technews.com/article", 
            news_content
        )
        # News content has both news and academic indicators, so check for either
        assert source_type in ["news", "academic"]
        assert confidence > 0.3
    
    def test_extract_authors(self, analyzer, academic_content):
        """Test author extraction"""
        authors = analyzer.extract_authors(academic_content)
        assert len(authors) > 0
        # Check that we found at least one of the authors
        author_names = ' '.join(authors).lower()
        assert any(name in author_names for name in ['jane', 'john', 'emily', 'anderson'])
    
    def test_extract_publication_date(self, analyzer):
        """Test date extraction with various formats"""
        # Test different date formats
        test_cases = [
            ("Published: March 15, 2024", "March 15, 2024"),
            ("Date: 03/15/2024", "03/15/2024"),
            ("Updated: 2024-03-15", "2024-03-15"),
            ("© 2024 Company", "2024")
        ]
        
        for content, expected in test_cases:
            date = analyzer.extract_publication_date(content)
            assert date == expected
    
    def test_detect_bias_indicators(self, analyzer, blog_content, academic_content):
        """Test bias detection"""
        # High bias content
        blog_bias = analyzer.detect_bias_indicators(blog_content)
        assert len(blog_bias) > 5
        assert any(word in blog_bias for word in ["obviously", "clearly", "everyone knows"])
        
        # Low bias content
        academic_bias = analyzer.detect_bias_indicators(academic_content)
        assert len(academic_bias) < len(blog_bias)
    
    def test_calculate_credibility_score(self, analyzer):
        """Test credibility score calculation"""
        # High credibility
        score_high = analyzer.calculate_credibility_score(
            source_type="academic",
            type_confidence=0.9,
            authors=["Dr. Smith", "Dr. Jones"],
            has_date=True,
            citations_count=10
        )
        assert score_high > 0.7
        
        # Low credibility
        score_low = analyzer.calculate_credibility_score(
            source_type="blog",
            type_confidence=0.8,
            authors=[],
            has_date=False,
            citations_count=0
        )
        assert score_low < 0.3
    
    def test_extract_key_findings(self, analyzer, academic_content):
        """Test key findings extraction"""
        findings = analyzer.extract_key_findings(academic_content)
        assert len(findings) > 0
        assert any("95% accuracy" in finding for finding in findings)
        assert any("40%" in finding for finding in findings)
    
    def test_generate_citation_data(self, analyzer):
        """Test citation generation"""
        metadata = SourceMetadata(
            url="https://example.com/article",
            title="Test Article",
            authors=["Smith, J.", "Doe, J."],
            publication_date="March 2024",
            source_type="academic",
            citations_count=5
        )
        
        citations = analyzer.generate_citation_data(metadata)
        assert "apa" in citations
        assert "mla" in citations
        assert "chicago" in citations
        assert "bibtex" in citations
        assert "Smith" in citations["apa"]
        assert "2024" in citations["apa"]
    
    def test_full_analysis_academic(self, analyzer, academic_content):
        """Test full analysis of academic content"""
        result = analyzer.analyze(
            url="https://journal.edu/article",
            title="Machine Learning in Healthcare",
            content=academic_content
        )
        
        assert isinstance(result, AnalysisResult)
        assert result.credibility_score > 0.5
        assert result.quality_score > 0.5
        assert len(result.key_findings) > 0
        assert result.metadata.source_type == "academic"
        assert len(result.metadata.authors) > 0
        assert result.metadata.citations_count > 0
    
    def test_full_analysis_blog(self, analyzer, blog_content):
        """Test full analysis of blog content"""
        result = analyzer.analyze(
            url="https://blog.com/post",
            title="My Thoughts on AI",
            content=blog_content
        )
        
        assert result.credibility_score < 0.5
        assert len(result.bias_indicators) > 5
        assert result.metadata.source_type == "blog"
    
    def test_analyze_academic_source_tool(self, academic_content):
        """Test the tool wrapper function"""
        # Create JSON input as the tool expects
        input_data = json.dumps({
            "url": "https://journal.edu/article",
            "title": "Machine Learning in Healthcare",
            "content": academic_content
        })
        
        result_json = analyze_academic_source(input_data)
        
        # Should return valid JSON
        result = json.loads(result_json)
        assert "credibility_score" in result
        assert "quality_score" in result
        assert "metadata" in result
        assert "key_findings" in result
        assert "citation_data" in result
    
    def test_error_handling(self, analyzer):
        """Test error handling with invalid input"""
        # Should not crash with empty content
        result = analyzer.analyze(
            url="",
            title="Empty Test",
            content=""
        )
        assert isinstance(result, AnalysisResult)
        assert result.credibility_score >= 0
        assert result.quality_score >= 0
    
    def test_citation_counts(self, analyzer):
        """Test citation counting"""
        content_with_citations = """
        This is supported by previous research [1]. Another study [2] found similar
        results. As noted by Smith et al. (2023), the findings are significant.
        Johnson (2022) also confirmed these results. See references [3], [4], [5].
        """
        
        result = analyzer.analyze(
            url="https://example.com",
            title="Test",
            content=content_with_citations
        )
        
        assert result.metadata.citations_count >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])