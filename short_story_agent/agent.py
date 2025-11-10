from google.adk.agents import LoopAgent, SequentialAgent

from .subagents import (
    editor_agent,
    refiner_agent,
    writer_agent,
    planner_agent
)

# The LoopAgent contains the agents that will run repeatedly: Critic -> Refiner.
story_refinement_loop = LoopAgent(
    name="StoryRefinementLoop",
    sub_agents=[editor_agent, refiner_agent],
    max_iterations=3, # Prevents infinite loops
)

# The root agent is a SequentialAgent that defines the overall workflow: Initial Write -> Refinement Loop.
root_agent = SequentialAgent(
    name="StoryPipeline",
    sub_agents=[planner_agent, writer_agent, story_refinement_loop],
)