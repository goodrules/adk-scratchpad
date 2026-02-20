import asyncio
import os
import sys

# Ensure the scratchpad agents are in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent
from agents.bq_agent.agent import root_agent

async def main():
    print("Testing the BigQuery Hacker News agent...")
    prompt_text = "What is the title of the story with the highest score on Hacker News?"
    print(f"Prompt: {prompt_text}\n")
    
    runner = InMemoryRunner(agent=root_agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="test_user"
    )
    content = UserContent(parts=[Part(text=prompt_text)])
    
    final_response = ""
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        if event.content and event.content.parts and event.content.parts[0].text:
            final_response += event.content.parts[0].text
            
    print("\n=== Agent Output ===")
    print(final_response)
    print("====================")

if __name__ == "__main__":
    asyncio.run(main())
