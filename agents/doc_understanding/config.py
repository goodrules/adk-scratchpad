import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model ID for document understanding
# The user's existing code used gemini-3-flash-preview.
# gemini-2.5-pro or gemini-2.5-flash are also good options.
MODEL_ID = os.environ.get("MODEL_ID", "gemini-3-flash-preview")

# You can specify other model IDs or configurations here.
# For example:
# EMBEDDING_MODEL_ID = "text-embedding-004"
