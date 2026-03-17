import os

from google.adk.agents.llm_agent import Agent
from google.adk.tools import VertexAiSearchTool

model_id = os.environ.get("MODEL_ID", "gemini-2.5-flash")
vais_data_store = os.environ.get("VAIS_DATA_STORE")

root_agent = Agent(
    model=model_id,
    name='root_agent',
    description='A helpful assistant that searches documents for grounded answers.',
    instruction='Use the Vertex AI Search tool to find relevant information and provide grounded answers based on the search results. Always cite sources from the search results when answering.',
    tools=[VertexAiSearchTool(data_store_id=vais_data_store)],
)
