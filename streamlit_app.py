import streamlit as st
from fpdf import FPDF
import io

from summarizer import extract_text, summarize_text
from quiz_generator import generate_quiz

# -----------------------------
# Helper: generate PDF from Markdown
# -----------------------------
def generate_pdf_from_md(md_text: str) -> io.BytesIO:
    """
    Convert markdown string into a simple PDF, returned as a BytesIO buffer.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in md_text.split("\n"):
        pdf.multi_cell(0, 8, line)
    # Return PDF as binary string, then wrap in BytesIO
    pdf_bytes = pdf.output(dest="S").encode('latin-1')
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer

# -----------------------------
# Streamlit page configuration
# -----------------------------
st.set_page_config(
    page_title="SummarIQ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Initialize session state keys
# -----------------------------
for key in ("summary_md", "summary_html", "quiz", "quiz_answers", "q_index", "quiz_submitted"):
    if key not in st.session_state:
        st.session_state[key] = None

# -----------------------------
# Sidebar: File upload & method
# -----------------------------
st.sidebar.header("📂 Upload & Settings")
method = st.sidebar.selectbox(
    "Summarization method",
    options=["easy", "80/20", "understanding"],
    format_func=lambda m: {
        "easy": "Easy – concise notes",
        "80/20": "80/20 – key vs supporting",
        "understanding": "Understanding – clear notes"
    }[m]
)
uploaded_file = st.sidebar.file_uploader("Select TXT or PDF file", type=["txt", "pdf"])

if st.sidebar.button("🔍 Summarize"):
    if not uploaded_file:
        st.sidebar.error("Please select a file first.")
    else:
        raw = extract_text(uploaded_file)
        if not raw:
            st.sidebar.error("Unable to extract text.")
        else:
            with st.spinner("Generating summary & quiz..."):
                md, html = summarize_text(raw, method)
                st.session_state.summary_md = md
                st.session_state.summary_html = html
                # Auto-generate quiz
                st.session_state.quiz = generate_quiz(md)
                st.session_state.q_index = 0
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False

# -----------------------------
# Main area: Title
# -----------------------------
st.title("📚 SummarIQ")
st.markdown("Generate AI-powered notes and dive straight into a quiz — no extra clicks!")

# -----------------------------
# Tabs: Notes & Quiz
# -----------------------------
tab1, tab2 = st.tabs(["📝 Notes", "❓ Quiz"])

# --- Notes Tab ---
with tab1:
    if st.session_state.summary_html:
        with st.expander("📖 View Full Notes", expanded=True):
            st.markdown(st.session_state.summary_html, unsafe_allow_html=True)

        # PDF download button
        pdf_buffer = generate_pdf_from_md(st.session_state.summary_md)
        st.download_button(
            label="💾 Download Notes as PDF",
            data=pdf_buffer,
            file_name="summary.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Upload a file and press 'Summarize' in the sidebar to see your notes.")

# --- Quiz Tab ---
with tab2:
    if not st.session_state.quiz:
        st.info("Create a summary first to unlock the quiz.")
    else:
        total = len(st.session_state.quiz)
        idx = st.session_state.q_index

        # Progress bar
        st.markdown(f"**Question {idx+1} of {total}**")
        st.progress((idx+1) / total)

        # Display current question
        q = st.session_state.quiz[idx]
        st.markdown(f"### Q{idx+1} ({q['difficulty'].capitalize()})")
        st.write(q['question'])

        # Capture answer
        options = [f"{opt}. {txt}" for opt, txt in q["options"].items()]
        sel = st.radio("Select an answer:", options, key=f"choice_{idx}")
        st.session_state.quiz_answers[idx] = sel

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Previous", key="prev") and idx > 0:
                st.session_state.q_index -= 1
        with col2:
            label = "Submit Quiz" if idx+1 == total else "Next"
            if st.button(label, key="next"):
                if idx+1 < total:
                    st.session_state.q_index += 1
                else:
                    st.session_state.quiz_submitted = True
        with col3:
            st.write("")

        # After submission: show results
        if st.session_state.quiz_submitted:
            score = sum(
                1 for i, q in enumerate(st.session_state.quiz)
                if st.session_state.quiz_answers[i].split(".")[0] == q["correct_answer"]
            )
            st.success(f"🏆 Your Score: {score}/{total}")
            for i, q in enumerate(st.session_state.quiz):
                st.markdown(f"**Q{i+1}.** {q['question']}")
                ans = st.session_state.quiz_answers.get(i, "No answer")
                correct_full = f"{q['correct_answer']}. {q['options'][q['correct_answer']]}"
                st.markdown(f"- Your Answer: {ans}")
                st.markdown(f"- Correct: **{correct_full}**")
                st.markdown(f"- Explanation: {q['explanation']}")
