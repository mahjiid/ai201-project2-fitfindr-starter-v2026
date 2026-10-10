"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import call_tool


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    price_match = re.search(
        r"\b(?:under|below|up to|max(?:imum)?(?: of)?|less than)\s*\$?\s*(\d+(?:\.\d+)?)",
        query,
        flags=re.IGNORECASE,
    )
    size_match = re.search(
        r"\b(?:size|sz)\s*[:=]?\s*([a-z0-9]+(?:[./][a-z0-9]+)?)\b",
        query,
        flags=re.IGNORECASE,
    )

    max_price = float(price_match.group(1)) if price_match else None
    size = size_match.group(1).upper() if size_match else None

    description = query
    if price_match:
        description = description.replace(price_match.group(0), " ")
    if size_match:
        description = description.replace(size_match.group(0), " ")

    description = re.sub(
        r"\b(?:looking for|find me|show me|i want|i need|please)\b",
        " ",
        description,
        flags=re.IGNORECASE,
    )
    words = re.findall(r"[A-Za-z0-9'-]+", description)
    filler = {"a", "an", "the", "for", "me"}
    description = " ".join(word for word in words if word.lower() not in filler).strip()

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }

    trace.step("parse_query", inputs=query, returned=session["parsed"])

    next_step = "search"
    iterations = 0

    while next_step:
        iterations += 1
        trace.check_iterations(iterations)

        if next_step == "search":
            parsed = session["parsed"]
            try:
                session["search_results"] = call_tool(
                    "search_listings",
                    {
                        "description": parsed["description"],
                        "size": parsed["size"],
                        "max_price": parsed["max_price"],
                    },
                )
            except Exception as exc:
                from mcp_client import MCPError
                if not isinstance(exc, MCPError):
                    raise
                session["error"] = (
                    "Listing search is temporarily unavailable. Please retry later "
                    "or check that the MCP server can start."
                )
                trace.step("search_listings (via MCP)", inputs=parsed, returned=str(exc),
                           note="MCP unavailable; stop")
                return session
            trace.step("search_listings (via MCP)", inputs=parsed,
                       returned=session["search_results"])

            if not session["search_results"]:
                session["error"] = (
                    "I couldn't find a matching listing. Try broadening the "
                    "description, changing the size, or raising the maximum price."
                )
                trace.step("empty_search_branch", returned=session["error"], note="stop before suggest_outfit")
                return session

            session["selected_item"] = session["search_results"][0]
            trace.step("select_item", returned=session["selected_item"], note="stored in session")
            next_step = "outfit"
            continue

        if next_step == "outfit":
            try:
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"],
                    session["wardrobe"],
                )
            except ModelUnavailable:
                session["error"] = (
                    "Outfit suggestions are temporarily unavailable because the "
                    "AI model could not be reached. Check your API key and connection, "
                    "then try again."
                )
                trace.step("suggest_outfit", inputs=session["selected_item"],
                           returned=session["error"], note="model unavailable; stop")
                return session
            trace.step("suggest_outfit", inputs={
                "item": session["selected_item"],
                "wardrobe_count": len(session["wardrobe"].get("items", []))
            }, returned=session["outfit_suggestion"])
            next_step = "fit_card"
            continue

        if next_step == "fit_card":
            try:
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"],
                    session["selected_item"],
                )
            except ModelUnavailable:
                session["error"] = (
                    "The outfit was suggested, but the AI fit-card generator is "
                    "unavailable. Check your API key and connection, then retry."
                )
                trace.step("create_fit_card", inputs=session["outfit_suggestion"],
                           returned=session["error"], note="model unavailable; stop")
                return session
            trace.step("create_fit_card", inputs={
                "outfit": session["outfit_suggestion"],
                "item": session["selected_item"],
            }, returned=session["fit_card"])
            next_step = None
            continue

        raise RuntimeError(f"Unknown planning step: {next_step}")

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
