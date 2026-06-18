# Respaid / AgentCollect — Hiring Challenge

Welcome. This challenge is **language-agnostic** and **plan-first**. We are not testing whether you know
our stack (Laravel + React). We are testing **how you think**: do you plan and ask high-value questions
before you build, and can you reason about a real, open-ended product problem?

> **Use AI tools.** Claude Code, Cursor, Copilot — we expect and want it. We evaluate how you *direct* AI,
> not whether you use it.

## Step 1 — Plan a real bug hunt (this IS the application, ~5 minutes)

**The whole application is ~5 minutes** (10 max). We believe a strong engineer lays the foundations in
five. Send us back **two things**:

**A. A GitHub repo** (private is fine — add **`johnbanr`** as a collaborator) containing a **`PLAN.md`
committed first** (the git timestamp is part of the signal). Your `PLAN.md` plans **how you'd
automatically catch a UX bug specific to AgentCollect, from our PostHog session replays, before any user
reports it.** Context: we run PostHog on our **debtor pages** (payment, dispute) and our **client
dashboard** (case management, reports). A "bug" here is rarely a crash — it's a button that does nothing, a
control users click 5 times in frustration, a page they abandon. Design for the bugs you *can't* predict,
not a checklist. Say what you **don't know yet** (the unknowns, where you'd get the "expected behaviour"
ground truth, which signals you'd start from, the questions you'd ask us).

**B. A short screen recording (≤5 min, 10 max — no face cam)** of how you **START**: open a project in
**plan mode first** (Claude Code's plan mode, your tool's planning step, or planning in writing) and talk
(or caption) your way through the plan above. We want to see you **plan before you touch code** — that's
the whole signal. Prefer not to narrate? Silent + captions, or just the `PLAN.md`, is fully accepted; tell
us which you chose. Keep secrets, customer data, and personal tabs off screen. (No judgment on accent,
delivery, or setup — only on whether you frame the problem before solving it.)

You don't build anything in Step 1. We're judging **how you start** and **how you reason about a real,
open-ended product problem** — the thing a strong engineer nails in five minutes and a weak one fakes.

### How to submit (2 links, that's it)
1. **Your GitHub repo** with `PLAN.md` committed first — add **`johnbanr`** as a collaborator (private is fine).
2. **Your screen-recording link** (Loom / YouTube-unlisted / Drive — ≤5 min).

Reply to our email with those two links. If you found this repo on your own, email **j@agentcollect.com**
with the two links. No cover letter, no forms. We reply to every complete submission.

## Step 2 — Build it for real (only if your plan clears Step 1)

If your plan is strong, we hand you **real (masked) session-event traces** and you build the detector you
just planned. Full spec: **[`challenge/ROUND2-PROBLEM.md`](challenge/ROUND2-PROBLEM.md)** — a runnable
detector that flags broken UX (severity + the signal that fired + a one-line reason), plus a short
`ROUND2-PLAN.md`. It must run on traces it hasn't seen, so **no hardcoding**.

Most applications end at Step 1 — a sharp 5-minute plan is worth more to us than a polished submission that
never framed the problem.

## How we score
- **Reasoning** ("is this actually broken, or intended?"): you go after the *expected-behaviour source of
  truth*, separate the surfaces (debtor pages vs client dashboard vs marketing), and refuse to trust the
  raw signal alone. **Highest.**
- **Generalization (hard gate):** a signal model that catches bugs you've never seen (rage/dead clicks,
  abandon-after-interaction, repeated identical action) — **not** a hardcoded list of known bugs.
- **The right questions:** sharp clarifying questions, each with why / your default / what changes.
- **Privacy reflex:** debtor payment/dispute replays are real PII — masking, no raw replay to a third-party
  LLM, retention limits.

## Conventions
[`CLAUDE.md`](CLAUDE.md) shows how we work. You don't need to follow our Laravel conventions for this
language-agnostic challenge, but skim it — how we think about conventions matters.

---

### Optional / legacy (ignore unless we ask)
A previous version used a **contact-finder** take-home ([`challenge/PROBLEM.md`](challenge/PROBLEM.md)) and
a Laravel `tickets/` sandbox. They're kept for reference only — the Step 1 → Step 2 flow above is the
current challenge. Don't do the legacy tasks unless we point you to them.
