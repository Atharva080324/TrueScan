import streamlit as st
import requests
from typing import Literal

SOURCE_TYPES = Literal["news", "reddit", "both"]
BACKEND_URL = "http://127.0.0.1:8000"


def check_backend_connection():
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None


def main():
    st.set_page_config(page_title="TrueScan", page_icon="🔍", layout="wide")
    st.markdown("<h1 style='text-align:center;'>🔍 TrueScan</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:gray;'>AI-powered news summaries & audio generator</p>", unsafe_allow_html=True)

    # Backend Check
    is_connected, _ = check_backend_connection()

    if not is_connected:
        st.error("🚨 Backend not running.")
        st.code("uvicorn backend:app --reload", language="bash")
        st.stop()

    # User Input
    st.markdown("### 📝 Enter Topics")
    topics = st.text_input("Example: AI, SpaceX, Elections", placeholder="Type your topics here...")

    source_type = st.radio(
        "Source:",
        ["both", "news", "reddit"],
        horizontal=True
    )

    generate = st.button("🚀 Generate Summary", use_container_width=True, type="primary")

    if generate:
        if not topics.strip():
            st.error("Please enter at least one topic.")
            return

        with st.spinner("Fetching and generating audio summary..."):
            response = requests.post(
                f"{BACKEND_URL}/generate-news-audio-with-script",
                json={
                    "topics": [t.strip() for t in topics.split(",")],
                    "source_type": source_type
                },
                timeout=300
            )

        if response.status_code == 200:
            result = response.json()
            script_text = result.get("script", "")
            audio_filename = result.get("audio_filename", "")

            st.success("✔ Summary Generated")

            st.markdown("---")
            st.markdown("### 📄 Summary Script")
            st.text_area("", script_text, height=300)

            st.download_button(
                "⬇ Download Script",
                data=script_text,
                file_name="summary.txt",
                mime="text/plain",
                use_container_width=True
            )

            st.markdown("---")
            st.markdown("### 🔊 Audio")

            audio_response = requests.get(f"{BACKEND_URL}/download-audio/{audio_filename}")

            if audio_response.status_code == 200:
                st.audio(audio_response.content, format="audio/mpeg")
                st.download_button(
                    "🎧 Download Audio",
                    data=audio_response.content,
                    file_name="summary.mp3",
                    mime="audio/mpeg",
                    use_container_width=True
                )
            else:
                st.error("Failed to load audio.")

        else:
            st.error(f"API Error: {response.status_code}")
            st.write(response.text)

    st.markdown(
        "<br><p style='text-align:center;color:gray;font-size:12px;'>TrueScan © 2025</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
