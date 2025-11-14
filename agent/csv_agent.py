from agents import Agent
from tools import save_csv

csv_agent = Agent(
    name="CSV Agent",
    instructions="Save the list of leads using save_csv tool.",
    tools=[save_csv]
)
