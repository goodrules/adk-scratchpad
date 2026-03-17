import os

from google.adk.agents.llm_agent import Agent
from google.adk.tools import VertexAiSearchTool

model_id = os.environ.get("MODEL_ID", "gemini-2.5-flash")
vais_data_store = os.environ.get("VAIS_DATA_STORE")

root_agent = Agent(
    model=model_id,
    name='root_agent',
    description='A helpful assistant that searches documents for grounded answers.',
    instruction='Your response must be based ONLY on the information returned from the Vertex AI Search tool. Do not provide any additional information or knowledge from outside the search results. If no search results are returned, or if the search results are not relevant to the query, clearly state that the information is not available. Always cite your sources from the search results when answering.',
    tools=[VertexAiSearchTool(data_store_id=vais_data_store)],
)
