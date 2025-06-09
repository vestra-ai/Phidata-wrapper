from flask import Flask, jsonify
from config import initialize_firebase
from firebase_admin import firestore

from firestore.routes import firestore_bp
from agents import agents_bp
from enterprise.financial_agent import stock_bp
from replicate_agents import veo_bp
from analytics import analytics_user_bp

# Initialize Firebase and store the app instance
firebase_app = initialize_firebase()
app = Flask(__name__)

# Get Firestore client from the specific app instance
db = firestore.client(firebase_app)

app.register_blueprint(firestore_bp, url_prefix='/firestore')
app.register_blueprint(agents_bp, url_prefix='/agents')
app.register_blueprint(stock_bp, url_prefix='/stock')
app.register_blueprint(veo_bp, url_prefix='/veo')
app.register_blueprint(analytics_user_bp, url_prefix='/analytics/users')

@app.route('/health')
def health():
    return jsonify({"status": "UP"})
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)