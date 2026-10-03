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
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
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


<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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
