
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
st.write("Upload a PDF or TXT and ask questions about its content.")

# Read API key securely from Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    api_key = None

uploaded_file = st.file_uploader(
    "Upload your document",
    type=["pdf", "txt"]
)

if not api_key:
    st.warning(
        "Please add GEMINI_API_KEY in "
        "Streamlit App Settings → Secrets."
    )

elif uploaded_file is not None:
    try:
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
        else:
            st.success("Document uploaded successfully!")

            with st.expander("Document Preview"):
                st.text_area(
                    "Extracted text",
                    text,
                    height=250
                )

            st.subheader("💬 Ask AI about your document")

            question = st.text_input(
                "Enter your question",
                placeholder="What is this document about?"
            )

            if st.button("Ask AI", type="primary"):
                if not question.strip():
                    st.warning("Please enter a question.")
                else:
                    # Keep requests within a practical size limit.
                    # This simple version sends the first 30,000
                    # characters of the extracted document.
                    document_text = text[:30000]

                    prompt = f"""
You are an assistant that answers questions about documents.
Use the document below to answer the user's question.
If the answer is not in the document, say that clearly.
Do not invent facts.

DOCUMENT:
{document_text}

USER QUESTION:
{question}
"""

                    try:
                        with st.spinner("AI is reading your document..."):
                            client = genai.Client(api_key=api_key)
                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=prompt
                            )

                        if response.text:
                            st.subheader("Answer")
                            st.write(response.text)
                        else:
                            st.warning(
                                "The AI returned an empty answer. "
                                "Please try again."
                            )
                            except Exception as e:
                                st.error("AI request failed.")
                                st.code(f"{type(e).__name__}: {e}")

    except Exception as e:
        st.error(f"Could not read the document: {e}")
