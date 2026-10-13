import streamlit as st
from pypdf import PdfReader
from io import BytesIO

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Document Assistant")
st.write("Upload a PDF or TXT document and explore its content.")

uploaded_file = st.file_uploader(
    "Upload your document",
    type=["pdf", "txt"]
)

if uploaded_file is not None:
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
                "The PDF may contain scanned images."
            )
        else:
            st.success("Document uploaded successfully!")
            st.subheader("Document Preview")
            st.text_area(
                "Extracted text",
                text,
                height=300
            )

            st.subheader("Ask about your document")
            question = st.text_input(
                "Enter your question"
            )

            if st.button("Search Document"):
                if question.strip():
                    paragraphs = [
                        p.strip()
                        for p in text.splitlines()
                        if p.strip()
                    ]
                    keywords = [
                        word.lower().strip(".,?!:")
                        for word in question.split()
                        if len(word) > 2
                    ]
                    matches = [
                        p for p in paragraphs
                        if any(
                            word in p.lower()
                            for word in keywords
                        )
                    ]

                    if matches:
                        st.write("Relevant text found:")
                        for match in matches[:10]:
                            st.write("- " + match)
                    else:
                        st.info(
                            "No matching text found. "
                            "Try different keywords."
                        )
                else:
                    st.warning("Please enter a question.")

    except Exception as e:
        st.error(f"Could not read the document: {e}")

