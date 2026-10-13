
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
st.write("Upload a document, summarize it, and ask questions.")

# Read API key securely from Streamlit Secrets
try:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    api_key = ""

if not api_key:
    st.warning(
        "Please add GEMINI_API_KEY in "
        "Streamlit App Settings → Secrets."
    )
    st.stop()

uploaded_file = st.file_uploader(
    "Upload your document",
    type=["pdf", "txt"]
)

if uploaded_file is not None:
    try:
        # Extract text from PDF or TXT
        if uploaded_file.name.lower().endswith(".pdf"):
            reader = PdfReader(BytesIO(uploaded_file.getvalue()))
            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )
        else:
            text = uploaded_file.getvalue().decode(
                "utf-8", errors="replace"
            )

        if not text.strip():
            st.warning(
                "No readable text found. "
                "Scanned PDFs may need OCR."
            )
            st.stop()

        st.success("Document uploaded successfully!")

        st.caption(
            f"File: {uploaded_file.name} | "
            f"Extracted characters: {len(text):,}"
        )

        with st.expander("📖 Document Preview"):
            st.text_area(
                "Extracted text",
                text,
                height=250
            )

        # Limit text sent to the AI
        document_text = text[:30000]

        st.subheader("📝 PDF / Document Summary")

        summary_style = st.selectbox(
            "Choose summary length",
            ["Short", "Detailed", "Bullet Points"]
        )

        if st.button("Generate Summary", type="primary"):
            summary_instructions = {
                "Short": "Write a concise summary in 5-7 sentences.",
                "Detailed": "Write a detailed summary with headings and key points.",
                "Bullet Points": "Summarize the document using clear bullet points."
            }

            summary_prompt = f"""
You are a helpful document summarization assistant.

Summarize the document using the following instruction:
{summary_instructions[summary_style]}

Use only information in the document.
Do not invent facts. If some content is unclear, mention that.
Write the summary in clear English.

DOCUMENT:
{document_text}
"""

            try:
                with st.spinner("Generating document summary..."):
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=summary_prompt
                    )

                if response.text:
                    st.session_state["document_summary"] = response.text
                else:
                    st.warning("The AI returned an empty summary.")

            except Exception as e:
                st.error("Could not generate the summary.")
                st.code(f"{type(e).__name__}: {e}")

        if st.session_state.get("document_summary"):
            st.markdown("### ✨ Summary")
            st.markdown(st.session_state["document_summary"])

            st.download_button(
                "Download Summary",
                data=st.session_state["document_summary"],
                file_name="document_summary.txt",
                mime="text/plain"
            )

        st.divider()

        st.subheader("💬 Ask AI about your document")

        with st.form("question_form"):
            question = st.text_input(
                "Enter your question",
                placeholder="What is this document about?"
            )
            ask_clicked = st.form_submit_button("Ask AI")

        if ask_clicked:
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                question_prompt = f"""
Answer the user's question using the document below.
If the answer is not present, say so clearly.
Do not invent facts. Answer in clear English.

DOCUMENT:
{document_text}

USER QUESTION:
{question}
"""

                try:
                    with st.spinner("AI is preparing your answer..."):
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=question_prompt
                        )

                    if response.text:
                        st.markdown("### 🤖 AI Answer")
                        st.markdown(response.text)
                    else:
                        st.warning("The AI returned an empty answer.")

                except Exception as e:
                    st.error("AI request failed.")
                    st.code(f"{type(e).__name__}: {e}")

    except Exception as e:
        st.error("Could not read the document.")
        st.code(f"{type(e).__name__}: {e}")
