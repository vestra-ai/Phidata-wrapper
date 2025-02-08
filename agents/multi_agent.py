import json
from typing import Dict, Any, List
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from .tools import get_tool
from dotenv import load_dotenv

load_dotenv()

class MultiAgent:
    def __init__(self, agent_config: Dict[str, Any]):
        self.agent_id = agent_config.get("agent_id")
        self.name = agent_config.get("name")
        self.agents = self.initialize_agents(agent_config.get("agents", []))
        self.team_agent = Agent(
            team=[agent for agent in self.agents],
            instructions=["Ensure logical flow between responses"],
            show_tool_calls=True,
            markdown=True,
        )

    def initialize_agents(self, agent_list: List[Dict[str, Any]]):
        """Initializes agents dynamically from JSON."""
        agents = []
        for agent_data in agent_list:
            tools = [get_tool(tool) for tool in agent_data.get("tools", [])]
            agent = Agent(
                name=agent_data["name"],
                role=agent_data["role"],
                model=OpenAIChat(id="gpt-4o"),
                tools=tools,
                instructions=agent_data.get("instructions", []),
                description=agent_data.get("description", ""),
                show_tool_calls=True,
                markdown=True,
            )
            agents.append(agent)
        return agents

    def run(self, user_input: str) -> Dict[str, Any]:
        """Runs the multi-agent team in sequence."""
        response = self.team_agent.run(user_input)
        return {"agent_id": self.agent_id, "input": user_input, "output": response}

# # 🔹 Example Usage
# if __name__ == "__main__":
#     # Load agent from JSON file
#     with open("agent_config.json", "r") as file:
#         agent_config = json.load(file)

#     multi_agent_team = MultiAgent(agent_config)
#     user_input = "Summarize analyst recommendations and share the latest news for NVDA"
#     response = multi_agent_team.run(user_input)

#     print(json.dumps(response, indent=2))
