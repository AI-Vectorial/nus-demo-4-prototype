# M04 — delivery plan

**How the three of you run 150 minutes.** The runbook says what happens and when.
This says **who does it, what you say, and what you do with your hands** while
five tables build the same thing at the same time.

Read it with `runbook.md` open beside you. Where they disagree, the runbook wins
on timing and this wins on delivery.

---

# The three of you

| | | |
|---|---|---|
| **Manraj** | front of room, projector | Runs the build **side by side** with the tables. Owns the clock. Is the release manager at both gates |
| **Roamer** | moving, constantly | Never sits. Reads screens over shoulders. Catches the table that is quietly stuck and has not said so |
| **Mentor** | floating, senior | Takes the hard question the roamer cannot answer in thirty seconds. Covers the front of the room when Manraj is at a table |

**The roamer's job is not to help.** It is to *notice*. A table that is stuck
and knows it will raise a hand. The table that costs you the room is the one
confidently building the wrong thing at 1:10, and the only way to find it is to
read their screen at 0:50.

---

# What "side by side" means — and the one rule

You are building the product **at the front, on the projector, at the same time
as they build it at their tables.** Not ahead of them. Not a recording. The same
six stages, the same clock.

This is the right call. A room that has never seen stage 01 done once will spend
twelve of its fifteen minutes working out what a stage *is*.

> ## ⛔ The one rule
>
> **You demonstrate the move. You never project the answer.**
>
> The moment your ten decisions are on the screen, five tables copy them, and
> the module is over — because *defending a decision you did not make* is the
> thing M04 assesses. Your D0 to D9 stay on your laptop, off the projector,
> out of your mouth.

In practice, every stage has the same rhythm:

```
   you, projected        them, at the table         you, projected
  ┌──────────────┐      ┌─────────────────┐       ┌──────────────┐
  │ do the move  │ ───▶ │ do it with THEIR│ ───▶  │ show what it │
  │ ~2-3 min     │      │ content, 10+ min│       │ produced     │
  └──────────────┘      └─────────────────┘       └──────────────┘
      "watch this"         roamer works             "mine looks
                           the floor                 like this.
                                                     yours won't."
```

That last beat matters more than it looks. **Show them your artefact and say it
should not match theirs.** A room that thinks there is a right answer stops
deciding and starts guessing what you want.

---

# Before anyone sits down

Runbook has the checklist. These are the three that are yours alone:

- [ ] **Two windows, not one.** Terminal on the projector, this plan on your
      laptop screen. You will read from one and type in the other
- [ ] **`/about` open in a tab**, on the reference deployment. It is your
      opening visual and you do not have to recite anything from it
- [ ] **Your own Codespace already warm**, dependencies installed, `claude`
      running. A cold start at 0:10 in front of a room is four dead minutes

> **Tell the roamer and mentor the one rule out loud before the room fills.**
> A well-meaning mentor who answers *"what should we set MIN_SCORE to?"* with a
> number has just cut the spine out of stage 02.

---

# 0:00 — Open · *10 min*

### 🎥 Projector: `/about`

| Beat | ~ | What you say |
|---|---|---|
| Where we are | 2 min | M01 built the mental model, M02 the tooling, **M03 you shipped with an agent.** Today is the one where it has to survive a review |
| What we're building | 2 min | Scroll the eight features. *"A policy assistant for a bank that will not make things up"* |
| The six stages | 3 min | Scroll slowly. **Stop on both gates.** *"Twice today, a human says yes or no. I am that human"* |
| What done means | 2 min | Read PRD §12 off the screen. **Cut scope, never a stage** |
| Go | 1 min | `START-HERE.md`, then `pipeline/01-shape.md` |

### 🗣️ The line that sets up the whole session

> *"Your agent is going to be faster than you all morning. Twice, it is going to
> be faster than you in the wrong direction. Those two moments are the module."*

### 👁️ Roamer
Count heads at each table. Note who is driving — **one keyboard per table.** A
table with five laptops open will produce five half-builds and no review.

### ⚠️ Watch for
Nobody reads `START-HERE.md`. **Say the filename twice**, and have the roamer
check all five screens are on it by 0:12.

---

# 0:10 — Stage 01 Shape · *15 min*

### 🎥 Projector: ~3 min, then get off the screen

Paste your shape prompt. Let the agent produce its five-line summary. Then:

> *"Look what it did. It told me what it thinks we're building and asked me to
> correct it — before writing a line. **That is the whole stage.** You are not
> getting requirements from the agent. You are giving them to it, in your words,
> so that later you can say whether they were met."*

**Then stop sharing and let them work.** They have twelve minutes.

### 🗣️ The thing to say before you go quiet

> *"The acceptance criteria have to be in your words. Not because I'm precious
> about it — because at 2:15 I'm going to ask you to read them to me from
> memory, and you cannot read back something you never wrote."*

### 👁️ Roamer — three screens to read

| Seen on screen | Means | Do |
|---|---|---|
| Agent wrote the criteria, team said "yes looks good" | ❌ the stage failed silently | *"Whose words are those?"* Nothing more |
| Criteria that cannot fail — "the system is reliable" | ❌ untestable | *"Show me the test that proves that"* |
| Team arguing about what "refuses" means | ✅ **this is the stage working** | Walk away |

### 🎓 Mentor
Take *"how precise should the criteria be?"* Answer: **precise enough that two
people would agree on pass or fail without talking to each other.**

### ⏱️ Running late?
A table still arguing at 0:24 is doing the right thing in the wrong slot. *"Lock
what you have. You can amend a ticket; you cannot un-ship a build."*

---

# 0:25 — Stage 02 Plan · *20 min* · ⚠️ **THE FIRST GATE**

**This is the most important twenty minutes of the day.** Everything before it is
set-up, everything after is execution.

### 🎥 Projector: ~3 min — the decision interview

Paste the interview prompt. The agent lists ten decisions with options and
trade-offs **and stops.**

> *"Ten decisions. It gave me options and trade-offs and then it waited. It did
> not pick. If yours picks for you — that is a finding, write it down, it's the
> most interesting thing you'll see today."*

### ⛔ Then close your laptop lid, physically

Do it visibly. It is the clearest possible signal that **your answers are not
coming.** You will be asked for them anyway. The answer is always:

> *"I'm not going to tell you, and at 2:15 you'll be glad I didn't."*

### 🗣️ For the table that says "you decide"

> *"Then tell me what you'd regret. If you set the threshold too low it answers
> questions it shouldn't. Too high and it refuses things it knows. Which of
> those two would you rather explain to the bank?"*

**That reframing works every time.** They are not choosing a number, they are
choosing which failure they can live with — and that they can do.

### ⚠️ **The gate — you approve or reject, table by table**

Walk to each table. Mentor covers the clock. **Give yourself ~90 seconds per
table and say it out loud so they feel it.**

| Ask | Looking for |
|---|---|
| *"Why this chunk size?"* | a reason about **their corpus**, not a default |
| *"Why this threshold?"* | that they know what it costs them |
| *"What are you not doing?"* | an actual answer. "Nothing" is a failed plan |

> **Reject one, if one deserves it.** A room where all five pass at first ask
> learns that the gate is theatre. Rejecting with *"come back in three minutes
> with a reason for D2"* costs three minutes and teaches the entire session.

### 🎓 Mentor — holds the front
Watch the clock while Manraj is at tables. **At 0:43, call it** regardless of
where he is. Stage 03 cannot be short.

---

# 0:45 — Stage 03 Build · *60 min*

The long one. **Your job changes completely here: you stop presenting and start
walking.** The projector goes quiet.

### 🎥 Projector: ~2 min, then leave it running

Start your build, let one test go green on the screen, then:

> *"Red, then green, then commit. I'm going to leave my screen up but I'm not
> going to talk about it. Come and look if you want to see where I am."*

**Leave your terminal projected all hour.** A table that is lost finds it easier
to glance at the screen than to raise a hand.

### ⏰ The four moments that matter

| Clock | What you do |
|---|---|
| **0:55** | Roamer confirms **all five tables have F1 running.** A table without ingestion at 0:55 will not finish F5. Mentor goes and sits with them |
| **1:15** | 🗣️ **The mid-point call.** Front of room, loud, 30 seconds |
| **1:30** | Quiet walk. Note which feature each table is on. **This is your 2:15 script** |
| **1:40** | 🗣️ *"Five minutes. Commit what works. Broken code does not go into a review"* |

### 🗣️ The 1:15 mid-point call — say this close to verbatim

> *"Half the build is gone. Decide now, as a table, where you're stopping.
> F6, F7 and F8 are cuttable and I mean that — a table that ships F1 to F5
> clean and tells me what they cut has the better run today. The one thing I
> will not accept is a product built by skipping the review. **Cut scope, never
> a stage.** Say your number out loud to each other now."*

Then **go quiet for a full ten seconds.** Let them actually decide.

### 👁️ Roamer — the four failures, in the order they appear

| Seen | Say |
|---|---|
| Agent added a dependency without asking | *"Did you approve that?"* — it's a stage-03 rule |
| Tests weakened to go green | ⛔ **stop them.** This is the one that cannot pass |
| Nobody has run the app, 45 min in | *"Open localhost:3000. Now."* |
| Watching the agent type, nobody reading | *"What's it building right now?"* If no answer, that table is a passenger |

### 🆘 If a table's Codespace dies
Roamer handles it, Manraj does not leave the front:
1. `./scripts/start.sh` — most things
2. 502 on `*.app.github.dev` → **use the editor preview**, that is the fix
3. Still dead → **new Codespace from `table-N`**, ~3 min, work is committed

---

# 1:45 — Stage 04 Review · *20 min*

### 🎥 Projector: ~3 min — the planted defect

Run pass 1 on `docs/review-example/expense_rules.py` **live.** It finds `> 75`
where the policy says *"£75 or more"*.

> *"One character. Every claim at exactly seventy-five pounds goes through
> without approval, and no test fails, and the code reads fine. **This is what
> five passes are for.** One pass finds the crash. The fifth finds this."*

**This is your best three minutes of the day.** Do not rush it and do not
pre-empt the answer — let the agent find it on screen.

### 🗣️ Then set them off

> *"Same five passes on your own diff. One pass per message — if you ask for all
> five at once you get five shallow ones. Every finding gets a decision written
> down, **including the ones you're not fixing.** 'We know and we accepted it' is
> a professional answer. 'We didn't look' is not."*

### 👁️ Roamer
Teams finding nothing in their own code are not reviewing — they are asking the
agent if its work is good. *"Which pass are you on, and what did it say?"*

### ⚠️ The honest risk here
Tables arrive at 1:45 mid-feature and want to keep building. **Hold the line.**
This stage is M04.4 and it is the one the certificate is about.

---

# 2:05 — Stage 05 Release · *10 min* · ⚠️ **THE SECOND GATE**

### 🎥 Projector: ~2 min

Write the release plan, then the push and the PR, on screen:

```bash
gh pr create --base table-3 --head work/table-3 \
  --title "T1: the policy assistant" --fill
```

> *"Four checks run. **Nothing deploys.** Three hours in and none of this has
> been near a URL. The merge is the deploy, and the merge needs a human."*

### 🗣️ On the rollback — the line that lands

> *"Write the rollback **before** you merge. Not because you'll need it. Because
> writing it afterwards is called an incident report."*

### ⚠️ Branch protection will bite one table
They cannot approve their own PR. **That is deliberate** — say so rather than
apologising for it:

> *"A different person approves. That's not GitHub being awkward, that's the
> control. Find someone at another table."*

---

# 2:15 — Stage 06 Verify · *15 min*

### ⚠️ **You are the release manager. Six questions, table by table.**

~2 minutes each. **Ask all six even when you can see the answer** — the room is
watching the ritual, not the result.

| | |
|---|---|
| 1 | Show me your ticket |
| 2 | Read me your acceptance criteria — **in your words** |
| 3 | Show me the test that was red and is now green |
| 4 | **Which review finding did you accept, and why?** |
| 5 | How do we get this back if it is wrong? |
| 6 | **What did you cut, and does the interface still offer it?** |

All six → **approve → merge → ~90 seconds → live.**

### 🕐 Then wait two minutes before reading `/healthz`

A fresh container indexes the corpus in the background, so for a minute or two
the vector store says *"collection not created yet"* and then flips to the
passage count. **It is a cold start, not a failed build.** Refresh before anyone
gets sent back to their agent.

### 🗣️ Say this when a table shows you a refusal

> *"Watch what it just did. It had a model that would happily have answered that,
> and it refused before it even called it. **That's not the product failing.
> That's the only reason a bank would let it near a staff member.**"*

### 🏆 And say this out loud, in front of everyone

> *"Table 4 cut two features and shipped something that works, with a review
> record and a rollback. **That is the better run today.** If you remember one
> thing from this module, make it that one."*

Otherwise the next cohort hears that eight features was the bar.

### Closing question, to every table

> *"Where did AI help, where did it displace or risk something, and which control
> caught it?"*

---

# If you are behind — cut in this order

**Never the gates, never the review.** In order:

| # | Cut | Costs you |
|---|---|---|
| 1 | Your own projector build after stage 03 | nothing — they have the pattern by then |
| 2 | Gate 1 to **three** tables, mentor takes two | consistency, not substance |
| 3 | Stage 06 to **one question**: *"which finding did you accept?"* | the ritual |
| 4 | F6–F8 room-wide at 1:15 | the demo looks thinner |

> **Nothing above touches the review or the two gates.** If you are so far behind
> that those are in question, run stage 06 for two tables in front of the room
> and let the other three watch. **Three tables seeing a real gate beats five
> tables having a rushed one.**

---

# Record while it is fresh

| | |
|---|---|
| 📊 | Which feature each table reached — **sets the real F-target for cohort 2** |
| ⚠️ | Did any agent decide D0–D9 without asking? Verbatim |
| ⚠️ | Did any table try to skip the review to finish a feature? |
| 💬 | The best answer to the closing question |

---

*M04 · Instructor material · not for participants*
