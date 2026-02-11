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

"""Multi-agent RAG workflow with Google Search fallback.

Architecture:
    root_agent (LoopAgent, max_iterations=1)
        |
        +-- rag_retrieval_agent
        |       - Uses VertexAiRagRetrieval tool
        |       - output_key="rag_answer"
        |
        +-- answer_evaluator_agent
        |       - Evaluates answer quality
        |       - If SUFFICIENT: calls skip_search() → escalates → loop exits
        |       - If INSUFFICIENT: passes through to search
        |       - output_key="evaluation"
        |
        +-- search_enrichment_agent
                - Only runs if evaluator doesn't escalate
                - Uses google_search tool
                - output_key="final_answer"
"""

from google.adk.agents import LoopAgent

from rag.subagents import (
    rag_retrieval_agent,
    answer_evaluator_agent,
    search_enrichment_agent,
)


root_agent = LoopAgent(
    name='rag_with_search_fallback',
    sub_agents=[
        rag_retrieval_agent,
        answer_evaluator_agent,
        search_enrichment_agent,
    ],
    max_iterations=1,
)
