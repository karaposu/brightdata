# brightdata/utils/thread_poll.py
"""
Thread-based “micro-service” poller for Bright Data snapshots.

Example
-------
from brightdata.utils.thread_poll import PollWorker
from brightdata.ready_scrapers.amazon import AmazonScraper
from dotenv import load_dotenv
import os, json, pathlib

load_dotenv()
scraper = AmazonScraper(bearer_token=os.getenv("BRIGHTDATA_TOKEN"))

snap_id = scraper.collect_by_url(
    ["https://www.amazon.com/dp/B0CRMZHDG8"])          # async → snapshot-id

def on_done(result):                                   # your callback
    if result.status == "ready":
        print("Done:", json.dumps(result.data[:1], indent=2))
    else:
        print("FAILED:", result.status, result.error)

worker = PollWorker(
    scraper       = scraper,
    snapshot_ids  = [snap_id],
    interval      = 15,          # seconds between probes
    timeout       = 600,         # per snapshot
    callback      = on_done      # or output_dir="results/"
)
worker.start()                   # returns immediately
# main thread continues on…
"""

from __future__ import annotations
import json, time, threading, pathlib, queue, os
from typing import List, Callable, Optional
from ..base_specialized_scraper import ScrapeResult, BrightdataBaseSpecializedScraper

class PollWorker(threading.Thread):
    """
    Fire-and-forget poller that watches one *or many* snapshot-IDs in the
    background and pushes the final `ScrapeResult` either to a **callback**
    you supply _or_ saves it to disk inside *output_dir*.

    Only blocking call is the ordinary `requests` GET Bright Data uses
    internally – but that’s inside a daemon thread, so your main code keeps
    running.
    """

    daemon = True          # die automatically when the main program exits

    # ------------------------------------------------------------------ #
    def __init__(
        self,
        scraper: BrightdataBaseSpecializedScraper,
        snapshot_ids: List[str],
        *,
        interval: int = 10,
        timeout:  int = 600,
        callback: Optional[Callable[[ScrapeResult], None]] = None,
        output_dir: Optional[str] = None,
    ):
        super().__init__(name="BD-PollWorker")
        if callback is None and output_dir is None:
            raise ValueError("Provide either callback=… or output_dir=…")

        self.scraper      = scraper
        self.snapshot_ids = list(snapshot_ids)
        self.interval     = max(1, interval)
        self.timeout      = timeout
        self.callback     = callback
        self.output_dir   = pathlib.Path(output_dir) if output_dir else None

        self._queue: "queue.Queue[ScrapeResult]" = queue.Queue()

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    def run(self) -> None:                                    # thread body
        start_time: dict[str, float] = {sid: time.time()
                                        for sid in self.snapshot_ids}

        remaining = set(self.snapshot_ids)

        while remaining:
            now = time.time()

            for sid in list(remaining):                       # copy -> mutate
                # timeout check
                if now - start_time[sid] > self.timeout:
                    res = ScrapeResult(False, "timeout",
                                        error="poll_timeout", data=None)
                    self._handle_result(res, sid)
                    remaining.remove(sid)
                    continue

                res = self.scraper.get_data(sid)              # blocking GET

                if res.status in {"ready", "error"}:
                    self._handle_result(res, sid)
                    remaining.remove(sid)

            time.sleep(self.interval)

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #
    def _handle_result(self, res: ScrapeResult, snapshot_id: str) -> None:
        """
        Route the finished ScrapeResult either to the user’s callback or to disk.
        """
        if self.callback:
            try:
                self.callback(res)            # user callback
            except Exception as exc:          # never crash the worker
                print("[PollWorker] callback raised:", exc)

        if self.output_dir:
            fname = self.output_dir / f"{snapshot_id}.json"
            try:
                with fname.open("w", encoding="utf-8") as fh:
                    json.dump({
                        "snapshot_id": snapshot_id,
                        "status":      res.status,
                        "error":       res.error,
                        "data":        res.data,
                    }, fh, ensure_ascii=False, indent=2)
            except Exception as exc:
                print("[PollWorker] failed to write", fname, "→", exc)
