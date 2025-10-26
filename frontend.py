import streamlit as st
import requests
from typing import Literal

# Constants
SOURCE_TYPES = Literal["news", "reddit", "both"]
BACKEND_URL = "http://127.0.0.1:8000"  # Fixed: Changed from 1234 to 8000

def check_backend_connection():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        return False, None
    except Exception:
        return False, None

def main(): 
    st.set_page_config(
        page_title="TrueScan - News Audio Generator",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 TrueScan")
    st.markdown("*Generate AI-powered audio summaries from news and social media*")
    
    # Check backend connection
    is_connected, health_data = check_backend_connection()
    
    # Connection status in sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Connection status indicator
        st.divider()
        st.subheader("🔌 Backend Status")
        if is_connected:
            st.success("🟢 Connected")
            if health_data:
                with st.expander("📊 Service Status"):
                    services = health_data.get("services", {})
                    for service, status in services.items():
                        icon = "✅" if status else "❌"
                        st.write(f"{icon} {service.capitalize()}")
        else:
            st.error("🔴 Disconnected")
            st.warning("Backend server not running!")
            st.info(f"Expected: `{BACKEND_URL}`")
            with st.expander("🛠️ How to fix"):
                st.code("uvicorn backend:app --reload", language="bash")
        
        if st.button("🔄 Refresh Connection", use_container_width=True):
            st.rerun()
        
        st.divider()
        
        # Source selection
        source_type = st.selectbox(
            "📡 Data Sources",
            options=["both", "news", "reddit"],
            format_func=lambda x: {
                "both": "🌐📱 News + Reddit",
                "news": "🌐 News Only",
                "reddit": "📱 Reddit Only"
            }[x],
            help="Choose which sources to analyze"
        )
    
    # Show warning if backend is not connected
    if not is_connected:
        st.error("⚠️ **Backend Connection Error**")
        st.markdown("""
        The backend server is not running. Please:
        1. Open a terminal
        2. Navigate to your project directory
        3. Run: `uvicorn backend:app --reload`
        4. Wait for "Application startup complete"
        5. Refresh this page
        """)
        st.stop()
    
    # Initialize session state
    if 'topics' not in st.session_state:
        st.session_state.topics = []
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0

    # Topic management
    st.subheader("📝 Topic Selection")
    st.markdown("*Add up to 3 topics to analyze*")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        new_topic = st.text_input(
            "Enter a topic to analyze",
            key=f"topic_input_{st.session_state.input_key}",
            placeholder="e.g., Artificial Intelligence, Climate Change, Space Exploration",
            label_visibility="collapsed"
        )
    with col2:
        add_disabled = len(st.session_state.topics) >= 3 or not new_topic.strip()
        if st.button("Add ➕", disabled=add_disabled, use_container_width=True):
            st.session_state.topics.append(new_topic.strip())
            st.session_state.input_key += 1
            st.rerun()

    # Display selected topics
    if st.session_state.topics:
        st.markdown("---")
        st.subheader("✅ Selected Topics")
        for i, topic in enumerate(st.session_state.topics):
            cols = st.columns([6, 1])
            cols[0].markdown(f"**{i+1}.** {topic}")
            if cols[1].button("🗑️", key=f"remove_{i}", help="Remove topic"):
                del st.session_state.topics[i]
                st.rerun()
    else:
        st.info("👆 Add at least one topic to get started")

    # Analysis controls
    st.markdown("---")
    st.subheader("🔊 Audio Generation")
    
    # Show topic count
    topic_count = len(st.session_state.topics)
    if topic_count > 0:
        st.write(f"Ready to analyze **{topic_count}** topic(s) from **{source_type}**")

    generate_button = st.button(
        "🚀 Generate Audio Summary", 
        disabled=len(st.session_state.topics) == 0,
        use_container_width=True,
        type="primary"
    )

    if generate_button:
        if not st.session_state.topics:
            st.error("Please add at least one topic")
        else:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔍 Scraping news sources...")
                progress_bar.progress(20)
                
                response = requests.post(
                    f"{BACKEND_URL}/generate-news-audio",
                    json={
                        "topics": st.session_state.topics,
                        "source_type": source_type
                    },
                    timeout=300  # 5 minutes timeout
                )

                progress_bar.progress(80)
                status_text.text("🎵 Generating audio...")

                if response.status_code == 200:
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    
                    st.success("🎉 Audio generated successfully!")
                    
                    # Audio player
                    st.audio(response.content, format="audio/mpeg")
                    
                    # Download button
                    st.download_button(
                        label="⬇️ Download Audio Summary",
                        data=response.content,
                        file_name="news-summary.mp3",
                        mime="audio/mpeg",
                        use_container_width=True,
                        type="primary"
                    )
                    
                    st.balloons()
                else:
                    progress_bar.empty()
                    status_text.empty()
                    handle_api_error(response)

            except requests.exceptions.Timeout:
                progress_bar.empty()
                status_text.empty()
                st.error("⏱️ Request timed out. The process is taking longer than expected.")
                st.info("This might happen with multiple topics. Try reducing the number of topics.")
                
            except requests.exceptions.ConnectionError:
                progress_bar.empty()
                status_text.empty()
                st.error("🔌 Connection Error: Lost connection to backend server")
                st.info("The backend might have crashed. Check the terminal running uvicorn.")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"⚠️ Unexpected Error: {str(e)}")
                with st.expander("🐛 Error Details"):
                    st.exception(e)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; padding: 20px;'>
            <p>🔍 TrueScan | Powered by AI</p>
            <p style='font-size: 12px;'>Generate news summaries from multiple sources</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def handle_api_error(response):
    """Handle API error responses"""
    try:
        error_detail = response.json().get("detail", "Unknown error")
        st.error(f"❌ API Error ({response.status_code}): {error_detail}")
        
        # Show detailed error in expander
        with st.expander("🔍 Error Details"):
            st.json(response.json())
            
    except ValueError:
        st.error(f"❌ Unexpected API Response ({response.status_code})")
        with st.expander("📄 Raw Response"):
            st.code(response.text)


if __name__ == "__main__":
    main()