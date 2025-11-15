from agents import Agent
from tools import search_web, save_csv, scrape_multiple_urls

orchestrator_agent = Agent(
    name="Lead Orchestrator",
    instructions="""
You generate leads from the internet.
Steps:

1. Use search_web to get URLs.
2. with the list of URLs:
      - use scrape_multiple_urls
3. When done, call save_csv
""",
    tools=[search_web, scrape_multiple_urls, save_csv]
)
