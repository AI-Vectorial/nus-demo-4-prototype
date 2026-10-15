/**
 * The API client. One place that knows how to reach the backend.
 *
 * Every network failure becomes an ApiError with a message a person can read,
 * so a component never has to interpret a fetch rejection.
 */

import type {
  AskResponse,
  ConversationSummary,
  ConversationView,
  DocumentDetail,
  DocumentSummary,
  Health,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong.";
}

async function request<T>(apiUrl: string, path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiUrl}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(`Could not reach the API at ${apiUrl}.`);
  }

  if (!response.ok) {
    // The API's own message is more useful than the status code when it has one,
    // e.g. "the exchange could not be recorded; try again".
    let detail: unknown;
    try {
      detail = (await response.json())?.detail;
    } catch {
      detail = undefined;
    }
    throw new ApiError(
      typeof detail === "string" ? detail : `The API returned ${response.status} for ${path}.`,
      response.status,
    );
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(`The API returned something that was not JSON.`);
  }
}

/**
 * Ask a policy question.
 *
 * A refusal is a SUCCESSFUL response, not an error -- it arrives as
 * outcome: "refused" with 200. Treating it as a failure would render the
 * product's defining behaviour as a bug.
 */
export function ask(
  apiUrl: string,
  question: string,
  conversationId: string | null = null,
): Promise<AskResponse> {
  return request<AskResponse>(apiUrl, "/ask", {
    method: "POST",
    body: JSON.stringify({ question, conversation_id: conversationId }),
  });
}

export function health(apiUrl: string): Promise<Health> {
  return request<Health>(apiUrl, "/healthz");
}

export function listConversations(apiUrl: string): Promise<ConversationSummary[]> {
  return request<ConversationSummary[]>(apiUrl, "/conversations?limit=50");
}

export function getConversation(apiUrl: string, id: string): Promise<ConversationView> {
  return request<ConversationView>(apiUrl, `/conversations/${encodeURIComponent(id)}`);
}

export function listCorpus(apiUrl: string): Promise<DocumentSummary[]> {
  return request<DocumentSummary[]>(apiUrl, "/corpus");
}

export function getDocument(apiUrl: string, id: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(apiUrl, `/corpus/${encodeURIComponent(id)}`);
}
