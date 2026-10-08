# D6 — When two current policies conflict

**Decided:** 2026-10-08, table 3, stage 02 decision interview
**Status:** locked

## What we chose

Option A — surface both and name the conflict. Do not resolve it.

For Q10 the answer communicates that:

- Outsourcing v1.8 §6.4 requires destruction within five years of termination
- Records Retention v4.0 §4.1 requires retention for seven years from the end of the
  relationship
- these requirements conflict
- the policy says to escalate to Group Legal and Group Operational Risk jointly

## Why

The software has no authority to decide which policy wins. B would invent a governance
rule. C is safer, but hides legitimate policy evidence and conflicts with C4, which
requires Q10 to get a grounded answer.

## Consequences

D3 must leave room for both documents. The generation prompt needs explicit
conflict-handling instructions. D7 must keep both citations.

## Careful about

Don't rely only on the model noticing the conflict. The team wants a criterion that Q10
cites both conflicting sections and does not present either as authoritative.
