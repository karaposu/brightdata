# brightdata/catalog.py
import json
def describe_scrapers() -> dict:
    return json.load(open("brightdata/catalog_for_ai_agents.json"))