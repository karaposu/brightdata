# brightdata/utils.py  (append near the bottom or any sensible place)

from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Any
import tldextract

from brightdata.models import ScrapeResult


import re, urllib.parse, tldextract

_BD_URL_RE = re.compile(r"[?&]url=([^&]+)")

def _real_domain_from_bd_url(api_url: str) -> str | None:
    """
    If *api_url* is a Bright-Data /progress or /snapshot link that
    embeds the original target, return that domain – else None.
    """
    m = _BD_URL_RE.search(api_url)
    if not m:
        return None

    dec = urllib.parse.unquote(m.group(1))
    ext = tldextract.extract(dec)
    return ext.domain or None


def _make_result_browserapi(                       # ← distinct name
    url: str,
    *,
    success: bool,
    status: str,
    data: Any = None,
    error: str | None = None,
    request_sent_at: datetime | None = None,
    browser_warmed_at: datetime | None = None,
    data_received_at: datetime | None = None,
) -> ScrapeResult:
    """
    Internal helper for BrowserAPI – parallels the `_make_result` helper
    that Bright-Data scrapers use, but lives in utils so we avoid code
    duplication and name clashes.
    """
    ext = tldextract.extract(url)
    
    return ScrapeResult(
        success=success,
        url=url,
        status=status,
        data=data,
        error=error,
        snapshot_id=None,
        cost=None,
        fallback_used=True,
        root_domain=ext.domain or None,
        request_sent_at=request_sent_at,
        browser_warmed_at=browser_warmed_at,
        data_received_at=data_received_at,
        html_char_size=(len(data) if isinstance(data, str) else None),
        event_loop_id=id(asyncio.get_running_loop()),
    )




def show_a_scrape_result_mini(label: str, res: ScrapeResult):
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    status = "✓" if res.success and res.status == "ready" else "✗"
    rows   = len(res.data) if isinstance(res.data, list) else "n/a"
    err    = f" err={res.error}" if res.error else ""
    print(f"{ts}  {label:30s} {status}  rows={rows}{err}")

def show_a_scrape_result(label: str, res: ScrapeResult) -> None:
    """
    Pretty-print one ScrapeResult with readable alignment:

    • snapshot_id is trimmed to 12 chars
    • snapshot_polled_at shows count + first/last timestamps
    • “–” for any missing field
    """
    def _fmt(ts):
        return ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "–"

    # rows = len(res.data) if isinstance(res.data, list) else "n/a"
    
    # how many keys in a row
    if isinstance(res.data, list) and res.data and isinstance(res.data[0], dict):
        total_keys = len(res.data[0])
    else:
        total_keys = "–"
    


    polls = res.snapshot_polled_at or []
    polls_info = (
        f"{len(polls)}×  [{_fmt(polls[0])} … {_fmt(polls[-1])}]"
        if polls else "–"
    )
    # cost = f"{res.cost:.2f}$" if res.cost is not None else "–"
    # cost = f"{res.cost}$" if res.cost is not None else "–"
    cost = f"{res.cost:.6f}$" if res.cost is not None else "–"

    
    sid  = (res.snapshot_id or "–")[:12] + ("…" if res.snapshot_id and len(res.snapshot_id) > 12 else "")
    
    print(f"\n{label}")
    print("─" * len(label))
    print(f"{'success':25s}: {res.success}")
    print(f"{'row_count':25s}: {res.row_count}")
    print(f"{'field_count':25s}: {res.field_count}")
    print(f"{'snapshot_id':25s}: {sid}")
    print(f"{'cost':25s}: {cost}")
    print(f"{'html_char_size':25s}: {res.html_char_size or '–'}")
    if res.browser_warmed_at:
        print(f"{'browser_warmed_at':25s}: {_fmt(res.browser_warmed_at)}")
    print(f"{'request_sent_at':25s}: {_fmt(res.request_sent_at)}")
    print(f"{'snapshot_id_received_at':25s}: {_fmt(res.snapshot_id_received_at)}")
    print(f"{'snapshot_polled_at':25s}: {polls_info}")
    print(f"{'data_received_at':25s}: {_fmt(res.data_received_at)}\n")
    if res.error:                                   # ← new line
        print(f"{'error':25s}: {res.error}")
    print()  # trailing newline


# def show_a_scrape_result(label: str, res: ScrapeResult) -> None:
#     """
#     Print one line with the raw ScrapeResult fields in the order requested:
#     success • data_rows • snapshot_id • cost • request_sent_at
#     snapshot_id_received_at • snapshot_polled_at • data_received_at
#     """
#     rows = len(res.data) if isinstance(res.data, list) else "n/a"

#     print(
#         f"{label:30s} "
#         f"success={res.success} "
#         f"data_rows={rows} "
#         f"snapshot_id={res.snapshot_id or '–'} "
#         f"cost={res.cost if res.cost is not None else '–'} "
#         f"request_sent_at={res.request_sent_at or '–'} "
#         f"snapshot_id_received_at={res.snapshot_id_received_at or '–'} "
#         f"snapshot_polled_at={res.snapshot_polled_at or '–'} "
#         f"data_received_at={res.data_received_at or '–'}"
#     )




def show_scrape_results(label: str, res_or_dict, miniform=False):
    """Pretty print ScrapeResult or {bucket: ScrapeResult}."""
    if isinstance(res_or_dict, ScrapeResult):
        show_a_scrape_result(label, res_or_dict)
    else:                      # multi-bucket dict
        for bucket, sub in res_or_dict.items():
            if miniform:
                show_a_scrape_result_mini(f"{label}/{bucket}", sub)
            else:
                 show_a_scrape_result(f"{label}/{bucket}", sub)