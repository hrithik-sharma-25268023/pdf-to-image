"""Streamlit UI"""

from io import BytesIO

import boto3
import streamlit as st
from pdf2image import convert_from_bytes

from file_system import FileSystem

S3_CLIENT = boto3.client("s3")
FILE_SYSTEM = FileSystem(s3_client=S3_CLIENT)
BUCKET_NAME = "pdf-to-image-mini-app"

st.set_page_config(layout="wide")

st.title("📄 PDF to Image")

# Upload PDF
uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if st.button("Convert"):

    if uploaded_file is None:
        st.error("Please upload a PDF first.")
        st.stop()

    pdf_filename = uploaded_file.name
    pdf_bytes = uploaded_file.getvalue()
    filename = pdf_filename.rsplit(".", 1)[0]

    # Upload PDF
    with st.spinner("Uploading PDF..."):
        FILE_SYSTEM.write_pdf(bucket=BUCKET_NAME, key=f"pdf/{filename}.pdf", pdf_bytes=pdf_bytes)

    # Convert PDF to images
    with st.spinner("Converting PDF to images..."):
        images = convert_from_bytes(pdf_bytes)

    total_pages = len(images)

    st.write(f"Found **{total_pages}** page(s).")

    # Progress widgets
    progress_bar = st.progress(0)
    status = st.empty()

    # Upload each page
    for page_number, image in enumerate(images, start=1):

        status.info(f"Uploading page {page_number} of {total_pages}")

        buffer = BytesIO()
        image.save(buffer, format="PNG")

        FILE_SYSTEM.write_png( bucket=BUCKET_NAME, key=f"images/{filename}/page_{page_number}.png", image_bytes=buffer.getvalue())
        progress_bar.progress(page_number / total_pages)
    status.success("All pages uploaded successfully!")
    st.success(f"Uploaded PDF and {total_pages} PNG image(s) successfully!")
