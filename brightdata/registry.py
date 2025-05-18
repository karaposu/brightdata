# brightdata/registry.py  (patched)
from __future__ import annotations
import importlib
import pkgutil
from functools import lru_cache
from typing import Dict, Type
from urllib.parse import urlparse
import tldextract

_COLLECT_REGISTRY: Dict[str, Type] = {}


# ------------------------------------------------------------------ #
# Decorator (unchanged)
# ------------------------------------------------------------------ #
def register(sld: str):
    def _inner(cls: Type) -> Type:
        _COLLECT_REGISTRY[sld.lower()] = cls
        return cls
    return _inner


def _sld(host: str) -> str:
    return tldextract.extract(host.lower()).domain


# ------------------------------------------------------------------ #
# One-time auto loader
# ------------------------------------------------------------------ #
@lru_cache(maxsize=1)          # run exactly once
def _import_all_scrapers():
    """
    Import every brightdata.ready_scrapers.<module>
    so that their @register() decorators execute.
    """
    import brightdata.ready_scrapers as pkg
    for mod in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        name = mod.name
        if name.endswith(".scraper") or ".scraper." in name:
            importlib.import_module(name)


# ------------------------------------------------------------------ #
# Public helper
# ------------------------------------------------------------------ #
def get_scraper_for(url: str):
    """
    Return the **scraper class** whose second-level domain matches *url*,
    or None if nothing registered.
    """
    _import_all_scrapers()                 # ensure registry is populated
    return _COLLECT_REGISTRY.get(_sld(url))
