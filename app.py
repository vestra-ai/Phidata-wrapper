from flask import Flask, render_template, request, jsonify
from config import initialize_firebase
from firestore.routes import firestore_bp
from agents import agents_bp
from firebase_admin import firestore

# Initialize Firebase and store the app instance
firebase_app = initialize_firebase()
app = Flask(__name__)

# Get Firestore client from the specific app instance
db = firestore.client(firebase_app)

app.register_blueprint(firestore_bp, url_prefix='/firestore')
app.register_blueprint(agents_bp, url_prefix='/agents')
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

