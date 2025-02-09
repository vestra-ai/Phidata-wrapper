from flask import Blueprint, request, jsonify
from .multi_agent import MultiAgent
from .utils.output_modifiers import CustomJSONEncoder
from firestore.utils import get_agent_config, create_run
from middleware.auth import jwt_required
from .utils.agent_utils import create_new_agent
import json

agents_bp = Blueprint('agents', __name__)

@agents_bp.route('/run_agent', methods=['POST'])
@jwt_required
def run_agent_with_config():
    try:
        user_id = request.user_id
        agent_config = request.json.get("agent_config")
        user_input = request.json.get("user_input")

        # Validate required fields
        if not all([user_id, agent_config, user_input]):
            return jsonify({
                "error": "Missing required fields",
                "required": ["user_id", "agent_config", "user_input"]
            }), 400

        # Create and save the agent first
        agent_response, status_code = create_new_agent(user_id, agent_config)
        if status_code != 201:
            return agent_response, status_code  # Return the response directly

        agent_id = agent_response.get_json().get('agent_id')
        if not agent_id:
            return jsonify({"error": "Failed to create agent"}), 500
        
        agent_config['agent_id'] = agent_id

        # Run the agent with the config
        multi_agent = MultiAgent(agent_config)
        result = multi_agent.run(user_input)
        result = json.loads(json.dumps(result, cls=CustomJSONEncoder))

        # Extract output content consistently
        output_content = (
            result.get("output", {}).get("content")
            if isinstance(result.get("output"), dict)
            else str(result)
        )

        # Store the run information
        run_data = {
            "user_id": user_id,
            "user_input": user_input,
            "output": output_content,
        }
        run_id = create_run(agent_id, run_data)

        response_data = {
            "agent_id": agent_id,
            "run_id": run_id,
            "result": result
        }

        return jsonify(response_data), 200
    except ValueError as e:
        return jsonify({"error": "Invalid input format", "details": str(e)}), 422
    except TypeError as e:
        return jsonify({"error": "Serialization error", "details": str(e)}), 400
    except Exception as e:
        # Log the full error
        return jsonify({"error": "Internal server error"+ str(e)}), 500

@agents_bp.route('/run_agent_by_id', methods=['POST'])
@jwt_required
def run_agent_by_id():
    try:
        user_id = request.user_id
        agent_id = request.json.get("agent_id")
        user_input = request.json.get("user_input")
        
        if not user_id or not agent_id or not user_input:
            return jsonify({"error": "user_id, agent_id, and user_input are required"}), 400

        # Get existing agent config
        agent_response, status_code = get_agent_config(user_id, agent_id)
        
        if status_code != 200:
            return jsonify(agent_response), status_code

        agent_data = agent_response.get_json()
        agent_data['agent_id'] = agent_id
        # Run the agent with the config
        multi_agent = MultiAgent(agent_data)
        result = multi_agent.run(user_input)
        result=json.loads(json.dumps(result, cls=CustomJSONEncoder))

        output_content = (
            result.get("output", {}).get("content")
            if isinstance(result.get("output"), dict)
            else str(result)
        )

        # Store the run information
        run_data = {
            "user_id": user_id,
            "user_input": user_input,
            "output": output_content
        }
        run_id = create_run(agent_id, run_data)

        response_data = {
            "run_id": run_id,
            "result": result
        }

        return jsonify(response_data), 200
    except TypeError as e:
        return jsonify({"error": f"Serialization error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

