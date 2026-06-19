# Automated UX Bug Detector — AgentCollect

This repository contains my solution to the AgentCollect / Respaid Hiring Challenge. It includes a fully functional, zero-dependency Python automated UX Bug Detector that analyzes PostHog session replay logs to flag silent and explicit user experience bugs.

---

## 🚀 How to Run

### Prerequisite
* Python 3.x (no external libraries are required)

### 1. Execute the Detector
Run the detector script on a session trace file (JSONL format):
```bash
python detector.py challenge/data/session_traces.jsonl
```

#### Output Schema
For each session input, the script outputs a single JSON line containing:
* `session_id`: Unique identifier of the session.
* `flagged`: Boolean indicating if anomalous UX friction was detected (`true` / `false`).
* `severity`: Severity classification (`low`, `medium`, `high`, `critical`).
* `signals`: List of specific trigger signals encountered (e.g. `http_error`, `rage_click`, `unhandled_exception`, `disabled_ui_click`, `funnel_abandonment_after_friction`, `silent_process_freeze`).
* `reason`: Descriptive explanation detailing the anomalies.

### 2. Run the Unit Test Suite
To verify the engine correctness and ensure regression safety:
```bash
python -m unittest test_detector.py
```

---

## 🛠️ Architecture and Heuristics

The detector works by evaluating session events chronologically and processing them across three dimensions:

1.  **Explicit Errors:**
    *   **HTTP Status Triggers (`http_error`):** Flags `$pageview` events returning status code $\ge 400$ (e.g. `404 - Page not found`).
    *   **Script Exceptions (`unhandled_exception`):** Flags unhandled JS client crashes.

2.  **User Frustration Signals:**
    *   **Rage Clicks (`rage_click`):** Flags multiple rapid consecutive clicks on identical UI targets (higher severity on actionable targets like buttons/links).
    *   **Dead Clicks (`dead_click`):** Flags clicks that did not result in standard page loads or transitions.

3.  **Behavioral Funnel Stalls:**
    *   **Disabled Form Deadlocks (`disabled_ui_click`):** Scans for clicks on buttons with `attrs: {"disabled": true}` followed by abandonment.
    *   **Debtor Funnel Abandonment (`funnel_abandonment_after_friction`):** Evaluates if a debtor reached advanced steps, scrolled to 100%, but ultimately exited (`converted: false`) after encountering dead ends or disabled components.
    *   **Silent Process Hangs (`silent_process_freeze`):** Detects when a client initiates a long-running dashboard process (like exports or imports) but exits the session after prolonged idle periods with zero progress.

---

## 📂 Repository Layout

*   [detector.py](file:///c:/Users/Rudresh_N_G/Desktop/challeange/detector.py): Main Python heuristics classification script.
*   [test_detector.py](file:///c:/Users/Rudresh_N_G/Desktop/challeange/test_detector.py): Automated unit tests covering all edge case patterns.
*   [PLAN.md](file:///c:/Users/Rudresh_N_G/Desktop/challeange/PLAN.md): Round 1 PostHog detector design plan.
*   [ROUND2-PLAN.md](file:///c:/Users/Rudresh_N_G/Desktop/challeange/ROUND2-PLAN.md): Round 2 implementation strategy.
*   [ABOUT.md](file:///c:/Users/Rudresh_N_G/Desktop/challeange/ABOUT.md): Candidate profile and AI engineering patterns.
*   [challenge/data/session_traces.jsonl](file:///c:/Users/Rudresh_N_G/Desktop/challeange/challenge/data/session_traces.jsonl): Synthetic session logs used for verification.
