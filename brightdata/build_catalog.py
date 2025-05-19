#!/usr/bin/env python
"""
Collect YAML headers from scraper doc-strings ➜ catalog_for_ai_agents.json

Add   --debug   (or set DEBUG=1) to see what the script finds.
"""
from __future__ import annotations
import importlib
import inspect
import json
import os
import pkgutil
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict

import yaml   # pip install pyyaml

# python -m brightdata.build_catalog --debug

DEBUG = ("--debug" in sys.argv) or os.getenv("DEBUG") == "1"

# ──────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────
def dbg(msg: str):
    if DEBUG:
        print("[build_catalog]", msg, file=sys.stderr)


def iterate_scraper_modules() -> list[ModuleType]:
    """
    Walk brightdata.ready_scrapers but **yield only the modules whose fully
    qualified name ends with “.scraper”.
    """
    root = importlib.import_module("brightdata.ready_scrapers")
    mods: list[ModuleType] = []
    seen: set[str] = set()                 # avoid double imports

    for pkg in pkgutil.walk_packages(root.__path__, root.__name__ + "."):
        # keep “…foo.scraper” but skip “…foo.tests”, “…foo.old_scraper”, …
        if not pkg.name.endswith(".scraper"):
            continue
        if pkg.name in seen:
            continue                       # pytest re-imports otherwise
        seen.add(pkg.name)

        dbg(f"importing {pkg.name}")
        mods.append(importlib.import_module(pkg.name))

    return mods


_RX_HEADER = re.compile(r"^---\n(.*?)\n---", re.S)


def yaml_header(obj) -> Dict[str, Any] | None:
    """Return the YAML header (if any) at the very top of *obj*’s doc-string."""
    doc = inspect.getdoc(obj) or ""
    m = _RX_HEADER.match(doc)
    if not m:
        dbg(f"no YAML header in {obj}")
        return None
    try:
        hdr = yaml.safe_load(m.group(1)) or {}
        dbg(f"parsed YAML for {obj}: {hdr}")
        return hdr
    except yaml.YAMLError as e:
        dbg(f"YAML error in {obj}: {e}")
        return None


# ──────────────────────────────────────────────────────────────
def collect_catalog() -> Dict[str, Any]:
    catalog: Dict[str, Any] = {}
    for mod in iterate_scraper_modules():
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            # look for subclasses of BrightdataBaseSpecializedScraper
            if "BrightdataBaseSpecializedScraper" not in (
                base.__name__ for base in cls.__mro__
            ):
                continue

            dbg(f"found scraper class {cls.__module__}.{cls.__name__}")

            head = yaml_header(cls)
            if not head or "agent_id" not in head:
                dbg(f"  ➜ skipped (no YAML header or missing agent_id)")
                continue

            agent_id = head["agent_id"]
            entry: Dict[str, Any] = {
                "title": head.get("title", agent_id),
                "desc": head.get("desc", ""),
                "endpoints": {},
            }

            for meth_name, meth in inspect.getmembers(cls, inspect.isfunction):
                if meth_name.startswith("_"):
                    continue
                m_head = yaml_header(meth)
                if not m_head:
                    dbg(f"    endpoint {meth_name} skipped (no header)")
                    continue
                ep_name = m_head.pop("endpoint", meth_name)
                entry["endpoints"][ep_name] = m_head
                dbg(f"    registered endpoint {ep_name}")

            catalog[agent_id] = entry
            dbg(f"  ✔ added agent '{agent_id}' with {len(entry['endpoints'])} endpoints")

    return catalog


# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    catalog = collect_catalog()

    out_file = Path(__file__).with_name("catalog_for_ai_agents.json")
    out_file.write_text(json.dumps(catalog, indent=2))
    print(f"Wrote {out_file}")

    if DEBUG:
        print("\nSummary:")
        for agent, spec in catalog.items():
            print(f"  {agent:15} – {len(spec['endpoints'])} endpoints")
        if not catalog:
            print("  (catalog is empty – check that your doc-strings contain YAML headers)")
