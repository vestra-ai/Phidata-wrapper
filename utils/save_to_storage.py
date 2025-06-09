from config import storage_client

import csv, os
from io import StringIO

import os
import re

def swap_gcs_to_cdn_url(url, old_base_url=os.environ.get("GOOGLE_STORAGE_BASE_URL")):
    """
    Swaps Google Cloud Storage URLs with the CDN URL defined in the CDN_BASE_URL environment variable.
    If CDN_BASE_URL is not set, the URL is returned unchanged.

    Parameters:
        url (str): The URL to replace.
        old_base_url (str): The Google Cloud Storage base URL to replace, defaults to DEFAULT_GCS_BASE_URL.

    Returns:
        str: The URL with Google Cloud Storage URLs replaced by the CDN URL if CDN_BASE_URL is set.
    """
    # Fetch CDN base URL from environment variable
    new_base_url = os.environ.get("CDN_BASE_URL")
    
    # If CDN_BASE_URL is not set, return the URL unchanged
    if not new_base_url:
        return url
    
    # Regular expression to match any URL starting with the old Google Cloud Storage base URL
    pattern = re.compile(re.escape(old_base_url) + r"/[^\s]+")
    
    # Replace the base URL while preserving the path after it
    updated_url = pattern.sub(lambda match: match.group(0).replace(old_base_url, new_base_url), url)
    
    return updated_url


def upload_blob_to_bucket(blob_file, destination_blob_name: str, content_type: str = None, timeout: int = 300) -> str:
    """
    Uploads the blob file to a Cloud Storage bucket.

    Args:
        blob_file: The file object to upload.
        destination_blob_name: The destination path in the bucket.
        content_type: The content type of the file.
        timeout: Timeout for the upload operation in seconds. Default is 60 seconds (google cloud docs recommend 300 seconds)
        
    Returns:
        str: The gs:// URL of the uploaded blob.
    """
    try:

        # Get the bucket
        bucket = storage_client.bucket(os.environ.get('BUCKET_NAME'))

        # Create a blob (object) in the bucket
        blob = bucket.blob(destination_blob_name)
        blob.chunk_size = 5 * 1024 * 1024 # 5MB

        # For image files, ensure file pointer is at beginning before upload
        if content_type and content_type.startswith('image/'):
            blob_file.seek(0)

        # Upload the file to the blob
        blob.upload_from_file(blob_file, timeout=timeout, content_type=content_type)
    except Exception as e:
        print(f"Error uploading blob to bucket: {str(e)}")
        raise

    # Return the public URL
    return swap_gcs_to_cdn_url(blob.public_url)

def upload_csv_to_bucket(csv_string:str, destination_blob_name: str, timeout: int = 300) -> str:
    """
    Uploads a CSV file to a Cloud Storage bucket.

    Args:
        data: A list of dictionaries representing the rows of the CSV.
        destination_blob_name: The destination path in the bucket.
        timeout: Timeout for the upload operation in seconds.

    Returns:
        str: The public URL of the uploaded CSV file.
    """
    try:
        # Upload the CSV to the bucket
        bucket = storage_client.bucket(os.environ.get('BUCKET_NAME'))
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(csv_string, content_type='text/csv', timeout=timeout)
        # Return the public URL
        return swap_gcs_to_cdn_url(blob.public_url)

    except Exception as e:
        print(f"Error uploading CSV to bucket: {str(e)}")
        raise
