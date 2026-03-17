"""Chainlit UI for the VAIS Agent.

Run with: chainlit run app.py -w
"""

import urllib.parse
import uuid

import chainlit as cl
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent import root_agent

session_service = InMemorySessionService()


def clean_uri(uri: str) -> str:
    """Clean URI for web display (convert gs://, encode spaces)."""
    if not uri:
        return ""
    if uri.startswith("gs://"):
        uri = uri.replace("gs://", "https://storage.cloud.google.com/", 1)
    return uri.replace(" ", "%20")


def format_grounding_sources(grounding_metadata) -> str:
    """Format grounding chunks as Markdown source links."""
    lines = []
    for i, chunk in enumerate(grounding_metadata.grounding_chunks or [], 1):
        ctx = chunk.retrieved_context
        if ctx:
            title = ctx.title or ctx.document_name or f"Source {i}"
            uri = clean_uri(ctx.uri or "")
            
            # Extract page number if available
            page = None
            if hasattr(ctx, "rag_chunk") and ctx.rag_chunk and hasattr(ctx.rag_chunk, "page_span") and ctx.rag_chunk.page_span:
                page = ctx.rag_chunk.page_span.first_page
                
            if page:
                title = f"{title} (Page {page})"
                if uri:
                    uri = f"{uri}#page={page}"
                    
            if uri:
                lines.append(f"- [{title}]({uri})")
            else:
                lines.append(f"- {title}")
        elif chunk.web:
            title = chunk.web.title or f"Source {i}"
            uri = clean_uri(chunk.web.uri or "")
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
                page = None
                if hasattr(ctx, "rag_chunk") and ctx.rag_chunk and hasattr(ctx.rag_chunk, "page_span") and ctx.rag_chunk.page_span:
                    page = ctx.rag_chunk.page_span.first_page
                    
                title_suffix = f" (Page {page})" if page else ""
                sections.append(f"\n**[{i}] {ctx.title or ctx.document_name or 'Untitled'}{title_suffix}**")
                if ctx.uri:
                    uri = clean_uri(ctx.uri)
                    if page:
                        uri = f"{uri}#page={page}"
                    sections.append(f"  URI: {uri}")
                if ctx.text:
                    snippet = ctx.text[:300] + "..." if len(ctx.text) > 300 else ctx.text
                    sections.append(f"  > {snippet}")
            elif chunk.web:
                sections.append(f"\n**[{i}] {chunk.web.title or 'Untitled'}**")
                if chunk.web.uri:
                    sections.append(f"  URI: {clean_uri(chunk.web.uri)}")

    # Grounding supports (text-to-source mappings)
    if grounding_metadata.grounding_supports:
        sections.append("\n**Grounding Supports:**")
        for support in grounding_metadata.grounding_supports:
            text = support.segment.text if support.segment else ""
            indices = support.grounding_chunk_indices or []
            scores = support.confidence_scores or []
            score_str = ", ".join(f"{s:.2f}" for s in scores) if scores else "N/A"
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

    msg = cl.Message(content="")
    await msg.send()

    final_text = ""
    grounding_metadata = None

    async for event in runner.run_async(
        user_id="chainlit-user",
        session_id=session_id,
        new_message=types.Content(parts=[types.Part(text=message.content)]),
    ):
        # Collect text from non-partial events and stream partials
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    if event.partial:
                        await msg.stream_token(part.text)
                    else:
                        final_text += part.text

        # Capture grounding metadata
        if event.grounding_metadata:
            grounding_metadata = event.grounding_metadata

    if final_text:
        msg.content = final_text

    # Build source links and collapsible step
    elements = []
    if grounding_metadata and grounding_metadata.grounding_chunks:
        sources_md = format_grounding_sources(grounding_metadata)
        if sources_md:
            msg.content += "\n\n---\n**Sources:**\n" + sources_md

        # Collapsible step with full metadata details
        async with cl.Step(name="View Grounding Metadata", type="tool") as step:
            step.output = format_detailed_metadata(grounding_metadata)

        # PDF side-panel framing removed to avoid '*/*' MIME type browser 
        # console errors, as GCS private URLs fail to load in iframes (403).

    msg.elements = elements
    await msg.update()
