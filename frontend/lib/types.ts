/**
 * The /ask and /corpus contracts, from docs/PRD.md section 5.
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
  /**
   * The conversation this turn belongs to. Sent back on the next question so
   * a follow-up is answered with the turns above it -- REQ-U8, REQ-C3.
   */
  conversation_id: string;
  /** This assistant turn. What a judgement (F8) or an audit export (F10) hangs on. */
  message_id: string;
  latency_ms: number;
}

/** One turn of a stored conversation -- GET /conversations/{id}. */
export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string | null;
  outcome?: Outcome | null;
  citations?: Citation[];
  latency_ms?: number | null;
}

export interface Conversation {
  id: string;
  started_at: string;
  messages: ConversationMessage[];
}

/**
 * A row of GET /conversations -- REQ-A6, REQ-C8.
 *
 * `title` is the first question, truncated by the API. There is no title to
 * store, so there is none to keep in step with the conversation.
 */
export interface ConversationSummary {
  id: string;
  started_at: string;
  /** When the thread was last touched. The list is ordered on this. */
  last_at: string;
  title: string;
  message_count: number;
}

/** A heading and its text, as GET /corpus/{id} serves them. */
export interface CorpusSection {
  heading: string;
  text: string;
}

/** What every corpus view needs to show: REQ-B1. */
interface CorpusDocumentMeta {
  id: string;
  title: string;
  owner: string;
  /** "3.1" -- rendered as v3.1. */
  version: string;
  /** ISO date, "2026-04-01". Formatted for reading by lib/format.ts. */
  effective: string;
  /** A superseded document must be visibly distinguished -- REQ-B2. */
  status: "current" | "superseded";
}

/**
 * A row of GET /corpus.
 *
 * PRD section 5 carries `sections` on the list payload too, but the list view
 * shows owner, version, effective date and status only -- so it is optional
 * here rather than a shape the list depends on.
 */
export interface CorpusListItem extends CorpusDocumentMeta {
  sections?: CorpusSection[];
}

/** GET /corpus/{id}. */
export interface CorpusDocument extends CorpusDocumentMeta {
  sections: CorpusSection[];
}

export interface Health {
  status: string;
  build: string;
  environment: string;
  dependencies: Record<string, string>;
}
