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

# @app.route('/add', methods=['POST'])
# def add_data():
#     try:
#         data = request.json
#         # Add data to Firestore
#         doc_ref = db.collection('your_collection').add(data)
#         return jsonify({"message": "Data added successfully"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @app.route('/get', methods=['GET'])
# def get_data():
#     try:
#         # Get data from Firestore
#         docs = db.collection('your_collection').stream()
#         data = [{doc.id: doc.to_dict()} for doc in docs]
#         return jsonify(data), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/get_user', methods=['GET'])
def get_user_by_id(current_user_id):
    try:
        # The user_id is now automatically extracted from the token
        user = db.collection('users').document(current_user_id).get()
        if user.exists:
            return jsonify(user.to_dict()), 200
        return jsonify({"error": "User not found"}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

