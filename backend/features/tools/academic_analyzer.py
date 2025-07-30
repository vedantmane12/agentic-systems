"""
Academic Source Analyzer Tool
Custom tool for analyzing and scoring academic sources
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
import json

logger = logging.getLogger(__name__)


class SourceMetadata(BaseModel):
    """Schema for source metadata"""
    url: Optional[str] = Field(None, description="Source URL")
    title: str = Field(..., description="Source title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    publication_date: Optional[str] = Field(None, description="Publication date")
    source_type: str = Field(..., description="Type of source (academic, news, blog, etc)")
    citations_count: int = Field(0, description="Number of citations found")
    
    
class AnalysisResult(BaseModel):
    """Schema for analysis results"""
    credibility_score: float = Field(..., description="Credibility score (0-1)")
    bias_indicators: List[str] = Field(default_factory=list, description="Detected bias indicators")
    quality_score: float = Field(..., description="Overall quality score (0-1)")
    metadata: SourceMetadata = Field(..., description="Extracted metadata")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from the source")
    citation_data: Dict[str, Any] = Field(default_factory=dict, description="Citation information")


class AcademicSourceAnalyzer:
    """Analyzer for evaluating academic and research sources"""
    
    # Source type indicators
    ACADEMIC_INDICATORS = [
        r"journal", r"university", r"\.edu", r"research", r"study",
        r"peer[\s-]?review", r"academic", r"scholar", r"thesis",
        r"dissertation", r"conference", r"proceedings"
    ]
    
    NEWS_INDICATORS = [
        r"news", r"times", r"post", r"guardian", r"reuters",
        r"bbc", r"cnn", r"press", r"daily", r"herald", r"breaking"
    ]
    
    BLOG_INDICATORS = [
        r"blog", r"medium\.com", r"wordpress", r"personal",
        r"opinion", r"thoughts", r"my\s+view"
    ]
    
    # Bias indicators
    BIAS_WORDS = [
        "obviously", "clearly", "everyone knows", "nobody believes",
        "always", "never", "completely", "totally", "undoubtedly",
        "definitely", "surely", "of course", "naturally"
    ]
    
    # Quality indicators
    QUALITY_POSITIVE = [
        "methodology", "results", "conclusion", "abstract",
        "references", "data", "analysis", "findings",
        "evidence", "statistical", "empirical", "systematic"
    ]
    
    def __init__(self):
        """Initialize the analyzer"""
        self.compiled_patterns = self._compile_patterns()
        logger.info("Academic Source Analyzer initialized")
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficiency"""
        return {
            "academic": [re.compile(pattern, re.IGNORECASE) for pattern in self.ACADEMIC_INDICATORS],
            "news": [re.compile(pattern, re.IGNORECASE) for pattern in self.NEWS_INDICATORS],
            "blog": [re.compile(pattern, re.IGNORECASE) for pattern in self.BLOG_INDICATORS],
            "bias": [re.compile(r"\b" + word + r"\b", re.IGNORECASE) for word in self.BIAS_WORDS],
            "quality": [re.compile(r"\b" + word + r"\b", re.IGNORECASE) for word in self.QUALITY_POSITIVE]
        }
    
    def identify_source_type(self, url: str, content: str) -> Tuple[str, float]:
        """
        Identify the type of source based on URL and content
        
        Returns:
            Tuple of (source_type, confidence)
        """
        url_lower = url.lower() if url else ""
        content_lower = content.lower()
        combined_text = url_lower + " " + content_lower[:1000]  # Check first 1000 chars
        
        scores = {
            "academic": 0,
            "news": 0,
            "blog": 0,
            "other": 0
        }
        
        # Check patterns
        for pattern in self.compiled_patterns["academic"]:
            if pattern.search(combined_text):
                scores["academic"] += 1
                
        for pattern in self.compiled_patterns["news"]:
            if pattern.search(combined_text):
                scores["news"] += 1
                
        for pattern in self.compiled_patterns["blog"]:
            if pattern.search(combined_text):
                scores["blog"] += 1
        
        # Determine source type
        max_score = max(scores.values())
        if max_score == 0:
            return "other", 0.5
        
        source_type = max(scores, key=scores.get)
        confidence = scores[source_type] / sum(scores.values()) if sum(scores.values()) > 0 else 0
        
        return source_type, confidence
    
    def extract_authors(self, content: str) -> List[str]:
        """Extract author names from content"""
        authors = []
        
        # Common author patterns - improved
        author_patterns = [
            r"(?:Authors?:)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)",
            r"(?:By|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+et\s+al\.",
            r"([A-Z]\.\s*[A-Z][a-z]+)",  # J. Smith format
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, content[:2000])  # Check beginning of content
            for match in matches:
                # Split by comma if it's a list of authors
                if ',' in match:
                    authors.extend([a.strip() for a in match.split(',')])
                else:
                    authors.append(match.strip())
        
        # Clean and deduplicate
        cleaned_authors = []
        for author in authors:
            author = author.strip()
            # Filter out common false positives
            if (len(author) > 3 and 
                not author.lower() in ['research', 'article', 'study', 'journal', 'university'] and
                re.search(r'[A-Z][a-z]+', author)):
                cleaned_authors.append(author)
        
        return list(set(cleaned_authors))[:5]  # Return top 5 unique authors
    
    def extract_publication_date(self, content: str) -> Optional[str]:
        """Extract publication date from content"""
        # Date patterns
        date_patterns = [
            r"(?:published|posted|updated|date[d]?)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(?:published|posted|updated|date[d]?)\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})",
            r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",  # ISO format
            r"(?:©|copyright)\s*(\d{4})"  # Copyright year
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def detect_bias_indicators(self, content: str) -> List[str]:
        """Detect potential bias indicators in content"""
        bias_found = []
        content_lower = content.lower()
        
        for pattern in self.compiled_patterns["bias"]:
            if pattern.search(content_lower):
                bias_found.append(pattern.pattern.strip(r"\b"))
        
        # Check for one-sided language
        if content_lower.count("however") < 1 and content_lower.count("although") < 1:
            if len(content) > 500:  # Only for substantial content
                bias_found.append("lack of balanced perspective")
        
        return list(set(bias_found))
    
    def calculate_credibility_score(self, source_type: str, type_confidence: float,
                                   authors: List[str], has_date: bool,
                                   citations_count: int) -> float:
        """Calculate credibility score based on various factors"""
        score = 0.0
        
        # Source type weight
        type_weights = {
            "academic": 0.4,
            "news": 0.25,
            "blog": 0.1,
            "other": 0.15
        }
        score += type_weights.get(source_type, 0.1) * type_confidence
        
        # Authors (0.2 weight)
        if authors:
            score += min(0.2, len(authors) * 0.05)
        
        # Publication date (0.1 weight)
        if has_date:
            score += 0.1
        
        # Citations (0.3 weight)
        if citations_count > 0:
            score += min(0.3, citations_count * 0.03)
        
        return min(1.0, score)
    
    def calculate_quality_score(self, content: str, credibility_score: float,
                               bias_indicators: List[str]) -> float:
        """Calculate overall quality score"""
        score = 0.0
        content_lower = content.lower()
        
        # Check for quality indicators (0.4 weight)
        quality_count = 0
        for pattern in self.compiled_patterns["quality"]:
            if pattern.search(content_lower):
                quality_count += 1
        score += min(0.4, quality_count * 0.05)
        
        # Length and structure (0.2 weight)
        if len(content) > 1000:
            score += 0.1
        if content.count('\n\n') > 3:  # Paragraphs
            score += 0.1
        
        # Credibility contribution (0.2 weight)
        score += credibility_score * 0.2
        
        # Bias penalty (0.2 weight)
        bias_penalty = min(0.2, len(bias_indicators) * 0.04)
        score += 0.2 - bias_penalty
        
        return min(1.0, score)
    
    def extract_key_findings(self, content: str) -> List[str]:
        """Extract key findings or important points from content"""
        findings = []
        
        # Look for sections with findings
        finding_patterns = [
            r"(?:key\s+)?findings?:?\s*([^.]+\.)",
            r"(?:main\s+)?results?:?\s*([^.]+\.)",
            r"(?:in\s+)?conclusions?:?\s*([^.]+\.)",
            r"the\s+study\s+(?:found|showed|demonstrated)\s+(?:that\s+)?([^.]+\.)",
            r"our\s+(?:research|analysis)\s+(?:indicates|suggests|shows)\s+(?:that\s+)?([^.]+\.)"
        ]
        
        for pattern in finding_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            findings.extend([match.strip() for match in matches])
        
        # Also look for bullet points or numbered lists
        list_items = re.findall(r"(?:^|\n)\s*[•·▪▫◦‣⁃]\s*([^•·▪▫◦‣⁃\n]+)", content)
        findings.extend([item.strip() for item in list_items if len(item.strip()) > 20])
        
        # Deduplicate and limit
        seen = set()
        unique_findings = []
        for finding in findings:
            if finding not in seen and len(finding) > 20:
                seen.add(finding)
                unique_findings.append(finding)
        
        return unique_findings[:5]  # Return top 5 findings
    
    def generate_citation_data(self, metadata: SourceMetadata) -> Dict[str, Any]:
        """Generate citation data in various formats"""
        authors_str = ", ".join(metadata.authors) if metadata.authors else "Unknown Author"
        year = metadata.publication_date.split()[-1] if metadata.publication_date else "n.d."
        
        # Extract year from date if it's a full date
        if metadata.publication_date and re.search(r'\d{4}', metadata.publication_date):
            year_match = re.search(r'\d{4}', metadata.publication_date)
            if year_match:
                year = year_match.group()
        
        citation_data = {
            "apa": f"{authors_str} ({year}). {metadata.title}.",
            "mla": f"{authors_str}. \"{metadata.title}.\" {year}.",
            "chicago": f"{authors_str}. \"{metadata.title}.\" Accessed {datetime.now().strftime('%B %d, %Y')}.",
            "bibtex": {
                "type": "@article" if metadata.source_type == "academic" else "@misc",
                "key": metadata.title.split()[0].lower() + year if metadata.title else "ref" + year,
                "author": authors_str,
                "title": metadata.title,
                "year": year
            }
        }
        
        if metadata.url:
            citation_data["apa"] += f" Retrieved from {metadata.url}"
            citation_data["mla"] += f" Web. <{metadata.url}>"
            citation_data["bibtex"]["url"] = metadata.url
            
        return citation_data
    
    def analyze(self, url: str, title: str, content: str) -> AnalysisResult:
        """
        Main analysis method
        
        Args:
            url: Source URL
            title: Source title
            content: Source content
            
        Returns:
            AnalysisResult with all extracted information
        """
        try:
            # Identify source type
            source_type, type_confidence = self.identify_source_type(url, content)
            
            # Extract metadata
            authors = self.extract_authors(content)
            publication_date = self.extract_publication_date(content)
            
            # Count citations (simple pattern matching)
            citations_count = len(re.findall(r"\[\d+\]|\(\w+,?\s+\d{4}\)", content))
            
            # Detect bias
            bias_indicators = self.detect_bias_indicators(content)
            
            # Create metadata
            metadata = SourceMetadata(
                url=url,
                title=title,
                authors=authors,
                publication_date=publication_date,
                source_type=source_type,
                citations_count=citations_count
            )
            
            # Calculate scores
            credibility_score = self.calculate_credibility_score(
                source_type, type_confidence, authors, 
                bool(publication_date), citations_count
            )
            
            quality_score = self.calculate_quality_score(content, credibility_score, bias_indicators)
            
            # Extract key findings
            key_findings = self.extract_key_findings(content)
            
            # Generate citation data
            citation_data = self.generate_citation_data(metadata)
            
            return AnalysisResult(
                credibility_score=credibility_score,
                bias_indicators=bias_indicators,
                quality_score=quality_score,
                metadata=metadata,
                key_findings=key_findings,
                citation_data=citation_data
            )
            
        except Exception as e:
            logger.error(f"Error analyzing source: {str(e)}")
            raise


@tool
def analyze_academic_source(query: str) -> str:
    """
    Analyze an academic or research source for credibility, bias, and quality.
    
    Args:
        query: A JSON string containing 'url', 'title', and 'content' fields
        
    Returns:
        JSON string with analysis results including credibility score, bias indicators,
        quality score, metadata, key findings, and citation data.
    """
    try:
        # Parse the input
        data = json.loads(query)
        url = data.get('url', '')
        title = data.get('title', '')
        content = data.get('content', '')
        
        analyzer = AcademicSourceAnalyzer()
        result = analyzer.analyze(url, title, content)
        return result.model_dump_json(indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input. Please provide a JSON string with 'url', 'title', and 'content' fields."})
    except Exception as e:
        return json.dumps({"error": f"Analysis failed: {str(e)}"})