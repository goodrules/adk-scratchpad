"""Chainlit UI for the VAIS Agent.

Run with: chainlit run app.py -w
"""

import uuid

import chainlit as cl
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent import root_agent

session_service = InMemorySessionService()


def format_grounding_sources(grounding_metadata) -> str:
    """Format grounding chunks as Markdown source links."""
    lines = []
    for i, chunk in enumerate(grounding_metadata.grounding_chunks or [], 1):
        ctx = chunk.retrieved_context
        if ctx:
            title = ctx.title or ctx.document_name or f"Source {i}"
            uri = ctx.uri or ""
            if uri:
                lines.append(f"- [{title}]({uri})")
            else:
                lines.append(f"- {title}")
        elif chunk.web:
            title = chunk.web.title or f"Source {i}"
            uri = chunk.web.uri or ""
            if uri:
                lines.append(f"- [{title}]({uri})")
            else:
                lines.append(f"- {title}")
    return "\n".join(lines)


def format_detailed_metadata(grounding_metadata) -> str:
    """Format full grounding metadata for the collapsible step."""
    sections = []

    # Retrieval queries
    if grounding_metadata.retrieval_queries:
        sections.append("**Retrieval Queries:**")
        for q in grounding_metadata.retrieval_queries:
            sections.append(f"- {q}")

    # Grounding chunks with details
    if grounding_metadata.grounding_chunks:
        sections.append("\n**Grounding Chunks:**")
        for i, chunk in enumerate(grounding_metadata.grounding_chunks, 1):
            ctx = chunk.retrieved_context
            if ctx:
                sections.append(f"\n**[{i}] {ctx.title or ctx.document_name or 'Untitled'}**")
                if ctx.uri:
                    sections.append(f"  URI: {ctx.uri}")
                if ctx.text:
                    snippet = ctx.text[:300] + "..." if len(ctx.text) > 300 else ctx.text
                    sections.append(f"  > {snippet}")
            elif chunk.web:
                sections.append(f"\n**[{i}] {chunk.web.title or 'Untitled'}**")
                if chunk.web.uri:
                    sections.append(f"  URI: {chunk.web.uri}")

    # Grounding supports (text-to-source mappings)
    if grounding_metadata.grounding_supports:
        sections.append("\n**Grounding Supports:**")
        for support in grounding_metadata.grounding_supports:
            text = support.segment.text if support.segment else ""
            indices = support.grounding_chunk_indices or []
            scores = support.confidence_scores or []
            score_str = ", ".join(f"{s:.2f}" for s in scores)
            sections.append(f'- "{text}" -> chunks {list(indices)} (confidence: {score_str})')

    return "\n".join(sections) if sections else "No detailed metadata available."


@cl.on_chat_start
async def on_chat_start():
    runner = Runner(
        agent=root_agent,
        app_name="vais_agent",
        session_service=session_service,
    )
    session_id = str(uuid.uuid4())

    # Create the session
    await session_service.create_session(
        app_name="vais_agent",
        user_id="chainlit-user",
        session_id=session_id,
    )

    cl.user_session.set("runner", runner)
    cl.user_session.set("session_id", session_id)

    await cl.Message(
        content="Hello! I'm a document search assistant powered by Vertex AI Search. Ask me anything about the indexed documents."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    runner: Runner = cl.user_session.get("runner")
    session_id: str = cl.user_session.get("session_id")

    response_text = ""
    grounding_metadata = None

    async for event in runner.run_async(
        user_id="chainlit-user",
        session_id=session_id,
        new_message=types.Content(parts=[types.Part(text=message.content)]),
    ):
        # Collect text from non-partial events
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text and not event.partial:
                    response_text += part.text

        # Capture grounding metadata
        if event.grounding_metadata:
            grounding_metadata = event.grounding_metadata

    # Build source links and collapsible step
    elements = []
    if grounding_metadata and grounding_metadata.grounding_chunks:
        sources_md = format_grounding_sources(grounding_metadata)
        if sources_md:
            response_text += "\n\n---\n**Sources:**\n" + sources_md

        # Collapsible step with full metadata details
        async with cl.Step(name="View Grounding Metadata", type="tool") as step:
            step.output = format_detailed_metadata(grounding_metadata)

        # Reach goal: PDF side-panel elements
        for chunk in grounding_metadata.grounding_chunks:
            ctx = chunk.retrieved_context
            if ctx and ctx.uri and ctx.uri.endswith(".pdf"):
                elements.append(
                    cl.Pdf(
                        name=ctx.title or "Document",
                        url=ctx.uri,
                        display="side",
                    )
                )

    await cl.Message(content=response_text, elements=elements).send()
