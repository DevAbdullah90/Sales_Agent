import asyncio
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
from connection import config

from agent.orchestator_Agent import orchestrator_agent
# from agent.search_agent import search_agent
# from agent.validator_agent import validator_agent
# from agent.csv_agent import csv_agent


async def run_agent_stream(agent, input_data, agent_name="Agent"):
    """
    Run an agent in streamed mode, print live output, and return the final output.
    """
    print(f"🔍 {agent_name} running...")
    stream = Runner.run_streamed(agent, input_data, run_config=config)

    # Stream and print output in real-time
    async for event in stream.stream_events():
        if event.type == 'raw_response_event' and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

    final_output = stream.final_output
    print(f"\n{agent_name} done.\n")
    return final_output


async def main():
    niche = "clinics in sydney"

    # Step 1 — Orchestrator decides the workflow
    triage_output = await run_agent_stream(orchestrator_agent, niche, "Orchestrator")

    # Step 2 — Search Agent fetches business URLs
    # search_output = await run_agent_stream(search_agent, triage_output, "Search Agent")

    # Step 3 — Scraper Agent extracts emails/phones from URLs
    # scraped_output = await run_agent_stream(scraper_agent, search_output, "Scraper Agent")

    # Step 4 — Validator cleans the scraped data
    # validated_output = await run_agent_stream(validator_agent, scraped_output, "Validator Agent")

    # Step 5 — CSV Agent saves the cleaned leads
    # csv_file_output = await run_agent_stream(csv_agent, validated_output, "CSV Agent")

    # print("💾 CSV saved at:", csv_file_output)
    print(f"Final Output: {triage_output}")

if __name__ == "__main__":
    asyncio.run(main())
