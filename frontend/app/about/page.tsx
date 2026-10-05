import type { Metadata } from "next";
import Link from "next/link";

import Shell from "@/components/Shell";

/**
 * The facilitator's page. It is not part of the product.
 *
 * It exists on the reference deployment only, and it is projected to the room
 * in the minutes before the lab starts: where the programme has got to, what
 * the next 150 minutes are, and what "done" means before anyone opens a
 * Codespace. Participants never build this -- their branch does not carry it.
 *
 * Nothing in the top bar points at it. A fourth action there measures 378px
 * at the bar's phone padding against the 360px a phone gives it, and the three
 * the product needs already come to 323px -- so the bar stays as it is and the
 * facilitator types the URL, which is what someone opening a page before a
 * room arrives is doing anyway.
 *
 * No `force-dynamic` here, unlike every other route. The other three read the
 * API location at request time because they talk to an API; this one states
 * what is already written in docs/ and AGENTS.md, so it is static, and a page
 * that needs nothing at request time should ask for nothing.
 *
 * Everything on it is quoted or paraphrased from the repository -- the brief,
 * PRD §1 and §12, AGENTS.md §1, pipeline/README.md and the stage files.
 * Nothing here is invented: a recap that has drifted contradicts the documents
 * the room is about to build from, and they will believe the screen.
 */

export const metadata: Metadata = {
  title: "M04 — AI-Native Development Lifecycle",
  description:
    "Where the programme has got to, and what the next 150 minutes are.",
};

type FlowStep =
  | { kind: "stage"; no: string; name: string; time: string; gate: string }
  | { kind: "gate"; text: string };

/**
 * The six stages with their gate and their slot in the 150 minutes, and the
 * two human gates sitting in the flow rather than beside it -- the gates are
 * steps, not annotations, and reading past one is the failure mode.
 */
const FLOW: readonly FlowStep[] = [
  {
    kind: "stage",
    no: "01",
    name: "Shape",
    time: "15 min",
    gate: "The team writes the acceptance criteria, in the team’s own words",
  },
  {
    kind: "stage",
    no: "02",
    name: "Plan",
    time: "25 min",
    gate: "The agent proposes an implementation plan, and the team defends it",
  },
  {
    kind: "gate",
    text: "A human — the release manager — approves or rejects the plan. A rejected plan is revised and presented again.",
  },
  {
    kind: "stage",
    no: "03",
    name: "Build",
    time: "60 min",
    gate: "Your own acceptance criteria pass — run, not asserted",
  },
  {
    kind: "stage",
    no: "04",
    name: "Review",
    time: "25 min",
    gate: "Every finding has a decision — fixed, accepted or deferred — with a reason",
  },
  {
    kind: "stage",
    no: "05",
    name: "Release",
    time: "10 min",
    gate: "A rollback exists, in writing, before anything merges",
  },
  {
    kind: "gate",
    text: "A human approves the pull request. Only then does it merge, and only then does it deploy.",
  },
  {
    kind: "stage",
    no: "06",
    name: "Verify",
    time: "15 min",
    gate: "It answers a real question on your own live URL — watched, not reported",
  },
];

/** AGENTS.md §1, with the one line of consequence that makes each one real. */
const RULES = [
  {
    no: "1",
    rule: "You may not edit protected files. Ever.",
    why: "The specification, the pipeline, the checks and the policy corpus belong to the exercise — if one of them is wrong, your agent says so and stops rather than editing it.",
  },
  {
    no: "2",
    rule: "Decisions belong to the humans. You present; they choose.",
    why: "The PRD leaves some things open on purpose, and an agent that settles them quietly has removed the lesson — at the plan gate, “the agent chose it” is a failed answer.",
  },
  {
    no: "3",
    rule: "Follow the stages in order. Do not run ahead.",
    why: "Code written during planning turns the plan review into theatre, and the plan review is the point.",
  },
] as const;

export default function AboutPage() {
  return (
    <Shell>
      <div className="about-scroll">
        <article className="about">
          <header className="about-head">
            <p className="about-eyebrow">Module 04 · 150 minutes</p>
            <h1 className="about-title">AI-Native Development Lifecycle</h1>
            <p className="about-lede">
              Six stages, two human gates, and one deployed increment on your
              own URL.
            </p>
          </header>

          <section className="about-section">
            <h2>Where we have got to</h2>
            <p>
              Three modules behind us. Today leans on all three at once, so it
              is worth saying out loud what each one left you with.
            </p>
            <ol className="recap">
              <li className="recap-item">
                <p className="recap-tag">M01</p>
                <h3>Foundations</h3>
                <p>
                  The shared vocabulary: what these systems are, and where they
                  do and do not belong. Today assumes it rather than revisits
                  it.
                </p>
              </li>
              <li className="recap-item">
                <p className="recap-tag">M02</p>
                <h3>RAG and model selection</h3>
                <p>
                  Grounding an answer in a corpus you control, and choosing a
                  model deliberately. Today you build one of those systems, and
                  the choices are yours to defend.
                </p>
              </li>
              <li className="recap-item">
                <p className="recap-tag">M03</p>
                <h3>Agentic systems and governance</h3>
                <p>
                  What an agent is, and what has to sit around one before it is
                  allowed to act. Today the agent under governance is the one
                  writing your code.
                </p>
              </li>
            </ol>
          </section>

          <section className="about-section">
            <h2>What today is</h2>
            <p>
              Today is not a lesson in whether an agent can write code. It
              can, and that is no longer the interesting part.
            </p>
            <p className="about-point">
              The question is the one that comes next: what has to be true
              around an agent before you would let its code reach production?
            </p>
            <p>
              The ticket you write, the plan you defend to a human, the review
              record, the rollback stated before the merge — each one is part of
              an answer to that question, and the lifecycle is what holds them
              together.
            </p>
          </section>

          <section className="about-section">
            <h2>What you are building</h2>
            <p>
              The <strong>Policy Assistant</strong> for{" "}
              <strong>Aldermere Bank</strong>. Operations and front-office staff
              hit a policy question in the middle of doing something else, and
              policy lives in four places of which none is definitive. The
              assistant answers the question in seconds, in plain language, and
              shows exactly which policy section the answer came from.
            </p>
            <blockquote className="about-quote">
              When the corpus cannot support an answer, it says so and stops.
            </blockquote>
            <p>
              That line is the product. A confident answer the corpus cannot
              support is worse than the situation the bank has today, because it
              carries an air of authority. A refusal is a good outcome. An
              invention is not.
            </p>
          </section>

          <section className="about-section">
            <h2>The six stages</h2>
            <p>
              Each stage has one job, one output and one gate. You do not begin
              a stage until the previous stage’s gate has passed.
            </p>
            <ol className="stages">
              {FLOW.map((step) =>
                step.kind === "stage" ? (
                  <li className="stage" key={step.no}>
                    <span className="stage-no">{step.no}</span>
                    <div className="stage-body">
                      <h3 className="stage-name">{step.name}</h3>
                      <p className="stage-gate">{step.gate}</p>
                    </div>
                    <span className="stage-time">{step.time}</span>
                  </li>
                ) : (
                  <li className="gate" key={step.text}>
                    <span className="gate-mark">
                      <GateIcon />
                    </span>
                    <div className="gate-body">
                      <p className="gate-label">Human gate</p>
                      <p className="gate-text">{step.text}</p>
                    </div>
                  </li>
                ),
              )}
            </ol>
            <p className="about-aside">
              The two gates are the module. Everything between them is
              engineering you already know how to do.
            </p>
          </section>

          <section className="about-section">
            <h2>What “done” means</h2>
            <blockquote className="about-quote">
              You are done when you have completed all six stages and deployed a
              working increment to your own URL. Not when the product is
              feature-complete.
            </blockquote>
            <p>
              A team that ships ingestion and retrieval but runs out of time
              before generation has still shaped a ticket, defended a plan to a
              human, built against their own acceptance criteria, reviewed in
              five passes, written a rollback, and released through a gate. That
              is the module.
            </p>
            <p className="about-point">
              If time is short, cut scope. Never cut a stage.
            </p>
            <p>A polished product with no review record is the worse outcome.</p>
          </section>

          <section className="about-section">
            <h2>The three rules</h2>
            <p>
              They are in <code className="md-code">AGENTS.md</code>. Your agent
              reads them before it does anything else, and CI refuses any commit
              that breaks the first one.
            </p>
            <ol className="rules">
              {RULES.map((rule) => (
                <li className="rule" key={rule.no}>
                  <span className="rule-no" aria-hidden="true">
                    {rule.no}
                  </span>
                  <div className="rule-body">
                    <h3 className="rule-name">{rule.rule}</h3>
                    <p>{rule.why}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section className="about-section">
            <h2>The target</h2>
            <p>
              This deployment is the reference build — the same brief, the same
              PRD, the same six stages. Ask it something the corpus covers, then
              ask it something it does not.
            </p>
            <Link href="/" className="about-cta">
              Open the Policy Assistant
              <span aria-hidden="true">→</span>
            </Link>
          </section>

          <footer className="about-foot">
            <p>
              Aldermere Bank is fictional. Every name, policy, figure and
              document in this project is invented.
            </p>
            <p>
              This page is <code className="md-code">/about</code> on the
              reference build. It is not part of the product, and no table’s
              branch carries it.
            </p>
          </footer>
        </article>
      </div>
    </Shell>
  );
}

/** A stop sign rather than a tick: the gate can reject, and that is the point. */
function GateIcon() {
  return (
    <svg className="icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M8.6 2.6h6.8L21.4 8.6v6.8L15.4 21.4H8.6L2.6 15.4V8.6L8.6 2.6Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M12 7.4v6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="12" cy="16.6" r="1.2" fill="currentColor" />
    </svg>
  );
}
