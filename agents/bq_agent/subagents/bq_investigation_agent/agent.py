from google.adk.agents.llm_agent import LlmAgent
from ...tools.bq_tools import bigquery_toolset
from .prompts import BQ_INVESTIGATION_AGENT_INSTRUCTION

bq_investigation_agent = LlmAgent(
    model='gemini-3-flash-preview',
    name='bq_investigation_agent',
    description='A specialized BigQuery agent that extracts data from bigquery-public-data.hacker_news to answer questions.',
    instruction=BQ_INVESTIGATION_AGENT_INSTRUCTION,
    tools=[bigquery_toolset]
)
