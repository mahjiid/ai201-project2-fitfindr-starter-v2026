# Unit 4 execution and evidence checklist

This file tracks work without inventing results. The existing `criteria.md` is the source of truth; **do not change its original targets**.

## Baseline setup

From the same FitFindr checkout and activated virtual environment:

```powershell
python test.py
python mcp_client.py
python app.py ask 'vintage graphic tee under $30' --trace
python app.py ask 'designer ballgown size XXS under $5' --trace
python app.py ask 'denim jacket under $50' --empty-wardrobe --trace
```

For the model-unavailable diagnostic, temporarily substitute an invalid key in the local `.env` (never commit that file), run **a new query**, verify the user-facing message, and restore the real key. Do not paste the key into any logs.

## Before evaluation

```powershell
python run_eval.py --label before
```

This performs five tries for each numbered criterion and also a separate empty-wardrobe diagnostic. Caching is disabled by `run_eval.py`.

**Scoring rule for each attempt:**

1. Matching query: `session.error is None`, selected item and outfit and fit card are non-empty, and all three tool names appear in the trace, including search via MCP.
2. Impossible query: `session.error` gives actionable guidance; `outfit_suggestion` and `fit_card` remain `None`, and neither downstream tool occurs in the trace.
3. State: `session.selected_item.id` equals the `new_item.id` passed to `suggest_outfit`. Check using an instrumented input/trace, not just comparing text in the final card.
4. Fit card: two through four sentences inclusive; exact selected listing title, price, and platform are present; caption describes an identifiable styling vibe.
5. Price ceiling: **every** dictionary in `session.search_results` has price less than or equal to the parsed `max_price` (not just the selected first listing).

For criteria 1, 3 and 4, at least 4/5 passes means MET. Criteria 2 and 5 require 5/5. Document failures with the tool or loop step and precise mechanism. Empty wardrobe is a required *diagnostic*, not a substitute for one of the five scored criteria.

## Improvement and after evaluation

Only after reading genuine baseline output, choose **one** diagnosed code change. Then:

```powershell
python run_eval.py --label after
```

Score the same criteria the same way. Paste both actual runs, sample outputs, failure messages, full trace, verdicts, and remaining failures into README.md. Never write a PASS for a run that was not executed.

## Evidence status

- [x] Existing criteria and original history preserved
- [x] MCP wrapper `search_listings` registered and used by the agent (code inspection)
- [x] Five numbered evaluation scenarios configured
- [x] Loop instrumentation and user-facing MCP/model-error handlers committed
- [ ] Live MCP interoperability check
- [ ] Three intentional failure demonstrations
- [ ] Recorded full happy-path and short-path traces
- [ ] Five real baseline attempts for each criterion
- [ ] One targeted improvement selected from the baseline diagnosis
- [ ] Five real post-fix attempts for each criterion
- [ ] Before-and-after README evidence and final verdicts

Note: The repository contains code changes but this checklist does **not** assert the code ran on the learner's computer.
