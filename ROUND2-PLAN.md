# ROUND2-PLAN.md — Detection Strategy & Design Rationale

This document explains the detection approach for the automated UX bug detector, why the
signals generalize to bugs we've never seen, and the open questions we'd want answered
before productionizing.

---

## 1. Core Design Principle: Behavioural Invariants, Not Bug Lists

We do **not** maintain a list of known-broken pages, hardcoded button labels, or specific
error messages. Instead, we define **expected behavioural invariants per persona surface**
and flag sessions where reality deviates from expectation. This means the detector catches
bugs we've never seen — including ones that haven't happened yet.

Two surfaces, two trust models:

| Surface | Expected shape | Broken shape |
|---|---|---|
| **Debtor pages** (`/pay/*`, `/dispute/*`) | Linear funnel → `converted: true` | High-intent activity + UI obstacle + exit without conversion |
| **Client dashboard** (`/dashboard`, `/reports`, `/imports`, etc.) | Exploratory nav, status codes < 400, actions produce page changes | 4xx/5xx pages, actions that hang without feedback, exceptions |

---

## 2. Detection Layers

### Layer 1: Explicit Failures
Always bugs; no ambiguity needed.

- **`http_error`** — any `$pageview` with `status >= 400`. Generalized: any path, any status ≥ 400.
- **`unhandled_exception`** — `$exception` with `handled: false`. Generalized: any uncaught JS error.

### Layer 2: User Frustration Signals (with Reasoning Gate)
Raw signals alone can be misleading. We always ask *"could this be intended?"* before
escalating severity.

- **`rage_click`** — multiple rapid clicks on the same target. Higher severity on action
  buttons (structural check: element = `button`/`input[type=submit]`, not navigational text)
  than on nav links.
- **`dead_click`** / **`dead_help_link`** — click produced no state change. A dead click on a
  *help/support* element is especially severe: the user is actively stuck and seeking
  an escape route that doesn't exist.
- **`disabled_ui_click`** — click on an element with `attrs.disabled = true`.

### Layer 3: Behavioural Heuristics (Generalised, Context-Aware)

#### Debtor Funnel Abandonment (`funnel_abandonment_after_friction`)
**Invariant:** A debtor who has demonstrated high intent (scrolled ≥ 80%, or clicked action
buttons) should be able to complete their transaction.

**Reasoning gate — the key differentiator:**
We distinguish three cases that produce identical raw signals but mean different things:

1. **Card declined → exit** — *Expected.* The user's card failed; the UI worked correctly.
   We do NOT flag `funnel_abandonment_after_friction`. The handled `$exception` (Stripe)
   is the exit cause, not a UI bug.

2. **Disabled submit + exit** — *Bug.* The button was locked when it shouldn't be (user
   had read and scrolled the full form). Flagged as `funnel_abandonment_after_friction`.

3. **Card declined + dead help link → exit** — *Mixed.* The decline is expected; the dead
   help link is a real UX bug. We flag `dead_help_link` but NOT
   `funnel_abandonment_after_friction` — conflating them would misidentify the root cause.

#### Silent Process Freeze (`silent_process_freeze`)
**Invariant:** Any action button click should produce visible feedback (page change, success
message, error state) within a reasonable window.

**Generalized:** We do not check for "Export" or "Process" specifically. Any `button` element
click that is followed by ≥ 10 seconds of inactivity with no subsequent pageview or click,
ending in session exit + rage clicking, is a freeze. A future "Reconcile accounts" button
with the same behavioural pattern would be caught automatically.

#### Repeated Identical Action Without Response (`repeated_identical_action`)
**Invariant:** If a user clicks the same action button twice and the UI produced *no response*
(no page change, no exception), the action is silently broken.

**Reasoning gate:** A payment retry after a card decline IS a response (the `$exception`
fires, the user sees an error, retries deliberately). We do NOT flag that as broken. We only
flag when *truly* nothing happened between the two clicks.

---

## 3. Why This Generalizes to Unforeseen Bugs

| Principle | Example of a bug we've never seen |
|---|---|
| **Status code invariant** | A new `/analytics/cashflow` page returns 503 → caught immediately |
| **Structural button check** | A new "Reconcile accounts" button hangs → silent_process_freeze fires |
| **High-intent + blocked exit** | New "Approve settlement" button is disabled → funnel_abandonment_after_friction fires |
| **Repeated action without feedback** | Any new workflow button that silently no-ops → repeated_identical_action fires |
| **Dead help elements** | Any help link, chat button, or FAQ anchor that dead-clicks → dead_help_link fires |

We never query "did the Export button break?" — we ask "did any action button the user
expected to work produce zero observable outcome?"

---

## 4. Privacy & Compliance

Because debtor sessions contain sensitive payment and dispute data, privacy is not an
afterthought:

- **PostHog-level masking:** Enforce `ph-no-capture` on all form inputs and mask text on
  payment fields. No card numbers, amounts, or debtor names should appear in `text` attributes.
- **Server-side scrubbing:** Before any log storage, redact values matching email, phone,
  or card-number regex patterns from `text` and `attrs` fields.
- **No raw replay to external LLMs:** Analysis is fully deterministic Python — we never
  send raw event arrays or session content to a third-party AI service. Only derived
  metadata (session_id, signal names, severity) ever leaves this process.
- **Retention window:** Raw event logs: 14-day TTL. Flagged session metadata (session_id +
  signal + severity): retained for trend analysis. Full replay: only accessible to
  authorized engineers via PostHog RBAC, never downloaded for external processing.
- **Anonymization for testing:** Test fixtures use synthetic traces (as here). Any
  production-data sampling for test coverage must be anonymized before use.

---

## 5. Open Questions

### Q1 — Do we have custom telemetry for API call state?
**Why it matters:** If a "Process" click fires a background job via XHR, the frontend may
show a spinner but PostHog captures nothing between click and eventual timeout. Our
`silent_process_freeze` heuristic works, but with better network timing data we could
distinguish "API hung" from "UI never sent the request."

**Default assumption:** We only have PostHog auto-captured events. We model the idle gap
(≥ 10s inactivity after action click) as a proxy for a stall.

**What changes:** If `$custom_event` or fetch-timing events are available, we can directly
correlate click → response latency and set tighter thresholds.

---

### Q2 — How do we distinguish "disabled by design" from "disabled by bug"?
**Why it matters:** A submit button that is correctly disabled until required fields are
filled is expected UX. A submit button that stays disabled even after the user has filled
everything (bug) looks identical in the event stream if we don't have form-validity state.

**Default assumption:** We require ≥ 1 disabled-click plus either rage-clicking or high
scroll depth + session exit to escalate. A single disabled-click gets low severity.

**What changes:** If PostHog captures `form.checkValidity()` state or field-fill counts as
custom properties on the click event, we can precisely detect the "form complete but button
still locked" deadlock without requiring the rage-click proxy.

---

### Q3 — What is the desired triage and alerting workflow?
**Why it matters:** If we emit every `high`-severity session to Slack, teams will mute the
channel within a week. Alert volume needs to be right-sized to the team's triage capacity.

**Default assumption:** We output clean JSONL per session, suitable for ingestion by a
webhook or Sentry intake. Separate `critical` (page-down level) from `high` (friction bug)
from `medium` (soft signal, log only).

**What changes:** If we route to PagerDuty, `critical` → immediate page; `high` → daily
digest; `medium` → weekly trend report. Threshold tuning should be based on false-positive
rate measured against a labelled sample of known-clean sessions.
