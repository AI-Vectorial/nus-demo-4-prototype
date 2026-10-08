/**
 * The /ask contract, from docs/PRD.md section 5.
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
  /** Added field: the passage itself, sent only in degraded mode. */
  text?: string | null;
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
  conversation_id: string;
  message_id: string;
  latency_ms: number;
}

export interface Health {
  status: string;
  build: string;
  environment: string;
  dependencies: Record<string, string>;
}

/** GET /corpus -- every document, both travel versions included. */
export interface DocumentSummary {
  id: string;
  title: string;
  owner: string;
  version: string;
  effective: string;
  status: "current" | "superseded";
  sections: string[];
}

/** GET /corpus/{id}?version= */
export interface PolicyDocument extends Omit<DocumentSummary, "sections"> {
  sections: { heading: string; text: string }[];
}
