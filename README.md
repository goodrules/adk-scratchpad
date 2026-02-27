# ADK Scratchpad & Guides

**A collection of guides and sample agents for the Google Agent Development Kit (ADK).**

**Author:** Mike Goodman (Github: goodrules)

---

## 📂 Repository Structure

This repository is organized into two main sections:

### 1. `adk_guide/`
Contains a step-by-step tutorial and reference implementations for learning ADK.
- **`simple_tutorial.md`**: A comprehensive workshop guide covering:
  - Environment setup & authentication
  - Building a "Hello World" agent
  - Adding tools (Python functions, Google Search, MCP)
  - Orchestrating multi-agent workflows (Sequential, Parallel, Loop)
- **Sample Agents**:
  - `my_first_agent/`: Basic "Hello World" agent.
  - `my_2_agent/`: Basic agent example.
  - `workflow_agent_seq/`: Example of a sequential workflow.
  - `mcp_test_agent/`: Example using the Model Context Protocol (filesystem access).

### 2. `agents/`
Contains standalone, functional agents demonstrating specific capabilities.
- **`google_search_agent/`**: Simple agent with `GoogleSearchTool` for grounded responses.
- **`bq_agent/`**: Analyzes Hacker News data using BigQuery with sub-agents.
- **`rag_agent/`**: RAG implementation using Vertex AI RAG Engine with retrieval, evaluation, and search fallback.
- **`short_story_agent/`**: Creative writing agent with sequential planning, writing, and iterative editing.
- **`short-movie-agents/`**: Multi-agent pipeline for end-to-end video creation using Imagen4 and Veo3.
- **`software-bug-assistant/`**: Bug triage agent using PostgreSQL, GitHub MCP, Google Search, and StackOverflow.
- **`travel-concierge/`**: Multi-agent travel concierge with 6 specialized sub-agents for trip planning and support.
- **`ai-location-strategy/`**: 7-stage pipeline for retail site selection with Maps API, code execution, and report generation.
- **`bidi-demo-WIP/`**: Bidirectional streaming demo with Gemini Live API (work in progress).

> **Note:** Some agents (e.g., `ai-location-strategy`, `short-movie-agents`) have their own `pyproject.toml` and `Makefile` with additional setup. Check each agent's README for details.

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- A Google Cloud Project with **Vertex AI API** enabled.
- [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed.

### 2. Environment Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Authentication & Configuration

1. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth application-default login
   ```

2. **Configure Environment Variables:**
   Copy `agents/.env.example` to `agents/.env` and fill in your project details:
   ```
   GOOGLE_GENAI_USE_VERTEXAI=TRUE
   GOOGLE_CLOUD_PROJECT=<your-project-id>
   GOOGLE_CLOUD_LOCATION=global
   ```

---

## 🏃 Running Agents

You can run any agent using the ADK CLI. Navigate to the directory containing the agent (parent of the agent folder) and run:

```bash
# Example: Running the Google Search Agent
cd agents
adk run google_search_agent
```

Or use the web interface:
```bash
adk web
```

Some complex agents have their own Makefile for running and development:
```bash
cd agents/ai-location-strategy
make install   # Install dependencies with uv
make dev       # Run ADK web UI locally
```

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 🛠 Troubleshooting

- **Authentication Errors:** Ensure you have run `gcloud auth application-default login` and set `GOOGLE_CLOUD_PROJECT`.
- **Model Not Found:** Verify `GOOGLE_CLOUD_LOCATION` is set (e.g., `us-central1` or `global`) and the model is available in that region.
- **"No agent found":** Ensure your agent's entry point variable is named `root_agent` in `agent.py`.

---

## 📚 Resources
- [ADK Documentation](https://google.github.io/adk-docs/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)