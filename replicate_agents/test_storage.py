from dotenv import load_dotenv
import os
from firebase_admin import credentials, initialize_app, storage
from . import save_video_stream_to_storage

def test_video_upload():
    """
    Test function to verify Firebase storage upload functionality
    using a sample video from a public URL
    """
    # Sample video URL (using a small sample video)
    sample_video_url = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
    
    try:
        # Test the upload function
        video_details = save_video_stream_to_storage(
            outputs=sample_video_url,
            destination_folder='test_uploads'
        )
        
        print("Upload Test Results:")
        print("-" * 50)
        for video in video_details:
            print(f"File Name: {video['file_name']}")
            print(f"Public URL: {video['signed_url']}")
            print(f"Content Type: {video['content_type']}")
            print("-" * 50)
            
        return True, video_details
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        return False, str(e)

# if __name__ == "__main__":
#     # Load environment variables
#     load_dotenv()
    
#     # Initialize Firebase if not already initialized
#     if not len(storage._apps):
#         cred = credentials.Certificate(os.environ.get('FIREBASE_CREDENTIALS_PATH'))
#         initialize_app(cred, {
#             'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET')
#         })
    
#     # Run the test
#     success, result = test_video_upload()
#     if success:
#         print("Test completed successfully!")
#     else:
#         print(f"Test failed: {result}")
