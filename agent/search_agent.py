from agents import Agent
from tools import search_web

search_agent = Agent(
    name="Search Agent",
    instructions="Use search_web to find websites for the given business niche.",
    tools=[search_web]
)
