# Respaid / AgentCollect — Hiring Challenge

Welcome. This challenge is **language-agnostic** and **plan-first**. We are not testing whether you know
our stack (Laravel + React). We are testing **how you think**: do you plan and ask high-value questions
before you build, and can you reason about a real, open-ended product problem?

> **Use AI tools.** Claude Code, Cursor, Copilot — we expect and want it. We evaluate how you *direct* AI,
> not whether you use it.

## Step 1 — Plan a real bug hunt, on screen (this IS the application, ~5–20 min)

This is the only thing you do to apply. **No 2-hour take-home up front.** Record your screen for up to
**20 minutes** (5 is plenty if you're sharp — no face cam needed) and show us how you'd START:

1. **Open a project in plan mode first** — Claude Code's plan mode, your tool's planning step, or just
   plan in writing. We want to see you plan before you touch code. Planning-first is the signal, not the
   tool.
2. **Plan how you'd automatically catch a UX bug specific to AgentCollect, from our PostHog session
   replays, before any user reports it.** Context: we run PostHog on our **debtor pages** (payment,
   dispute) and our **client dashboard** (case management, reports). A "bug" here is rarely a crash — it's
   a button that does nothing, a control users click 5 times in frustration, a page they abandon. Design
   for the bugs you *can't* predict, not a checklist.
3. **Say what you don't know yet** — the unknowns, where you'd get the "expected behaviour" ground truth,
   which signals you'd start from, and the questions you'd ask us. "I'm not sure, here's how I'd find out"
   beats a confident wrong guess.

You don't build anything in this step. We're judging **how you start** and **how you reason about a real,
open-ended product problem** — the thing a strong engineer nails in 5 minutes and a weak one fakes.

**Format & privacy:** prefer not to narrate aloud? A **silent screen-recording with captions**, or a
**written `PLAN.md` of your start**, is fully accepted — just make your planning-first thinking visible and
tell us which you chose. Keep secrets, customer data, and personal tabs off screen. (No judgment on accent,
delivery, or setup — only on whether you frame the problem before solving it.)

## Step 2 — Build it for real (only if your plan clears Step 1)

If your plan is strong, we hand you **real (masked) session-event traces** and you build the detector you
just planned. Full spec: **[`challenge/ROUND2-PROBLEM.md`](challenge/ROUND2-PROBLEM.md)** — a runnable
detector that ingests session traces and flags broken UX (with a severity + the signal that fired + a
one-line reason), plus a short `ROUND2-PLAN.md`. It must run on traces it hasn't seen, so **no hardcoding**.

Most applications end at Step 1 — a sharp 5-minute plan is worth more to us than a polished submission that
never framed the problem.

## How we score
- **Reasoning** (à la "is this actually broken, or intended?"): you go after the *expected-behaviour source
  of truth*, separate the surfaces (debtor pages vs client dashboard vs marketing), and refuse to trust the
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
