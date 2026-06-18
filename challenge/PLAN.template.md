# PLAN.md (commit this BEFORE writing any solution code)

> Delete the prompts below and replace with your own. Keep it tight.

## Architecture
<!-- How would you structure a system that takes a debtor row (name + address + maybe a registration code)
and returns a verified contact? Components, data flow. How does it generalize to thousands of unseen rows
(not a hardcoded path per company)? -->

## Sources & strategy
<!-- What kinds of public sources would you combine and why (registries, DUNS/D&B, the company's own site,
archived pages)? How does each fail, and how do you prove you resolved the RIGHT entity (e.g. matching a
registry record's city to the debtor address) rather than a same-named one? -->

## Quality
<!-- Dedupe. Your confidence_score (0-1) logic. Provenance (every value traceable). How you represent
"cannot verify". False-positive risk. How you avoid hallucinated contacts. -->

## Privacy / compliance
<!-- What you will and will NOT do. Passive verification only — no contacting real people. -->

## Clarifying questions
<!-- For EACH question: (a) why it matters, (b) your default assumption if unanswered, (c) what changes in
your design depending on the answer. 3 sharp > 15 shallow. -->

1. **Question:**
   - Why it matters:
   - Default assumption:
   - What changes if answered:
