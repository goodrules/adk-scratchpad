"""
Sea Captain Agent Evaluation Demo

Defines a sea-captain-persona Google Search agent, runs it against an
evaluation dataset using Vertex AI's EvalTask, and prints results to
the terminal.

Usage:
    uv run python demos/eval_sea_captain.py
    uv run python demos/eval_sea_captain.py --experiment-name my_experiment
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

import pandas as pd
import vertexai
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
from vertexai.preview.evaluation import EvalTask

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)

# --- Sea Captain Agent ---

captain_agent = Agent(
    name="captain_search_agent",
    model="gemini-2.5-flash",
    description="A sea captain who answers questions using Google Search.",
    instruction=(
        "You are Captain Barnacle, a grizzled sea captain. "
        "Answer questions using the Google Search tool. "
        "Deliver all answers in the voice of a weathered sailor — "
        "use nautical metaphors and sea jargon."
    ),
    tools=[google_search],
)

APP_NAME = "captain_eval"
USER_ID = "eval_user"


# --- Agent Runnable ---

async def agent_runnable_async(prompt: str) -> dict:
    """Run the captain agent and return response + predicted trajectory."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=captain_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )

    response_text = ""
    predicted_trajectory = []

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=types.Content(
            parts=[types.Part(text=prompt)]
        ),
    ):
        # Collect tool calls for trajectory
        for fc in event.get_function_calls():
            predicted_trajectory.append({
                "tool_name": fc.name,
                "tool_input": dict(fc.args) if fc.args else {},
            })
        # Collect final response text
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    return {
        "response": response_text,
        "predicted_trajectory": predicted_trajectory,
    }


def agent_runnable(prompt: str) -> dict:
    """Sync wrapper for the async agent runnable."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(agent_runnable_async(prompt))
    finally:
        loop.close()


# --- Evaluation Dataset ---

def build_eval_dataset() -> pd.DataFrame:
    """Build a small eval dataset with prompts and reference trajectories."""
    data = [
        {
            "prompt": "What is the current weather in the Caribbean?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "google_search", "tool_input": {}}]
            ),
        },
        {
            "prompt": "Who won the America's Cup sailing race most recently?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "google_search", "tool_input": {}}]
            ),
        },
        {
            "prompt": "What are the major shipping routes through the Panama Canal?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "google_search", "tool_input": {}}]
            ),
        },
        {
            "prompt": "What is the tallest lighthouse in the world?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "google_search", "tool_input": {}}]
            ),
        },
        {
            "prompt": "What sea creatures have been discovered in the Mariana Trench?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "google_search", "tool_input": {}}]
            ),
        },
    ]
    return pd.DataFrame(data)


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate the Sea Captain search agent"
    )
    parser.add_argument(
        "--experiment-name",
        default="captain-eval",
        help="Vertex AI experiment name (default: captain-eval)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Sea Captain Agent Evaluation")
    print("=" * 60)
    print(f"  Project:    {GOOGLE_CLOUD_PROJECT}")
    print(f"  Location:   {GOOGLE_CLOUD_LOCATION}")
    print(f"  Experiment: {args.experiment_name}")
    print("=" * 60)

    eval_dataset = build_eval_dataset()
    print(f"\nEval dataset: {len(eval_dataset)} prompts\n")

    trajectory_metrics = [
        "trajectory_exact_match",
        "trajectory_in_order_match",
        "trajectory_any_order_match",
        "trajectory_precision",
        "trajectory_recall",
    ]
    response_metrics = ["coherence", "safety"]

    eval_task = EvalTask(
        dataset=eval_dataset,
        metrics=trajectory_metrics + response_metrics,
        experiment=args.experiment_name,
    )

    print("Running evaluation...\n")
    result = eval_task.evaluate(runnable=agent_runnable)

    # Print summary metrics
    print("\n" + "=" * 60)
    print("  SUMMARY METRICS")
    print("=" * 60)
    summary = result.summary_metrics
    for metric_name, value in sorted(summary.items()):
        print(f"  {metric_name:<45} {value}")

    # Print per-row results
    print("\n" + "=" * 60)
    print("  PER-ROW RESULTS")
    print("=" * 60)
    metrics_df = result.metrics_table
    for idx, row in metrics_df.iterrows():
        print(f"\n--- Prompt {idx + 1}: {row.get('prompt', 'N/A')[:60]} ---")
        if "response" in row:
            resp_preview = str(row["response"])[:120]
            print(f"  Response: {resp_preview}...")
        for col in metrics_df.columns:
            if col not in ("prompt", "response", "reference_trajectory",
                           "predicted_trajectory"):
                print(f"  {col}: {row[col]}")

    print("\n" + "=" * 60)
    print("  Evaluation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
