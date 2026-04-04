import streamlit as st
import json
import pandas as pd
from dotenv import load_dotenv
import os
from src.mcqgenerator.MCQGenerator import generate_mcqs
from src.mcqgenerator.utils import read_file, read_url, get_table_data, save_response

load_dotenv()

# ── Page Config ───────────────────────────────────────────
st.set_page_config(page_title="MCQ Generator", page_icon="📝", layout="wide")
st.title("📝 MCQ Generator")
st.markdown("**Generate MCQs from any document using LangChain + Groq AI**")
st.divider()

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    default_key = os.getenv("GROQ_API_KEY", "")
    groq_api_key = st.text_input("🔑 Groq API Key", value=default_key, type="password")
    
    model = st.selectbox("🤖 Model", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-8b-8192",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ])

    st.divider()
    st.subheader("📊 MCQ Settings")
    num_questions = st.slider("Number of Questions", 3, 20, 5)
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    num_options = st.selectbox("Options per Question", [3, 4, 5], index=1)
    subject = st.text_input("📚 Subject Filter (optional)", placeholder="e.g. Machine Learning")

# ── Input Type Selection ──────────────────────────────────
st.subheader("📂 Upload Document")

input_type = st.radio(
    "Choose Input Type",
    ["📄 PDF", "📃 TXT", "📝 DOCX", "📊 CSV", "🌐 URL"],
    horizontal=True
)

# ── Session State Init ────────────────────────────────────
if "document_text" not in st.session_state:
    st.session_state.document_text = ""
if "file_info" not in st.session_state:
    st.session_state.file_info = ""
if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "checked" not in st.session_state:
    st.session_state.checked = {}
if "last_url" not in st.session_state:        # ← ADD AT END OF THIS BLOCK
    st.session_state.last_url = ""

# ── URL Input ─────────────────────────────────────────────
# ── URL Input ─────────────────────────────────────────────
if input_type == "🌐 URL":
    url = st.text_input("Enter URL", placeholder="https://example.com/article")

    # ── Auto load as soon as URL is entered ───────────────
    if url:
        # Only reload if URL changed
        if st.session_state.get("last_url") != url:
            with st.spinner("🌐 Loading URL content..."):
                try:
                    text, file_info = read_url(url)
                    st.session_state.document_text = text
                    st.session_state.file_info = file_info
                    st.session_state.last_url = url      # ← save last loaded url
                    st.success(f"✅ {file_info}")
                except Exception as e:
                    st.error(f"❌ Error loading URL: {str(e)}")
        else:
            st.success(f"✅ {st.session_state.file_info}")  # already loaded
# ── File Upload ───────────────────────────────────────────
else:
    ext_map = {
        "📄 PDF":  ["pdf"],
        "📃 TXT":  ["txt"],
        "📝 DOCX": ["docx"],
        "📊 CSV":  ["csv"],
    }

    uploaded_file = st.file_uploader(
        f"Upload {input_type} file",
        type=ext_map[input_type]
    )

    if uploaded_file:
        with st.spinner(f"📖 Reading {input_type} file..."):
            try:
                text, file_info = read_file(uploaded_file)
                st.session_state.document_text = text
                st.session_state.file_info = file_info
                st.success(f"✅ {file_info} | {len(text)} characters loaded")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

# ── Preview Document ──────────────────────────────────────
if st.session_state.document_text:
    with st.expander("👁️ Preview Document Content"):
        preview = st.session_state.document_text[:1000]
        st.write(preview + "..." if len(st.session_state.document_text) > 1000 else preview)
    st.info(f"📌 Loaded: {st.session_state.file_info}")

st.divider()

# ── Generate Button ───────────────────────────────────────
if st.button("🚀 Generate MCQs", use_container_width=True, type="primary"):

    if not groq_api_key:
        st.error("❌ Please enter your Groq API Key in the sidebar!")

    elif not st.session_state.document_text:
        st.error("❌ Please upload a file or load a URL first!")

    else:
        # ── Reset previous MCQs and answers ───────────────
        st.session_state.mcqs = []
        st.session_state.checked = {}

        with st.spinner("🤖 Generating MCQs... Please wait"):
            try:
                mcqs = generate_mcqs(
                    text=st.session_state.document_text,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    num_options=num_options,
                    subject=subject,
                    groq_api_key=groq_api_key,
                    model_name=model
                )
                save_response(mcqs)

                # ── Save to session state ──────────────────
                st.session_state.mcqs = mcqs

            except Exception as e:
                st.error(f"❌ Error generating MCQs: {str(e)}")
                st.stop()

# ── Show MCQs if available in session state ───────────────
if st.session_state.mcqs:
    mcqs = st.session_state.mcqs

    st.success(f"✅ Successfully generated {len(mcqs)} MCQs!")
    st.divider()

    # ── Tabs ──────────────────────────────────────────────
    tab1, tab2 = st.tabs(["🎮 Quiz Mode", "📊 Table View"])

    # ── Tab 1: Quiz Mode ──────────────────────────────────
    with tab1:
        st.subheader("🎮 Quiz Mode")

        for i, mcq in enumerate(mcqs):
            with st.expander(f"**Q{i+1}. {mcq['question']}**", expanded=True):

                selected = st.radio(
                    "Choose your answer:",
                    mcq["options"],
                    key=f"q_{i}",
                    index=None
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Check Answer", key=f"check_{i}"):
                        if not selected:
                            st.session_state.checked[i] = {"type": "warning"}
                        elif selected == mcq["correct_answer"]:
                            st.session_state.checked[i] = {
                                "type": "correct",
                                "correct": mcq["correct_answer"],
                                "explanation": mcq["explanation"]
                            }
                        else:
                            st.session_state.checked[i] = {
                                "type": "wrong",
                                "correct": mcq["correct_answer"],
                                "explanation": mcq["explanation"]
                            }

                with col2:
                    if st.button("👁️ Show Answer", key=f"show_{i}"):
                        st.session_state.checked[i] = {
                            "type": "show",
                            "correct": mcq["correct_answer"],
                            "explanation": mcq["explanation"]
                        }

                # ── Persistent Result ──────────────────────
                if i in st.session_state.checked:
                    result = st.session_state.checked[i]

                    if result["type"] == "warning":
                        st.warning("⚠️ Please select an option first!")

                    elif result["type"] == "correct":
                        st.success("🎉 Correct!")
                        st.info(f"💡 {result['explanation']}")

                    elif result["type"] == "wrong":
                        st.error(f"❌ Wrong! Correct: **{result['correct']}**")
                        st.info(f"💡 {result['explanation']}")

                    elif result["type"] == "show":
                        st.success(f"✅ Answer: **{result['correct']}**")
                        st.info(f"💡 {result['explanation']}")

    # ── Tab 2: Table View ─────────────────────────────────
    with tab2:
        st.subheader("📊 All MCQs Overview")
        table_data = get_table_data(mcqs)
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

    # ── Download Section ──────────────────────────────────
    st.divider()
    st.subheader("💾 Download MCQs")

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="⬇️ Download as JSON",
            data=json.dumps(mcqs, indent=2),
            file_name="mcqs.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        table_data = get_table_data(mcqs)
        df = pd.DataFrame(table_data)
        st.download_button(
            label="⬇️ Download as CSV",
            data=df.to_csv(index=False),
            file_name="mcqs.csv",
            mime="text/csv",
            use_container_width=True
        )