from agents import Agent
from tools import search_web, fetch_html, extract_contacts, save_csv

orchestrator_agent = Agent(
    name="Lead Orchestrator",
    instructions="""
You generate leads from the internet.
Steps:

1. Use search_web to get URLs.
2. For each URL:
      - use fetch_html
      - use extract_contacts
3. When done, call save_csv
""",
    tools=[search_web, fetch_html, extract_contacts, save_csv]
)
