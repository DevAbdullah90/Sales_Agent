from agents import Agent
from tools import extract_and_save_leads
orchestrator_agent = Agent(
    name="Lead Orchestrator",
    instructions="""
You generate leads from the internet.
Steps:

1. Use extract_and_save_leads with parameters location(the location of the place), keyword(the business name) to extract leads and save data as csv.
""",
    tools=[extract_and_save_leads]
)
