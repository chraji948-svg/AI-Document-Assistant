
import streamlit as st
from pypdf import PdfReader
from io import BytesIO
from google import genai
import hashlib

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Document Assistant")
st.write(
    "Upload documents, generate summaries, "
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
        "upload": "మీ PDF లేదా TXT documents upload చేయండి",
        "success": "Documents విజయవంతంగా చదవబడ్డాయి!",
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
        "no_text": "చదవగల text ఏ document‌లోనూ కనిపించలేదు.",
        "working_summary": "Summary తయారవుతోంది...",
        "working_answer": "AI సమాధానం సిద్ధం చేస్తోంది...",
        "download": "Summary Download చేయండి",
        "history": "📚 గత ప్రశ్నలు మరియు సమాధానాలు",
        "clear": "Chat History తొలగించండి",
        "no_history": "ఇంకా ప్రశ్నలు అడగలేదు.",
        "empty_summary": "AI నుంచి Summary రాలేదు.",
        "empty_answer": "AI నుంచి సమాధానం రాలేదు.",
        "summary_error": "Summary తయారు చేయలేకపోయాం.",
        "answer_error": "AI సమాధానం ఇవ్వలేకపోయింది.",
        "read_error": "Document చదవలేకపోయాం."
    }
    output_language = "Telugu"
else:
    labels = {
        "upload": "Upload your PDF or TXT documents",
        "success": "Documents read successfully!",
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
        "no_text": "No readable text was found in the documents.",
        "working_summary": "Generating summary...",
        "working_answer": "Preparing AI answer...",
        "download": "Download Summary",
        "history": "📚 Chat History",
        "clear": "Clear Chat History",
        "no_history": "No questions asked yet.",
        "empty_summary": "The AI returned an empty summary.",
        "empty_answer": "The AI returned an empty answer.",
        "summary_error": "Could not generate summary.",
        "answer_error": "AI request failed.",
        "read_error": "Could not read the documents."
    }
    output_language = "English"

# Upload multiple documents
uploaded_files = st.file_uploader(
    labels["upload"],
    type=["pdf", "txt"],
    accept_multiple_files=True
)

if uploaded_files:
    extracted_documents = []
    document_names = []

    # Read every uploaded file
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.lower().endswith(".pdf"):
                reader = PdfReader(
                    BytesIO(uploaded_file.getvalue())
                )
                file_text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )
            else:
                file_text = uploaded_file.getvalue().decode(
                    "utf-8",
                    errors="replace"
                )

            if file_text.strip():
                extracted_documents.append(
                    f"DOCUMENT NAME: {uploaded_file.name}\n"
                    f"DOCUMENT CONTENT:\n{file_text}"
                )
                document_names.append(uploaded_file.name)
            else:
                st.warning(
                    f"No readable text found in "
                    f"{uploaded_file.name}."
                )

        except Exception as e:
            st.error(
                f"Could not read {uploaded_file.name}: "
                f"{type(e).__name__}: {e}"
            )

    if extracted_documents:
        st.success(labels["success"])

        # Combine document text for AI
        all_text = "\n\n--- NEXT DOCUMENT ---\n\n".join(
            extracted_documents
        )

        # Limit total text sent to AI
        document_text = all_text[:30000]

        # Create a unique key for these documents and language
        identity = "|".join(document_names) + "|" + language
        file_hash = hashlib.md5(
            (identity + document_text).encode("utf-8")
        ).hexdigest()

        summary_key = f"summary_{file_hash}"

        # Document preview
        with st.expander(labels["preview"]):
            st.caption(
                "Uploaded documents: "
                + ", ".join(document_names)
            )
            st.text_area(
                "Extracted text",
                document_text,
                height=250,
                key=f"preview_{file_hash}"
            )

        # Summary section
        st.subheader(labels["summary"])

        summary_style = st.selectbox(
            labels["length"],
            [
                labels["short"],
                labels["detailed"],
                labels["bullets"]
            ],
            key=f"style_{file_hash}"
        )

        if st.button(
            labels["generate"],
            type="primary",
            key=f"generate_{file_hash}"
        ):
            if summary_style == labels["short"]:
                style_instruction = (
                    "Write a concise summary in 5 to 7 sentences."
                )
            elif summary_style == labels["detailed"]:
                style_instruction = (
                    "Write a detailed summary with headings "
                    "and key points."
                )
            else:
                style_instruction = (
                    "Summarize the documents using clear "
                    "bullet points."
                )

            summary_prompt = f"""
You are a helpful document summarization assistant.
Write the entire answer in {output_language}.
{style_instruction}

Use only information from the supplied documents.
Do not invent facts. Preserve important names, dates,
and numbers. Clearly distinguish information from
different documents when relevant.

DOCUMENTS:
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
                    st.warning(labels["empty_summary"])

            except Exception as e:
                st.error(labels["summary_error"])
                st.code(f"{type(e).__name__}: {e}")

        # Display and download summary
        if st.session_state.get(summary_key):
            st.markdown(st.session_state[summary_key])

            st.download_button(
                labels["download"],
                data=st.session_state[summary_key],
                file_name="document_summary.txt",
                mime="text/plain",
                key=f"download_{file_hash}"
            )

        # Ask AI section
        st.divider()
        st.subheader("💬 Ask AI")

        with st.form(f"question_form_{file_hash}"):
            question = st.text_input(
                labels["question"],
                key=f"question_{file_hash}"
            )
            ask_clicked = st.form_submit_button(labels["ask"])

        if ask_clicked:
            if not question.strip():
                st.warning(labels["empty"])
            else:
                question_prompt = f"""
You answer questions about the supplied documents.
Answer entirely in {output_language}.
Use only the documents as your source.
If the answer is not present in the documents,
say so clearly. Do not invent facts.
If multiple documents are relevant, distinguish
between their information.

DOCUMENTS:
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

                        st.session_state.chat_history.append({
                            "question": question,
                            "answer": answer,
                            "document": ", ".join(document_names)
                        })

                        st.subheader(labels["answer"])
                        st.markdown(answer)
                    else:
                        st.warning(labels["empty_answer"])

                except Exception as e:
                    st.error(labels["answer_error"])
                    st.code(f"{type(e).__name__}: {e}")

    else:
        st.warning(labels["no_text"])

# Display chat history
st.divider()
st.subheader(labels["history"])

if st.session_state.chat_history:
    for i, chat in enumerate(
        reversed(st.session_state.chat_history),
        start=1
    ):
        question_title = chat["question"][:80]

        with st.expander(f"Q{i}: {question_title}"):
            st.caption(f"Document(s): {chat['document']}")
            st.markdown("**Question:**")
            st.write(chat["question"])
            st.markdown("**Answer:**")
            st.markdown(chat["answer"])

    if st.button(labels["clear"]):
        st.session_state.chat_history = []
        st.rerun()
else:
    st.info(labels["no_history"])
