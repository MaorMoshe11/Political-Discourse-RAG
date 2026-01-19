import os
import time
from google.cloud import vision_v1
from google.cloud import storage
from google.cloud.exceptions import NotFound

# --- CONFIGURATION ---
GCP_PROJECT_ID = 'gen-lang-client-0883899420'
GCS_BUCKET_NAME = 'my-knesset-protocol-ocr-2025'
GCS_OUTPUT_PREFIX = 'ocr_protocol1_results/'

# Local file paths
FULL_PDF_PATH = 'משק החשמל פרוטוקול 8 (1).pdf'
OUTPUT_FILENAME = "extracted_text_google_vision_hebrew.txt"

# GCS processing paths
GCS_PDF_FILENAME = os.path.basename(FULL_PDF_PATH)


def create_or_check_bucket(bucket_name, project_id, location='US'):
    """Checks if a GCS bucket exists and creates it if it does not."""
    if not project_id or project_id == 'YOUR_GCP_PROJECT_ID':
        raise ValueError("GCP_PROJECT_ID is missing or invalid.")

    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)

    if bucket.exists():
        print(f"Bucket '{bucket_name}' already exists.")
        return True

    print(f"Bucket '{bucket_name}' does not exist. Creating it now...")
    try:
        new_bucket = storage_client.create_bucket(bucket_name, location=location)
        print(f"Bucket '{new_bucket.name}' created successfully in {new_bucket.location}.")
        return True
    except Exception as e:
        print(f"ERROR: Could not create bucket. Error: {e}")
        return False


def upload_pdf_to_gcs(local_path, bucket_name, gcs_filename, project_id):
    """Uploads the local PDF file to the GCS bucket."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_filename)

    if os.path.exists(local_path):
        print(f"\n1. UPLOADING: {gcs_filename} to GCS...")
        blob.upload_from_filename(local_path)
        print("   Upload complete.")
        return f"gs://{bucket_name}/{gcs_filename}"
    else:
        raise FileNotFoundError(f"Local PDF file not found at: {local_path}")


def async_detect_document(gcs_source_uri, gcs_destination_uri, project_id):
    """Executes asynchronous OCR job on the PDF and waits for completion."""
    client = vision_v1.ImageAnnotatorClient(
        client_options={"quota_project_id": project_id}
    )

    input_config = vision_v1.InputConfig(
        gcs_source=vision_v1.GcsSource(uri=gcs_source_uri),
        mime_type="application/pdf"
    )

    output_config = vision_v1.OutputConfig(
        gcs_destination=vision_v1.GcsDestination(uri=gcs_destination_uri),
        batch_size=20
    )

    feature = vision_v1.Feature(type_=vision_v1.Feature.Type.DOCUMENT_TEXT_DETECTION)

    annotate_file_request = vision_v1.AsyncAnnotateFileRequest(
        input_config=input_config,
        features=[feature],
        output_config=output_config
    )

    operation = client.async_batch_annotate_files(requests=[annotate_file_request])
    print("\n2. OCR STARTED: Waiting for operation to complete (max 10 min)...")
    operation.result(timeout=600)
    print("   OCR Operation completed. Results saved to GCS.")


def process_vision_output(bucket_name, prefix, output_filename, project_id):
    """Downloads JSON output from GCS, extracts text, and saves to a local file."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob_list = list(bucket.list_blobs(prefix=prefix))

    full_text = ""
    print(f"\n3. PROCESSING: Found {len(blob_list)} result files. Extracting text...")

    for blob in blob_list:
        if blob.name.endswith("/"):
            continue

        json_string = blob.download_as_text()
        response = vision_v1.AnnotateFileResponse.from_json(json_string)

        for response_page in response.responses:
            if response_page.full_text_annotation:
                text = response_page.full_text_annotation.text
                full_text += f"\n\n--- PAGE BREAK ---\n\n"
                full_text += text

    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print(f"\nSUCCESS: Extracted text saved locally to: {output_filename}")


if __name__ == "__main__":
    try:
        # Check environment and setup bucket
        if create_or_check_bucket(GCS_BUCKET_NAME, GCP_PROJECT_ID):
            # 1. Upload
            gcs_input_uri = upload_pdf_to_gcs(
                FULL_PDF_PATH, GCS_BUCKET_NAME, GCS_PDF_FILENAME, GCP_PROJECT_ID
            )

            # 2. Setup Output path
            gcs_output_uri = f"gs://{GCS_BUCKET_NAME}/{GCS_OUTPUT_PREFIX}"

            # 3. OCR Process
            async_detect_document(gcs_input_uri, gcs_output_uri, GCP_PROJECT_ID)

            # 4. Results processing
            process_vision_output(
                GCS_BUCKET_NAME, GCS_OUTPUT_PREFIX, OUTPUT_FILENAME, GCP_PROJECT_ID
            )

    except Exception as e:
        print(f"\n--- FATAL ERROR ---")
        print(f"An error occurred: {e}")