from flask import Blueprint, request, jsonify
from .utils import get_user, create_agent, update_agent_config, delete_agent_config

firestore_bp = Blueprint('firestore', __name__)

@firestore_bp.route('/get_user', methods=['GET'])
def get_user_by_id():
    try:
        user_id = request.args.get('id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        return get_user(user_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@firestore_bp.route('/add_agent', methods=['POST'])
def add_agent():
    try:
        user_id = request.json.get('user_id')
        agent_data = request.json.get('agent_data')
        if not user_id or not agent_data:
            return jsonify({"error": "User ID and agent data are required"}), 400
        return create_agent(user_id, agent_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@firestore_bp.route('/update_agent', methods=['PUT'])
def update_agent():
    try:
        user_id = request.json.get('user_id')
        agent_id = request.json.get('agent_id')
        agent_data = request.json.get('agent_data')
        if not user_id or not agent_id or not agent_data:
            return jsonify({"error": "User ID, agent ID, and agent data are required"}), 400
        return update_agent_config(user_id, agent_id, agent_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@firestore_bp.route('/delete_agent', methods=['DELETE'])
def delete_agent():
    try:
        user_id = request.json.get('user_id')
        agent_id = request.json.get('agent_id')
        if not user_id or not agent_id:
            return jsonify({"error": "User ID and agent ID are required"}), 400
        return delete_agent_config(user_id, agent_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
