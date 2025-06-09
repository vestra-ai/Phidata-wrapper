import os

import firebase_admin
from firebase_admin import credentials
# from firebase_admin import apps

def initialize_firebase():
    """Initialize Firebase with a named instance if it doesn't already exist"""
    try:
        if not firebase_admin.get_app('vestra-app'):
            # Initialize Firebase Admin SDK with your service account credentials
            cred = credentials.Certificate('./serviceAccountKey.json')
            return firebase_admin.initialize_app(cred, name='vestra-app')
        else:
            # If already initialized, get the named app instance
            return firebase_admin.get_app('vestra-app')
    except ValueError:
        # If the named app doesn't exist but other apps do
        cred = credentials.Certificate('./serviceAccountKey.json')
        return firebase_admin.initialize_app(cred, name='vestra-app')

from google.cloud import storage
from google.oauth2 import service_account

# Initialize Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="serviceAccountKey.json"
gcp_credentials = service_account.Credentials.from_service_account_file(
    os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
)

storage_client = storage.Client(credentials=gcp_credentials)