# Automated UX Bug Detector — AgentCollect

A zero-dependency Python detector that ingests PostHog session replay logs and flags
silent and explicit UX bugs — **before users report them**.

---

## 🚀 How to Run

### Prerequisite
* Python 3.x (no external libraries required)

### 1. Run the Detector
```bash
python detector.py challenge/data/session_traces.jsonl
```

#### Output schema (one JSON line per session)
| Field | Type | Description |
|---|---|---|
| `session_id` | string | Session identifier |
| `flagged` | bool | `true` if anomalous UX friction was detected |
| `severity` | string | `low` / `medium` / `high` / `critical` |
| `signals` | list | Triggered signal names |
| `reason` | string | Human-readable explanation |

#### Signal catalogue
| Signal | What it means |
|---|---|
| `http_error` | `$pageview` returned status ≥ 400 |
| `unhandled_exception` | Uncaught JS crash (`$exception`, `handled: false`) |
| `rage_click` | Multiple rapid clicks on the same target |
| `dead_click` | Click produced no state change |
| `dead_help_link` | Dead click on a help/support element — user sought an escape route that doesn't exist |
| `disabled_ui_click` | Click on an element with `attrs.disabled = true` |
| `funnel_abandonment_after_friction` | Debtor exited without converting *because of UI obstacles* (not a card decline) |
| `funnel_abandonment` | Debtor exited without converting, no obvious friction captured |
| `silent_process_freeze` | Action button click → no feedback for ≥10s → rage-click and exit |
| `process_stalled` | Action button click → no follow-up before session exit (no rage-click) |
| `repeated_identical_action` | Same action button clicked twice with no response between |

### 2. Run the Test Suite
```bash
python -m unittest test_detector.py -v
```
16 tests covering healthy sessions, all signal types, reasoning gates, and generalization.

---

## 🛠 Architecture

### Design principle: Behavioural invariants, not bug lists

The detector models **expected behavioural invariants per persona surface** and flags deviations.
No hardcoded page names, button labels, or element selectors. A bug we've never seen before
— on a page that didn't exist yesterday — will be caught if it violates the same structural invariants.

```
PostHog JSONL
      │
      ▼
┌─────────────────────────────┐
│  Chronological event scan   │  ← per-event state machine
└─────────────┬───────────────┘
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
 Explicit  Frustration  Session
 failures  signals     context
 (4xx/5xx, (rage/dead/ (funnel,
 crashes)  disabled)   stalls)
              │
              ▼
┌─────────────────────────────┐
│  Reasoning gate             │  ← "Is this actually broken, or intended?"
│  • Card decline → expected  │
│  • Disabled submit → bug    │
│  • Dead help link → bug     │
└─────────────┬───────────────┘
              ▼
        Severity score → JSONL output
```

### Reasoning gate (key differentiator)

The same raw signals can mean different things. Before escalating severity, we ask:
*"What is the most plausible root cause?"*

| Scenario | Signals present | Verdict |
|---|---|---|
| Card declined, user retries, leaves | handled `$exception`, `converted: false` | ❌ Not a bug — expected payment failure |
| Disabled submit, rage-clicks, leaves | `disabled_ui_click`, `rage_click`, `converted: false` | ✅ Bug — UI blocked submission |
| Card declined + dead help link | handled `$exception`, `dead_click` on help | ✅ `dead_help_link` flagged; funnel abandonment NOT blamed on UI |
| Action button → silent hang → rage-exit | `$rageclick`, no page change, ≥10s idle | ✅ `silent_process_freeze` — works for any button text |

### Generalization

| Invariant | Generalizes to... |
|---|---|
| Any `$pageview` status ≥ 400 | Any future 4xx/5xx page, any path |
| Any unhandled `$exception` | Any new JS crash |
| Any `button` → no feedback ≥ 10s | Any new action button that silently hangs |
| Same button clicked twice, no response | Any new workflow button that no-ops |
| Any help-element dead click | Any help link, chat button, FAQ anchor |

---

## 📂 Repository Layout

* [detector.py](detector.py) — Core heuristic engine
* [test_detector.py](test_detector.py) — 16-test suite (healthy, signals, reasoning gates, generalization)
* [ROUND2-PLAN.md](ROUND2-PLAN.md) — Detection strategy, reasoning rationale, open questions
* [PLAN.md](PLAN.md) — Round 1 architectural design
* [ABOUT.md](ABOUT.md) — Candidate profile
* [challenge/data/session_traces.jsonl](challenge/data/session_traces.jsonl) — Synthetic session logs
