export const CHATBOT_INPUT_MAX_LEN = 400;

export interface SendChatMessageResult {
  completion: string;
}

interface ChatbotSuccessResponse {
  completion: string;
}

interface ChatbotErrorResponse {
  error?: string;
}

export async function sendChatMessage(
  input: string,
  sessionId: string,
  signal?: AbortSignal,
): Promise<SendChatMessageResult> {
  const endpoint = import.meta.env.VITE_CHATBOT_LAMBDA_ENDPOINT;
  if (!endpoint) {
    throw new Error(
      "VITE_CHATBOT_LAMBDA_ENDPOINT is not set — check the build env / GitHub Actions secret",
    );
  }
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input, id: sessionId }),
    signal,
  });
  if (!res.ok) {
    let errorMessage = `Chatbot request failed: ${res.status}`;
    try {
      const data = (await res.json()) as ChatbotErrorResponse;
      if (data?.error) errorMessage = data.error;
    } catch {
      // response body wasn't JSON; keep the generic status-based message
    }
    throw new Error(errorMessage);
  }
  const data = (await res.json()) as ChatbotSuccessResponse;
  return { completion: data.completion ?? "" };
}
