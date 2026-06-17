# Respaid / AgentCollect — Hiring Challenge

Welcome. This challenge is **language-agnostic** and **plan-first**. We are not testing whether you know
our stack (Laravel + React). We are testing **how you think**: do you plan and ask high-value questions
before you build, and can you reach a result an off-the-shelf tool can't?

> **Use AI tools.** Claude Code, Cursor, Copilot — we expect and want it. We evaluate how you *direct* AI,
> not whether you use it.

## First gate — show how you START (required, reviewed first)

Before we score anything else, we look at **how you begin the project**. Include a short recording
(**≤20 min**) of your first 20 minutes:

1. **Plan first, before implementation** — use your tool's planning/plan mode if it has one; if not, plan
   in writing. The signal is planning-first, not which tool you use.
2. **Walk through your approach** — what the task really is, what's unknown, and how you'd find out before
   coding. Thinking aloud beats a polished script.
3. **Say what you don't know yet** — "I'm not sure, here's how I'd find out" scores higher than a
   confident wrong guess.

Prefer not to talk on camera? A **silent screen-recording with captions**, or a **written `PLAN.md`
walkthrough of your start**, is fully accepted — just make your planning-first thinking visible, and tell
us which format you chose. Keep secrets, customer data, and personal tabs off screen.

We review this first; if it doesn't show planning-first thinking before coding, we won't advance the
application, regardless of how strong the rest is. (No judgment on accent, delivery, or setup — only on
whether you frame the problem before solving it.)

## Two rounds

This is a **two-round funnel.** Do Round 1 first; Round 2 is released only to candidates who clear it.

### Round 1 — Find the contact nobody else can find (start here)
Everything is in **[`challenge/PROBLEM.md`](challenge/PROBLEM.md)**. You get **5 hand-picked HARD debtor
rows** ([`challenge/data/hard_cases.csv`](challenge/data/hard_cases.csv)) — tiny companies, no web
presence, name collisions, registration codes. For each, find the best reachable contact **and prove it**.
**One impossible row solved and proven beats five easy guesses.** Plan-first (commit `PLAN.md` before any
code), passive verification only, and a required "what I tried that was clever" page where every claimed
trick carries proof.

### Round 2 — Catch the bug before the user reports it (released after Round 1)
[`challenge/ROUND2-PROBLEM.md`](challenge/ROUND2-PROBLEM.md). Design a system that flags broken UX from
session replays before a user complains. Don't open it until we give you the go-ahead.

## How to submit
- Your own repo (private is fine — add **`johnbanr`** as a collaborator), with `PLAN.md` committed
  **first** (git timestamps are part of the signal), then your slice + the 5 enriched rows + the
  clever-tricks page + `ABOUT.md`.
- **Do not squash or rewrite commits** before submitting — we read the commit timeline.
- **The "how you START" recording/walkthrough from the first gate above** (required, reviewed first).
- Process evidence for the rest: a clean commit timeline is enough, async, no webcam.
- An `ABOUT.md` at the repo root — template: [`ABOUT.template.md`](ABOUT.template.md).

## How we score
See the rubric in [`challenge/PROBLEM.md`](challenge/PROBLEM.md#how-we-score). In short: **reasoning**
(resolve the real entity, refuse the surface, go to the source of truth) and **creativity** are the top
axes; sharp clarifying questions are high; no hallucinated contacts, debtor-not-creditor, and a
**generalizing** (not hardcoded) approach are hard gates.

## Conventions
[`CLAUDE.md`](CLAUDE.md) shows how we work. You don't need to follow our Laravel conventions for this
language-agnostic challenge, but skim it — how we think about conventions matters.

---

### Legacy (optional, ignore unless asked)
The `tickets/` folder + the Laravel sandbox app are from a previous stack-specific challenge. The two-round
funnel above is the current challenge. Do not do the legacy tickets.
