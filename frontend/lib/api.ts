/**
 * The API client. One place that knows how to reach the backend.
 *
 * Every network failure becomes an ApiError with a message a person can read,
 * so a component never has to interpret a fetch rejection.
 */

import type {
  AskResponse,
  Conversation,
  CorpusDocument,
  CorpusListItem,
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
    throw new ApiError(
      `The API returned ${response.status} for ${path}.`,
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
export function ask(apiUrl: string, question: string): Promise<AskResponse> {
  return askWithConversation(apiUrl, question, null);
}

/**
 * Ask within a conversation.
 *
 * `conversationId` is null on the first question and the id returned by the
 * previous turn thereafter -- PRD section 5. Sending it is the whole of
 * REQ-U8 on this side of the wire: the backend decides how much of the
 * conversation a follow-up sees (D8), the client only has to keep the thread.
 */
export function askWithConversation(
  apiUrl: string,
  question: string,
  conversationId: string | null,
): Promise<AskResponse> {
  return request<AskResponse>(apiUrl, "/ask", {
    method: "POST",
    body: JSON.stringify({ question, conversation_id: conversationId }),
  });
}

export function getConversation(apiUrl: string, id: string): Promise<Conversation> {
  return request<Conversation>(apiUrl, `/conversations/${encodeURIComponent(id)}`);
}

/** Every policy document, with owner, version, effective date and status -- REQ-B1. */
export function getCorpus(apiUrl: string): Promise<CorpusListItem[]> {
  return request<CorpusListItem[]>(apiUrl, "/corpus");
}

/**
 * One document and its sections -- REQ-B3.
 *
 * `version` is needed because two versions of the travel policy share one id.
 * Omitted, the API serves the current one, which is the right default and the
 * wrong answer when the reader clicked the superseded card.
 */
export function getCorpusDocument(
  apiUrl: string,
  id: string,
  version?: string,
): Promise<CorpusDocument> {
  const query = version ? `?version=${encodeURIComponent(version)}` : "";
  return request<CorpusDocument>(apiUrl, `/corpus/${encodeURIComponent(id)}${query}`);
}

export function health(apiUrl: string): Promise<Health> {
  return request<Health>(apiUrl, "/healthz");
}
