// Transforms raw ADK Events into ChatMessage[] for rendering

import {
  ADKEvent,
  AgentTextMessage,
  ArtifactMessage,
  ChatMessage,
  CodeExecutionMessage,
  ErrorMessage,
  HandoffMessage,
  InlineImageMessage,
  ToolCallMessage,
  ToolResponseMessage,
  UserMessage,
} from "./types";

let msgCounter = 0;
function nextId(): string {
  return `msg-${Date.now()}-${++msgCounter}`;
}

export interface ParseResult {
  /** New messages to append */
  newMessages: ChatMessage[];
  /**
   * If set, the ID of an existing streaming message whose text should be
   * updated (appended or replaced).
   */
  streamingUpdateId?: string;
  streamingAppendText?: string;
  /** If set, finalize this streaming message (mark isStreaming=false) */
  finalizeStreamingId?: string;
}

/**
 * Parse a single ADK event and return instructions for updating the UI state.
 *
 * @param event - Raw ADK event
 * @param currentAgentName - The agent that is currently active (tracked externally)
 * @param streamingMessageId - ID of the currently open streaming message (if any)
 */
export function parseEvent(
  event: ADKEvent,
  currentAgentName: string,
  streamingMessageId: string | null
): ParseResult {
  const result: ParseResult = { newMessages: [] };

  // Error events
  if (event.errorCode || event.errorMessage) {
    const msg: ErrorMessage = {
      id: nextId(),
      type: "error",
      timestamp: Date.now(),
      errorCode: event.errorCode,
      errorMessage: event.errorMessage ?? event.errorCode ?? "Unknown error",
    };
    result.newMessages.push(msg);
    return result;
  }

  // Agent handoff via actions
  if (event.actions?.transferToAgent) {
    const msg: HandoffMessage = {
      id: nextId(),
      type: "handoff",
      timestamp: Date.now(),
      fromAgent: event.author ?? currentAgentName,
      toAgent: event.actions.transferToAgent,
    };
    result.newMessages.push(msg);
    return result;
  }

  const author = event.author ?? currentAgentName;

  // Artifact outputs (e.g. matplotlib charts saved by analysis_agent).
  // Must run BEFORE the early return below so artifact events with
  // partial===false are never skipped.
  if (event.actions?.artifactDelta) {
    for (const [filename, version] of Object.entries(event.actions.artifactDelta)) {
      if (/\.(png|jpg|jpeg|gif|svg|webp)$/i.test(filename)) {
        const msg: ArtifactMessage = {
          id: nextId(),
          type: "artifact",
          timestamp: Date.now(),
          filename,
          version,
          agentName: author,
        };
        result.newMessages.push(msg);
      }
    }
  }

  // ADK sends a final non-partial event that replays ALL content already
  // delivered via partial events. Skip processing to avoid duplicates.
  // Just finalize the open streaming bubble.
  if (event.partial === false && streamingMessageId) {
    result.finalizeStreamingId = streamingMessageId;
    return result;
  }

  const parts = event.content?.parts ?? [];

  for (const part of parts) {
    // User text (typically not streamed, comes as a single event)
    if (event.content?.role === "user" && part.text) {
      const msg: UserMessage = {
        id: nextId(),
        type: "user",
        timestamp: Date.now(),
        text: part.text,
      };
      result.newMessages.push(msg);
      continue;
    }

    // Streaming partial text
    if (event.partial && part.text) {
      if (streamingMessageId) {
        // Append to existing streaming bubble
        result.streamingUpdateId = streamingMessageId;
        result.streamingAppendText = (result.streamingAppendText ?? "") + part.text;
      } else {
        // Start a new streaming bubble
        const msg: AgentTextMessage = {
          id: nextId(),
          type: "streaming",
          timestamp: Date.now(),
          text: part.text,
          agentName: author,
          isStreaming: true,
        };
        result.newMessages.push(msg);
      }
      continue;
    }

    // Non-partial agent text
    if (part.text && event.content?.role !== "user") {
      if (streamingMessageId && !event.partial) {
        // Finalize the streaming bubble
        result.finalizeStreamingId = streamingMessageId;
        result.streamingAppendText = (result.streamingAppendText ?? "") + part.text;
      } else {
        const msg: AgentTextMessage = {
          id: nextId(),
          type: "agent-text",
          timestamp: Date.now(),
          text: part.text,
          agentName: author,
          isStreaming: false,
        };
        result.newMessages.push(msg);
      }
      continue;
    }

    // Function call (tool invocation)
    if (part.functionCall) {
      const msg: ToolCallMessage = {
        id: nextId(),
        type: "tool-call",
        timestamp: Date.now(),
        callId: part.functionCall.id ?? nextId(),
        toolName: part.functionCall.name,
        args: part.functionCall.args ?? {},
        agentName: author,
      };
      result.newMessages.push(msg);
      continue;
    }

    // Function response (tool result)
    if (part.functionResponse) {
      const msg: ToolResponseMessage = {
        id: nextId(),
        type: "tool-response",
        timestamp: Date.now(),
        callId: part.functionResponse.id ?? nextId(),
        toolName: part.functionResponse.name,
        response: part.functionResponse.response ?? {},
        agentName: author,
      };
      result.newMessages.push(msg);
      continue;
    }

    // Code execution request
    if (part.executableCode) {
      const msg: CodeExecutionMessage = {
        id: nextId(),
        type: "code-execution",
        timestamp: Date.now(),
        language: part.executableCode.language ?? "python",
        code: part.executableCode.code,
        agentName: author,
      };
      result.newMessages.push(msg);
      continue;
    }

    // Code execution result - attach to previous code block if possible
    if (part.codeExecutionResult) {
      // We emit a separate code-execution message with just output;
      // the ChatContainer pairs them by index order.
      const msg: CodeExecutionMessage = {
        id: nextId(),
        type: "code-execution",
        timestamp: Date.now(),
        language: "",
        code: "",
        output: part.codeExecutionResult.output,
        outcome: part.codeExecutionResult.outcome,
        agentName: author,
      };
      result.newMessages.push(msg);
      continue;
    }

    // Inline image data from Gemini code execution (fallback when no artifactDelta)
    if (part.inlineData && /^image\//i.test(part.inlineData.mimeType)) {
      const msg: InlineImageMessage = {
        id: nextId(),
        type: "inline-image",
        timestamp: Date.now(),
        mimeType: part.inlineData.mimeType,
        data: part.inlineData.data,
        agentName: author,
      };
      result.newMessages.push(msg);
      continue;
    }
  }

  // If turnComplete and there is an open streaming bubble, finalize it
  if (event.turnComplete && streamingMessageId && !result.finalizeStreamingId) {
    result.finalizeStreamingId = streamingMessageId;
  }

  return result;
}
