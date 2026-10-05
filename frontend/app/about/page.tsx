import type { Metadata } from "next";
import Link from "next/link";

import Shell from "@/components/Shell";

/**
 * The facilitator's page. It is not part of the product.
 *
 * It exists on the reference deployment only, and it is projected to the room
 * in the minutes before the lab starts. Participants never build this -- their
 * branch does not carry it.
 *
 * Nothing in the top bar points at it. A fourth action there measures 378px at
 * the bar's phone padding against the 360px a phone gives it, and the three the
 * product needs already come to 323px -- so the bar stays as it is and the
 * facilitator types the URL.
 *
 * Laid out in grids rather than one reading column. An earlier version capped
 * prose at 48rem inside a 62rem page, which reads well on a laptop and wastes
 * the right-hand third of a projector.
 *
 * Everything here is quoted or paraphrased from the repository -- the brief,
 * PRD §1 and §12, AGENTS.md §1, features.md and the stage files -- and the
 * session titles come from the lab plan's coverage matrix. Nothing is invented:
 * a recap that has drifted contradicts the documents the room is about to build
 * from, and they will believe the screen.
 */

export const metadata: Metadata = {
  title: "Before we start — M04",
  description:
    "Where we got to yesterday, and what the next 150 minutes are.",
};

const M03: [string, string, string][] = [
  ["M03.1", "What agentic AI is", "Who decides the next step. Read-only tool use against state-changing action, the agent loop, and when it terminates."],
  ["M03.2", "Architecture patterns", "Supervisor and worker. Specialist roles. Agentic RAG as one agent with tools, applied to retrieval."],
  ["M03.3", "Architecture deep dive", "State and memory, tool contracts and isolation, control flow, checkpoints, step budgets and timeouts."],
  ["M03.4", "Risk and oversight", "Grounding and abstention thresholds. Approve, Notify, Automate. Audit evidence and reconstructing a decision."],
  ["M03.5", "Security and containment", "Prompt injection through retrieved content. Tool reach and blast radius. Containment rather than prevention."],
  ["M03.6", "The Glass Box lab", "A multi-agent KYC workflow, with every dial exposed and every outcome traceable."],
];

const M04: [string, string, string, string][] = [
  ["M04.1", "Shaping the work", "If it doesn’t fit one page, the slice is too big", "And the question that comes before it: does AI belong in this runtime at all?"],
  ["M04.2", "Criteria as executable", "A bounded contract, not an ambiguous request", "Acceptance criteria are the specification, and CI runs them."],
  ["M04.3", "Permission boundaries", "The AI proposes; the human disposes", "Protected paths, a check that refuses the build, and a plan a human can reject."],
  ["M04.4", "The five-pass review", "AI-generated tests can assert the bug", "Correctness, security, data, dependencies, maintainability — one pass at a time."],
  ["M04.6", "The lab", "Five tables, five deployments", "Everything above, lived rather than described."],
];

const FEATURES: [string, string, string, boolean][] = [
  ["F1", "Ingest", "Read five policy documents, split on section boundaries, embed, store.", false],
  ["F2", "Retrieve", "Embed the question, search, return the closest passages with their scores.", false],
  ["F3", "Refuse", "Below the threshold, decline — and do not call the model at all.", false],
  ["F4", "Generate", "Compose from the retrieved passages only. Plus a kill switch.", false],
  ["F5", "Ask and show", "The endpoint, the stored record, and an interface for every outcome.", false],
  ["F6", "Follow-up", "“And what about above £500?” has to mean something.", true],
  ["F7", "Corpus", "Browse the documents, so a citation can be checked rather than trusted.", true],
  ["F8", "History", "Past conversations — because the record is half the point.", true],
];

type Step =
  | { kind: "stage"; no: string; name: string; time: string; produces: string; why: string }
  | { kind: "gate"; produces: string; why: string };

const STAGES: Step[] = [
  { kind: "stage", no: "01", name: "Shape", time: "15 min", produces: "The ticket, and acceptance criteria in your own words.", why: "The agent summarises what it believes you are building so you can correct it, then asks what done looks like — one question at a time. It does not write your criteria for you." },
  { kind: "stage", no: "02", name: "Plan", time: "25 min", produces: "The implementation plan, and the decisions behind it.", why: "Ten decisions are deliberately left open: chunk size, the refusal threshold, what happens when two policies contradict each other. The agent presents them all, with trade-offs, and then stops." },
  { kind: "gate", produces: "A human approves the plan — or rejects it.", why: "You will be asked why you chose what you chose. “The agent suggested it” is a failed answer, and a rejected plan goes back to stage 02." },
  { kind: "stage", no: "03", name: "Build", time: "60 min", produces: "F1 through F8, committed to your work branch.", why: "Tests before code where you reasonably can. Stop and ask before adding a dependency. Nothing deploys at this stage — that comes later, and only through a gate." },
  { kind: "stage", no: "04", name: "Review", time: "25 min", produces: "Five passes, with a decision recorded against every finding.", why: "Warm up on somebody else’s code first. It has a real defect in it and its tests all pass — which is exactly the point. Then turn the same five passes on your own work." },
  { kind: "stage", no: "05", name: "Release", time: "10 min", produces: "One pull request carrying the code and the record together.", why: "The rollback is written before the merge, not after. The PR carries the ticket, the plan, the review record and the code — approved as one thing." },
  { kind: "gate", produces: "A human approves the release. Then it merges, and deploys.", why: "This is the only path to a deployment. A push cannot deploy — if it could, the gate would be decoration." },
  { kind: "stage", no: "06", name: "Verify", time: "15 min", produces: "It answers on your own URL.", why: "An answer with citations, a refusal, and the cited section opened in the corpus. Then the closing question: where did AI help, where did it risk something, and which control caught it?" },
];

const RULES: [string, string, string][] = [
  ["1", "You may not edit protected files", "The PRD, the pipeline, the checks, the corpus. If one of them is wrong, say so — do not change it. CI refuses the build either way."],
  ["2", "Decisions belong to the humans", "Some things are specified. Some are deliberately open, and those are not the agent’s to settle. It presents, you choose, it records your reason."],
  ["3", "Follow the stages in order", "You will be able to see the whole solution at stage 01. Write it down and wait — coding during planning makes the plan review theatre."],
];

export default function AboutPage() {
  return (
    <Shell>
      <div className="about-scroll">
        <main className="about">
          <p className="about-eyebrow">Module 04 · AI-Native Development Lifecycle</p>
          <h1 className="about-title">Before we start</h1>
          <p className="about-lede">
            The next 150 minutes are not about whether an agent can write code.
            It can. They are about what has to be true <em>around</em> an agent
            before you would let its code reach production.
          </p>

          <section className="about-section">
            <h2>Where we got to yesterday</h2>
            <p className="about-sub">
              <strong>Module 03 — Agentic AI: Building &amp; Governing.</strong>{" "}
              Six sessions, ending in the Glass Box lab.
            </p>
            <ul className="grid grid-3">
              {M03.map(([id, name, body]) => (
                <li key={id} className="card">
                  <span className="card-tag">{id}</span>
                  <h3>{name}</h3>
                  <p>{body}</p>
                </li>
              ))}
            </ul>
            <p className="about-point">Two of those carry straight into today.</p>
            <p>
              <strong>M03.4</strong> gave you grounding and abstention — a system
              that declines when the evidence is thin. <strong>M03.5</strong>{" "}
              gave you containment — text arriving as data cannot be allowed to
              instruct. Today the same instinct moves one level out: from
              governing what an agent does at <em>runtime</em>, to governing what
              an agent does to your <em>codebase</em>.
            </p>
          </section>

          <section className="about-section">
            <h2>What today is</h2>
            <p>
              An agent will write most of the code you ship this afternoon. That
              is not the interesting part. The interesting part is that it will
              also settle decisions you should be making, reach for files it
              should not touch, and write tests that assert its own bugs — unless
              something stops it.
            </p>
            <p className="about-point">Today you build the something.</p>
            <ul className="grid grid-2">
              {M04.map(([id, name, tagline, body]) => (
                <li key={id} className="card">
                  <span className="card-tag">{id}</span>
                  <h3>{name}</h3>
                  <p className="card-quote">“{tagline}”</p>
                  <p>{body}</p>
                </li>
              ))}
            </ul>
            <p className="about-aside">
              M04.5 is on hold; its release content is carried by the lab itself.
            </p>
          </section>

          <section className="about-section">
            <h2>What you are building</h2>
            <p>
              The <strong>Policy Assistant</strong> for Aldermere Bank — a
              fictional bank, with five invented policy documents. Operations and
              front-office staff hit a policy question in the middle of doing
              something else. The assistant answers it from the bank’s own
              policies, in seconds, and shows exactly which section the answer
              came from.
            </p>
            <blockquote className="about-quote">
              When the corpus cannot support an answer, it says so and stops.
            </blockquote>
            <p>
              That line is the product. A confident answer the corpus cannot
              support is worse than the situation the bank has today, because it
              carries an air of authority.{" "}
              <strong>A refusal is a good outcome. An invention is not.</strong>
            </p>

            <h3 className="about-h3">Eight features. One pull request.</h3>
            <ul className="grid grid-4">
              {FEATURES.map(([id, name, body, cuttable]) => (
                <li key={id} className={cuttable ? "card card-cut" : "card"}>
                  <span className="card-tag">{id}</span>
                  <h3>{name}</h3>
                  <p>{body}</p>
                  {cuttable ? <span className="card-note">cuttable</span> : null}
                </li>
              ))}
            </ul>
            <p className="about-aside">
              The corpus holds a deliberate conflict between two current
              policies, one withdrawn version still sitting in the index, and a
              plausible question nothing in it answers. All three are there so
              the hard cases are real rather than hypothetical.
            </p>
          </section>

          <section className="about-section">
            <h2>The six stages</h2>
            <p>
              Each stage has a gate, and you do not begin one until the previous
              gate has passed. <strong>Two of those gates are a person.</strong>
            </p>
            <ol className="stages">
              {STAGES.map((s, i) =>
                s.kind === "gate" ? (
                  <li key={i} className="gate">
                    <span className="gate-mark" aria-hidden="true" />
                    <div className="gate-body">
                      <span className="gate-label">Human gate</span>
                      <p className="gate-text">{s.produces}</p>
                      <p className="gate-why">{s.why}</p>
                    </div>
                  </li>
                ) : (
                  <li key={i} className="stage">
                    <span className="stage-no">{s.no}</span>
                    <div className="stage-body">
                      <h3 className="stage-name">
                        {s.name} <span className="stage-time">{s.time}</span>
                      </h3>
                      <p className="stage-produces">{s.produces}</p>
                      <p className="stage-why">{s.why}</p>
                    </div>
                  </li>
                ),
              )}
            </ol>
          </section>

          <section className="about-section">
            <h2>What “done” means</h2>
            <blockquote className="about-quote">
              You are done when you have completed all six stages and deployed a
              working increment to your own URL. Not when the product is
              feature-complete.
            </blockquote>
            <p>
              A team that ships ingestion, retrieval and refusal but runs out of
              time before history has still shaped a ticket, defended a plan to a
              human, built against their own acceptance criteria, reviewed in
              five passes, written a rollback and released through a gate.{" "}
              <strong>That is the module.</strong>
            </p>
            <p className="about-point">
              If time is short, cut scope. Never cut a stage.
            </p>
            <p>
              F6, F7 and F8 are the scope that gets cut — and what you cut, you
              cut from the interface too. A product that offers five features and
              delivers five is finished. One that offers eight and delivers five
              is not, and it is obvious to everyone you show it to.
            </p>
          </section>

          <section className="about-section">
            <h2>The three rules</h2>
            <ul className="rules">
              {RULES.map(([no, name, body]) => (
                <li key={no} className="rule">
                  <span className="rule-no">{no}</span>
                  <div className="rule-body">
                    <h3 className="rule-name">{name}</h3>
                    <p>{body}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="about-section about-last">
            <h2>The target</h2>
            <p>
              This is a finished build of the same product, on the same scaffold
              you are about to open. Ask it something. Then ask it something the
              policies do not cover, and watch what it does.
            </p>
            <Link href="/" className="about-cta">
              Open the Policy Assistant
            </Link>
          </section>

          <footer className="about-foot">
            <p>
              This page exists on the reference build only, at <code>/about</code>.
              No table’s branch carries it.
            </p>
            <p>
              Aldermere Bank is fictional. Every policy, figure and name in it is
              invented.
            </p>
          </footer>
        </main>
      </div>
    </Shell>
  );
}
