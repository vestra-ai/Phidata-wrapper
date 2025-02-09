from firestore.utils import create_agent
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