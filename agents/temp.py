from flask import Blueprint, request, jsonify
import logging
from .multi_agent import MultiAgent
from .utils.output_modifiers import CustomJSONEncoder
from firestore.utils import get_agent_config, create_run
from middleware.auth import jwt_required
from .utils.agent_utils import create_new_agent
import json

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

agents_bp = Blueprint('agents', __name__)

@agents_bp.route('/run_agent', methods=['POST'])
@jwt_required
def run_agent_with_config():
    try:
        # Log the incoming request data
        logger.debug(f"Received request headers: {dict(request.headers)}")
        raw_data = request.get_data(as_text=True)
        logger.debug(f"Received request data: {raw_data}")

        # Validate content type
        if not request.headers.get('Content-Type', '').startswith('application/json'):
            return jsonify({
                "error": "Invalid Content-Type",
                "message": "Content-Type must be application/json"
            }), 400

        # Pre-validate JSON format
        try:
            # First try to parse the raw JSON to catch syntax errors
            data = json.loads(raw_data)
            logger.debug(f"Successfully parsed JSON data: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError as e:
            # Provide more helpful error messages for common JSON errors
            error_msg = str(e)
            if "Expecting property name enclosed in double quotes" in error_msg:
                hint = "Make sure all property names are enclosed in double quotes and there are no trailing commas"
            elif "Expecting value" in error_msg:
                hint = "Check for missing values or trailing commas in arrays or objects"
            else:
                hint = "Check JSON syntax for valid formatting"
            
            return jsonify({
                "error": "Invalid JSON format",
                "details": error_msg,
                "hint": hint,
                "location": f"line {e.lineno}, column {e.colno}",
                "received_data": raw_data[:1000]  # First 1000 chars for debugging
            }), 400

        # Continue with the rest of the validation
        user_id = request.user_id
        agent_config = data.get("agent_config")
        user_input = data.get("user_input")

        # Validate required fields
        missing_fields = []
        if not agent_config:
            missing_fields.append("agent_config")
        if not user_input:
            missing_fields.append("user_input")

        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }), 400

        # Validate agent_config structure
        if not isinstance(agent_config, dict):
            return jsonify({
                "error": "Invalid agent_config format",
                "message": "agent_config must be a JSON object"
            }), 400

        # Create and save the agent first
        agent_response, status_code = create_new_agent(user_id, agent_config)
        if status_code != 201:
            print("agent_response"+str(agent_response))
            return agent_response, status_code  # Return the response directly

        agent_id = agent_response.get_json().get('agent_id')
        if not agent_id:
            return jsonify({"error": "Failed to create agent"}), 500
        
        agent_config['agent_id'] = agent_id

        # Run the agent with the config
        multi_agent = MultiAgent(agent_config)
        try:
            result = multi_agent.run(user_input)
            if not result:
                logger.error(f"Empty result from MultiAgent for user_id: {user_id}")
                return jsonify({"error": "Agent produced no result"}), 500
        except Exception as e:
            logger.error(f"MultiAgent run failed: {str(e)}")
            return jsonify({"error": "Failed to execute agent", "details": str(e)}), 500

        # Enhanced JSON serialization
        try:
            result = json.loads(json.dumps(result, cls=CustomJSONEncoder))
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"JSON serialization error: {str(e)}")
            return jsonify({"error": "Failed to serialize result", "details": str(e)}), 500

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
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@agents_bp.route('/run_agent_by_id', methods=['POST'])
@jwt_required
def run_agent_by_id():
    try:
        # Validate JSON format first
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        try:
            data = request.get_json()
        except Exception as e:
            return jsonify({"error": "Invalid JSON format", "details": str(e)}), 400

        user_id = request.user_id
        agent_id = data.get("agent_id")
        user_input = data.get("user_input")
        
        if not user_id or not agent_id or not user_input:
            return jsonify({"error": "user_id, agent_id, and user_input are required"}), 400

        # Get existing agent config
        agent_response, status_code = get_agent_config(user_id, agent_id)
        
        if status_code != 200:
            return jsonify(agent_response), status_code

        agent_data = agent_response.get_json()

        if not isinstance(agent_data, dict):
            logger.error(f"Invalid agent_data type: {type(agent_data)}")
            return jsonify({"error": "Invalid agent configuration"}), 500

        # Run the agent with the config
        multi_agent = MultiAgent(agent_data)
        try:
            result = multi_agent.run(user_input)
            if not result:
                logger.error(f"Empty result from MultiAgent for agent_id: {agent_id}")
                return jsonify({"error": "Agent produced no result"}), 500
        except Exception as e:
            logger.error(f"MultiAgent run failed: {str(e)}")
            return jsonify({"error": "Failed to execute agent", "details": str(e)}), 500

        # Enhanced JSON serialization
        try:
            result = json.loads(json.dumps(result, cls=CustomJSONEncoder))
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"JSON serialization error: {str(e)}")
            return jsonify({"error": "Failed to serialize result", "details": str(e)}), 500


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
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

