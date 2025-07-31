import streamlit as st
import asyncio
import json
from datetime import datetime
import time
import pandas as pd
import plotly.express as px
import sys
import os

# Add the project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(current_dir)

from utils.api_client import SyncAPIClient

# Page configuration
st.set_page_config(
    page_title="Research Assistant - Sync",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stProgress .st-bo {
        background-color: #e0e0e0;
    }
    .stProgress .st-bp {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'sync_api_client' not in st.session_state:
        st.session_state.sync_api_client = SyncAPIClient()
    
    if 'research_results' not in st.session_state:
        st.session_state.research_results = None
    
    if 'research_history' not in st.session_state:
        st.session_state.research_history = []

def render_results_display(results):
    """Render the research results"""
    if not results:
        st.info("No results to display")
        return
    
    # Main results tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Executive Summary", 
        "📊 Full Report", 
        "🔗 Sources", 
        "💾 Export"
    ])
    
    with tab1:
        st.header("📋 Executive Summary")
        
        report = results.get("report", {})
        metadata = results.get("metadata", {})
        
        # Quick metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sources", metadata.get("total_sources", "N/A"))
        with col2:
            st.metric("Research Time", f"{metadata.get('execution_time', 0):.1f}s")
        with col3:
            st.metric("Credibility", f"{metadata.get('avg_credibility', 0):.1f}/10")
        with col4:
            st.metric("Confidence", f"{metadata.get('confidence', 0)}%")
        
        # Executive summary
        if "executive_summary" in report:
            st.markdown("### 🎯 Key Findings")
            st.markdown(report["executive_summary"])
        
        # Key conclusions
        if "conclusions" in report:
            st.markdown("### 📋 Conclusions")
            st.markdown(report["conclusions"])
    
    with tab2:
        st.header("📊 Full Research Report")
        
        report = results.get("report", {})
        
        # Display all report sections
        section_order = [
            ("introduction", "🔍 Introduction"),
            ("methodology", "🔬 Methodology"),
            ("findings", "📈 Key Findings"),
            ("analysis", "🧠 Analysis & Insights"),
            ("conclusions", "🎯 Conclusions"),
            ("recommendations", "💡 Recommendations"),
            ("references", "📚 References")
        ]
        
        for section_key, section_title in section_order:
            if section_key in report and report[section_key]:
                st.markdown(f"### {section_title}")
                st.markdown(report[section_key])
                st.markdown("---")
    
    with tab3:
        st.header("🔗 Sources and References")
        
        sources = results.get("sources", [])
        
        if sources:
            for i, source in enumerate(sources, 1):
                with st.expander(f"{i}. {source.get('title', 'Untitled')} ⭐ {source.get('credibility_score', 0):.1f}"):
                    col_s1, col_s2 = st.columns([2, 1])
                    
                    with col_s1:
                        st.markdown(f"**URL:** {source.get('url', 'N/A')}")
                        st.markdown(f"**Authors:** {', '.join(source.get('authors', ['Unknown']))}")
                        st.markdown(f"**Date:** {source.get('date', 'Unknown')}")
                        st.markdown(f"**Summary:** {source.get('summary', 'No summary available')}")
                    
                    with col_s2:
                        st.markdown("**Quality Metrics:**")
                        st.markdown(f"Type: {source.get('type', 'Unknown')}")
                        st.markdown(f"Credibility: {source.get('credibility_score', 0):.1f}/10")
                        st.markdown(f"Relevance: {source.get('relevance_score', 0):.1f}/10")
        else:
            st.info("No sources available")
    
    with tab4:
        st.header("💾 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON export
            json_str = json.dumps(results, indent=2)
            st.download_button(
                label="📋 Download JSON",
                data=json_str,
                file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # Markdown export
            markdown_report = generate_markdown_report(results)
            st.download_button(
                label="📝 Download Markdown",
                data=markdown_report,
                file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )

def generate_markdown_report(results):
    """Generate markdown report"""
    report = results.get("report", {})
    metadata = results.get("metadata", {})
    
    markdown = f"""# Research Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
{report.get('executive_summary', 'No summary available')}

## Key Metrics
- **Sources:** {metadata.get('total_sources', 'N/A')}
- **Execution Time:** {metadata.get('execution_time', 0):.1f} seconds
- **Credibility:** {metadata.get('avg_credibility', 0):.1f}/10
- **Confidence:** {metadata.get('confidence', 0)}%

## Findings
{report.get('findings', 'No findings available')}

## Analysis
{report.get('analysis', 'No analysis available')}

## Conclusions
{report.get('conclusions', 'No conclusions available')}

## Recommendations
{report.get('recommendations', 'No recommendations available')}

## References
{report.get('references', 'No references available')}
"""
    return markdown

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🔬 AI Research Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### *Synchronous Research Processing*")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # API Status
        with st.spinner("Checking API..."):
            api_status = asyncio.run(st.session_state.sync_api_client.health_check())
        
        if api_status.get("status") == "healthy":
            st.success("✅ API: Ready")
        else:
            st.error("❌ API: Offline")
            st.error(api_status.get("error", "Unknown error"))
            st.stop()
        
        st.markdown("---")
        
        # Settings
        st.subheader("⚙️ Research Settings")
        
        research_depth = st.selectbox(
            "Research Depth",
            ["Quick", "Standard", "Comprehensive"],
            index=1
        )
        
        max_sources = st.slider(
            "Maximum Sources",
            min_value=5,
            max_value=50,
            value=20
        )
        
        include_citations = st.checkbox(
            "Include Citations",
            value=True
        )
        
        st.markdown("---")
        
        # Recent Research
        st.subheader("📚 Recent Research")
        try:
            recent = asyncio.run(st.session_state.sync_api_client.get_recent_research())
            if recent.get("research"):
                for research in recent["research"][-3:]:  # Show last 3
                    status_icon = "✅" if research.get("success") else "❌"
                    st.write(f"{status_icon} {research.get('query', 'Unknown')[:30]}...")
                    st.caption(f"Time: {research.get('execution_time', 0):.1f}s")
            else:
                st.info("No recent research")
        except:
            st.info("No recent research")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔍 Research Query")
        
        # Query input
        query = st.text_area(
            "Enter your research question:",
            placeholder="Example: What are the latest developments in renewable energy storage technologies?",
            height=100
        )
        
        # Buttons
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            start_research = st.button(
                "🔍 Start Research",
                type="primary",
                use_container_width=True,
                disabled=not query.strip()
            )
        
        with col_btn2:
            clear_results = st.button(
                "🗑️ Clear Results",
                use_container_width=True
            )
        
        # Handle button clicks
        if clear_results:
            st.session_state.research_results = None
            st.success("✅ Results cleared!")
            st.rerun()
        
        if start_research and query.strip() and api_status.get("status") == "healthy":
            research_config = {
                "depth": research_depth.lower(),
                "max_sources": max_sources,
                "include_citations": include_citations
            }
            
            # Execute research synchronously
            st.info("🚀 Starting comprehensive research...")
            st.warning("⏱️ This will take 2-4 minutes. Please wait...")
            
            # Create progress indicators
            progress_bar = st.progress(0)
            stage_text = st.empty()
            time_text = st.empty()
            
            start_time = time.time()
            
            try:
                # Show initial progress
                progress_bar.progress(10)
                stage_text.info("🔄 Submitting research request...")
                
                # Execute research with periodic UI updates
                async def research_with_progress():
                    # Start the research
                    research_task = asyncio.create_task(
                        st.session_state.sync_api_client.execute_research_sync(
                            query, config=research_config
                        )
                    )
                    
                    # Update progress while waiting
                    while not research_task.done():
                        elapsed = time.time() - start_time
                        
                        # Estimate progress based on typical research time
                        expected_duration = 180  # 3 minutes
                        progress = min(10 + (elapsed / expected_duration * 85), 95)
                        progress_bar.progress(int(progress))
                        
                        # Update stage text based on time
                        if elapsed < 20:
                            stage_text.info("🧠 Research Coordinator creating strategy...")
                        elif elapsed < 60:
                            stage_text.info("🔍 Information Gatherer searching sources...")
                        elif elapsed < 120:
                            stage_text.info("📊 Data Analyst processing information...")
                        elif elapsed < 180:
                            stage_text.info("✍️ Content Synthesizer creating report...")
                        else:
                            stage_text.info("🔬 Finalizing research and quality checks...")
                        
                        time_text.caption(f"⏱️ Elapsed time: {elapsed:.0f}s")
                        
                        await asyncio.sleep(2)
                    
                    return await research_task
                
                # Execute research with progress updates
                result = asyncio.run(research_with_progress())
                
                # Handle results
                if result.get("status") == "success":
                    progress_bar.progress(100)
                    stage_text.success("✅ Research completed successfully!")
                    
                    research_data = result["data"]
                    st.session_state.research_results = research_data
                    
                    # Add to history
                    st.session_state.research_history.append({
                        "query": query,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "execution_time": research_data.get("execution_time", 0),
                        "success": True
                    })
                    
                    # Show success
                    st.balloons()
                    st.success("🎉 Research completed! Results are displayed below.")
                    time.sleep(1)
                    st.rerun()
                
                else:
                    progress_bar.progress(0)
                    stage_text.error("❌ Research failed!")
                    error_msg = result.get("error", "Unknown error")
                    st.error(f"Research Error: {error_msg}")
                    
                    # Add failed research to history
                    st.session_state.research_history.append({
                        "query": query,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "execution_time": time.time() - start_time,
                        "success": False,
                        "error": error_msg
                    })
                
            except Exception as e:
                progress_bar.progress(0)
                stage_text.error("❌ Unexpected error!")
                st.error(f"Error: {str(e)}")
    
    with col2:
        st.header("📊 System Metrics")
        
        try:
            metrics = asyncio.run(st.session_state.sync_api_client.get_metrics())
            
            if "total_research" in metrics:
                # Display metrics
                st.metric("Total Research", metrics.get("total_research", 0))
                st.metric("Success Rate", f"{metrics.get('success_rate', 0):.1f}%")
                st.metric("Avg Time", f"{metrics.get('avg_execution_time', 0):.1f}s")
                
                # Success rate chart
                if metrics.get("total_research", 0) > 0:
                    success_data = {
                        "Status": ["Successful", "Failed"],
                        "Count": [metrics.get("successful", 0), metrics.get("failed", 0)]
                    }
                    
                    fig = px.pie(
                        values=success_data["Count"],
                        names=success_data["Status"],
                        title="Research Success Rate",
                        color_discrete_map={
                            "Successful": "#28a745",
                            "Failed": "#dc3545"
                        }
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No metrics available yet")
                
        except Exception as e:
            st.warning(f"Could not load metrics: {str(e)}")
    
    # Results display
    if st.session_state.research_results:
        st.markdown("---")
        st.header("📋 Research Results")
        render_results_display(st.session_state.research_results)
    
    # Research history
    if st.session_state.research_history:
        st.markdown("---")
        st.header("📚 Research History")
        
        history_df = pd.DataFrame(st.session_state.research_history)
        
        # Format the dataframe
        if not history_df.empty:
            history_df["query"] = history_df["query"].str[:50] + "..."
            history_df["execution_time"] = history_df["execution_time"].round(1).astype(str) + "s"
            
            st.dataframe(
                history_df[["timestamp", "query", "execution_time", "success"]],
                use_container_width=True
            )

if __name__ == "__main__":
    main()