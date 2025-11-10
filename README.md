# ADK WebSocket Chat App

A minimal FastAPI websocket application using Google ADK bidirectional streaming for real-time chat with an agent powered by Google Search.

## Features

- Real-time bidirectional streaming chat
- Google Search integration for grounded responses
- WebSocket-based communication
- Support for both text and audio modes (text mode shown in example)

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set SSL certificate

```bash
export SSL_CERT_FILE=$(python -m certifi)
```

### 4. Configure Vertex AI

This app uses Google Cloud Vertex AI. You need:

1. A [Google Cloud](https://cloud.google.com/) account and project
2. Set up the [gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. Authenticate to Google Cloud:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```
4. [Enable the Vertex AI API](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com)

Edit the `.env` file and replace `<YOUR_PROJECT_ID>` with your actual Google Cloud project ID:

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

## Running the App

### Start the server

```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

### Test the WebSocket connection

In a new terminal (with the same virtual environment activated):

```bash
python test_client.py
```

This will connect to the websocket server and allow you to chat with the agent.

## Example Usage

```
Connecting to ws://localhost:8000/ws/test_user_123?is_audio=false...
Connected! Type your messages (or 'quit' to exit):

You: What time is it now?

[Agent streams response in real-time...]

[Turn complete]

You: What's the weather in San Francisco?

[Agent searches and responds...]
```

## Project Structure

```
adk-scratchpad/
├── google_search_agent/
│   ├── __init__.py
│   └── agent.py           # Agent definition with google_search tool
├── main.py                # FastAPI websocket server
├── test_client.py         # Simple test client
├── .env                   # Environment configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## How It Works

1. **Agent Definition** (`google_search_agent/agent.py`): Defines an agent with the `google_search` built-in tool
2. **WebSocket Server** (`main.py`): FastAPI app that handles bidirectional streaming between clients and the ADK agent
3. **Client Connection**: Clients connect via WebSocket and send/receive JSON messages with text or audio data

## API Endpoints

- `GET /` - Health check endpoint
- `WebSocket /ws/{user_id}?is_audio=false` - WebSocket endpoint for chat

### WebSocket Message Format

**Client to Server:**
```json
{
  "mime_type": "text/plain",
  "data": "Your message here"
}
```

**Server to Client:**
```json
{
  "mime_type": "text/plain",
  "data": "Agent response chunk"
}
```

Or for turn completion:
```json
{
  "turn_complete": true,
  "interrupted": false
}
```

## Customization

- To use a different model, edit `model` in `google_search_agent/agent.py`
- To add more tools, import them and add to the `tools` list in the agent definition
- To enable audio mode, set `is_audio=true` in the WebSocket URL

## Troubleshooting

- If `gemini-2.0-flash-exp` doesn't work, try `gemini-2.0-flash-live-001` in `agent.py`
- Make sure your Google Cloud project ID is correctly set in `.env`
- Verify you're authenticated: run `gcloud auth application-default login`
- Ensure the Vertex AI API is enabled in your Google Cloud project
- Check that you have the latest version of `google-adk` installed
- Verify your project has billing enabled
