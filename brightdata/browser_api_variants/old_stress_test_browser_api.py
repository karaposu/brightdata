#!/usr/bin/env python3
"""
stress_test_browser_api.py

Run three stress scenarios (10, 25, 50 parallel fetches) against example.com
using NewBrowserAPI with four configs each:

  • noop (cold-start every request)
  • semaphore limited to half the batch size
  • semaphore limited to full batch size
  • pool sized to the batch size

For each sub-test we collect:
  – avg / max latency
  – error rate (and log each exception)
  – delta RSS memory
  – delta open-FD count

Usage:
  python stress_test_browser_api.py
"""
import asyncio
import time
import statistics
import logging
import psutil

from .new_browser_api import NewBrowserAPI

logger = logging.getLogger("stress")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# define our three stress tests:
STRESSES = [
    ("A", 10),
    ("B", 25),
    ("C", 50),
]

async def run_batch(label: str, n: int):
    logger.info("=== Stress %s: %d parallel fetches ===", label, n)
    proc = psutil.Process()
    mem0 = proc.memory_info().rss
    fds0 = proc.num_fds()

    configs = [
        dict(strategy="noop",      max_concurrent=None, pool_size=None),
        dict(strategy="semaphore", max_concurrent=max(n//2,1), pool_size=None),
        dict(strategy="semaphore", max_concurrent=n,          pool_size=None),
        dict(strategy="pool",      max_concurrent=None, pool_size=n),
    ]

    summary = []
    for cfg in configs:
        strat = cfg["strategy"]
        desc = (
            f"{strat}"
            + (f"({cfg['max_concurrent']})" if strat == "semaphore" else "")
            + (f"(pool={cfg['pool_size']})" if strat == "pool" else "")
        )
        logger.info("--- %s ---", desc)

        api = NewBrowserAPI(
            strategy=strat,
            max_concurrent=cfg["max_concurrent"],
            pool_size=cfg["pool_size"] or 0,
        )

        # fire N fetches in parallel
        tasks = [api.fetch_async("https://example.com") for _ in range(n)]
        start = time.time()
        answers = await asyncio.gather(*tasks, return_exceptions=True)
        batch_time = time.time() - start

        latencies = []
        errors = 0
        for idx, ans in enumerate(answers, 1):
            if isinstance(ans, Exception):
                errors += 1
                # Log each error with its context
                logger.error("  [%s #%d] ERROR: %s", desc, idx, ans)
            else:
                html, took = ans
                latencies.append(took)

        avg = statistics.mean(latencies) if latencies else float("nan")
        mx  = max(latencies)        if latencies else float("nan")
        err_rate = errors / n * 100

        logger.info(
            "→ avg latency: %.2fs   max: %.2fs   errors: %d/%d (%.1f%%)",
            avg, mx, errors, n, err_rate
        )
        logger.info("→ wall-clock batch time: %.2fs", batch_time)

        await api.close()
        summary.append((desc, avg, mx, err_rate, batch_time))

    mem1 = proc.memory_info().rss
    fds1 = proc.num_fds()
    logger.info(">>> memory Δ: %.1f MB   fds Δ: %d",
                (mem1 - mem0) / 1e6, fds1 - fds0)

    return summary

async def main():
    all_results = {}
    for label, n in STRESSES:
        try:
            results = await run_batch(label, n)
            all_results[label] = results
        except Exception as e:
            logger.exception("Stress %s FAILED", label)

    # final summary
    print("\n=== SUMMARY ===")
    for label, results in all_results.items():
        print(f"\nStress {label}:")
        for desc, avg, mx, err, batch_time in results:
            print(
                f"  • {desc:20s}  avg={avg:.2f}s  max={mx:.2f}s  "
                f"err={err:.1f}%  total={batch_time:.2f}s"
            )

if __name__ == "__main__":
    asyncio.run(main())
