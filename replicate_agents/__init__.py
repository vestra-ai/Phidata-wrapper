from dotenv import load_dotenv
import os
import replicate
import requests
from enum import Enum
from flask import Flask, request, jsonify, Blueprint

import uuid
from config import storage_client

# Load environment variables
load_dotenv()



class VideoTypes(Enum):
    MP4 = 'mp4'
    
class VideoMimeTypes(Enum):
    mp4 = 'video/mp4'

def generate_unique_upload_id():
    return str(uuid.uuid4())

def generate_signed_url(blob_name, expiration=3600):
    """Generate a signed URL for a blob that expires after specified seconds."""

    bucket = storage_client.bucket(os.environ.get('BUCKET_NAME'))
    blob = bucket.blob(blob_name)
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="GET",
    )
    return url

def upload_blob_to_bucket(file_obj, destination_blob_name, content_type):
    bucket = storage_client.bucket(os.environ.get('BUCKET_NAME'))
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file_obj, content_type=content_type)
    # Generate a signed URL instead of making the blob public
    signed_url = generate_signed_url(destination_blob_name)
    return signed_url

def save_video_stream_to_storage(outputs, destination_folder, output_type=VideoTypes.MP4.value):
    """
    Upload a video stream directly to Firebase Storage.
    Args:
        outputs (iterable): An iterable that yields file chunks.
        destination_folder (str): The folder to save the output to in Firebase Storage.
        output_type (str): The type of the file. Defaults to 'mp4'.
    Returns:
        dict: Details of the uploaded file including public URL.
    """
    video_details = []
    
    # Handle single URL string case
    if isinstance(outputs, str):
        if not outputs.startswith('http'):
            raise ValueError("URL must start with http")
        outputs = [outputs]
        
    # Handle list of URLs case
    elif isinstance(outputs, list):
        if not all(isinstance(url, str) and url.startswith('http') for url in outputs):
            raise ValueError("All URLs must be strings starting with http")
            
    # Handle FileOutput case from Replicate
    elif hasattr(outputs, '__class__') and outputs.__class__.__name__ == 'FileOutput':
        output_url = str(outputs)
        if not output_url.startswith('http'):
            raise ValueError("FileOutput URL must start with http")
        outputs = [output_url]
    
    # Invalid input case
    else:
        raise ValueError("outputs must be either a URL string or list of URL strings")

    for output in outputs:
        file_name = f"{generate_unique_upload_id()}.{output_type}"
        destination_blob_name = f"output/generated_files/{destination_folder}/{file_name}"
        content_type = VideoMimeTypes[output_type].value

        response = requests.get(output, stream=True)
        if response.status_code == 200:
            response.raw.decode_content = True
            signed_url = upload_blob_to_bucket(response.raw, destination_blob_name, content_type)
            response.close()
        else:
            response.close()
            raise ValueError(f"Failed to download video from {output}")

        video_details.append({
            "signed_url": signed_url,
            "file_name": file_name,
            "content_type": content_type
        })
        print("print video_details")
        print(f"Uploaded video to: {signed_url}")
        print(video_details)
        
    return video_details

def generate_video(prompt, duration, aspect_ratio):

    replicate_key = os.environ.get("REPLICATE_API_KEY")

    # Set your Replicate API Token
    if replicate_key:
        replicate.Client(api_token=replicate_key)
    if not replicate_key:
        raise ValueError("REPLICATE_API_KEY environment variable is not set. Please ensure it exists in your .env file.")
    
    os.environ["REPLICATE_API_TOKEN"] = replicate_key

    try:
        output = replicate.run(
            "google/veo-2",
            input={
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "enhance_prompt": True
            }
        )
        
        video_details = save_video_stream_to_storage(output, 'Google_VEO_LABS')
        
        return {
            'outputs': {
                'generated_videos': [
                    {
                        'signed_url': video['signed_url'],
                        'file_name': video['file_name'],
                        'content_type': video['content_type'],
                        'aspect_ratio': aspect_ratio
                    } for video in video_details
                ]
            }
        }
    
    except Exception as e:
        print(f"Error in generate_video: {str(e)}")
        return {"error": str(e)}

# Create a new Blueprint for the /veo endpoint
veo_bp = Blueprint('veo',  __name__)

@veo_bp.route("/generate-video", methods=["POST"])
def generate_video_endpoint():
    try:
        data = request.json
        prompt = data.get("prompt")
        duration = data.get("duration", 5)
        aspect_ratio = data.get("aspect_ratio", "16:9")

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        result = generate_video(prompt, duration, aspect_ratio)
        
        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 500
            
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add this new route to the Blueprint
@veo_bp.route("/test-storage", methods=["POST"])
def test_storage_endpoint():
    try:
        from .test_storage import test_video_upload
        success, result = test_video_upload()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Storage test completed successfully",
                "details": result
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Storage test failed",
                "error": result
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
