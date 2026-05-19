"""
Arjun - Code Review Automation Tool
Streamlit User Interface

A precision-focused AI-powered code review assistant.
"""

import streamlit as st
import sys
from pathlib import Path
import requests

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core import ArjunReviewer, ReviewResult
from llm import get_severity_color, get_severity_emoji

# Page configuration
st.set_page_config(
    page_title="Arjun - Code Review",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .issue-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.75rem;
        border-left: 4px solid;
    }
    .issue-critical { background-color: #ffebee; border-left-color: #f44336; }
    .issue-high { background-color: #fff3e0; border-left-color: #ff9800; }
    .issue-medium { background-color: #fffde7; border-left-color: #ffeb3b; }
    .issue-low { background-color: #e8f5e9; border-left-color: #4caf50; }
    .issue-resolved { background-color: #e3f2fd; border-left-color: #2196f3; }
    
    .stat-card {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .stat-label {
        font-size: 0.875rem;
        color: #666;
    }
    
    .section-header {
        font-size: 1.25rem;
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }
    
    .new-issues { color: #f44336; }
    .existing-issues { color: #ff9800; }
    .resolved-issues { color: #4caf50; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'reviewer' not in st.session_state:
        st.session_state.reviewer = None
    if 'review_result' not in st.session_state:
        st.session_state.review_result = None
    if 'connection_checked' not in st.session_state:
        st.session_state.connection_checked = False
    if 'model_name' not in st.session_state:
        st.session_state.model_name = "qwen2.5-coder:7b"


def render_header():
    """Render the application header."""
    st.markdown('<div class="main-header">🎯 Arjun</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Code Review Automation Tool</div>', unsafe_allow_html=True)


def get_local_ollama_models() -> list:
    """Fetch locally available Ollama models from local Ollama server."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        response.raise_for_status()
        data = response.json()
        models = [item.get("name") for item in data.get("models", []) if item.get("name")]
        return models
    except Exception:
        return []


def render_sidebar():
    """Render the sidebar with configuration options."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection
        model_options = get_local_ollama_models()
        if not model_options:
            model_options = [st.session_state.model_name]
            st.warning("Could not fetch local Ollama models. Ensure Ollama is running on localhost:11434")
        elif st.session_state.model_name not in model_options:
            if "qwen2.5-coder:7b" in model_options:
                st.session_state.model_name = "qwen2.5-coder:7b"
            else:
                st.session_state.model_name = model_options[0]
        
        selected_model = st.selectbox(
            "Select Ollama Model",
            options=model_options,
            index=model_options.index(st.session_state.model_name) if st.session_state.model_name in model_options else 0,
            help="Choose an installed local Ollama model"
        )
        
        if selected_model != st.session_state.model_name:
            st.session_state.model_name = selected_model
            st.session_state.reviewer = None
            st.session_state.connection_checked = False
        
        st.divider()
        
        # Connection status
        st.subheader("🔌 Connection Status")
        
        if st.button("Check Ollama Connection", use_container_width=True):
            with st.spinner("Checking connection..."):
                try:
                    reviewer = ArjunReviewer(model_name=st.session_state.model_name)
                    if reviewer.check_connection():
                        st.success("✅ Ollama is connected!")
                        st.session_state.reviewer = reviewer
                        st.session_state.connection_checked = True
                    else:
                        st.error("❌ Cannot connect to Ollama")
                        st.info("Make sure Ollama is running: `ollama serve`")
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")
        
        if st.session_state.connection_checked:
            st.success(f"Using: {st.session_state.model_name}")
        
        st.divider()
        
        # Global statistics
        st.subheader("📊 Global Statistics")
        if st.session_state.reviewer:
            stats = st.session_state.reviewer.get_global_stats()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Issues", stats['total_issues'])
                st.metric("Open Issues", stats['open_issues'])
            with col2:
                st.metric("Resolved", stats['resolved_issues'])
                st.metric("Acknowledged", stats['acknowledged_issues'])
            
            st.metric("Acceptance Rate", f"{stats['acceptance_ratio']}%")
            st.metric("Resolution Rate", f"{stats['resolution_ratio']}%")
        else:
            st.info("Connect to Ollama to see statistics")
        
        st.divider()
        
        # About section
        st.subheader("ℹ️ About Arjun")
        st.markdown("""
        **Arjun** symbolizes precision and focus in code review.
        
        **Features:**
        - 🔍 Automated code analysis
        - 💾 Persistent issue tracking
        - 📈 Resolution monitoring
        - 🎯 Smart issue categorization
        
        **Powered by:**
        - LangChain
        - Ollama (Local LLM)
        - SQLite
        - Streamlit
        """)


def render_issue_card(issue: dict, issue_type: str = "existing"):
    """Render a single issue card."""
    severity = issue.get('severity', 'medium').lower()
    emoji = get_severity_emoji(severity)
    
    css_class = f"issue-{severity}" if issue_type != "resolved" else "issue-resolved"
    
    with st.container():
        st.markdown(f"""
        <div class="issue-card {css_class}">
            <strong>{emoji} {issue.get('issue_type', 'Unknown').title()}</strong> 
            <span style="float: right; font-size: 0.75rem; text-transform: uppercase;">{severity}</span>
            <br><br>
            <strong>Line {issue.get('issue_line', 'N/A')}:</strong> {issue.get('issue_description', 'No description')}
            <br><br>
            <em>💡 Solution:</em> {issue.get('issue_solution', 'No solution provided')}
        </div>
        """, unsafe_allow_html=True)

        if issue_type == "existing" and issue.get('line_updated'):
            old_line = issue.get('previous_issue_line', 'N/A')
            new_line = issue.get('issue_line', 'N/A')
            st.caption(f"↔️ Line updated from {old_line} to {new_line} (issue still open)")
        
        # Add acknowledge button for existing issues
        if issue_type == "existing" and not issue.get('user_acknowledged'):
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"✅ Acknowledge", key=f"ack_{issue.get('id', 0)}"):
                    if st.session_state.reviewer and issue.get('id'):
                        st.session_state.reviewer.acknowledge_issue(issue['id'])
                        st.rerun()


def render_issues_section(title: str, issues: list, css_class: str, issue_type: str = "existing"):
    """Render a section of issues."""
    count = len(issues)
    icon = "🆕" if issue_type == "new" else ("⏳" if issue_type == "existing" else "✅")
    
    st.markdown(f"""
    <div class="section-header {css_class}">
        {icon} {title} ({count})
    </div>
    """, unsafe_allow_html=True)
    
    if count == 0:
        st.info(f"No {title.lower()} found")
    else:
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.get('severity', 'medium').lower(), 2))
        
        for issue in sorted_issues:
            render_issue_card(issue, issue_type)


def render_acceptance_ratio(stats: dict):
    """Render the user acceptance ratio section."""
    st.markdown("""
    <div class="section-header" style="color: #1E88E5;">
        📊 User Acceptance Ratio
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total_issues']}</div>
            <div class="stat-label">Total Issues</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['acknowledged_issues']}</div>
            <div class="stat-label">Acknowledged</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #4caf50;">{stats['acceptance_ratio']}%</div>
            <div class="stat-label">Acceptance Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #2196f3;">{stats['resolution_ratio']}%</div>
            <div class="stat-label">Resolution Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Progress bar for acceptance
    if stats['open_issues'] > 0:
        st.progress(stats['acceptance_ratio'] / 100, text=f"Acceptance Progress: {stats['acknowledged_issues']}/{stats['open_issues']} issues acknowledged")
    else:
        st.success("All issues have been resolved! 🎉")


def render_review_results(result: ReviewResult):
    """Render the complete review results."""
    # Summary
    st.markdown("---")
    
    # File info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("File", result.filename)
    with col2:
        st.metric("Language", result.language)
    with col3:
        status = "🆕 New File" if result.is_new_file else "📝 Re-scanned"
        st.metric("Status", status)
    
    # Summary
    if result.summary:
        with st.expander("📋 Review Summary", expanded=True):
            st.write(result.summary)
            if "No code changes detected" in result.summary:
                st.info("No code changes detected in this upload, so issue state is preserved and resolved count remains 0 for this scan.")
    
    # Error handling
    if result.error:
        st.error(f"⚠️ Error during review: {result.error}")
        return
    
    st.markdown("---")
    
    # Three sections in tabs
    tab1, tab2, tab3 = st.tabs([
        f"🆕 New Issues ({len(result.new_issues)})",
        f"⏳ Existing Issues ({len(result.existing_issues)})",
        f"✅ Resolved Issues ({len(result.resolved_issues)})"
    ])
    
    with tab1:
        render_issues_section("New Issues", result.new_issues, "new-issues", "new")
    
    with tab2:
        render_issues_section("Existing Issues", result.existing_issues, "existing-issues", "existing")
    
    with tab3:
        render_issues_section("Resolved Issues", result.resolved_issues, "resolved-issues", "resolved")
        if len(result.resolved_issues) == 0 and len(result.historical_resolved_issues) > 0:
            st.markdown("---")
            st.caption("Showing previously resolved issues from scan history for this file")
            render_issues_section(
                "Previously Resolved Issues",
                result.historical_resolved_issues,
                "resolved-issues",
                "resolved"
            )
    
    st.markdown("---")
    
    # Acceptance ratio at the bottom
    render_acceptance_ratio(result.acceptance_stats)


def main():
    """Main application entry point."""
    init_session_state()
    render_header()
    render_sidebar()
    
    # Main content area
    st.markdown("### 📤 Upload Code File for Review")
    
    uploaded_file = st.file_uploader(
        "Choose a code file",
        type=['py', 'js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'h', 'cs', 
              'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala', 'sql', 'sh'],
        help="Upload a code file to analyze for issues"
    )
    
    if uploaded_file is not None:
        # Show file preview
        with st.expander("📄 File Preview", expanded=False):
            content = uploaded_file.read().decode('utf-8')
            st.code(content, language=uploaded_file.name.split('.')[-1])
            uploaded_file.seek(0)  # Reset file pointer
        
        # Review button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            review_clicked = st.button(
                "🎯 Review Code with Arjun",
                use_container_width=True,
                type="primary"
            )
        
        if review_clicked:
            if not st.session_state.reviewer:
                # Initialize reviewer
                with st.spinner("Initializing Arjun..."):
                    try:
                        st.session_state.reviewer = ArjunReviewer(
                            model_name=st.session_state.model_name
                        )
                    except Exception as e:
                        st.error(f"Failed to initialize: {str(e)}")
                        st.info("Make sure Ollama is running with the selected model.")
                        return
            
            # Perform review
            with st.spinner("🎯 Arjun is analyzing your code..."):
                try:
                    content = uploaded_file.read().decode('utf-8')
                    result = st.session_state.reviewer.review_file(
                        filename=uploaded_file.name,
                        content=content
                    )
                    st.session_state.review_result = result
                except Exception as e:
                    st.error(f"Review failed: {str(e)}")
                    return
    
    # Display results if available
    if st.session_state.review_result:
        render_review_results(st.session_state.review_result)


if __name__ == "__main__":
    main()
