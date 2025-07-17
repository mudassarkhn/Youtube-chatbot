import streamlit as st
from rag_youtube import extract_video_id, load_transcript, build_vector_store, get_retrieval_chain, CHROMA_DIR
import os
from langchain_community.vectorstores import Chroma

st.set_page_config(page_title="YouTube RAG Chatbot", layout="centered")

st.title("📺 YouTube Video QA Bot")

video_id = st.text_input("🔗 Enter YouTube Video ID")

if video_id:
    st.video(f"https://www.youtube.com/watch?v={video_id}")

    if "transcript_loaded" not in st.session_state:
        transcript = load_transcript(video_id)
        if transcript:
            st.session_state.transcript_loaded = True
            st.session_state.db = build_vector_store(transcript)
            st.session_state.chain = get_retrieval_chain(st.session_state.db)
            st.success("Transcript loaded and vector store created.")
        else:
            st.error("Transcript not available for this video.")

if st.session_state.get("transcript_loaded"):
    st.markdown("### 💬 Ask a question about the video")
    user_input = st.text_input("Your Question", key="question_input")

    if user_input:
        response = st.session_state.chain.invoke({"input": user_input})
        st.markdown(f"**Answer:** {response['answer']}")
