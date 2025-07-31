import streamlit as st
from datetime import datetime

def render_query_input() -> str:
    """
    Render the query input component
    
    Returns:
        The research query if submitted, None otherwise
    """
    
    # Query input form
    with st.form("research_form", clear_on_submit=True):
        st.markdown("### Enter your research question:")
        
        # Main query input
        query = st.text_area(
            "Research Query",
            placeholder="Example: What are the latest developments in renewable energy storage technologies?",
            height=100,
            help="Enter a detailed research question. The more specific you are, the better results you'll get.",
            label_visibility="collapsed"
        )
        
        # Example queries
        st.markdown("**💡 Example Queries:**")
        example_queries = [
            "What are the environmental impacts of electric vehicles compared to traditional cars?",
            "How effective are remote work policies on employee productivity?",
            "What are the latest breakthroughs in artificial intelligence for healthcare?",
            "What is the current state of quantum computing research?",
            "How do different social media platforms affect mental health?"
        ]
        
        selected_example = st.selectbox(
            "Or choose an example:",
            [""] + example_queries,
            help="Select an example query to get started quickly"
        )
        
        # Use example if selected
        if selected_example and not query:
            query = selected_example
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_button = st.form_submit_button(
                "🔍 Start Research",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            clear_button = st.form_submit_button(
                "🗑️ Clear",
                use_container_width=True
            )
        
        # Advanced options expander
        with st.expander("🔧 Advanced Options"):
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                focus_areas = st.multiselect(
                    "Focus Areas",
                    ["Academic Papers", "News Articles", "Government Reports", 
                     "Industry Reports", "Blog Posts", "Statistics"],
                    help="Specify which types of sources to prioritize"
                )
                
                time_range = st.selectbox(
                    "Time Range",
                    ["Any time", "Past year", "Past 2 years", "Past 5 years"],
                    help="Limit results to a specific time period"
                )
            
            with col_adv2:
                language = st.selectbox(
                    "Language",
                    ["English", "Spanish", "French", "German", "Any"],
                    help="Preferred language for sources"
                )
                
                geographic_focus = st.text_input(
                    "Geographic Focus",
                    placeholder="e.g., United States, Europe, Global",
                    help="Focus on specific regions or countries"
                )
    
    # Handle form submission
    if submit_button and query.strip():
        # Store advanced options in session state for use in main app
        st.session_state.research_options = {
            "focus_areas": focus_areas,
            "time_range": time_range,
            "language": language,
            "geographic_focus": geographic_focus
        }
        
        return query.strip()
    
    elif submit_button and not query.strip():
        st.error("⚠️ Please enter a research query")
        return None
    
    elif clear_button:
        st.rerun()
        return None
    
    return None