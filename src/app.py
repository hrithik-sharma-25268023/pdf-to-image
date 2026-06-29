"""Streamlit UI"""

import streamlit as 


st.set_page_config(layout="wide")

st.title("📄 Invoice Processing System")

# Upload PDF
uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if uploaded_file is not None:

    # Two columns
    col1, col2 = st.columns(2)

    # Use the original filename for S3 key
    pdf_filename = uploaded_file.name
    base_name = os.path.splitext(pdf_filename)[0]
    
    # S3 paths
    s3_key_pdf = f"app/input/{pdf_filename}"
    s3_key_image = f"app/interim/images/{base_name}.png"
    s3_key_text = f"app/interim/text/{base_name}.txt"
    s3_json_key = f"app/output/{base_name}.json"
    
    # Read PDF bytes
    pdf_bytes = uploaded_file.read()
    
    # Upload PDF to S3
    with st.spinner("Uploading PDF to S3..."):
        FILE_SYSTEM.write_pdf(
            bucket=BUCKET_NAME, 
            key=s3_key_pdf, 
            pdf_bytes=pdf_bytes
        )
    
    # Convert PDF to image (single page)
    with st.spinner("Converting PDF to PNG..."):
        images = convert_from_bytes(pdf_bytes)
        img = images[0]
        
        # Convert PIL Image to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
    
    # Upload PNG to S3
    with st.spinner("Uploading PNG to S3..."):
        FILE_SYSTEM.write_png(
            bucket=BUCKET_NAME,
            key=s3_key_image,
            image_bytes=img_bytes
        )
    
    # LEFT: PDF Preview
    with col1:
        st.subheader("📄 Invoice Preview")
        st.image(img, width="stretch")

    # RIGHT: Storage Info & Operations
    with col2:
        st.subheader("📄 JSON Preview")
        text = run_ocr(FILE_SYSTEM, BUCKET_NAME, s3_key_image, s3_key_text)
        json_data = extract_invoice_with_llm(text)
        st.json(json_data)

        with st.spinner("Uploading JSON to S3..."):
            FILE_SYSTEM.write_json(bucket=BUCKET_NAME, key=s3_json_key, data=json_data)

    # Saving JSON to Database into RDS (Relational Database Table)
    with st.spinner("Saving to database..."):
        insert_invoice_into_db(json_data=json_data, s3_uri=f"s3://{BUCKET_NAME}/"+s3_json_key)
    
    st.divider()
    st.subheader("📊 Displaying Stored Data")


    with st.spinner("Fetching data from database..."):
        try:
            invoices_df, items_df = fetch_tables_from_db()
            invoices_df = invoices_df.drop(columns=["pdf_file_name"], errors="ignore")
            items_df = items_df.drop(columns=["pdf_file_name"], errors="ignore")

            st.markdown("### Invoices Table")
            invoices_df = invoices_df[invoices_df['s3_json_path']==f"s3://{BUCKET_NAME}/" + s3_json_key]
            st.dataframe(invoices_df, use_container_width=True)

            st.markdown("### Invoice Items Table")
            items_df = items_df[items_df['s3_json_path']==f"s3://{BUCKET_NAME}/" + s3_json_key]
            st.dataframe(items_df, use_container_width=True)

        except Exception as e:
            st.error(f"Error fetching data: {e}")

    

    metadata = {
        "request_id": str(uuid.uuid4()),
        "upload_timestamp": datetime.utcnow().isoformat(),

        "file_info": {
            "pdf_file_name": pdf_filename,
            "file_type": "pdf",
            "bucket_name": BUCKET_NAME
        },

        "s3_paths": {
            "pdf_path": s3_key_pdf,
            "image_path": s3_key_image,
            "text_path": s3_key_text,
            "json_path": s3_json_key
        },

        "file_sizes": {
            "pdf_size_kb": round(len(pdf_bytes) / 1024, 2),
            "image_size_kb": round(len(img_bytes) / 1024, 2)
        },

        "invoice_summary": {
            "invoice_number": json_data.get("invoice_number"),
            "invoice_date": json_data.get("invoice_date"),
            "vendor_name": json_data.get("vendor", {}).get("name"),
            "customer_name": json_data.get("customer", {}).get("name"),
            "total_amount": json_data.get("total_amount"),
            "num_items": len(json_data.get("items", []))
        },

        "processing_info": {
            "ocr_status": "success",
            "llm_status": "success",
            "processing_status": "completed",
            "source": "streamlit_app"
        }
    }


    with st.spinner("Saving metadata to DynamoDB..."):
        metadata = save_metadata_to_dynamodb(
            pdf_filename=pdf_filename,
            bucket_name=BUCKET_NAME,
            s3_key_pdf=s3_key_pdf,
            s3_key_image=s3_key_image,
            s3_key_text=s3_key_text,
            s3_json_key=s3_json_key,
            pdf_bytes=pdf_bytes,
            img_bytes=img_bytes,
            json_data=json_data
        )

    st.success("Metadata saved to DynamoDB!")
    st.json(metadata)