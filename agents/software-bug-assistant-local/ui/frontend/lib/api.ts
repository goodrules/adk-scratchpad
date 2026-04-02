// Session CRUD and SSE streaming client for ADK backend

import { ADKEvent } from "./types";

const APP_NAME = "software_bug_assistant";
const USER_ID = "demo_user";
const BASE_URL = "/api";
const SSE_BASE_URL = "http://localhost:8000"; // Direct to FastAPI, bypasses Next.js proxy buffering

export async function fetchArtifact(
  sessionId: string,
  filename: string
): Promise<{ mimeType: string; data: string }> {
  const res = await fetch(
    `${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${sessionId}/artifacts/${encodeURIComponent(filename)}`
  );
  if (!res.ok) throw new Error(`Failed to fetch artifact: ${res.statusText}`);
  const part = await res.json();
  // Support both camelCase (by_alias=true) and snake_case field names
  const blob = part.inlineData ?? part.inline_data;
  if (!blob) throw new Error("Artifact has no inline data");
  return {
    mimeType: blob.mimeType ?? blob.mime_type,
    data: blob.data,
  };
}

export async function createSession(): Promise<string> {
  const response = await fetch(
    `${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.statusText}`);
  }

  const data = await response.json();
  return data.id as string;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(
    `${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${sessionId}`,
    { method: "DELETE" }
  );
}

export function sendMessage(
  sessionId: string,
  text: string,
  onEvent: (event: ADKEvent) => void,
  onComplete: () => void,
  onError: (error: Error) => void
): AbortController {
  const controller = new AbortController();

  const payload = {
    app_name: APP_NAME,
    user_id: USER_ID,
    session_id: sessionId,
    new_message: {
      role: "user",
      parts: [{ text }],
    },
    streaming: true,
  };

  (async () => {
    try {
      const response = await fetch(`${SSE_BASE_URL}/run_sse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status} ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("Response body is null");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE format: lines starting with "data: ", separated by "\n\n"
        const parts = buffer.split("\n\n");
        // Keep last part (potentially incomplete) in buffer
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          for (const line of part.split("\n")) {
            if (line.startsWith("data: ")) {
              const jsonStr = line.slice(6).trim();
              if (jsonStr === "[DONE]" || jsonStr === "") continue;
              try {
                const event = JSON.parse(jsonStr) as ADKEvent;
                onEvent(event);
                await new Promise(resolve => requestAnimationFrame(resolve));
              } catch {
                // Skip malformed JSON
              }
            }
          }
        }
      }

      onComplete();
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // User cancelled - not an error
        onComplete();
      } else {
        onError(err instanceof Error ? err : new Error(String(err)));
      }
    }
  })();

  return controller;
}
