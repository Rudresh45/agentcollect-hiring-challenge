# ROUND2-PLAN.md — Round 2 Bug Detection Strategy

This document outlines the implementation strategy and architectural details of the runnable Python automated UX bug detector.

---

## 1. Detection Approach

Our detector ingests the JSONL stream chronologically and monitors user session behavior across three layers:

1.  **Explicit Signal Triggers:**
    *   **HTTP Errors (`http_error`):** Tracks page load status codes. Any `$pageview` with a status code $\ge 400$ represents a broken page layout or resource loading error.
    *   **Exceptions (`unhandled_exception`):** Identifies script crashes (`$exception` with `handled: false`).
    *   **Rage Clicks (`rage_click`):** Identifies multiple consecutive rapid clicks on identical UI targets.

2.  **Implicit Behavioral Anomalies (Funnel Abandonment):**
    *   **Friction Abandonment (`funnel_abandonment_after_friction`):** For debtor pages, if a user scrolls deeply (scroll depth $\ge 80\%$) or clicks checkout action buttons but ultimately abandons the page (`converted: false` on `$pageleave`) after triggering disabled elements or dead clicks.

3.  **Process Stalls & UI Hangs (`silent_process_freeze` / `process_stalled`):**
    *   For interactive client dashboard routes, if the user starts a complex process (e.g. clicking "Upload CSV", "Process", or "Export") and remains idle for $>10$ seconds without succeeding page navigation or subsequent actions before exiting.

### Generalization to Unforeseen Bugs
Instead of hardcoding a list of known bug pages, the system looks at generalized behavioral state changes. For example:
*   An error doesn't need to be hardcoded; we look for status codes and exceptions.
*   A button freeze is detected by the delta between a click and succeeding events.
*   A form deadlock is detected by looking for high-intent scrolls and form clicks followed by unsubmitted exits.

---

## 2. How We Judge "Broken"

We separate "expected user paths" from "broken UX flows" using a state-machine model:

1.  **Expected Path:**
    *   *Debtor:* Funnel steps progress linearly. A conversion status of `converted: true` represents success. Handled exceptions (such as card declines) are considered normal user-error inputs unless they result in terminal deadlocks or dead clicks on help options.
    *   *Client:* Dashboard navigation yields status codes $<400$ and does not terminate with unresolved processing actions.

2.  **Broken Path:**
    *   Any route resulting in a `404` status code.
    *   Interactive elements (like the dispute text fields or buttons) containing state properties (`attrs: {"disabled": true}`) that user engagement checks indicate should be open (e.g. the user scrolls down, reads, but is locked out from submitting).
    *   Actions (e.g. Export buttons) that do not result in subsequent state changes, error prompts, or loading pages, causing the user to click repeatedly and leave.

---

## 3. Open Questions

1.  **How are partial API response timeouts represented in the telemetry stream?**
    *   *Why it matters:* If a button click hangs due to a server-side timeout but throws no frontend exception, we must verify if there are custom loading state timers we can track.
    *   *Default assumption:* Timeouts present as long idle durations ($>10s$) after a click followed directly by a `$pageleave`.
    *   *What changes:* If API latencies or specific network logs are tracked, we can directly tag latency-induced aborts versus design-induced dead clicks.

2.  **Should validation-related disabled states be treated differently from runtime-bug disabled states?**
    *   *Why it matters:* A button that is disabled because a user has not filled out a required form field is *correct* behavior, whereas a button that remains disabled due to validation glitches is *broken*.
    *   *Default assumption:* Clicks on disabled buttons are rated as *low* severity if the user makes $<3$ clicks and completes the form. They are rated *high* severity if the user makes $>3$ clicks (rage clicking) or scrolls extensively and abandons.
    *   *What changes:* If input element completion statuses (e.g. form validity state) are available, we can distinguish valid UI locking from a broken deadlock.

3.  **What is the desired alert triage workflow?**
    *   *Why it matters:* If we integrate with Slack or email alerts, we must optimize thresholds to prevent alert fatigue.
    *   *Default assumption:* We export flagged sessions directly as a clean JSONL output file for automated ingestion by an alerting webhook.
    *   *What changes:* If we output to specific queues (e.g. Sentry/PagerDuty), we can map severity labels (`critical`, `high`, `medium`) to different alerting channels.
