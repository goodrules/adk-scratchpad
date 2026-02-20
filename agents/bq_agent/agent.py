from google.adk.agents.llm_agent import LlmAgent
from .prompts import CORE_ANALYSIS_AGENT_INSTRUCTION
from .subagents import bq_investigation_agent

# Setup the Root Agent
root_agent = LlmAgent(
    model='gemini-3-flash-preview',
    name='core_analysis_agent',
    description='The core assistant that analyzes Hacker News data.',
    instruction=CORE_ANALYSIS_AGENT_INSTRUCTION,
    sub_agents=[bq_investigation_agent]
)
