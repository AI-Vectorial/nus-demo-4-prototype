# D7 — How citations are grouped

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked

## What we chose

Option B — the API keeps one citation per section; the UI groups them under document
headers.

Each citation record stays precise: document, version, status, section, score and link.
The UI shows, for example, *Travel and Expense Policy v3.1 — Current* once, with §4.2 and
§5.1 underneath.

**What counts as a citation:** every passage that survives the threshold and is given to
the model. Not just the passages the model says it used.

## Why

Giving the model's passages is deterministic and auditable. Asking the model to report
which passages it "used" adds another unreliable layer.

## Options we did not choose

- A — a flat list per section: precise but repetitive.
- C — one citation per document: breaks the §5 contract and makes "open the cited
  section" ambiguous.

## Consequences

Affects C10, C11, C12, C18 and the citation UI. No change to the §5 contract.

## Careful about

Grouping is presentation only. Each citation keeps its section-level identity.
