
import streamlit as st
from pypdf import PdfReader
from io import BytesIO
from google import genai

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Document Assistant")
st.write(
    "Upload a document, generate a summary, "
    "and ask questions in your preferred language."
)

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Read API key securely from Streamlit Secrets
try:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    api_key = ""

if not api_key:
    st.error(
        "Please configure GEMINI_API_KEY in "
        "Streamlit App Settings → Secrets."
    )
    st.stop()

# Language selection
language = st.selectbox(
    "🌐 Choose your language / భాషను ఎంచుకోండి",
    ["English", "తెలుగు"]
)

if language == "తెలుగు":
    labels = {
        "upload": "మీ PDF లేదా TXT document upload చేయండి",
        "success": "Document విజయవంతంగా upload అయింది!",
        "preview": "Document Preview",
        "summary": "📝 Document Summary",
        "length": "Summary రకం ఎంచుకోండి",
        "short": "చిన్న Summary",
        "detailed": "వివరణాత్మక Summary",
        "bullets": "ముఖ్యమైన Points",
        "generate": "Summary తయారు చేయండి",
        "question": "మీ ప్రశ్నను ఇక్కడ టైప్ చేయండి",
        "ask": "AIని అడగండి",
        "answer": "🤖 AI సమాధానం",
        "empty": "దయచేసి ప్రశ్న టైప్ చేయండి.",
        "no_text": "ఈ document‌లో చదవగల text కనిపించలేదు. Scanned PDF కావచ్చు.",
        "working_summary": "Summary తయారవుతోంది...",
        "working_answer": "AI సమాధానం సిద్ధం చేస్తోంది...",
        "download": "Summary Download చేయండి",
    }
    output_language = "Telugu"
else:
    labels = {
        "upload": "Upload your PDF or TXT document",
        "success": "Document uploaded successfully!",
        "preview": "Document Preview",
        "summary": "📝 Document Summary",
        "length": "Choose summary style",
        "short": "Short Summary",
        "detailed": "Detailed Summary",
        "bullets": "Bullet Points",
        "generate": "Generate Summary",
        "question": "Type your question here",
        "ask": "Ask AI",
        "answer": "🤖 AI Answer",
        "empty": "Please enter a question.",
        "no_text": "No readable text found. This may be a scanned PDF.",
        "working_summary": "Generating summary...",
        "working_answer": "Preparing AI answer...",
        "download": "Download Summary",
    }
    output_language = "English"

uploaded_file = st.file_uploader(
    labels["upload"],
    type=["pdf", "txt"]
)

if uploaded_file is not None:
    try:
        # Extract text from PDF or TXT
        if uploaded_file.name.lower().endswith(".pdf"):
            reader = PdfReader(
                BytesIO(uploaded_file.getvalue())
            )
            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )
        else:
            text = uploaded_file.getvalue().decode(
                "utf-8", errors="replace"
            )

        if not text.strip():
            st.warning(labels["no_text"])
            st.stop()

        st.success(labels["success"])

        with st.expander(labels["preview"]):
            st.text_area(
                "Extracted text",
                text,
                height=250
            )

        # Keep prompt size practical for this first version
        document_text = text[:30000]

        # Create a new summary when the document or language changes
        summary_key = f"summary_{uploaded_file.name}_{language}"
        answer_key = f"answer_{uploaded_file.name}_{language}"

        st.subheader(labels["summary"])

        summary_style = st.selectbox(
            labels["length"],
            [
                labels["short"],
                labels["detailed"],
                labels["bullets"]
            ]
        )

        if st.button(labels["generate"], type="primary"):
            if summary_style == labels["short"]:
                style_instruction = (
                    "Write a concise summary in 5 to 7 sentences."
                )
            elif summary_style == labels["detailed"]:
                style_instruction = (
                    "Write a detailed summary with headings and key points."
                )
            else:
                style_instruction = (
                    "Summarize the document using clear bullet points."
                )

            summary_prompt = f"""
You are a helpful document summarization assistant.
Write the entire answer in {output_language}.
{style_instruction}
Use only information from the document.
Do not invent facts. Preserve important names, dates, and numbers.

DOCUMENT:
{document_text}
"""

            try:
                with st.spinner(labels["working_summary"]):
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=summary_prompt
                    )

                if response.text:
                    st.session_state[summary_key] = response.text
                else:
                    st.warning("The AI returned an empty summary.")

            except Exception as e:
                st.error("Could not generate summary.")
                st.code(f"{type(e).__name__}: {e}")

        if st.session_state.get(summary_key):
            st.markdown(st.session_state[summary_key])

            st.download_button(
                labels["download"],
                data=st.session_state[summary_key],
                file_name="document_summary.txt",
                mime="text/plain"
            )

        st.divider()
        st.subheader("💬 Ask AI")

        with st.form("question_form"):
            question = st.text_input(labels["question"])
            ask_clicked = st.form_submit_button(labels["ask"])

        if ask_clicked:
            if not question.strip():
                st.warning(labels["empty"])
            else:
                question_prompt = f"""
You answer questions about documents.
Answer entirely in {output_language}.
Use the document as your source.
If the answer is not in the document, say so clearly.
Do not invent facts.

DOCUMENT:
{document_text}

USER QUESTION:
{question}
"""

                try:
                    with st.spinner(labels["working_answer"]):
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=question_prompt
                        )
                        
if response.text:
    answer = response.text

    # Save question and answer
    st.session_state.chat_history.append({
        "question": question,
        "answer": answer
    })

    st.subheader(labels["answer"])
    st.markdown(answer)
else:
    st.warning("The AI returned an empty answer.")

                except Exception as e:
                    st.error("AI request failed.")
                    st.code(f"{type(e).__name__}: {e}")

    except Exception as e:
        st.error("Could not read the document.")
        st.code(f"{type(e).__name__}: {e}")

# Display chat history
st.divider()
st.subheader("📚 Chat History")

if st.session_state.chat_history:
    for i, chat in enumerate(
        st.session_state.chat_history, start=1
    ):
        with st.expander(f"Question {i}: {chat['question']}"):
            st.markdown("**Answer:**")
            st.write(chat["answer"])

    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
else:
    st.info("మీరు ఇంకా ప్రశ్నలు అడగలేదు. / No questions asked yet.")
