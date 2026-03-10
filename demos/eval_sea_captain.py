"""
Cruise Captain Agent Evaluation Demo

Defines a cruise-captain-persona agent with multiple tools (Google Search,
weather, port lookup, unit conversion), runs it against an evaluation dataset
using Vertex AI's EvalTask, and prints results to the terminal.

Usage:
    uv run python demos/eval_sea_captain.py
    uv run python demos/eval_sea_captain.py --experiment-name my_experiment
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import googlemaps
import pandas as pd
import requests
import vertexai
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.google_search_tool import GoogleSearchTool

google_search = GoogleSearchTool(bypass_multi_tools_limit=True)
from google.genai import types
from vertexai.preview.evaluation import EvalTask

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)


# --- Tools ---

def get_weather(latitude: float, longitude: float) -> dict:
    """Get current weather conditions for a given latitude and longitude.

    Args:
        latitude: The latitude coordinate (e.g., 25.76 for Miami).
        longitude: The longitude coordinate (e.g., -80.19 for Miami).

    Returns:
        dict with temperature, humidity, wind_speed, and precipitation.
    """
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        units = data.get("current_units", {})
        return {
            "status": "success",
            "temperature": f"{current.get('temperature_2m')} {units.get('temperature_2m', '')}",
            "humidity": f"{current.get('relative_humidity_2m')} {units.get('relative_humidity_2m', '')}",
            "wind_speed": f"{current.get('wind_speed_10m')} {units.get('wind_speed_10m', '')}",
            "precipitation": f"{current.get('precipitation')} {units.get('precipitation', '')}",
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def lookup_port(query: str) -> dict:
    """Look up information about a cruise port or maritime location.

    Uses the Google Maps Places API to find details about ports,
    harbors, and maritime facilities.

    Args:
        query: Search query for the port (e.g., "cruise port in Miami").

    Returns:
        dict with a list of matching places including name, address,
        lat/lng, and rating.
    """
    try:
        maps_api_key = os.environ.get("MAPS_API_KEY", "")
        if not maps_api_key:
            return {
                "status": "error",
                "error_message": "MAPS_API_KEY environment variable not set.",
                "results": [],
            }

        gmaps = googlemaps.Client(key=maps_api_key)
        result = gmaps.places(query)

        places = []
        for place in result.get("results", []):
            location = place.get("geometry", {}).get("location", {})
            places.append({
                "name": place.get("name", "Unknown"),
                "address": place.get("formatted_address", place.get("vicinity", "N/A")),
                "lat": location.get("lat"),
                "lng": location.get("lng"),
                "rating": place.get("rating", 0),
            })

        return {"status": "success", "results": places, "count": len(places)}
    except Exception as e:
        return {"status": "error", "error_message": str(e), "results": []}


# Conversion factors to a common base unit per category
_CONVERSION_TABLE = {
    # Speed: base unit = knots
    "knots": ("speed", 1.0),
    "mph": ("speed", 1.15078),
    "kph": ("speed", 1.852),
    # Distance: base unit = nautical_miles
    "nautical_miles": ("distance", 1.0),
    "miles": ("distance", 1.15078),
    "km": ("distance", 1.852),
    # Depth: base unit = fathoms
    "fathoms": ("depth", 1.0),
    "feet": ("depth", 6.0),
    "meters": ("depth", 1.8288),
}


def convert_nautical_units(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert between nautical and standard units.

    Supported conversions:
      - Speed: knots, mph, kph
      - Distance: nautical_miles, miles, km
      - Depth: fathoms, feet, meters

    Args:
        value: The numeric value to convert.
        from_unit: The source unit (e.g., "knots").
        to_unit: The target unit (e.g., "mph").

    Returns:
        dict with the converted value, from_unit, and to_unit.
    """
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()

    if from_unit not in _CONVERSION_TABLE:
        return {"status": "error", "error_message": f"Unknown unit: {from_unit}"}
    if to_unit not in _CONVERSION_TABLE:
        return {"status": "error", "error_message": f"Unknown unit: {to_unit}"}

    from_category, from_factor = _CONVERSION_TABLE[from_unit]
    to_category, to_factor = _CONVERSION_TABLE[to_unit]

    if from_category != to_category:
        return {
            "status": "error",
            "error_message": f"Cannot convert between {from_category} ({from_unit}) and {to_category} ({to_unit}).",
        }

    # Convert: from_unit -> base -> to_unit
    # Factors represent "1 base unit = factor of this unit"
    base_value = value / from_factor
    converted = base_value * to_factor

    return {
        "status": "success",
        "original_value": value,
        "from_unit": from_unit,
        "converted_value": round(converted, 4),
        "to_unit": to_unit,
    }


# --- Cruise Captain Agent ---

captain_agent = Agent(
    name="captain_search_agent",
    model="gemini-2.5-flash",
    description="Captain Sterling, a distinguished cruise ship captain who assists with maritime queries.",
    instruction=(
        "You are Captain Sterling, a distinguished and experienced cruise ship captain. "
        "You speak with a formal but warm tone, using proper nautical terminology. "
        "You have four tools at your disposal:\n"
        "1. google_search — for general knowledge questions about maritime history, events, or facts.\n"
        "2. get_weather — for checking current weather conditions at specific coordinates.\n"
        "3. lookup_port — for finding information about cruise ports and maritime facilities.\n"
        "4. convert_nautical_units — for converting between nautical and standard units "
        "(speed: knots/mph/kph, distance: nautical_miles/miles/km, depth: fathoms/feet/meters).\n\n"
        "Always select the most appropriate tool for the question. "
        "For multi-part requests, use multiple tools in sequence. "
        "When a port lookup returns coordinates, you may use those to check weather."
    ),
    tools=[google_search, get_weather, lookup_port, convert_nautical_units],
)

APP_NAME = "captain_eval"
USER_ID = "eval_user"

THRESHOLDS = {
    "coherence/mean": 4.0,
    "fluency/mean": 4.0,
    "safety/mean": 1.0,
    "trajectory_any_order_match/mean": 0.5,
}


def check_eval_results(result) -> bool:
    """Check eval summary metrics against thresholds. Returns True if all pass."""
    summary = result.summary_metrics
    failures = []
    for metric, threshold in THRESHOLDS.items():
        actual = summary.get(metric)
        if actual is None:
            failures.append(f"  {metric}: MISSING (expected >= {threshold})")
        elif actual < threshold:
            failures.append(f"  {metric}: {actual} < {threshold}")

    if failures:
        print("\nThreshold check FAILED:")
        for f in failures:
            print(f)
        return False
    else:
        print("\nAll metrics passed.")
        return True


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
    """Build eval dataset with prompts and reference trajectories across all tools."""
    data = [
        # google_search_agent only (2)
        {
            "prompt": "Who won the America's Cup sailing race most recently?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "google_search_agent", "tool_input": {"request": "Who won the America's Cup sailing race most recently?"}}]
            ),
        },
        {
            "prompt": "What are the major shipping routes through the Panama Canal?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "google_search_agent", "tool_input": {"request": "major shipping routes through the Panama Canal"}}]
            ),
        },
        # get_weather only (2)
        {
            "prompt": "What is the current weather at latitude 25.76, longitude -80.19?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "get_weather", "tool_input": {"latitude": 25.76, "longitude": -80.19}}]
            ),
        },
        {
            "prompt": "Check the weather conditions at latitude 36.14, longitude -5.35 near the Strait of Gibraltar.",
            "reference_trajectory": json.dumps(
                [{"tool_name": "get_weather", "tool_input": {"latitude": 36.14, "longitude": -5.35}}]
            ),
        },
        # lookup_port only (2)
        {
            "prompt": "Find information about the cruise port in Miami.",
            "reference_trajectory": json.dumps(
                [{"tool_name": "lookup_port", "tool_input": {"query": "cruise port in Miami"}}]
            ),
        },
        {
            "prompt": "Look up the cruise terminal in Southampton, England.",
            "reference_trajectory": json.dumps(
                [{"tool_name": "lookup_port", "tool_input": {"query": "cruise terminal in Southampton, England"}}]
            ),
        },
        # convert_nautical_units only (2)
        {
            "prompt": "Convert 30 knots to miles per hour.",
            "reference_trajectory": json.dumps(
                [{"tool_name": "convert_nautical_units", "tool_input": {"value": 30, "from_unit": "knots", "to_unit": "mph"}}]
            ),
        },
        {
            "prompt": "How many meters is 12 fathoms?",
            "reference_trajectory": json.dumps(
                [{"tool_name": "convert_nautical_units", "tool_input": {"value": 12, "from_unit": "fathoms", "to_unit": "meters"}}]
            ),
        },
        # Multi-tool chains (3)
        {
            "prompt": "Look up the cruise port in Cozumel, Mexico and then check the current weather there.",
            "reference_trajectory": json.dumps(
                [
                    {"tool_name": "lookup_port", "tool_input": {"query": "cruise port in Cozumel, Mexico"}},
                    {"tool_name": "get_weather", "tool_input": {}},
                ]
            ),
        },
        {
            "prompt": "Our ship is traveling at 22 knots. Convert that to kilometers per hour, and also search for the current speed record for cruise ships.",
            "reference_trajectory": json.dumps(
                [
                    {"tool_name": "convert_nautical_units", "tool_input": {"value": 22, "from_unit": "knots", "to_unit": "kph"}},
                    {"tool_name": "google_search_agent", "tool_input": {"request": "current speed record for cruise ships"}},
                ]
            ),
        },
        {
            "prompt": "Find the cruise port in Nassau, Bahamas, check the weather at that location, and convert 50 nautical miles to kilometers.",
            "reference_trajectory": json.dumps(
                [
                    {"tool_name": "lookup_port", "tool_input": {"query": "cruise port in Nassau, Bahamas"}},
                    {"tool_name": "get_weather", "tool_input": {}},
                    {"tool_name": "convert_nautical_units", "tool_input": {"value": 50, "from_unit": "nautical_miles", "to_unit": "km"}},
                ]
            ),
        },
    ]
    return pd.DataFrame(data)


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate the Cruise Captain agent"
    )
    parser.add_argument(
        "--experiment-name",
        default="captain-eval",
        help="Vertex AI experiment name (default: captain-eval)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Cruise Captain Agent Evaluation")
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
    response_metrics = [
        "coherence",       # How logically consistent is the response
        "fluency",         # How natural and readable is the response
        "safety"           # How safe is the response
    ]

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
        print(f"\n--- Prompt {idx + 1}: {row.get('prompt', 'N/A')} ---")
        if "response" in row:
            resp_preview = str(row["response"])
            print(f"  Response: {resp_preview}...")
        for col in metrics_df.columns:
            if col not in ("prompt", "response", "reference_trajectory",
                           "predicted_trajectory"):
                print(f"  {col}: {row[col]}")

    print("\n" + "=" * 60)
    print("  Evaluation complete!")
    print("=" * 60)

    if not check_eval_results(result):
        sys.exit(1)


if __name__ == "__main__":
    main()
