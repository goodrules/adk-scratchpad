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
  - `workflow_agent_seq/`: Example of a sequential workflow.
  - `mcp_test_agent/`: Example using the Model Context Protocol (filesystem access).

### 2. `agents/`
Contains standalone, functional agents demonstrating specific capabilities.
- **`google_search_agent/`**: A simple agent equipped with the `GoogleSearchTool` for grounded responses.
- **`rag_agent/`**: A sophisticated RAG (Retrieval-Augmented Generation) implementation using Vertex AI.
- **`short_story_agent/`**: A creative writing agent demonstrating complex orchestration (planning, writing, editing).

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
   Copy the `.env.example` (if available) or create a `.env` file in the root directory:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export GOOGLE_CLOUD_LOCATION="us-central1"
   export GOOGLE_GENAI_USE_VERTEXAI=true
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

---

## 🛠 Troubleshooting

- **Authentication Errors:** Ensure you have run `gcloud auth application-default login` and set `GOOGLE_CLOUD_PROJECT`.
- **Model Not Found:** Verify `GOOGLE_CLOUD_LOCATION` is set (e.g., `us-central1` or `global`) and the model is available in that region.
- **"No agent found":** Ensure your agent's entry point variable is named `root_agent` in `agent.py`.

---

## 📚 Resources
- [ADK Documentation](https://google.github.io/adk-docs/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)