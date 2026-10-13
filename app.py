
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
    "Upload a PDF or TXT document and ask AI questions about it."
)

# Get API key securely from Streamlit Secrets
try:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    api_key = ""

# Upload PDF or TXT
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
        # Extract document text
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
                "utf-8",
                errors="replace"
            )

        if not text.strip():
            st.warning(
                "No readable text found. "
                "This PDF may be scanned or image-only."
            )

        else:
            st.success("Document uploaded successfully!")

            with st.expander("📖 Document Preview"):
                st.text_area(
                    "Extracted text",
                    text,
                    height=250
                )

            st.subheader("💬 Ask AI about your document")

            # Keep the question and answer interaction
            # together in a form.
            with st.form("question_form"):
                question = st.text_input(
                    "Enter your question",
                    placeholder="What is this document about?"
                )

                submitted = st.form_submit_button(
                    "Ask AI",
                    type="primary"
                )

            if submitted:
                if not question.strip():
                    st.warning("Please enter a question.")

                else:
                    # Send a limited amount of document text
                    document_text = text[:30000]

                    prompt = f"""
You are an assistant that answers questions about documents.

Instructions:
- Answer using the document provided below.
- If the answer is not in the document, say so clearly.
- Do not invent facts.
- Give a clear and helpful answer.

DOCUMENT:
{document_text}

USER QUESTION:
{question}
"""

                    try:
                        with st.spinner(
                            "AI is reading your document..."
                        ):
                            client = genai.Client(
                                api_key=api_key
                            )

                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=prompt
                            )

                        if response.text:
                            st.subheader("🤖 AI Answer")
                            st.markdown(response.text)
                        else:
                            st.warning(
                                "The AI returned an empty answer. "
                                "Please try another question."
                            )

                    except Exception as e:
                        st.error("AI request failed.")
                        st.write(
                            "Error type:",
                            type(e).__name__
                        )
                        st.code(str(e))

    except Exception as e:
        st.error("Could not read the document.")
        st.code(f"{type(e).__name__}: {e}")
