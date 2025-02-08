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

# Add this constant
# JWT_SECRET_KEY = 'your-secret-key'  # Replace with a secure secret key in production

# firebaseConfig = {
#   "apiKey": "AIzaSyBJe8Jy7CTqekypGTz0-NJUQ2T2LyPXCt8",
#   "authDomain": "project-vestra.firebaseapp.com",
#   "databaseURL": "https://project-vestra-default-rtdb.firebaseio.com",
#   "projectId": "project-vestra",
#   "storageBucket": "project-vestra.appspot.com",
#   "messagingSenderId": "659580688135",
#   "appId": "1:659580688135:web:fdfde531145b7287a2d7a2"
# }