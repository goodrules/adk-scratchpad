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

"""RAG Retrieval subagent that queries the Vertex AI RAG corpus."""

import os

from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

from rag.prompts import return_instructions_rag_retrieval

rag_corpus_id = os.environ.get("RAG_CORPUS")
if not rag_corpus_id:
    raise ValueError(
        "RAG_CORPUS environment variable is not set. "
        "Please set it to your Vertex AI RAG Corpus resource name."
    )

ask_vertex_retrieval = VertexAiRagRetrieval(
    name='retrieve_rag_documentation',
    description=(
        'Use this tool to retrieve documentation and reference materials '
        'for the question from the RAG corpus.'
    ),
    rag_resources=[
        rag.RagResource(
            rag_corpus=rag_corpus_id
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)


rag_retrieval_agent = Agent(
    name='rag_retrieval_agent',
    model=os.environ.get("MODEL_ID", "gemini-2.5-flash"),
    instruction=return_instructions_rag_retrieval(),
    tools=[ask_vertex_retrieval],
    output_key='rag_answer',
)
