from google.cloud import firestore
from flask import jsonify

def get_user(user_id):
    from app import db
    user = db.collection('users').document(user_id).get()
    if user.exists:
        return jsonify(user.to_dict()), 200
    return jsonify({"error": "User not found"}), 404

def create_agent(user_id, agent_data):
    from app import db
    agent_data['user_id'] = user_id
    agent_ref = db.collection('custom_agents').document()
    agent_ref.set(agent_data)
    return jsonify({"message": "Agent created successfully", "agent_id": agent_ref.id}), 201

def get_agent_config(user_id, agent_id):
    from app import db
    agent_ref = db.collection('custom_agents').document(agent_id)
    agent = agent_ref.get()
    if agent.exists and agent.to_dict().get('user_id') == user_id:
        return jsonify(agent.to_dict()), 200
    return jsonify({"error": "Agent not found or not authorized to used this agent"}), 404

def update_agent_config(user_id, agent_id, agent_data):
    from app import db
    agent_ref = db.collection('custom_agents').document(agent_id)
    agent = agent_ref.get()
    if agent.exists and agent.to_dict().get('user_id') == user_id:
        agent_ref.update(agent_data)
        return jsonify({"message": "Agent updated successfully"}), 200
    return jsonify({"error": "Agent not found or user_id mismatch"}), 404

def delete_agent_config(user_id, agent_id):
    from app import db
    agent_ref = db.collection('custom_agents').document(agent_id)
    agent = agent_ref.get()
    if agent.exists and agent.to_dict().get('user_id') == user_id:
        agent_ref.delete()
        return jsonify({"message": "Agent deleted successfully"}), 200
    return jsonify({"error": "Agent not found or user_id mismatch"}), 404

def get_all_agents(user_id):
    from app import db
    agents = db.collection('custom_agents').where('user_id', '==', user_id).stream()
    agents_list = [agent.to_dict() for agent in agents]
    return jsonify(agents_list), 200
