/**
 * The /ask contract, from docs/PRD.md section 4.
 *
 * THIS SHAPE IS FIXED. Five tables build against it so five results are
 * comparable and the checks in ci/ can test any of them. Add fields if you
 * need them; do not rename these.
 */

/** One policy section an answer drew on. */
export interface Citation {
  document_id: string;
  document_title: string;
  section: string;
  version: string;
  /** "superseded" must be shown differently from "current" -- REQ-U4. */
  status: "current" | "superseded";
  score: number;
}

/**
 * What happened. Always explicit, never inferred from a null answer.
 *
 *   answered  retrieval was sufficient and the model composed an answer
 *   refused   the corpus could not support an answer -- no model call was made
 *   degraded  the model was off or unreachable; passages are shown without one
 */
export type Outcome = "answered" | "refused" | "degraded";

export interface AskResponse {
  outcome: Outcome;
  /** The composed answer, or the reason for a refusal. null when degraded. */
  answer: string | null;
  citations: Citation[];
  /** PRD section 5: the conversation this exchange belongs to. */
  conversation_id: string;
  /** PRD section 5: the assistant's stored turn for this exchange. */
  message_id: string;
  latency_ms: number;
}

export interface ConversationSummary {
  id: string;
  started_at: string;
  last_at: string;
  title: string;
  message_count: number;
}

export interface StoredMessage {
  id: string;
  role: "user" | "assistant";
  content: string | null;
  outcome: Outcome | null;
  created_at: string;
  citations: Citation[];
}

export interface ConversationView {
  id: string;
  started_at: string;
  last_at: string;
  messages: StoredMessage[];
}

export interface Section {
  heading: string;
  text: string;
}

/** One corpus entry. id is "{document_id}-{version}", so both travel versions are distinct. */
export interface DocumentDetail {
  id: string;
  title: string;
  owner: string;
  version: string;
  effective: string;
  status: "current" | "superseded";
  sections: Section[];
}

export type DocumentSummary = DocumentDetail;

export interface Health {
  status: string;
  build: string;
  environment: string;
  dependencies: Record<string, string>;
}
