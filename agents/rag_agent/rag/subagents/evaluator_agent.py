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

"""Evaluator subagent that decides whether RAG answer is sufficient or needs search."""

import os

from google.adk.agents import Agent

from rag.prompts import return_instructions_evaluator
from rag.tools import skip_search


answer_evaluator_agent = Agent(
    name='answer_evaluator_agent',
    model=os.environ.get("MODEL_ID", "gemini-2.5-flash"),
    instruction=return_instructions_evaluator(),
    tools=[skip_search],
    output_key='evaluation',
)
