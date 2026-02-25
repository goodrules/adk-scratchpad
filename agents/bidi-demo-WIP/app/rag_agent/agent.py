"""RAG Agent definition for ADK Bidi-streaming demo."""

import os

import vertexai
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.google_search_tool import google_search
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION"),
)

RAG_CORPUS = os.environ.get("RAG_CORPUS")
if not RAG_CORPUS:
    raise ValueError(
        "RAG_CORPUS environment variable is not set. "
        "Please set it to your Vertex AI RAG Corpus resource name."
    )

rag_retrieval_tool = VertexAiRagRetrieval(
    name="retrieve_rag_documentation",
    description=(
        "Use this tool to retrieve documentation and reference materials "
        "for the question from the RAG corpus."
    ),
    rag_resources=[
        rag.RagResource(
            rag_corpus=RAG_CORPUS
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)

# Step 1: RAG retrieval + answer synthesis via text API (no Live API,
# no truncation bug). Uses runner.run_async() via AgentTool.
rag_retrieval_agent = Agent(
    name="rag_retrieval_agent",
    model=os.getenv("RAG_AGENT_MODEL", "gemini-2.5-flash"),
    tools=[rag_retrieval_tool],
    description="Retrieves and answers questions using the RAG corpus.",
    instruction=(
        "You are a helpful assistant that answers questions using "
        "information retrieved from the RAG corpus.\n"
        "When listing steps or items, start giving them immediately "
        "without preamble like 'Here are the steps:'. "
        "Keep responses concise and complete."
    ),
)

# Step 2: YouTube video search via Google Search
youtube_search_agent = Agent(
    name="youtube_search_agent",
    model=os.getenv("RAG_AGENT_MODEL", "gemini-2.5-flash"),
    tools=[google_search],
    description="Searches for relevant YouTube video tutorials.",
    instruction=(
        "You search for YouTube videos related to aircraft maintenance tasks.\n"
        "Based on the previous answer in the conversation, search for "
        "relevant YouTube video tutorials.\n"
        "Always include 'youtube' and 'aircraft maintenance' in your search "
        "queries along with the specific topic.\n"
        "Return a concise list of 2-3 relevant video titles with their URLs.\n"
        "If no relevant videos are found, say so briefly."
    ),
)

# Sequential pipeline: RAG first, then YouTube search. Wrapped in AgentTool so
# the root agent invokes it via run_async() (text API) — not run_live() — which
# means neither sub-agent needs a Live API model.
rag_and_video_search = SequentialAgent(
    name="rag_and_video_search",
    description=(
        "Answers technical questions using the RAG corpus, then finds "
        "relevant YouTube video tutorials for the same topic."
    ),
    sub_agents=[rag_retrieval_agent, youtube_search_agent],
)

# Root agent: native audio Live API, delegates to sequential pipeline via
# AgentTool. AgentTool runs the pipeline via run_async() (text API), so the
# sub-agents are not subject to the native audio model truncation bug.
# Default models for Live API with native audio support:
# - Gemini Live API: gemini-2.5-flash-native-audio-preview-12-2025
# - Vertex AI Live API: gemini-live-2.5-flash-native-audio
agent = Agent(
    name="rag_agent",
    model=os.getenv("DEMO_AGENT_MODEL", "gemini-live-2.5-flash-native-audio"),
    tools=[AgentTool(agent=rag_and_video_search)],
    instruction=(
        "You are a friendly voice assistant for aircraft maintenance technicians. "
        "When the user asks a technical or procedural question, "
        "use the rag_and_video_search tool. It will retrieve the answer "
        "from documentation and find relevant YouTube tutorial videos. "
        "Relay the answer and any video suggestions naturally in your own voice. "
        "For casual conversation, answer directly without using any tools."
    ),
)
