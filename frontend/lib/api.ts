/**
 * The API client. One place that knows how to reach the backend.
 *
 * Every network failure becomes an ApiError with a message a person can read,
 * so a component never has to interpret a fetch rejection.
 */

import type { AskResponse, DocumentSummary, Health, PolicyDocument } from "./types";

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
export function ask(
  apiUrl: string,
  question: string,
  conversationId: string | null,
): Promise<AskResponse> {
  return request<AskResponse>(apiUrl, "/ask", {
    method: "POST",
    body: JSON.stringify({ question, conversation_id: conversationId }),
  });
}

export function health(apiUrl: string): Promise<Health> {
  return request<Health>(apiUrl, "/healthz");
}

export function corpus(apiUrl: string): Promise<DocumentSummary[]> {
  return request<DocumentSummary[]>(apiUrl, "/corpus", { cache: "no-store" });
}

export function policy(apiUrl: string, id: string, version?: string): Promise<PolicyDocument> {
  const query = version ? `?version=${encodeURIComponent(version)}` : "";
  return request<PolicyDocument>(apiUrl, `/corpus/${encodeURIComponent(id)}${query}`, {
    cache: "no-store",
  });
}
