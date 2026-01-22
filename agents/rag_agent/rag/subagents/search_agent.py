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

"""Search enrichment subagent that uses Google Search when RAG is insufficient."""

from google.adk.agents import Agent
from google.adk.tools import google_search

from rag.prompts import return_instructions_search_enrichment


search_enrichment_agent = Agent(
    name='search_enrichment_agent',
    model='gemini-2.0-flash',
    instruction=return_instructions_search_enrichment(),
    tools=[google_search],
    output_key='final_answer',
)
