# T1 — <what this delivers, in a few words>

*The epic. One increment, F1 to F8, released in one pull request.*

**Table:** N
**Stage:** 01 shape
**Covers:** REQ-I1 .. REQ-U8   *(the PRD requirement ids this ticket satisfies)*

## What we are building

<Two or three sentences, in your own words. Not copied from the PRD.>

## Who it is for, and the moment they need it

<Who asks the question, and what they are in the middle of when they ask it.
"A relationship manager with a client on the phone" tells you more about the
latency budget than any number will.>

## Why it matters

<What is worse if this does not exist? What do they do today instead?>

## What we are NOT building

*Different from "Out of scope" below. These are things we would not build even
with another day — they are someone else's product. Out of scope is what we cut
for time.*

- <e.g. a general-purpose chatbot. It answers from the corpus or it refuses>

## Acceptance criteria

*Every line is pass or fail. No "properly", "correctly", "well". Someone who
has not read the PRD should be able to check each one.*

- [ ] <criterion>   *(REQ-??)*
- [ ] <criterion>   *(REQ-??)*

## The decisions this rides on

*From `docs/PRD.md` §10. Filled in at stage 02 — left blank here on purpose, so
that a value appearing in the plan without a reason beside it is visible.*

| | Decision | What we chose | Why we chose it |
|---|---|---|---|
| **D0** | embedding model and dimensions | | |
| **D1** | chunk size and overlap | | |
| **D2** | the refusal threshold | | |

## How we will know it worked

*From the success measures in `docs/project-brief.md`.*

- <e.g. S2 — a question the corpus cannot answer is refused, not guessed at>

## Features

*One child ticket each. They carry the tracking; the criteria above stay here.*

| | | |
|---|---|---|
| F1 | [ingest](T1-F1-ingest.md) | `todo` |
| F2 | [retrieve](T1-F2-retrieve.md) | `todo` |
| F3 | [refuse](T1-F3-refuse.md) | `todo` |
| F4 | [generate](T1-F4-generate.md) | `todo` |
| F5 | [ask + UI](T1-F5-ask-and-ui.md) | `todo` |
| F6 | [follow-up](T1-F6-follow-up.md) | `todo` · cuttable |
| F7 | [corpus browser](T1-F7-corpus.md) | `todo` · cuttable |
| F8 | [history](T1-F8-history.md) | `todo` · cuttable |

*Cut from the back — F8, then F7, then F6 — and move what you cut into "Out of
scope" below, with its top-bar action.*

## Out of scope

*What we **cut for time**, with the reason. A feature cut here is a decision and
is read as one — leaving its criteria unticked in the list above instead would
read as a failure. Move them down here.*

- <what we cut, when we cut it, and why>

## Open questions

- <anything we could not answer, and who can>
