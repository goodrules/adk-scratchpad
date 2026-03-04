// TypeScript types mirroring the ADK Event model and UI state

// ---- ADK Raw Event Types ----

export interface FunctionCall {
  id?: string;
  name: string;
  args: Record<string, unknown>;
}

export interface FunctionResponse {
  id?: string;
  name: string;
  response: Record<string, unknown>;
}

export interface ExecutableCode {
  language: string;
  code: string;
}

export interface CodeExecutionResult {
  outcome: string; // "OUTCOME_OK" | "OUTCOME_ERROR" etc.
  output: string;
}

export interface Part {
  text?: string;
  functionCall?: FunctionCall;
  functionResponse?: FunctionResponse;
  executableCode?: ExecutableCode;
  codeExecutionResult?: CodeExecutionResult;
  inlineData?: { mimeType: string; data: string };
}

export interface Content {
  role: "user" | "model";
  parts: Part[];
}

export interface EventActions {
  transferToAgent?: string;
  escalate?: boolean;
  skipSummarization?: boolean;
  stateDelta?: Record<string, unknown>;
  artifactDelta?: Record<string, number>;
}

export interface ADKEvent {
  id?: string;
  author?: string;
  content?: Content;
  partial?: boolean;
  turnComplete?: boolean;
  errorCode?: string;
  errorMessage?: string;
  actions?: EventActions;
  invocationId?: string;
}

// ---- UI Chat Message Types ----

export type MessageType =
  | "user"
  | "agent-text"
  | "intermediate-text"
  | "tool-call"
  | "tool-response"
  | "handoff"
  | "code-execution"
  | "error"
  | "streaming"
  | "artifact"
  | "inline-image";

export interface BaseMessage {
  id: string;
  type: MessageType;
  timestamp: number;
}

export interface UserMessage extends BaseMessage {
  type: "user";
  text: string;
}

export interface AgentTextMessage extends BaseMessage {
  type: "agent-text" | "intermediate-text" | "streaming";
  text: string;
  agentName: string;
  isStreaming?: boolean;
}

export interface ToolCallMessage extends BaseMessage {
  type: "tool-call";
  callId: string;
  toolName: string;
  args: Record<string, unknown>;
  agentName: string;
}

export interface ToolResponseMessage extends BaseMessage {
  type: "tool-response";
  callId: string;
  toolName: string;
  response: Record<string, unknown>;
  agentName: string;
}

export interface HandoffMessage extends BaseMessage {
  type: "handoff";
  fromAgent: string;
  toAgent: string;
}

export interface CodeExecutionMessage extends BaseMessage {
  type: "code-execution";
  language: string;
  code: string;
  output?: string;
  outcome?: string;
  agentName: string;
}

export interface ErrorMessage extends BaseMessage {
  type: "error";
  errorCode?: string;
  errorMessage: string;
}

export interface ArtifactMessage extends BaseMessage {
  type: "artifact";
  filename: string;
  version: number;
  agentName: string;
}

export interface InlineImageMessage extends BaseMessage {
  type: "inline-image";
  mimeType: string;
  data: string;
  agentName: string;
}

export type ChatMessage =
  | UserMessage
  | AgentTextMessage
  | ToolCallMessage
  | ToolResponseMessage
  | HandoffMessage
  | CodeExecutionMessage
  | ErrorMessage
  | ArtifactMessage
  | InlineImageMessage;
