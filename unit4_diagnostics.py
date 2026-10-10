"""Deliberate Unit 4 failure and deterministic price checks.

Uses a separate process: an intentionally invalid API key does not
alter the real .env file or the user's terminal environment.
"""
from mcp_client import call_tool

LIMIT = 20.0
for attempt in range(1, 6):
    found = call_tool("search_listings", {
        "description": "vintage graphic tee", "size": None, "max_price": LIMIT
    })
    valid = bool(found) and all(float(item["price"]) <= LIMIT for item in found)
    maximum = max((float(item["price"]) for item in found), default=0.0)
    print(f"PRICE TRY {attempt}: {'PASS' if valid else 'FAIL'}; "
          f"count={len(found)}; highest=USD {maximum:.2f}; limit=USD {LIMIT:.2f}")

print()
print("MODEL UNAVAILABLE: deliberate invalid key; real .env unchanged")
import os
os.environ["GEMINI_API_KEY"] = "intentionally_invalid_test_key"
import config
config.CACHE_ENABLED = False
from agent import run_agent
from utils.data_loader import get_example_wardrobe

result = run_agent("vintage graphic tee under $30", get_example_wardrobe())
print("User-facing error:", result["error"])
print("Fit card remains None:", result["fit_card"] is None)
