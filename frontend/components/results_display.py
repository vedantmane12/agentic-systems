import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any

def render_results_display(results: Dict[str, Any]):
    """
    Render the research results display
    
    Args:
        results: Research results from the API
    """
    
    if not results:
        st.info("No results to display")
        return
    
    # Check if research was successful
    if not results.get("success", False):
        st.error("❌ Research was not successful")
        if "error" in results:
            st.error(f"Error: {results['error']}")
        return
    
    # Extract main components
    report = results.get("report", {})
    metadata = results.get("metadata", {})
    sources = results.get("sources", [])
    
    # Main results tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Executive Summary", 
        "📊 Full Report", 
        "🔗 Sources", 
        "📈 Analytics",
        "💾 Export"
    ])
    
    with tab1:
        render_executive_summary(report, metadata)
    
    with tab2:
        render_full_report(report)
    
    with tab3:
        render_sources(sources)
    
    with tab4:
        render_analytics(sources, metadata)
    
    with tab5:
        render_export_options(results)

def render_executive_summary(report: Dict[str, Any], metadata: Dict[str, Any]):
    """Render the executive summary tab"""
    
    st.header("📋 Executive Summary")
    
    # Key findings
    if "executive_summary" in report:
        st.markdown("### 🎯 Key Findings")
        st.markdown(report["executive_summary"])
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Sources Analyzed", 
            metadata.get("total_sources", "N/A")
        )
    
    with col2:
        st.metric(
            "Research Time", 
            f"{metadata.get('execution_time', 0):.1f}s"
        )
    
    with col3:
        st.metric(
            "Credibility Score", 
            f"{metadata.get('avg_credibility', 0):.1f}/10"
        )
    
    with col4:
        st.metric(
            "Confidence Level", 
            f"{metadata.get('confidence', 0):.0f}%"
        )
    
    # Main conclusions
    if "conclusions" in report:
        st.markdown("### 🎯 Conclusions")
        conclusions = report["conclusions"]
        if isinstance(conclusions, list):
            for i, conclusion in enumerate(conclusions, 1):
                st.markdown(f"{i}. {conclusion}")
        else:
            st.markdown(conclusions)

def render_full_report(report: Dict[str, Any]):
    """Render the full report tab"""
    
    st.header("📊 Full Research Report")
    
    # Report sections
    sections = [
        ("introduction", "🔍 Introduction"),
        ("methodology", "🔬 Methodology"),
        ("findings", "📈 Findings"),
        ("analysis", "🧠 Analysis"),
        ("implications", "💡 Implications"),
        ("limitations", "⚠️ Limitations"),
        ("recommendations", "🎯 Recommendations")
    ]
    
    for section_key, section_title in sections:
        if section_key in report:
            st.markdown(f"### {section_title}")
            content = report[section_key]
            
            if isinstance(content, list):
                for item in content:
                    st.markdown(f"• {item}")
            elif isinstance(content, dict):
                for key, value in content.items():
                    st.markdown(f"**{key.title()}:** {value}")
            else:
                st.markdown(content)
            
            st.markdown("---")

def render_sources(sources: list):
    """Render the sources tab"""
    
    st.header("🔗 Sources and References")
    
    if not sources:
        st.info("No sources available")
        return
    
    # Source filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        source_types = list(set([s.get("type", "unknown") for s in sources]))
        selected_type = st.selectbox("Filter by Type", ["All"] + source_types)
    
    with col2:
        credibility_filter = st.selectbox(
            "Credibility Level", 
            ["All", "High (8-10)", "Medium (5-7)", "Low (0-4)"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by", 
            ["Credibility", "Date", "Relevance", "Title"]
        )
    
    # Filter sources
    filtered_sources = sources.copy()
    
    if selected_type != "All":
        filtered_sources = [s for s in filtered_sources if s.get("type") == selected_type]
    
    if credibility_filter != "All":
        if credibility_filter == "High (8-10)":
            filtered_sources = [s for s in filtered_sources if s.get("credibility_score", 0) >= 8]
        elif credibility_filter == "Medium (5-7)":
            filtered_sources = [s for s in filtered_sources if 5 <= s.get("credibility_score", 0) < 8]
        elif credibility_filter == "Low (0-4)":
            filtered_sources = [s for s in filtered_sources if s.get("credibility_score", 0) < 5]
    
    # Sort sources
    if sort_by == "Credibility":
        filtered_sources.sort(key=lambda x: x.get("credibility_score", 0), reverse=True)
    elif sort_by == "Date":
        filtered_sources.sort(key=lambda x: x.get("date", ""), reverse=True)
    elif sort_by == "Relevance":
        filtered_sources.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # Display sources
    st.markdown(f"**Showing {len(filtered_sources)} of {len(sources)} sources**")
    
    for i, source in enumerate(filtered_sources, 1):
        with st.expander(f"{i}. {source.get('title', 'Untitled')} ⭐ {source.get('credibility_score', 0):.1f}"):
            col_s1, col_s2 = st.columns([2, 1])
            
            with col_s1:
                st.markdown(f"**URL:** {source.get('url', 'N/A')}")
                st.markdown(f"**Authors:** {', '.join(source.get('authors', ['Unknown']))}")
                st.markdown(f"**Publication Date:** {source.get('date', 'Unknown')}")
                
                if "summary" in source:
                    st.markdown(f"**Summary:** {source['summary']}")
                
                if "key_findings" in source:
                    st.markdown("**Key Findings:**")
                    for finding in source["key_findings"]:
                        st.markdown(f"• {finding}")
            
            with col_s2:
                st.markdown("**Metrics:**")
                st.markdown(f"Type: {source.get('type', 'Unknown')}")
                st.markdown(f"Credibility: {source.get('credibility_score', 0):.1f}/10")
                st.markdown(f"Relevance: {source.get('relevance_score', 0):.1f}/10")
                
                if "bias_indicators" in source:
                    bias_count = len(source["bias_indicators"])
                    st.markdown(f"Bias Indicators: {bias_count}")

def render_analytics(sources: list, metadata: Dict[str, Any]):
    """Render the analytics tab"""
    
    st.header("📈 Research Analytics")
    
    if not sources:
        st.info("No data available for analytics")
        return
    
    # Source type distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Source Type Distribution")
        source_types = {}
        for source in sources:
            source_type = source.get("type", "Unknown")
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        if source_types:
            fig_pie = px.pie(
                values=list(source_types.values()),
                names=list(source_types.keys()),
                title="Sources by Type"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Credibility Distribution")
        credibility_scores = [s.get("credibility_score", 0) for s in sources]
        
        if credibility_scores:
            fig_hist = px.histogram(
                x=credibility_scores,
                nbins=10,
                title="Credibility Score Distribution",
                labels={"x": "Credibility Score", "y": "Number of Sources"}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
    
    # Timeline analysis
    st.subheader("Publication Timeline")
    dates = []
    for source in sources:
        if source.get("date"):
            try:
                # Try to parse different date formats
                date_str = source["date"]
                dates.append(date_str)
            except:
                continue
    
    if dates:
        df_timeline = pd.DataFrame({"date": dates})
        df_timeline["count"] = 1
        
        # Group by year if we have enough data
        if len(dates) > 10:
            df_timeline["year"] = pd.to_datetime(df_timeline["date"], errors="coerce").dt.year
            yearly_counts = df_timeline.groupby("year")["count"].sum().reset_index()
            
            fig_timeline = px.bar(
                yearly_counts,
                x="year",
                y="count",
                title="Sources by Publication Year"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Quality metrics table
    st.subheader("Quality Metrics Summary")
    
    metrics_data = {
        "Metric": ["Average Credibility", "Average Relevance", "High Quality Sources (%)", "Sources with Authors"],
        "Value": [
            f"{sum(s.get('credibility_score', 0) for s in sources) / len(sources):.2f}",
            f"{sum(s.get('relevance_score', 0) for s in sources) / len(sources):.2f}",
            f"{len([s for s in sources if s.get('credibility_score', 0) >= 8]) / len(sources) * 100:.1f}%",
            f"{len([s for s in sources if s.get('authors') and len(s['authors']) > 0])}"
        ]
    }
    
    st.dataframe(pd.DataFrame(metrics_data), use_container_width=True)

def render_export_options(results: Dict[str, Any]):
    """Render the export options tab"""
    
    st.header("💾 Export Research Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Report Formats")
        
        # JSON export
        if st.button("📋 Download as JSON"):
            json_str = json.dumps(results, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # CSV export (sources)
        if st.button("📊 Download Sources as CSV"):
            sources = results.get("sources", [])
            if sources:
                df = pd.DataFrame(sources)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"research_sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        st.subheader("📝 Formatted Report")
        
        # Generate markdown report
        if st.button("📝 Generate Markdown Report"):
            markdown_report = generate_markdown_report(results)
            st.download_button(
                label="Download Markdown",
                data=markdown_report,
                file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        
        # Citation export
        if st.button("📚 Export Citations"):
            citations = generate_citations(results.get("sources", []))
            st.download_button(
                label="Download Citations",
                data=citations,
                file_name=f"citations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

def generate_markdown_report(results: Dict[str, Any]) -> str:
    """Generate a markdown formatted report"""
    
    report = results.get("report", {})
    metadata = results.get("metadata", {})
    sources = results.get("sources", [])
    
    markdown = f"""# Research Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
{report.get('executive_summary', 'No summary available')}

## Key Metrics
- **Sources Analyzed:** {metadata.get('total_sources', 'N/A')}
- **Research Time:** {metadata.get('execution_time', 0):.1f} seconds
- **Average Credibility:** {metadata.get('avg_credibility', 0):.1f}/10
- **Confidence Level:** {metadata.get('confidence', 0):.0f}%

## Findings
{report.get('findings', 'No findings available')}

## Analysis
{report.get('analysis', 'No analysis available')}

## Conclusions
{report.get('conclusions', 'No conclusions available')}

## Sources
"""
    
    for i, source in enumerate(sources, 1):
        markdown += f"""
### {i}. {source.get('title', 'Untitled')}
- **URL:** {source.get('url', 'N/A')}
- **Authors:** {', '.join(source.get('authors', ['Unknown']))}
- **Date:** {source.get('date', 'Unknown')}
- **Credibility Score:** {source.get('credibility_score', 0):.1f}/10
- **Type:** {source.get('type', 'Unknown')}

{source.get('summary', 'No summary available')}
"""
    
    return markdown

def generate_citations(sources: list) -> str:
    """Generate citation text"""
    
    citations = "# Citations\n\n"
    
    for i, source in enumerate(sources, 1):
        # Generate APA-style citation
        authors = source.get('authors', ['Unknown'])
        author_str = ', '.join(authors) if authors else 'Unknown'
        title = source.get('title', 'Untitled')
        date = source.get('date', 'n.d.')
        url = source.get('url', '')
        
        citation = f"{i}. {author_str} ({date}). {title}. Retrieved from {url}\n\n"
        citations += citation
    
    return citations