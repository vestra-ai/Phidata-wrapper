from firestore.utils import create_agent

def validate_agent_config(agent_config):
    """Validate the agent configuration structure"""
    # Validate base config has required name
    if not isinstance(agent_config, dict):
        return False, "Agent config must be a dictionary"
        
    if 'name' not in agent_config:
        return False, "Agent config must have a name"
        
    if not isinstance(agent_config['name'], str) or len(agent_config['name'].strip()) < 3:
        return False, "Agent name must be a string with at least 3 characters"

    # Validate agents array
    if 'agents' not in agent_config:
        return False, "Agent config must have an 'agents' array"
        
    if not isinstance(agent_config['agents'], list):
        return False, "Agents must be an array"
        
    if len(agent_config['agents']) < 1:
        return False, "At least one agent is required"

    # Validate each agent in the array
    required_agent_fields = {
        'name': str,
        'role': str,
        'model': str,
        'instructions': list
    }

    for idx, agent in enumerate(agent_config['agents']):
        # Check if agent is a dictionary
        if not isinstance(agent, dict):
            return False, f"Agent at index {idx} must be a dictionary"

        # Check required fields and their types
        for field, expected_type in required_agent_fields.items():
            if field not in agent:
                return False, f"Agent '{agent.get('name', f'at index {idx}')}' missing required field: {field}"
            
            if not isinstance(agent[field], expected_type):
                return False, f"Agent '{agent.get('name', f'at index {idx}')}' field '{field}' must be of type {expected_type.__name__}"

        # Validate name length
        if len(agent['name'].strip()) < 2:
            return False, f"Agent name '{agent['name']}' must be at least 2 characters"

        # Validate instructions
        if len(agent['instructions']) < 1:
            return False, f"Agent '{agent['name']}' must have at least one instruction"

    return True, None

def create_new_agent(user_id, agent_config):
    """
    Create a new agent with the given configuration
    """
    try:
        # Basic input validation
        if not user_id or not agent_config:
            return {"error": "user_id and agent_config are required"}, 400
            
        if not isinstance(agent_config, dict):
            return {"error": "agent_config must be a dictionary"}, 400

        # Validate agent configuration structure
        is_valid, error_message = validate_agent_config(agent_config)
        if not is_valid:
            return {"error": error_message}, 400

        # If all validations pass, create the agent
        response, status_code = create_agent(user_id, agent_config)
        return response, status_code

    except Exception as e:
        return {"error": str(e)}, 400