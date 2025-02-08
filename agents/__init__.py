from flask import Blueprint, request, jsonify
from .multi_agent import MultiAgent
from .utils.output_modifiers import CustomJSONEncoder
from firestore.utils import get_agent_config, create_agent
from middleware.auth import jwt_required
import json

agents_bp = Blueprint('agents', __name__)

def create_new_agent(user_id, agent_config):
    """
    Create a new agent with the given configuration
    """
    try:
        if not user_id or not agent_config:
            return {"error": "user_id and agent_config are required"}, 400

        response, status_code = create_agent(user_id, agent_config)
        return response, status_code
    except Exception as e:
        return {"error": str(e)}, 400

@agents_bp.route('/run_agent', methods=['POST'])
# @jwt_required
def run_agent_with_config():
    try:
        print("runnning agent")
        user_id = request.json.get("user_id")
        agent_config = request.json.get("agent_config")
        user_input = request.json.get("user_input")

        if not user_id or not agent_config or not user_input:
            return jsonify({"error": "user_id, agent_config and user_input are required"}), 400

        # Create and save the agent first
        agent_response, status_code = create_new_agent(user_id, agent_config)
        if status_code != 201:
            return jsonify(agent_response), status_code

        # Extract agent_id from the response JSON
        agent_id = agent_response.get_json().get('agent_id')

        # Run the agent with the config
        multi_agent = MultiAgent(agent_config)
        result = multi_agent.run(user_input)

        response_data = {
            "message": "Agent created and executed successfully",
            "agent_id": agent_id,
            "result": json.loads(json.dumps(result, cls=CustomJSONEncoder))
        }

        return jsonify(response_data), 200
    except TypeError as e:
        return jsonify({"error": f"Serialization error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@agents_bp.route('/run_agent_by_id', methods=['POST'])
# @jwt_required
def run_agent_by_id():
    try:
        user_id = request.json.get("user_id")
        agent_id = request.json.get("agent_id")
        user_input = request.json.get("user_input")
        
        if not user_id or not agent_id or not user_input:
            return jsonify({"error": "user_id, agent_id, and user_input are required"}), 400

        # Get existing agent config
        agent_response, status_code = get_agent_config(user_id, agent_id)
        
        if status_code != 200:
            return jsonify(agent_response), status_code

        agent_data = agent_response.get_json()

        # Run the agent with the config
        multi_agent = MultiAgent(agent_data)
        result = multi_agent.run(user_input)

        response_data = {
            "message": "Agent executed successfully",
            "result": json.loads(json.dumps(result, cls=CustomJSONEncoder))
        }

        return jsonify(response_data), 200
    except TypeError as e:
        return jsonify({"error": f"Serialization error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400
