# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are implemented. Unit 4 verifies the MCP search tool, failure handling,
> five acceptance criteria, traced execution, and measured before/after improvement.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr takes a natural-language request for a thrift item, such as a vintage graphic tee under a certain price, and searches the local listings dataset for matching items. It chooses the best result, carries that selected listing through session state, and uses the user's saved wardrobe to suggest one or two outfits. It then turns the selected item and outfit suggestion into a short social-style fit card. If the search returns no matches, the agent stops before calling the later tools and tells the user what they can change in the request.

---

## Tool Inventory

### `search_listings`

- **What it does:** Searches the local listings dataset for items that match the requested description, with optional size and maximum-price filters.
- **Inputs:** `description` (str), `size` (str | None), `max_price` (float | None). Size matching is case-insensitive; slash-separated clothing sizes may match either component, while numeric shoe sizes must match the requested numeric size rather than by substring.
- **Returns:** A list of listing dictionaries ordered by keyword-overlap score, best match first, limited to `config.SEARCH_RESULT_LIMIT`. Each dictionary contains `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
- **When it has nothing:** Returns an empty list `[]`; it does not return `None` and does not raise just because there are no matches.

### `suggest_outfit`

- **What it does:** Uses the selected thrift listing and the user's wardrobe to generate one or two practical outfit ideas.
- **Inputs:** `new_item` (dict) containing one listing, and `wardrobe` (dict) containing an `items` list of saved wardrobe pieces.
- **Returns:** A non-empty string with outfit suggestions. When wardrobe items exist, the response should name pieces the user already owns.
- **When it has nothing:** If `wardrobe["items"]` is empty, returns general styling advice for the selected item instead of failing or returning an empty string.

### `create_fit_card`

- **What it does:** Turns the selected item and outfit suggestion into a short social-style caption for the thrift find.
- **Inputs:** `outfit` (str) and `new_item` (dict).
- **Returns:** A non-empty two-to-four sentence caption that mentions the item, its price, its platform, and the overall styling vibe.
- **When it has nothing:** If `outfit` is empty or whitespace, returns a descriptive fallback message rather than raising an exception.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, store a useful message in `session["error"]` telling the user to broaden the description, change the size, or raise the budget, then return immediately. Otherwise, select the first search result and continue to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex and string cleanup: extract an optional price ceiling from phrases such as `under $30`, extract an optional size from phrases such as `size M`, and use the remaining words as the search description.

**What moves through the session:** `query` → `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. If search returns nothing, `error` is set and the later fields remain unchanged.

---

## Sample Run

**One full query**

```text
$ python app.py ask 'vintage graphic tee under $30'

Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

Outfit:   ### Outfit 1: Y2K Streetwear Contrast

Pair the tight, graphic Y2K baby tee with relaxed denim for a classic early-2000s silhouette.

* Top: Y2K Baby Tee — Butterfly Print
* Bottoms: Baggy straight-leg jeans, dark wash
* Outerwear: Vintage black denim jacket
* Shoes: Chunky white sneakers
* Accessories: Black crossbody bag

### Outfit 2: Retro Casual Prep

Balance the pastel butterfly print against neutral earth tones for an easy, everyday look.

* Top: Y2K Baby Tee — Butterfly Print
* Bottoms: Wide-leg khaki trousers
* Accessories: Brown leather belt, Black crossbody bag
* Shoes: Chunky white sneakers

Fit card: Channel early-2000s streetwear vibes by styling this Y2K Baby Tee with baggy dark wash jeans and chunky white sneakers. Grab this vintage graphic piece on depop for just $18.00.

2 model calls this session, 700 prompt + 226 output tokens
```

**The three tools, tested one at a time**

```text
$ python -c "from tools import search_listings; print([(x['title'], x['price']) for x in search_listings('graphic tee', max_price=30)])"
[('Y2K Baby Tee — Butterfly Print', 18.0), ('Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('Mesh Long-Sleeve Top — Black', 15.0), ('Vintage Band Tee — Faded Grey', 19.0), ('Low-Rise Cargo Pants — Khaki', 27.0), ('Vintage Graphic Hoodie — Faded Black', 26.0)]
```

```text
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()).replace(chr(10), ' '))"
### Outfit: Vintage Streetwear Layer  * Thrift Item: Vintage Levi's 501 Jeans — Medium Wash * Top: White ribbed tank top * Outerwear: Vintage black denim jacket * Shoes: Chunky white sneakers * Accessories: Black crossbody bag  Why it works: The fitted white tank balances the straight-leg vintage denim, while the slightly cropped black denim jacket adds a cool double-denim contrast without overwhelming the frame. Finished with chunky sneakers and a minimal crossbody for an effortless, everyday streetwear look.
```

```text
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]).replace(chr(10), ' '))"
Grab these classic Vintage Levi's 501 Jeans in a timeless medium wash for just $38.00 on depop. Channel effortless streetwear energy by pairing them with crisp white sneakers for an instantly cool, everyday look. Add this essential denim staple to your rotation today!
```

**Empty-search branch**

```text
$ python app.py ask 'designer ballgown size XXS under $5'

I couldn't find a matching listing. Try broadening the description, changing the size, or raising the maximum price.

0 model calls this session
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* I asked AI to review the FitFindr tool requirements and help turn them into precise tool specifications before implementation.
- *What came back:* It proposed explicit input types, return shapes, empty-case behavior, and warned that simple substring size matching could confuse values such as `L` and `XL` or clothing sizes and shoe sizes.
- *What I changed:* I kept the starter's required empty-list behavior and implemented case-insensitive size matching using standard-size tokens and exact numeric size tokens instead of a plain substring test.

**Moment 2**

- *What I asked for:* I asked AI to help structure the planning loop so the branch and session state would be visible and testable instead of being three unconditional function calls.
- *What came back:* It suggested a small state-machine loop with separate search, outfit, and fit-card steps and an early return when search results are empty.
- *What I changed:* I stored each result in the session before the next step reads it, used `session["selected_item"]` as the input to `suggest_outfit`, and added an actionable empty-search message before returning early.


**Unit 4 — Testing assistance**

- *What I asked for:* Help instrument MCP calls and agent traces, construct five repeatable acceptance scenarios, and inspect real before/after logs against my existing criteria.
- *What came back:* Suggestions to trace tool inputs and outputs, handle an unavailable model with actionable messages, and measure literal title retention as a separate diagnostic.
- *What I changed:* Kept the original acceptance targets, verified the actual tests and errors, changed only the fit-card prompt for the measured improvement, and preserved the full output files for review.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

This is the full baseline captured **before** the one prompt improvement. Original acceptance targets in `criteria.md` were preserved. Every scenario was run five times with cache disabled using `run_eval.py::main`; all agent decisions came from `agent.py::run_agent`. The full unedited evidence, including individual outfit suggestions, fit cards, and step-by-step traces, is in [the baseline report](results/run_2026-10-10_2130_before.md).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |
| 2. Impossible query stops before second tool | 5/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |
| 3. Selected item ID reaches suggest_outfit unchanged | 4/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |
| 4. Fit card has 2–4 sentences, item, price, platform, vibe | 4/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |
| 5. No returned listing exceeds price ceiling | 5/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |

**Representative real output for each criterion** (from the full baseline log, unless noted):

1. **Three-tool run —** `run_eval.py::run_once`, `agent.py::run_agent`: search returned 10 listings, selected `lst_002`, then called `suggest_outfit` and `create_fit_card`. The complete first card was: “Embrace authentic Y2K proportions with this butterfly print baby tee, featuring a fitted, cropped silhouette that balances perfectly with baggy dark-wash jeans. Grab this nostalgic piece on depop for just $18.00 to complete your go-to streetwear look. Pair it with chunky white sneakers and a black crossbody bag for an effortless finish.”
2. **Empty-search branch —** `agent.py::run_agent`: “I couldn't find a matching listing. Try broadening the description, changing the size, or raising the maximum price.” The trace stopped at `empty_search_branch` and did not execute either model tool.
3. **State handoff —** `agent.py::run_agent`: `select_item → stored item id=lst_002`; `suggest_outfit → received new_item id=lst_002`. This pair matched in all five attempts, and the call site passes `session["selected_item"]` directly.
4. **Fit-card details —** `tools.py::create_fit_card`: “Channel major 2000s energy with this Y2K Baby Tee featuring a cute butterfly print. Available now on depop for $18.00, it's the ultimate piece for a retro streetwear look when paired with baggy straight-leg denim and chunky sneakers. Grab it before it's gone!” This is three sentences and includes all four required details.
5. **Price ceiling —** `mcp_client.py::call_tool` invoking `tools.py::search_listings`: independent repeat checks gave `PRICE TRY 1–5: PASS; count=8; highest=USD 20.00; limit=USD 20.00`. These inspect **every returned price**, not merely the selected first item. The checks are reproducible with `python unit4_diagnostics.py`.

The separately required **empty-wardrobe diagnostic** also returned nonempty styling guidance and completed a fit card in all five baseline attempts. It was not counted as a sixth acceptance criterion.

---

## Verdicts and Diagnoses

| # | Target | Verdict | Decision and mechanism |
|---|---|---|---|
| 1 | 4/5 | **MET (5/5)** | All five traces show MCP search, outfit suggestion, and card creation, with no early stop |
| 2 | 5/5 | **MET (5/5)** | All five empty searches stopped in the loop branch before the second tool |
| 3 | 4/5 | **MET (5/5)** | Each trace recorded matching `lst_002` IDs at selection and outfit handoff |
| 4 | 4/5 | **MET (5/5)** | All five cards contained 3 sentences, recognizable butterfly baby tee, $18, Depop, and specific Y2K/streetwear styling |
| 5 | 5/5 | **MET (5/5)** | The tool's per-listing filter and five independent MCP checks confirmed all eight returned prices were at or below $20 |

**Miss diagnosis:** No scored criterion missed its original target. The criteria were limited enough that they did not detect one consistency weakness: in the five baseline runs for criterion 4, the model **paraphrased the selected item's full title in 5/5 cards** instead of preserving the exact string `Y2K Baby Tee — Butterfly Print`. The cause was `tools.py::create_fit_card`'s *prompt wording*: it asked the model to “mention the item” but did not require a verbatim title. This was a measurable weakness in model output, not an MCP or session-state failure. I kept the original criterion and target untouched and selected this as the one improvement.

**Three deliberately triggered failure modes:**

- **Empty search:** impossible `designer ballgown size XXS under $5` query; the loop returned actionable search guidance, no outfit or card; tested 5/5.
- **Empty wardrobe:** `denim jacket under $50` with no saved pieces; `suggest_outfit` generated general advice and card; tested 5/5.
- **Model unavailable:** `unit4_diagnostics.py` set an intentionally invalid key **only inside its own process**, disabled the cache, and invoked a real matching query. The user saw: “Outfit suggestions are temporarily unavailable because the AI model could not be reached. Check your API key and connection, then try again.” The fit card remained `None`. The real `.env` was not changed or committed.

---

## Loop Trace

**Full happy-path trace — real first baseline run**

```text
[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    stored item id=lst_002
[4] suggest_outfit
      in:  dict with keys: item, wardrobe_count
      out: ### Outfit: Y2K Street Denim  * **Top:** Y2K Baby Tee — Butterfly Print * **Bottoms:** Baggy straight-leg jean…
      →    received new_item id=lst_002
[5] create_fit_card
      in:  dict with keys: outfit, item
      out: Embrace authentic Y2K proportions with this butterfly print baby tee, featuring a fitted, cropped silhouette t…
```

**Empty-search trace — real baseline run**

```text
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] empty_search_branch
      out: I couldn't find a matching listing. Try broadening the description, changing the size, or raising the maximum …
      →    stop before suggest_outfit
```

**MCP rewire:** `mcp_server.py` exposes exactly one registered, typed `search_listings` tool, while `agent.py::run_agent` calls it through `mcp_client.call_tool`. `python mcp_client.py` independently listed the tool and its required description / optional size / optional maximum-price inputs. The list-of-dictionaries return behavior stayed consistent; `python test.py` passed 10/10 checks.

---

## The Improvement

**One change only:** Reworded the existing `create_fit_card` prompt in `tools.py` to require the **full, literal listing title, including punctuation, at the start of the first sentence**. No acceptance criteria, datasets, temperature, search algorithm, output filters, or other model prompts were changed.

**Reason:** All five baseline fit-card attempts satisfied criterion 4, but none reproduced the exact title. That inconsistency can make it harder for someone to identify the precise listing. The improvement targets the prompt assumption that “mention the item” would preserve the title.

### Run Log — After

Same five scenarios and original targets, five fresh attempts each, with caching off. Full verbatim outputs and traces are in [the after report](results/run_2026-10-10_2142_after.md).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |
| 2. Impossible query stops before second tool | 5/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |
| 3. Selected item ID reaches suggest_outfit unchanged | 4/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |
| 4. Fit card has 2–4 sentences, item, price, platform, vibe | 4/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |
| 5. No returned listing exceeds price ceiling | 5/5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** |

**Actual after-run output for criterion 4 —** `tools.py::create_fit_card`:

```text
Y2K Baby Tee — Butterfly Print is available now on depop for just $18.00! Channel ultimate turn-of-the-millennium energy by pairing it with baggy dark-wash jeans and chunky white sneakers. It's the sweetest way to elevate your everyday streetwear rotation.
```

**Did it help? Yes, on the targeted secondary measure.**

| Measurement | Before | After |
|---|---:|---:|
| Original acceptance criteria MET | 5/5 | 5/5 |
| Criterion 4 attempts with 2–4 sentences and all required details | 5/5 | 5/5 |
| Criterion 4 attempts beginning with the exact full listing title | **0/5** | **5/5** |

The baseline used 52 model requests including retries; after used 50. Differences in request count do not establish performance improvement because provider rate limits can fluctuate. The measured improvement is title fidelity, not speed or cost.

---

## What's Still Broken

**No original acceptance criterion remains missed.** There are still limits worth tracking: the model provider imposed occasional rate-limit pauses, MCP search starts a server subprocess per tool call, and the five-try scenarios reuse a small number of listing queries rather than proving behavior across a diverse catalog. Also, an exact title is now requested by prompt but is not enforced by a deterministic output validator. A larger future test suite should cover multiple item types, edge-case titles, and explicit output validation.

I stopped after **one prompt change**, as required, so the before/after comparison isolates that one improvement. The original Unit 3 criterion definitions and repository history were preserved.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
