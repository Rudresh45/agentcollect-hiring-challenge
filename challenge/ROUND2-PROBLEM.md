# Round 2 — Catch the bug before the user reports it (plan-first, async, no live call)

> **Round 2 is released to you only after you clear Round 1.** If you're reading this without an explicit
> go-ahead from us, finish [Round 1](PROBLEM.md) first.

AgentCollect is AI debt collection. Two communities use our web app:
- **Debtors** — a payment page and a dispute page.
- **Clients / users** — a dashboard (case management, imports, reports).

We record every session as a screen replay. Today we only find UX bugs when someone complains — too late.

## Your task
Design a system that **flags** broken UX from the replays **before** a user reports it. **Flagging only,
not fixing.**

Below are **2 illustrative replays** — one with an obvious error, one subtler. **They are NOT
exhaustive: the real product has bugs you cannot predict in advance.** Don't solve "these two" — design
for the ones you'll never see coming.

### Replay A
> A client user logs into the dashboard and clicks **"Recovery report"** in the left nav. The page goes
> to a blank screen reading **"404 — Page not found"** with a broken header. The user clicks the link 3
> more times, waits a few seconds, navigates back to the dashboard home, and the session ends. No report
> ever loads.

### Replay B
> A debtor opens the **dispute page** for an invoice, reads it, scrolls to the bottom, and reaches the
> **"Reply / Submit dispute"** button — which is rendered **greyed-out and disabled.** They click it 5
> times (nothing happens), click the text field again, re-read the page, and **close the tab without
> submitting.** No error message is shown. Nothing visibly "crashed"; the page looked complete.

## The data — session event traces

So this isn't just an essay, we give you **8 synthetic session event traces** in
[`data/session_traces.jsonl`](data/session_traces.jsonl) — one JSON object per line, each a session with
an ordered `events` array (`$pageview`, `$autocapture` clicks with element/state, `$rageclick`,
`$pageleave`, `$exception`, etc.), mirroring the shape PostHog session-replay exports. The two replays
above (A and B) are among them. The rest are a mix of healthy sessions and other anomalies. **We also hold
back additional traces you won't see, and we'll run your detector on them.**

## Deliver
- A **runnable detector** that ingests `session_traces.jsonl` and outputs, per session: a
  `flagged` boolean, a `severity` or score, the `signal(s)` that fired, and a one-line `reason`. It must
  run on traces it hasn't seen (we'll feed it the held-back ones) — so **no hardcoding the 8 sessions.**
- A **`ROUND2-PLAN.md`**: your detection approach, why your signals generalize to unforeseen bugs, and the
  open questions you'd need answered.
- **You may ask clarifying questions — high-signal questions may unlock additional context.** If no one
  answers in time, state your assumptions and proceed.

> The traces here are **synthetic and approved for AI use.** In production these are real debtor / payment
> / dispute sessions, so in your PLAN note how you'd handle PII: masking, not shipping raw replay data to a
> third-party LLM, retention limits. We read that as a signal.

We score your detector's output on the hidden traces (does it catch the obvious AND the subtle without
drowning in false positives?) **and** the reasoning in your PLAN. We're looking at how you decide "what is
broken?" when nothing literally crashes, and how your detector generalizes to bugs neither you nor we have
seen yet.
