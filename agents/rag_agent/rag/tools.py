# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tool definitions for the RAG multi-agent workflow."""

from google.adk.tools.tool_context import ToolContext


def skip_search(tool_context: ToolContext):
    """Call when RAG answer is sufficient - skips Google Search.

    This tool signals that the RAG-retrieved answer is complete and accurate,
    so there's no need to fall back to Google Search for enrichment.
    """
    print(f"  [Tool Call] skip_search triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    return {"status": "sufficient", "message": "RAG answer complete. Skipping search."}
