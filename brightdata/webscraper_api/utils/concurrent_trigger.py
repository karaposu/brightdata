# brightdata/utils/concurrent_trigger.py
from concurrent.futures import ThreadPoolExecutor, as_completed

def trigger_keywords_concurrently(scraper, keywords, max_workers=32):
    """
    Fire discover_by_keyword() for many keywords in parallel.

    Returns dict {keyword: snapshot_id}
    """
    def _single(kw):
        return kw, scraper.discover_by_keyword([kw])

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_single, kw) for kw in keywords]
        for fut in as_completed(futures):
            kw, snap = fut.result()
            results[kw] = snap
    return results
